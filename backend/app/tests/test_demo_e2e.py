import pytest
from httpx import AsyncClient, ASGITransport
import sys
import asyncio

# Windows의 psycopg 비동기 이슈 방지
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from backend.app.main import app

@pytest.mark.anyio
async def test_extension_e2e():
    print("\n====================================")
    print("🚀 AI 리터러시 케어 E2E 데모 시작 (Pytest AsyncClient)")
    print("====================================\n")
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        print("1. [REST] 세션 시작 API 호출 (/api/extension_session/start)")
        start_payload = {
            "userId": "test_extension_user",
            "source": {"url": "https://news.example.com", "title": "Test Article", "type": "web"},
            "content": ["AI 기술이 발전함에 따라...", "특히 문해력이 중요한 시대가 되었습니다."]
        }
        
        start_res = await ac.post("/api/extension_session/start", json=start_payload)
        assert start_res.status_code == 200
        start_data = start_res.json()
        session_id = start_data["sessionId"]
        print(f"✅ 세션 시작 성공! Session ID: {session_id}")
        
        print("2. [REST] 단어 Hover Lookup API 호출 (/api/terms/lookup)")
        lookup_res = await ac.get("/api/terms/lookup?word=문해력")
        assert lookup_res.status_code == 200
        print(f"✅ 단어 찾기 성공! '{lookup_res.json()['term']}': {lookup_res.json()['definition']}\n")
            
        print("3. [REST] 이벤트 전송 (/api/extension_session/events)")
        good_events = {"events": [{"type": "scroll", "timestamp_ms": 1000, "position": 0.1}]}
        ev_res1 = await ac.post(f"/api/extension_session/{session_id}/events", json=good_events)
        print(f"✅ 이벤트 1 응답: {ev_res1.json()}")
        
        bad_events = {"events": [{"type": "blur", "timestamp_ms": 3000, "duration_ms": 4000}]}
        ev_res2 = await ac.post(f"/api/extension_session/{session_id}/events", json=bad_events)
        print(f"✅ 이벤트 2 응답 (넛지): {ev_res2.json()}")
        
        print("\n4. [REST] 세션 종료 결과 조회 (/api/extension_session/result)")
        res_req = await ac.get(f"/api/extension_session/{session_id}/result")
        assert res_req.status_code == 200
        print(f"✅ 세션 종료 성공!")
            
        print("5. [REST] 사용자 데이터 삭제 (/api/user/data)")
        del_req = await ac.delete("/api/user/test_extension_user/data")
        assert del_req.status_code == 200
        print(f"✅ 데이터 삭제 성공! {del_req.json().get('message')}")
