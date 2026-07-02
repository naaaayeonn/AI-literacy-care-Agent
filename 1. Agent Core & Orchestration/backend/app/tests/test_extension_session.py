"""확장 인입 alias 라우트 테스트 — API_CONTRACT §9, ADR-001/002."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.api.reading_session import SESSION_STORE
from backend.app.main import app

client = TestClient(app)


def setup_function():
    SESSION_STORE.clear()


def test_extension_e2e_flow():
    start = client.post(
        "/api/session/start",
        json={
            "userId": "u_uuid_123",
            "articleId": "https://example.com/article",
            "source": {"url": "https://example.com/article", "title": "글", "type": "web"},
            "content": ["AI literacy care observes reading behavior.", "It intervenes when focus drops."],
        },
    )

    assert start.status_code == 200
    start_body = start.json()
    session_id = start_body["sessionId"]
    assert session_id  # UUID 발급됨
    # camelCase 응답 계약(§9-1)
    assert "chunks" in start_body
    assert "simplifiedText" in start_body
    assert "difficultyScore" in start_body
    # content[]가 raw_text로 합쳐져 문서 식별자/유저가 매핑됨
    stored = SESSION_STORE[session_id]
    assert stored["user_id"] == "u_uuid_123"
    assert stored["document_id"] == "https://example.com/article"
    assert "reading behavior" in stored["raw_text"]

    events = client.post(
        f"/api/session/{session_id}/events",
        json={
            "events": [
                {"type": "scroll", "timestamp_ms": 1000, "position": 0.2, "duration_ms": 250},
                {"type": "blur", "timestamp_ms": 2000, "duration_ms": 500},
            ]
        },
    )

    assert events.status_code == 200
    cmd = events.json()
    # 개입 명령 계약(§9-2): {type, payload{focusScore, progress}}
    assert cmd["type"] in {"nudge", "highlight", "quiz", "score_update"}
    assert "focusScore" in cmd["payload"]
    assert "progress" in cmd["payload"]

    result = client.get(f"/api/session/{session_id}/result")

    assert result.status_code == 200
    res = result.json()
    # 최종 결과 계약(성장 그래프용)
    assert res["sessionId"] == session_id
    assert "literacyScore" in res
    assert "scoreSeries" in res
    assert isinstance(res["scoreSeries"], list)


def test_start_requires_non_empty_content():
    # content 누락
    missing = client.post("/api/session/start", json={"userId": "u1"})
    assert missing.status_code == 422

    # content가 리스트가 아님
    not_list = client.post("/api/session/start", json={"content": "raw string"})
    assert not_list.status_code == 422

    # 빈/공백만 있는 리스트
    empty = client.post("/api/session/start", json={"content": ["", "   "]})
    assert empty.status_code == 422


def test_start_defaults_anonymous_user():
    """userId 미제공 시 익명 폴백(ADR-002)."""
    start = client.post(
        "/api/session/start",
        json={"content": ["some readable content here"]},
    )
    assert start.status_code == 200
    stored = SESSION_STORE[start.json()["sessionId"]]
    assert stored["user_id"] == "anonymous"
    assert stored["document_id"] == "document_unknown"


def test_events_on_unknown_session_returns_404():
    response = client.post(
        "/api/session/missing/events",
        json={"events": []},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "session not found"


def test_events_reject_non_list():
    start = client.post("/api/session/start", json={"content": ["readable content"]})
    session_id = start.json()["sessionId"]

    response = client.post(
        f"/api/session/{session_id}/events",
        json={"events": "not-a-list"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "events must be a list"


def test_result_on_unknown_session_returns_404():
    response = client.get("/api/session/missing/result")
    assert response.status_code == 404


def test_cors_allows_extension_and_site_origins():
    """확장(chrome-extension)·임의 사이트 origin 모두 CORS 허용(dev/demo)."""
    # content script가 읽는 임의 사이트 origin
    site = client.post(
        "/api/session/start",
        json={"content": ["readable content"]},
        headers={"Origin": "https://news.example.com"},
    )
    assert site.headers.get("access-control-allow-origin") == "*"

    # pdf 뷰어(chrome-extension) origin — preflight
    preflight = client.options(
        "/api/session/start",
        headers={
            "Origin": "chrome-extension://abcdefghijklmnop",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert preflight.status_code in (200, 204)
    assert preflight.headers.get("access-control-allow-origin") == "*"
