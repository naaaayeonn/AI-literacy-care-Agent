from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
import re
import json

from ..core.db import get_db
from ..core.redis import get_redis
from ..models.models import ReadingSession, ReadingEvent, User
from ..orchestrator.state import create_initial_state
from ..orchestrator.graph import run_reading_session
from .frontend_contract import to_intervention_command, to_session_result
from ..services.cognitive_care import calculate_focus_score, determine_intervention
from ..agents.content_reducer.agent import run_content_reducer

router = APIRouter(prefix="/api/extension_session", tags=["Extension Sessions"])

# -----------------
# 1. Models
# -----------------
class SessionStartRequestModel(BaseModel):
    userId: str | None = Field("anonymous", description="사용자 익명 식별자")
    source: dict = Field(..., description="출처 정보 (url, title, type)")
    content: list[str] = Field(..., description="Readability 또는 pdf.js에서 추출한 본문 문단 배열")

class EventItem(BaseModel):
    type: str
    timestamp_ms: int
    duration_ms: int | None = None
    position: float | None = None

class EventsRequestModel(BaseModel):
    events: list[EventItem]

# -----------------
# 2. Helpers
# -----------------
def remove_repeated_lines(paragraphs: list[str]) -> list[str]:
    from collections import Counter
    if not paragraphs: return []
    line_counter = Counter()
    for para in paragraphs:
        lines = [line.strip() for line in para.split("\n") if line.strip()]
        for unique_line in set(lines):
            line_counter[unique_line] += 1
    num_paras = len(paragraphs)
    min_frequency = max(3, int(num_paras * 0.1))
    repeated_lines = {line for line, count in line_counter.items() if count >= min_frequency and len(line) <= 50}
    cleaned_paragraphs = []
    for para in paragraphs:
        lines = para.split("\n")
        filtered_lines = [line for line in lines if line.strip() not in repeated_lines]
        cleaned_para = "\n".join(filtered_lines).strip()
        if cleaned_para:
            cleaned_paragraphs.append(cleaned_para)
    return cleaned_paragraphs

def _content_to_raw_text(content: list[str]) -> str:
    if not content: return ""
    cleaned = [p.strip() for p in content if p.strip()]
    cleaned = remove_repeated_lines(cleaned)
    return "\n\n".join(cleaned)

# -----------------
# 3. Endpoints
# -----------------
@router.post("/start")
async def start_session(req: SessionStartRequestModel, db: AsyncSession = Depends(get_db)):
    user_id = req.userId if req.userId else "anonymous"
    # User UPSERT
    user_result = await db.execute(select(User).filter(User.id == user_id))
    user = user_result.scalars().first()
    if not user:
        new_user = User(id=user_id)
        db.add(new_user)
        await db.commit()

    raw_text = _content_to_raw_text(req.content)
    if not raw_text:
        raise HTTPException(status_code=422, detail="No readable content found.")

    session_id = f"s_{uuid.uuid4().hex[:8]}"
    document_id = req.source.get("title", "doc")
    document_id = re.sub(r"[^a-zA-Z0-9가-힣]", "_", document_id)[:30] or "doc"

    new_session = ReadingSession(id=session_id, user_id=user_id, document_id=document_id)
    db.add(new_session)
    await db.commit()

    state = create_initial_state(session_id=session_id, user_id=user_id, document_id=document_id, raw_text=raw_text)
    
    # 2번 모듈(Content Reducer) 가동하여 초기 상태 세팅
    updated_state = run_content_reducer(state)
    
    # 세션의 초기 상태(chunks, terms 등)를 Redis에 저장해두면 좋지만, 우선은 응답만 반환
    # (실제 프로덕션에서는 Redis Session Store를 써야 함)

    def map_term(t):
        return {
            "term": t["term"], "definition": t["definition"], "source": t["source"],
            "faithfulnessScore": t.get("faithfulness_score", 1.0),
            "chunkId": t["chunk_id"]
        }

    def map_chunk(c):
        return {
            "chunkId": c["chunk_id"], "originalText": c["original_text"],
            "restructuredText": c.get("restructured_text", ""), "difficulty": c["difficulty"],
            "charStart": c["char_start"], "charEnd": c["char_end"],
            "terms": [map_term(t) for t in c.get("terms", [])]
        }

    chunks_mapped = [map_chunk(c) for c in updated_state.get("chunks", [])]
    terms_mapped = [map_term(t) for t in updated_state.get("terms", [])]

    return {
        "sessionId": session_id,
        "chunks": chunks_mapped,
        "simplifiedText": updated_state.get("simplified_text", ""),
        "terms": terms_mapped,
        "difficultyScore": updated_state.get("difficulty_score", 50.0)
    }

