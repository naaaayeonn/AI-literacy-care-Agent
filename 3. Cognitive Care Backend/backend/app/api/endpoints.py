from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
import json

from ..core.db import get_db
from ..core.redis import get_redis
from ..models.models import ReadingSession, ReadingEvent, User
from ..schemas.schemas import (
    SessionStartRequest, SessionStartResponse, SessionFinishRequest, SessionFinishResponse, EventsRequestModel,
    QuizSubmitRequest, QuizSubmitResponse, TermExplainRequest, TermExplainResponse
)
from ..orchestrator.state import create_initial_state
from ..orchestrator.graph import run_reading_session
from .frontend_contract import to_intervention_command, to_session_result
from ..services.cognitive_care import calculate_focus_score, determine_intervention

router = APIRouter(prefix="/api/session", tags=["Sessions"])

@router.post("/start", response_model=SessionStartResponse)
async def start_session(req: SessionStartRequest, request: Request, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.exc import IntegrityError
    user_result = await db.execute(select(User).filter(User.id == req.userId))
    user = user_result.scalars().first()
    if not user:
        new_user = User(id=req.userId)
        db.add(new_user)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()

    session_id = f"s_{uuid.uuid4().hex[:8]}"
    document_id = req.articleId or "doc"
    
    new_session = ReadingSession(
        id=session_id,
        user_id=req.userId,
        document_id=document_id
    )
    db.add(new_session)
    await db.commit()
    
    host = request.headers.get("host", "localhost:8000")
    ws_endpoint = f"ws://{host}/ws/reading/{session_id}"
    
    # 2번 연동 (실제 Content Reducer 에이전트 적용)
    from ..agents.content_reducer.agent import run_content_reducer
    
    if req.content:
        mock_raw_text = "\n\n".join(req.content)
    else:
        mock_raw_text = "AI 기술이 발전함에 따라 우리의 삶은 크게 변화하고 있습니다. 특히 문해력이 중요한 시대가 되었습니다. 다양한 정보를 비판적으로 수용하고 활용하는 능력이 필수적입니다. 인공지능이 제공하는 정보를 그대로 믿기보다는 스스로 생각하고 판단하는 힘을 길러야 합니다."
    
    state = create_initial_state(session_id=session_id, user_id=req.userId, document_id=document_id, raw_text=mock_raw_text)
    updated_state = run_content_reducer(state)
    
    def map_term(t):
        return {"term": t["term"], "definition": t["definition"], "source": t["source"], "faithfulnessScore": t.get("faithfulness_score", 1.0), "chunkId": t["chunk_id"]}

    def map_chunk(c):
        return {
            "chunkId": c["chunk_id"], "originalText": c["original_text"],
            "restructuredText": c.get("restructured_text", ""), "difficulty": c["difficulty"],
            "charStart": c["char_start"], "charEnd": c["char_end"],
            "terms": [map_term(t) for t in c.get("terms", [])]
        }
        
        
    article_data = {
        "id": document_id,
        "title": "AI 리터러시 데모 아티클 (2번 연동)",
        "category": "Technology",
        "author": "AI Care System",
        "content": [c["original_text"] for c in updated_state.get("chunks", [])],
        "difficulty": str(updated_state.get("difficulty_score", 50.0)),
        "chunks": [map_chunk(c) for c in updated_state.get("chunks", [])]
    }
    
    return SessionStartResponse(
        sessionId=session_id, 
        article=article_data,
        wsEndpoint=ws_endpoint
    )

@router.post("/{session_id}/events")
async def process_events(session_id: str, req: EventsRequestModel):
    redis_client = await get_redis()
    try:
        redis_key = f"session:{session_id}:events"
        for ev in req.events:
            await redis_client.rpush(redis_key, ev.model_dump_json())
            
        all_events_raw = await redis_client.lrange(redis_key, 0, -1)
        reading_events = []
        for raw in all_events_raw:
            data = json.loads(raw)
            reading_events.append({
                "type": data["type"],
                "timestamp_ms": data["timestamp_ms"],
                "position": data.get("position"),
                "duration_ms": data.get("duration_ms"),
                "metadata": data
            })

        focus_score = calculate_focus_score(reading_events)
        intervention_needed, intervention_level, msg = determine_intervention(focus_score)
        
        level_to_type = {"none": "none", "soft": "highlight", "medium": "nudge", "hard": "quiz"}
        internal_type = level_to_type.get(intervention_level, "none")
        
        state = create_initial_state(session_id=session_id, user_id="", document_id="", raw_text="")
        state["reading_events"] = reading_events
        state["focus_score"] = focus_score
        state["intervention"] = {
            "level": intervention_level,
            "type": internal_type,
            "message": msg
        }
        
        return to_intervention_command(state)
    finally:
        await redis_client.aclose()

@router.post("/{session_id}/finish", response_model=SessionFinishResponse)
async def finish_session(
    session_id: str, 
    req: SessionFinishRequest, 
    db: AsyncSession = Depends(get_db),
):
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
                "position": event_dict.get("position"),
                "duration_ms": event_dict.get("duration_ms"),
                "metadata": event_dict
            })
            
        # 3. 오케스트레이터(Role 1) 파이프라인 실행
        initial_state = create_initial_state(
            session_id=session_id,
            user_id=session.user_id,
            document_id=session.document_id,
            raw_text="Sample Document Text"
        )
        initial_state["reading_events"] = state_events
        final_state = run_reading_session(initial_state)

        # 4. 세션 정보 업데이트
        session.literacy_score = final_state.get("literacy_score", req.literacy_score)
        session.comprehension_score = final_state.get("score_breakdown", {}).get("comprehension_score", req.comprehension_score)
        session.engagement_score = final_state.get("score_breakdown", {}).get("engagement_score", req.engagement_score)
        
        await db.commit()
        await redis_client.delete(redis_key)
        
        return SessionFinishResponse(
            session_id=session_id, 
            message="Session finished and flushed to PostgreSQL.",
            saved_events_count=saved_count
        )
    finally:
        await redis_client.aclose()

