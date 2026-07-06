import pytest
from httpx import AsyncClient, ASGITransport
import sys
import asyncio

# Windows의 psycopg 비동기 이슈 방지
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.main import app

@pytest.mark.anyio
async def test_extension_e2e():
    print("\n====================================")
    print("*** AI Literacy Care E2E Demo Start (Pytest AsyncClient)")
    print("====================================\n")
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        print("1. [REST] Start Session API (/api/extension_session/start)")
        start_payload = {
            "userId": "test_extension_user",
            "source": {"url": "https://news.example.com", "title": "Test Article", "type": "web"},
            "content": ["AI 기술이 발전함에 따라...", "특히 문해력이 중요한 시대가 되었습니다."]
        }
        
        start_res = await ac.post("/api/extension_session/start", json=start_payload)
        assert start_res.status_code == 200
        start_data = start_res.json()
        session_id = start_data["sessionId"]
        print(f"[OK] Session started. Session ID: {session_id}")
        
        print("2. [REST] Word Hover Lookup API (/api/terms/lookup)")
        lookup_res = await ac.get("/api/terms/lookup?word=문해력")
        assert lookup_res.status_code == 200
        print(f"[OK] Word lookup success! '{lookup_res.json()['term']}': {lookup_res.json()['definition']}\n")
            
        print("3. [REST] Send Events (/api/extension_session/events)")
        good_events = {"events": [{"type": "scroll", "timestamp_ms": 1000, "position": 0.1}]}
        ev_res1 = await ac.post(f"/api/extension_session/{session_id}/events", json=good_events)
        print(f"[OK] Event 1 Response: {ev_res1.json()}")
        
        bad_events = {"events": [{"type": "blur", "timestamp_ms": 3000, "duration_ms": 4000}]}
        ev_res2 = await ac.post(f"/api/extension_session/{session_id}/events", json=bad_events)
        print(f"[OK] Event 2 Response (Nudge): {ev_res2.json()}")
        
        print("\n4. [REST] Get Session Result (/api/extension_session/result)")
        res_req = await ac.get(f"/api/extension_session/{session_id}/result")
        assert res_req.status_code == 200
        print(f"[OK] Get session result success!")
            
        print("5. [REST] Delete User Data (/api/user/data)")
        del_req = await ac.delete("/api/user/test_extension_user/data")
        assert del_req.status_code == 200
        print(f"[OK] Delete user data success! {del_req.json().get('message')}")
