from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
import json

from ..core.db import get_db
from ..core.redis import get_redis
from ..models.models import ReadingSession, ReadingEvent, User
from ..schemas.schemas import SessionStartRequest, SessionStartResponse, SessionFinishRequest, SessionFinishResponse, EventsRequestModel
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
        
        from ..agents.stubs.qa_evaluation_stub import evaluate_quiz_stub
        from ..agents.content_reducer.quiz_generator import generate_quiz
        
        quiz = generate_quiz("chunk_result_test", "AI 리터러시 메타인지 핵심 내용입니다.")
        initial_state["quiz_result"] = evaluate_quiz_stub(session_id, quiz)
        
        final_state = run_reading_session(initial_state)
        return to_session_result(final_state)
    finally:
        await redis_client.aclose()
