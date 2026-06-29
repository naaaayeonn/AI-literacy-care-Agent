from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import json
import time
from ..core.redis import get_redis
from ..services.cognitive_care import calculate_focus_score, determine_intervention
import redis.asyncio as redis

router = APIRouter(prefix="/ws", tags=["WebSocket"])

@router.websocket("/session/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    redis_client: redis.Redis = await get_redis()
    
    redis_key = f"session:{session_id}:events"
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                event_payload = json.loads(data)
                events = event_payload.get("events", [])
                
                # 1. 이벤트를 Redis List에 적재 (버퍼링)
                for event in events:
                    await redis_client.rpush(redis_key, json.dumps(event))
                    
                # TTL 설정 (예: 24시간)
                await redis_client.expire(redis_key, 86400)
                
                # 2. Redis에서 전체 이벤트 가져와서 Focus Score 계산
                all_events_raw = await redis_client.lrange(redis_key, 0, -1)
                all_events = [json.loads(e) for e in all_events_raw]
                
                focus_score = calculate_focus_score(all_events)
                needed, level, msg = determine_intervention(focus_score)
                
                # 3. 계산된 결과(또는 1번 오케스트레이터로 전달할 플래그) 리턴
                response = {
                    "session_id": session_id,
                    "focus_score": focus_score,
                    "intervention_needed": needed,
                    "intervention_level": level,
                    "message": msg,
                    "timestamp": int(time.time() * 1000)
                }
                
                await websocket.send_text(json.dumps(response))
                
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "Invalid JSON format"}))

    except WebSocketDisconnect:
        print(f"Client {session_id} disconnected")
