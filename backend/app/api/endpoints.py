from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func as sql_func, desc
import uuid
import json
from datetime import datetime, timezone

from ..core.db import get_db
from ..core.redis import get_redis
from ..models.models import ReadingSession, ReadingEvent, User, QuizResult, LiteracyProfile
from ..schemas.schemas import (
    SessionStartRequest, SessionStartResponse,
    SessionFinishRequest, SessionFinishResponse,
    QuizSubmitRequest, QuizSubmitResponse,
    SessionResultResponse, ScoreSeriesItem, BadgeItem,
    TermExplainRequest, TermExplainResponse,
    ProfileResponse,
    AnalyticsSummaryResponse,
)
from ..orchestrator.state import create_initial_state
from ..orchestrator.graph import run_reading_session
from ..services.reward_service import calculate_xp, get_level_for_xp, check_level_up, check_badges
from ..services.profile_service import update_profile_on_session_complete, get_profile

router = APIRouter(prefix="/api", tags=["API"])

# ==============================
# Session Endpoints (6/20~6/22)
# ==============================

@router.post("/session/start", response_model=SessionStartResponse)
async def start_session(req: SessionStartRequest, db: AsyncSession = Depends(get_db)):
    """읽기 세션 시작."""
    # 사용자 자동 생성 (없으면)
    user_result = await db.execute(select(User).filter(User.id == req.user_id))
    user = user_result.scalars().first()
    if not user:
        new_user = User(id=req.user_id)
        db.add(new_user)
        await db.commit()

    session_id = f"s_{uuid.uuid4().hex[:8]}"
    
    new_session = ReadingSession(
        id=session_id,
        user_id=req.user_id,
        document_id=req.document_id
    )
    db.add(new_session)
    await db.commit()
    
    return SessionStartResponse(session_id=session_id, message="Session started successfully.")


@router.post("/session/{session_id}/finish", response_model=SessionFinishResponse)
async def finish_session(
    session_id: str, 
    req: SessionFinishRequest, 
    db: AsyncSession = Depends(get_db),
):
    """세션 종료 + Redis 이벤트 PostgreSQL 벌크 저장 + Orchestrator 실행."""
    from ..core.redis import get_redis
    redis_client = await get_redis()
    
    try:
        # 1. DB에서 세션 조회
        result = await db.execute(select(ReadingSession).filter(ReadingSession.id == session_id))
        session = result.scalars().first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
            
        # 2. Redis에서 이벤트 가져오기
        redis_key = f"session:{session_id}:events"
        all_events_raw = await redis_client.lrange(redis_key, 0, -1)
        
        saved_count = 0
        state_events = []
        for raw_event in all_events_raw:
            event_dict = json.loads(raw_event)
            new_event = ReadingEvent(
                session_id=session_id,
                event_type=event_dict.get("type", "unknown"),
                timestamp_ms=event_dict.get("timestamp_ms", 0),
                metadata_json=event_dict
            )
            db.add(new_event)
            saved_count += 1
            
            state_events.append({
                "type": event_dict.get("type", "unknown"),
                "timestamp_ms": event_dict.get("timestamp_ms", 0),
                "metadata": event_dict
            })
            
        # 3. Orchestrator(Role 1) 실행
        initial_state = create_initial_state(
            session_id=session_id,
            user_id=session.user_id,
            document_id=session.document_id,
            raw_text="Sample Document Text"
        )
        initial_state["reading_events"] = state_events
        final_state = run_reading_session(initial_state)

        # 4. 세션 업데이트
        session.literacy_score = final_state.get("literacy_score", req.literacy_score)
        session.comprehension_score = final_state.get("comprehension_score", req.comprehension_score)
        session.engagement_score = final_state.get("engagement_score", req.engagement_score)
        session.finished_at = datetime.now(timezone.utc)
        
        # 5. XP 계산 및 프로필 업데이트
        xp_earned = final_state.get("reward", {}).get("xp", 0)
        session.xp_earned = xp_earned
        
        await update_profile_on_session_complete(
            db=db,
            user_id=session.user_id,
            session_literacy_score=session.literacy_score or 0,
            session_comprehension=session.comprehension_score or 0,
            session_engagement=session.engagement_score or 0,
            xp_earned=xp_earned,
        )
        
        await db.commit()
        
        # 6. Redis 캐시 정리
        await redis_client.delete(redis_key)
        
        return SessionFinishResponse(
            session_id=session_id, 
            message="Session finished and flushed to PostgreSQL.",
            saved_events_count=saved_count
        )
    finally:
        await redis_client.aclose()


