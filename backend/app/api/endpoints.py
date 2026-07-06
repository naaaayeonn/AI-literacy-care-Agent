from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
import json

from ..core.db import get_db
from ..core.redis import get_redis
from ..models.models import ReadingSession, ReadingEvent, User
from ..schemas.schemas import SessionStartRequest, SessionStartResponse, SessionFinishRequest, SessionFinishResponse
from ..orchestrator.state import create_initial_state
from ..orchestrator.graph import run_reading_session
from .frontend_contract import to_session_result

router = APIRouter(prefix="/api/session", tags=["Sessions"])

@router.post("/start", response_model=SessionStartResponse)
async def start_session(req: SessionStartRequest, request: Request, db: AsyncSession = Depends(get_db)):
    user_result = await db.execute(select(User).filter(User.id == req.userId))
    user = user_result.scalars().first()
    if not user:
        new_user = User(id=req.userId)
        db.add(new_user)
        await db.commit()

    session_id = f"s_{uuid.uuid4().hex[:8]}"
    
    new_session = ReadingSession(
        id=session_id,
        user_id=req.userId,
        document_id=req.articleId
    )
    db.add(new_session)
    await db.commit()
    
    host = request.headers.get("host", "localhost:8000")
    ws_endpoint = f"ws://{host}/ws/reading/{session_id}"
    
    # 2번 연동 (실제 Content Reducer 에이전트 적용)
    from ..agents.content_reducer.agent import run_content_reducer
    
    mock_raw_text = "AI 기술이 발전함에 따라 우리의 삶은 크게 변화하고 있습니다. 특히 문해력이 중요한 시대가 되었습니다. 다양한 정보를 비판적으로 수용하고 활용하는 능력이 필수적입니다. 인공지능이 제공하는 정보를 그대로 믿기보다는 스스로 생각하고 판단하는 힘을 길러야 합니다."
    
    state = create_initial_state(session_id=session_id, user_id=req.userId, document_id=req.articleId, raw_text=mock_raw_text)
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
        "id": req.articleId,
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

@router.post("/{session_id}/finish", response_model=SessionFinishResponse)
async def finish_session(
    session_id: str, 
    req: SessionFinishRequest, 
    db: AsyncSession = Depends(get_db),
):
    from ..core.redis import REDIS_URL
    import redis.asyncio as redis
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    
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
        session.comprehension_score = final_state.get("comprehension_score", req.comprehension_score)
        session.engagement_score = final_state.get("engagement_score", req.engagement_score)
        
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
    # DB 세션 조회
    result = await db.execute(select(ReadingSession).filter(ReadingSession.id == session_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # ReadingEvent 조회 (DB에 Flush 되었다고 가정)
    events_result = await db.execute(select(ReadingEvent).filter(ReadingEvent.session_id == session_id))
    events = events_result.scalars().all()
    
    state_events = []
    for ev in events:
        state_events.append({
            "type": ev.event_type,
            "timestamp_ms": ev.timestamp_ms,
            "metadata": ev.metadata_json,
            "position": ev.metadata_json.get("position"),
            "duration_ms": ev.metadata_json.get("duration_ms")
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
    
    # 5번 목업 연결점 (나중에 실제 모듈로 교체)
    # 퀴즈 생성을 위해 임의의 데모 컨텍스트를 넘겨준다.
    quiz = generate_quiz("chunk_result_test", "AI 리터러시 메타인지 핵심 내용입니다.")
    initial_state["quiz_result"] = evaluate_quiz_stub(session_id, quiz)
    
    final_state = run_reading_session(initial_state)
    return to_session_result(final_state)
