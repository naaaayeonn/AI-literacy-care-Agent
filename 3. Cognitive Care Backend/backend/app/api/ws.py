from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import time
from ..core.redis import get_redis
from ..services.cognitive_care import calculate_focus_score, determine_intervention
from ..orchestrator.state import create_initial_state
from .frontend_contract import to_intervention_command
import redis.asyncio as redis

router = APIRouter(prefix="/ws", tags=["WebSocket"])

_TYPE_MAP = {"scroll": "scroll", "dwell": "pause", "blur": "blur", "focus": "focus"}

def to_reading_event(front_event: dict) -> dict:
    p = front_event.get("payload", {})
    ev = {
        "type": _TYPE_MAP.get(front_event.get("type"), "click"),
        "timestamp_ms": int(front_event.get("timestamp", 0)),
    }
    if p.get("progress") is not None:
        ev["position"] = p["progress"] / 100
    if p.get("dwellMs") is not None:
        ev["duration_ms"] = int(p["dwellMs"])
    if p.get("scrollVelocity") is not None:
        ev["velocity"] = p["scrollVelocity"]
    return ev

@router.websocket("/reading/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    redis_client = await get_redis()
    redis_key = f"session:{session_id}:events"
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                front_event = json.loads(data)
                internal_event = to_reading_event(front_event)
                
                # 1. 이벤트를 Redis List에 적재
                await redis_client.rpush(redis_key, json.dumps(internal_event))
                await redis_client.expire(redis_key, 86400)
                
                # 2. Redis에서 전체 이벤트 가져와서 Focus Score 계산
                all_events_raw = await redis_client.lrange(redis_key, 0, -1)
                all_events = [json.loads(e) for e in all_events_raw]
                
                focus_score = calculate_focus_score(all_events)
                _, level, msg = determine_intervention(focus_score)
                
                # 내부 intervention type 결정
                level_to_type = {"none": "none", "soft": "highlight", "medium": "nudge", "hard": "quiz"}
                internal_type = level_to_type.get(level, "none")
                
                state = create_initial_state(session_id=session_id, user_id="", document_id="", raw_text="")
                state["reading_events"] = all_events
                state["focus_score"] = focus_score
                state["intervention"] = {
                    "level": level,
                    "type": internal_type,
                    "message": msg
                }
                
                # 3. 프론트엔드 계약(Contract)에 맞춰 변환 후 전송
                response_payload = to_intervention_command(state)
                await websocket.send_text(json.dumps(response_payload, ensure_ascii=False))
                
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "payload": {"message": "Invalid JSON format"}}))
                
                
    except WebSocketDisconnect:
        print(f"Client {session_id} disconnected")
    finally:
        await redis_client.aclose()
