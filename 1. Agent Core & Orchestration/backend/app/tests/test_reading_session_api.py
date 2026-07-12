from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.api.reading_session import SESSION_STORE
from backend.app.main import app

client = TestClient(app)


def setup_function():
    SESSION_STORE.clear()


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_reading_session_api_e2e_flow():
    start = client.post(
        "/api/reading-sessions/start",
        json={
            "session_id": "api_s1",
            "user_id": "u1",
            "document_id": "doc1",
            "raw_text": "AI literacy care observes reading behavior and intervenes.",
            "profile": {"previous_literacy_score": 60},
        },
    )

    assert start.status_code == 200
    start_body = start.json()
    assert start_body["session_id"] == "api_s1"
    assert start_body["chunks"][0]["chunk_id"] == "chunk_01"
    assert start_body["difficulty_score"] == 60.0

    events = client.post(
        "/api/reading-sessions/api_s1/events",
        json={
            "events": [
                {"type": "scroll", "timestamp_ms": 1000, "position": 0.2, "duration_ms": 250},
                {"type": "blur", "timestamp_ms": 2000, "duration_ms": 500},
            ]
        },
    )

    assert events.status_code == 200
    events_body = events.json()
    assert events_body["focus_score"] == 53.0
    assert events_body["intervention"]["type"] == "highlight"

    quiz = client.post(
        "/api/reading-sessions/api_s1/quiz",
        json={"quiz_id": "q1", "correct_count": 4, "total_count": 5, "answers": []},
    )

    assert quiz.status_code == 200
    assert quiz.json()["quiz_result"]["correct_count"] == 4

    finish = client.post("/api/reading-sessions/api_s1/finish")

    assert finish.status_code == 200
    finish_body = finish.json()
    assert finish_body["session_id"] == "api_s1"
    assert finish_body["intervention"]["type"] == "highlight"
    assert finish_body["literacy_score"] == 64.0
    assert finish_body["reward"]["badge"] == "steady_reader"
    assert finish_body["updated_profile"]["trend"] == "improving"
    assert [entry["step"] for entry in finish_body["trace"][-7:]] == [
        "content_reducer",
        "cognitive_care",
        "routing_decision",
        "score_engine",
        "reward",
        "profile_update",
        "self_correction",
    ]
    assert finish_body["warnings"] == []

    result = client.get("/api/reading-sessions/api_s1/result")

    assert result.status_code == 200
    assert result.json()["literacy_score"] == finish_body["literacy_score"]


def test_start_requires_raw_text():
    response = client.post("/api/reading-sessions/start", json={"user_id": "u1"})

    assert response.status_code == 422
    assert response.json()["detail"] == "raw_text is required"


def test_unknown_session_returns_404():
    response = client.get("/api/reading-sessions/missing/result")

    assert response.status_code == 404
    assert response.json()["detail"] == "session not found"


def test_push_events_normalizes_and_filters_invalid_entries():
    client.post(
        "/api/reading-sessions/start",
        json={"session_id": "n1", "raw_text": "sample"},
    )

    response = client.post(
        "/api/reading-sessions/n1/events",
        json={
            "events": [
                {"type": "scroll", "timestamp_ms": 1000, "position": 1.5},  # position clamp
                {"type": "unknown", "timestamp_ms": 2000},  # 잘못된 type → drop
                {"type": "blur", "timestamp_ms": "bad"},  # timestamp 비정수 → drop
                "not-a-dict",  # dict 아님 → drop
            ]
        },
    )

    assert response.status_code == 200
    events = SESSION_STORE["n1"]["reading_events"]
    assert len(events) == 1
    assert events[0]["type"] == "scroll"
    assert events[0]["position"] == 1.0  # 0.0~1.0으로 clamp


def test_push_events_passes_read_chunk_index_and_drops_invalid():
    client.post(
        "/api/reading-sessions/start",
        json={"session_id": "rc1", "raw_text": "sample"},
    )

    client.post(
        "/api/reading-sessions/rc1/events",
        json={
            "events": [
                {"type": "scroll", "timestamp_ms": 1000, "position": 0.5, "readChunkIndex": 2},
                {"type": "scroll", "timestamp_ms": 2000, "position": 0.6, "readChunkIndex": True},
                {"type": "scroll", "timestamp_ms": 3000, "position": 0.7, "readChunkIndex": "x"},
            ]
        },
    )

    events = SESSION_STORE["rc1"]["reading_events"]
    assert events[0]["readChunkIndex"] == 2
    assert "readChunkIndex" not in events[1]  # bool 제외
    assert "readChunkIndex" not in events[2]  # 비정수 제외


def test_push_events_rejects_non_list_events():
    client.post(
        "/api/reading-sessions/start",
        json={"session_id": "n2", "raw_text": "sample"},
    )

    response = client.post(
        "/api/reading-sessions/n2/events",
        json={"events": "not-a-list"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "events must be a list"
