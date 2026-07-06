"""WebSocket 엔드포인트 - 실시간 읽기 행동 수집 및 개입 명령 전송 (6/27~6/28 안정화)"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import time
import traceback
from ..core.redis import get_redis
from ..services.cognitive_care import calculate_focus_score, determine_intervention
import redis.asyncio as aioredis

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/reading/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    print(f"[WS] Client connected: session={session_id}")
    
    redis_client = None
    redis_key = f"session:{session_id}:events"
    
    try:
        redis_client = await get_redis()
        
        while True:
            data = await websocket.receive_text()
            
            try:
                event_payload = json.loads(data)
                events = event_payload.get("events", [])
                
                # 단일 이벤트도 지원 (events 키가 없으면 payload 자체를 이벤트로 취급)
                if not events and event_payload.get("type"):
                    events = [event_payload]
                
                # 1. 이벤트를 Redis List에 저장 (스트리밍)
                for event in events:
                    await redis_client.rpush(redis_key, json.dumps(event))
                    
                # TTL 설정 (예: 24시간)
                await redis_client.expire(redis_key, 86400)
                
                # 2. Redis에서 전체 이벤트 가져와서 Focus Score 계산
                all_events_raw = await redis_client.lrange(redis_key, 0, -1)
                all_events = [json.loads(e) for e in all_events_raw]
                
                focus_score = calculate_focus_score(all_events)
                needed, level, msg = determine_intervention(focus_score)
                
                # 3. 응답 전송 (프론트엔드 InterventionCommand 형식)
                response = {
                    "type": "score_update",
                    "session_id": session_id,
                    "payload": {
                        "focusScore": focus_score,
                        "progress": min(len(all_events), 100),  # 대략적 진행률
                    },
                    "timestamp": int(time.time() * 1000)
                }
                await websocket.send_text(json.dumps(response))
                
                # 개입이 필요한 경우 추가 메시지 전송
                if needed:
                    nudge_response = {
                        "type": "nudge",
                        "session_id": session_id,
                        "payload": {
                            "nudgeLevel": level,
                            "nudgeMessage": msg,
                        },
                        "timestamp": int(time.time() * 1000)
                    }
                    await websocket.send_text(json.dumps(nudge_response))
                    
                    # hard 레벨이면 퀴즈 전송
                    if level == "hard":
                        quiz_response = {
                            "type": "quiz",
                            "session_id": session_id,
                            "payload": {
                                "quiz": {
                                    "id": f"auto-quiz-{int(time.time())}",
                                    "question": "방금 읽은 내용의 핵심 주제는 무엇인가요?",
                                    "options": [
                                        {"id": "A", "text": "AI의 활용과 윤리"},
                                        {"id": "B", "text": "요리 레시피"},
                                        {"id": "C", "text": "운동 방법"},
                                        {"id": "D", "text": "여행 계획"},
                                    ],
                                    "correctAnswer": "A",
                                }
                            },
                            "timestamp": int(time.time() * 1000)
                        }
                        await websocket.send_text(json.dumps(quiz_response))
                
            except json.JSONDecodeError:
                error_resp = {"type": "error", "payload": {"message": "Invalid JSON format"}}
                await websocket.send_text(json.dumps(error_resp))
            except Exception as e:
                print(f"[WS] Error processing event for {session_id}: {e}")
                traceback.print_exc()
                error_resp = {"type": "error", "payload": {"message": f"Server error: {str(e)[:100]}"}}
                await websocket.send_text(json.dumps(error_resp))

    except WebSocketDisconnect:
        print(f"[WS] Client disconnected: session={session_id}")
    except Exception as e:
        print(f"[WS] Unexpected error for session {session_id}: {e}")
        traceback.print_exc()
    finally:
        # 안전한 정리
        if redis_client:
            try:
                # Redis TTL 확인 (데이터는 유지, TTL만 갱신)
                await redis_client.expire(redis_key, 86400)
                await redis_client.aclose()
            except Exception:
                pass
        print(f"[WS] Cleanup complete for session={session_id}")