@router.post("/{session_id}/events")
async def process_events(session_id: str, req: EventsRequestModel):
    from ..core.redis import REDIS_URL
    import redis.asyncio as aioredis
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    
    redis_key = f"session:{session_id}:events"
    
    # 1. 버퍼에 이벤트 추가
    for ev in req.events:
        await redis_client.rpush(redis_key, ev.model_dump_json())
    
    # 2. 버퍼에서 전체 읽어와서 집중도 재계산
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

    # 집중도 계산 (3번 엔진)
    focus_score, penalties = calculate_focus_score(reading_events)
    
    # 임시 State 생성
    state = create_initial_state(session_id=session_id, user_id="", document_id="", raw_text="")
    state["reading_events"] = reading_events
    state["focus_score"] = focus_score
    state["focus_score_breakdown"] = {"penalties": penalties}
    
    # 개입 판단
    intervention_type, intervention_level = determine_intervention(state)
    state["intervention_needed"] = intervention_type != "none"
    state["intervention_level"] = intervention_level
    
    # 응답 포맷
    cmd = to_intervention_command(state)
    
    await redis_client.aclose()
    return cmd

@router.get("/{session_id}/result")
async def get_session_result(session_id: str, db: AsyncSession = Depends(get_db)):
    from ..core.redis import REDIS_URL
    import redis.asyncio as aioredis
    
    result = await db.execute(select(ReadingSession).filter(ReadingSession.id == session_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    redis_key = f"session:{session_id}:events"
    all_events_raw = await redis_client.lrange(redis_key, 0, -1)
    
    state_events = []
    for raw in all_events_raw:
        data = json.loads(raw)
        state_events.append({
            "type": data["type"],
            "timestamp_ms": data["timestamp_ms"],
            "position": data.get("position"),
            "duration_ms": data.get("duration_ms"),
            "metadata": data
        })
        
        # DB에 저장
        db.add(ReadingEvent(
            session_id=session_id,
            event_type=data["type"],
            timestamp_ms=data["timestamp_ms"],
            metadata_json=data
        ))
    
    initial_state = create_initial_state(session_id=session_id, user_id=session.user_id, document_id=session.document_id, raw_text="")
    initial_state["reading_events"] = state_events
    initial_state["quiz_result"] = {"score": 85.0} # 5번 목업 연결점
    
    # 1. 2번 모듈 초기 text/chunk 연산
    updated_state = run_content_reducer(initial_state)
    
    # 임시 퀴즈 생성 로직 연동 (5번 모듈 대체)
    from ..agents.content_reducer.quiz_generator import generate_quiz
    if updated_state.get("chunks"):
        first_chunk = updated_state["chunks"][0]
        quiz = generate_quiz(first_chunk["chunk_id"], first_chunk.get("restructured_text", first_chunk["original_text"]))
        # 5번 모듈 임시 목업 연결 (실제 평가 로직)
        from ..agents.stubs.qa_evaluation_stub import evaluate_quiz_stub
        updated_state["quiz_result"] = evaluate_quiz_stub(session_id, quiz)
    else:
        updated_state["quiz_result"] = {"score": 85.0}
    
    # 2. 오케스트레이터 그래프 실행 (점수 반영 등)
    final_state = run_reading_session(updated_state)
    
    session.literacy_score = final_state.get("literacy_score", 0.0)
    await db.commit()
    await redis_client.delete(redis_key)
    await redis_client.aclose()
    
    return to_session_result(final_state)