@router.get("/{session_id}/result")
async def get_session_result(session_id: str, db: AsyncSession = Depends(get_db)):
    redis_client = await get_redis()
    try:
        # DB 세션 조회
        result = await db.execute(select(ReadingSession).filter(ReadingSession.id == session_id))
        session = result.scalars().first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
            
        # Redis에서 먼저 가져오기 (M4 fallback)
        redis_key = f"session:{session_id}:events"
        all_events_raw = await redis_client.lrange(redis_key, 0, -1)
        
        state_events = []
        if all_events_raw:
            for raw in all_events_raw:
                data = json.loads(raw)
                state_events.append({
                    "type": data["type"],
                    "timestamp_ms": data["timestamp_ms"],
                    "position": data.get("position"),
                    "duration_ms": data.get("duration_ms"),
                    "metadata": data
                })
                db.add(ReadingEvent(
                    session_id=session_id,
                    event_type=data["type"],
                    timestamp_ms=data["timestamp_ms"],
                    metadata_json=data
                ))
            # Redis에 있던 걸 DB에 넣었으니 Flush 처리
            await db.commit()
            await redis_client.delete(redis_key)
        else:
            # Redis에 없으면 DB에서 조회
            events_result = await db.execute(select(ReadingEvent).filter(ReadingEvent.session_id == session_id))
            events = events_result.scalars().all()
            for ev in events:
                state_events.append({
                    "type": ev.event_type,
                    "timestamp_ms": ev.timestamp_ms,
                    "position": ev.metadata_json.get("position"),
                    "duration_ms": ev.metadata_json.get("duration_ms"),
                    "metadata": ev.metadata_json
                })

        initial_state = create_initial_state(
            session_id=session_id,
            user_id=session.user_id,
            document_id=session.document_id,
            raw_text=""
        )
        initial_state["reading_events"] = state_events
        
        # Q1/Q2: Redis에서 실제 퀴즈 채점 결과 읽기 (stub 제거)
        quiz_key = f"session:{session_id}:quiz_result"
        quiz_raw = await redis_client.get(quiz_key)
        if quiz_raw:
            quiz_data = json.loads(quiz_raw)
            initial_state["quiz_result"] = {
                "correct_count": quiz_data.get("correct_count", 0),
                "total_count":   quiz_data.get("total_count", 0),
                "answers":       quiz_data.get("answers", [])
            }
        else:
            # 퀴즈를 아예 안 풀었을 때 기본값 (점수 반영 안 됨)
            initial_state["quiz_result"] = {"correct_count": 0, "total_count": 0}

        # Q4: 5번 QA 품질 게이트 (실패해도 세션 유지)
        try:
            from backend.evaluation.evaluation_pipeline import run_evaluation_from_state
            initial_state["qa_evaluation"] = run_evaluation_from_state(initial_state)
        except Exception as _qa_err:
            # state의 errors는 list 규약이므로 append로 기록(과거 dict 인덱싱은 TypeError 유발)
            initial_state.setdefault("errors", []).append({"step": "qa_evaluation", "error": str(_qa_err)})

        final_state = run_reading_session(initial_state)
        return to_session_result(final_state)
    finally:
        await redis_client.aclose()