# ==============================
# Quiz Endpoints (6/25)
# ==============================

@router.post("/session/{session_id}/quiz/submit", response_model=QuizSubmitResponse)
async def submit_quiz(
    session_id: str,
    req: QuizSubmitRequest,
    db: AsyncSession = Depends(get_db),
):
    """퀴즈 답안 제출 및 채점 (6/25 구현)."""
    # 세션 존재 확인
    result = await db.execute(select(ReadingSession).filter(ReadingSession.id == session_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 간단한 채점 로직 (실제로는 정답 DB와 비교)
    # 현재 스텁: 선택지에 따라 간단 판정
    is_correct = req.selectedOption in ["A", "a", "1", "true", "True"]
    
    quiz_record = QuizResult(
        session_id=session_id,
        quiz_id=req.quizId,
        selected_option=req.selectedOption,
        is_correct=is_correct,
    )
    db.add(quiz_record)
    await db.commit()
    
    explanation = "정답입니다! 잘 이해하고 있어요." if is_correct else "아쉽지만 틀렸어요. 다시 한번 읽어보세요."
    
    return QuizSubmitResponse(
        correct=is_correct,
        explanation=explanation,
        quiz_id=req.quizId,
    )


# ==============================
# Session Result (6/26)
# ==============================

@router.get("/session/{session_id}/result", response_model=SessionResultResponse)
async def get_session_result(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """세션 결과 조회 - Literacy Score + 시계열 데이터 (6/26 구현)."""
    result = await db.execute(select(ReadingSession).filter(ReadingSession.id == session_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 프로필 조회
    profile_data = await get_profile(db, session.user_id)
    total_xp = profile_data["total_xp"] if profile_data else 0
    level = profile_data["current_level"] if profile_data else 1
    total_sessions = profile_data["total_sessions"] if profile_data else 1
    
    # XP 계산
    xp_earned = session.xp_earned or calculate_xp(literacy_score=session.literacy_score or 0)
    
    # 시계열 데이터 - 최근 세션들의 점수 추이
    recent_result = await db.execute(
        select(ReadingSession)
        .filter(ReadingSession.user_id == session.user_id)
        .filter(ReadingSession.literacy_score.isnot(None))
        .order_by(desc(ReadingSession.created_at))
        .limit(7)
    )
    recent_sessions = list(reversed(recent_result.scalars().all()))
    
    score_series = []
    for i, s in enumerate(recent_sessions):
        label = f"{i+1}회" if i < len(recent_sessions) - 1 else "이번"
        score_series.append(ScoreSeriesItem(
            label=label,
            before=s.comprehension_score or 50,
            after=s.literacy_score or 50,
        ))
    
    if not score_series:
        score_series = [
            ScoreSeriesItem(label="이번", before=50, after=session.literacy_score or 50)
        ]
    
    # 배지 체크
    new_badges = check_badges(
        total_sessions=total_sessions,
        literacy_score=session.literacy_score or 0,
        engagement_score=session.engagement_score or 0,
    )
    badges = [
        BadgeItem(
            id=b["id"],
            name=b["name"],
            emoji=b["emoji"],
            description=b["description"],
            acquiredAt=datetime.now(timezone.utc).isoformat(),
        )
        for b in new_badges
    ]
    
    # 세션 시간 계산
    duration_ms = 0
    if session.finished_at and session.created_at:
        delta = session.finished_at - session.created_at
        duration_ms = int(delta.total_seconds() * 1000)
    
    return SessionResultResponse(
        sessionId=session_id,
        literacyScore=round(session.literacy_score or 0, 1),
        comprehensionScore=round(session.comprehension_score or 0, 1),
        engagementScore=round(session.engagement_score or 0, 1),
        difficultyBonus=round((session.difficulty_score or 50) * 0.15, 1),
        completionRate=100.0,
        xpEarned=xp_earned,
        totalXp=total_xp,
        level=level,
        scoreSeries=score_series,
        badges=badges,
        sessionDurationMs=duration_ms,
    )


# ==============================
# Term Explanation / RAG Stub (7/5)
# ==============================

@router.post("/session/{session_id}/explain", response_model=TermExplainResponse)
async def explain_term(
    session_id: str,
    req: TermExplainRequest,
    db: AsyncSession = Depends(get_db),
):
    """용어 설명 API - Strict RAG 및 Fallback 구현 (7/7~7/9 M3)"""
    # 세션 존재 확인
    result = await db.execute(select(ReadingSession).filter(ReadingSession.id == session_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    from ..services.rag_service import explain_term_with_rag
    
    # 세션에 기록된 실제 원문을 문맥으로 활용할 수 있도록 전달
    # (여기서는 기본 샘플 텍스트를 문맥으로 결합합니다)
    sample_raw_text = (
        "디지털 시대의 필수 역량은 리터러시(Literacy)와 인공지능 윤리입니다. "
        "최근 LLM 기술의 급격한 발전으로 인해 AI 환각 현상이나 알고리즘의 편향 문제가 사회적 이슈로 대두되고 있습니다. "
        "이러한 문제를 해결하기 위해 다양한 AI 정렬 연구와 편향 제어 기술이 개발되고 있습니다."
    )
    
    explanation = await explain_term_with_rag(
        term=req.term,
        raw_text=sample_raw_text
    )
    
    return TermExplainResponse(explanation=explanation)


# ==============================
# Profile (6/30)
# ==============================

@router.get("/profile/{user_id}", response_model=ProfileResponse)
async def get_user_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """사용자 장기 리터러시 프로필 조회 (6/30 구현)."""
    profile_data = await get_profile(db, user_id)
    if not profile_data:
        # 프로필이 없으면 기본값 반환
        return ProfileResponse(
            user_id=user_id,
            total_sessions=0,
            avg_literacy_score=0.0,
            current_level=1,
            total_xp=0,
            trend="stable",
        )
    return ProfileResponse(**profile_data)


# ==============================
# Analytics Summary (7/1)
# ==============================

@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """성장 보고서/통계 집계 API (7/1 구현)."""
    # 프로필 조회
    profile_data = await get_profile(db, user_id)
    
    # 최근 세션들 조회
    recent_result = await db.execute(
        select(ReadingSession)
        .filter(ReadingSession.user_id == user_id)
        .filter(ReadingSession.literacy_score.isnot(None))
        .order_by(desc(ReadingSession.created_at))
        .limit(10)
    )
    recent_sessions_raw = list(reversed(recent_result.scalars().all()))
    
    # 시계열 데이터
    score_trend = []
    for i, s in enumerate(recent_sessions_raw):
        score_trend.append(ScoreSeriesItem(
            label=f"{i+1}회",
            before=s.comprehension_score or 50,
            after=s.literacy_score or 50,
        ))
    
    # 최근 세션 요약 (최대 5개)
    recent_sessions = []
    for s in recent_sessions_raw[-5:]:
        recent_sessions.append({
            "session_id": s.id,
            "document_id": s.document_id,
            "literacy_score": s.literacy_score,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "duration_seconds": s.duration_seconds,
        })
    
    # 총 읽기 시간 (분)
    total_time_result = await db.execute(
        select(sql_func.sum(ReadingSession.duration_seconds))
        .filter(ReadingSession.user_id == user_id)
    )
    total_seconds = total_time_result.scalar() or 0
    
    return AnalyticsSummaryResponse(
        user_id=user_id,
        total_sessions=profile_data["total_sessions"] if profile_data else 0,
        total_reading_time_minutes=round(total_seconds / 60, 1),
        avg_literacy_score=profile_data["avg_literacy_score"] if profile_data else 0.0,
        score_trend=score_trend,
        recent_sessions=recent_sessions,
        level=profile_data["current_level"] if profile_data else 1,
        total_xp=profile_data["total_xp"] if profile_data else 0,
    )