@router.post("/{session_id}/quiz/submit", response_model=QuizSubmitResponse)
async def submit_quiz(
    session_id: str,
    req: QuizSubmitRequest,
    db: AsyncSession = Depends(get_db),
):
    """퀴즈 답안 제출 및 채점 — Q1/Q3: 실제 정답키 기준 채점 후 Redis 누적 저장."""
    # 세션 존재 확인
    result = await db.execute(select(ReadingSession).filter(ReadingSession.id == session_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Q3: generate_quiz correct_option 기준으로 채점
    # req.quizCorrectOption (1-indexed) 이 없으면 일반 텍스트 비교 폴백
    is_correct = False
    if hasattr(req, 'correctOption') and req.correctOption is not None:
        # 프론트가 correct_option(1~4 인덱스)을 같이 보낸 경우
        is_correct = (req.selectedOption == req.correctOption)
    elif hasattr(req, 'selectedIndex') and hasattr(req, 'correctIndex'):
        is_correct = (req.selectedIndex == req.correctIndex)
    else:
        # 폴백: 선택지 텍스트 직접 비교 (프론트 계약 구버전 호환)
        is_correct = str(req.selectedOption).strip() == str(getattr(req, 'correctAnswer', '')).strip()

    explanation = "정답입니다! 잘 이해하고 있어요." if is_correct else "아쉽지만 틀렸어요. 다시 한번 읽어보세요."

    # Q1: 채점 결과를 Redis에 누적 저장 (session:{id}:quiz_result)
    redis_client = await get_redis()
    try:
        quiz_key = f"session:{session_id}:quiz_result"
        existing_raw = await redis_client.get(quiz_key)
        if existing_raw:
            existing = json.loads(existing_raw)
        else:
            existing = {"correct_count": 0, "total_count": 0, "answers": []}

        existing["total_count"] += 1
        if is_correct:
            existing["correct_count"] += 1
        existing["answers"].append({
            "quiz_id":  req.quizId,
            "selected": req.selectedOption,
            "correct":  is_correct
        })
        await redis_client.set(quiz_key, json.dumps(existing), ex=86400)  # 24h TTL
    finally:
        await redis_client.aclose()

    return QuizSubmitResponse(
        correct=is_correct,
        explanation=explanation,
        quiz_id=req.quizId,
    )

@router.post("/{session_id}/explain", response_model=TermExplainResponse)
async def explain_term(
    session_id: str,
    req: TermExplainRequest,
    db: AsyncSession = Depends(get_db),
):
    """용어 설명 API - RAG 스텁 (7/5 구현). 2번 Content Reducer 연동용."""
    # 세션 존재 확인
    result = await db.execute(select(ReadingSession).filter(ReadingSession.id == session_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # RAG 스텁: 시나리오용 고정 용어 사전
    term_dict = {
        "리터러시": "리터러시(Literacy)는 글을 읽고 이해하며 활용하는 능력을 뜻합니다. 디지털 시대에는 정보를 비판적으로 분석하는 능력까지 포함합니다.",
        "LLM": "LLM(Large Language Model)은 대규모 텍스트 데이터로 학습된 인공지능 언어 모델입니다. GPT, Claude 등이 대표적인 예시입니다.",
        "환각": "AI 환각(Hallucination)은 AI 모델이 사실이 아닌 정보를 마치 사실인 것처럼 생성하는 현상을 말합니다.",
        "편향": "편향(Bias)은 데이터나 알고리즘에 내재된 불공정한 경향성을 의미합니다. AI 시스템의 공정성에 큰 영향을 미칩니다.",
        "윤리": "AI 윤리는 인공지능 기술의 개발과 활용 과정에서 지켜야 할 도덕적 원칙과 가이드라인을 말합니다.",
        "Literacy Score": "Literacy Score는 사용자의 읽기 이해도, 집중도, 난이도 보정을 종합한 0~100 사이의 문해력 점수입니다.",
    }
    
    term = req.term.strip()
    explanation = term_dict.get(
        term,
        f"'{term}'은(는) 이 글에서 중요한 개념입니다. AI가 맥락을 분석하여 쉬운 설명을 제공합니다. (RAG 연동 예정)"
    )
    
    return TermExplainResponse(explanation=explanation)

@router.post("/reset")
async def reset_demo_data(db: AsyncSession = Depends(get_db)):
    """전체 데이터베이스 및 Redis 세션 데이터를 완전 초기화하여 시연 리허설 반복 실행을 보장함 (7/13, 7/14)"""
    from sqlalchemy import delete
    from ..models.models import ReadingEvent, ReadingSession, User, LiteracyProfile, QuizResult
    
    redis_client = await get_redis()
    
    try:
        # 1. DB 모든 레코드 삭제
        await db.execute(delete(QuizResult))
        await db.execute(delete(ReadingEvent))
        await db.execute(delete(ReadingSession))
        await db.execute(delete(LiteracyProfile))
        await db.execute(delete(User))
        await db.commit()
        
        # 2. Redis 세션 캐시 버퍼 제거
        # Redis 내의 모든 키를 탐색하여 삭제
        # InMemoryRedisClient의 경우 store를 직접 비워줌
        if hasattr(redis_client, "store"):
            redis_client.store.clear()
        else:
            # 실제 Redis일 경우 keys 조회 및 삭제
            keys = await redis_client.keys("session:*:events")
            for k in keys:
                await redis_client.delete(k)
                
        print("[Reset] Database and Redis cache successfully cleared for demo rehearsal.")
        return {"status": "success", "message": "Demo data successfully reset."}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database reset failed: {str(e)}")
    finally:
        await redis_client.aclose()
