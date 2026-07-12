"""O/X 문항형 퀴즈 배선 회귀 (편지 FEEDBACK_TO_ROLE3_OX_QUIZ 스펙).

prebuild_quizzes / pick_quiz(트리거 A·B·쿨다운·상하한) / submit_ox_quiz 글루와
확장 /api/session/{id}/quiz/submit 채점 경로, payload.quiz 노출(정답·해설 제외)을 박제한다.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.api.reading_session import SESSION_STORE
from backend.app.main import app
from backend.app.orchestrator.quiz import (
    apply_pick_quiz,
    pick_quiz,
    prebuild_quizzes,
    submit_ox_quiz,
)
from backend.app.orchestrator.state import create_initial_state

client = TestClient(app)


def setup_function():
    SESSION_STORE.clear()


def _state_with_chunks():
    state = create_initial_state(
        session_id="s1", user_id="u1", document_id="doc1", raw_text="본문"
    )
    state["chunks"] = [
        {"chunk_id": "chunk_01", "original_text": "엑스선의 파장은 가시광선보다 짧다."},
        {"chunk_id": "chunk_02", "original_text": "가시광선은 사람 눈으로 볼 수 있는 빛이다."},
    ]
    return state


# ── prebuild ──────────────────────────────────────────────


def test_prebuild_quizzes_builds_one_ox_per_chunk():
    state = prebuild_quizzes(_state_with_chunks())
    quizzes = state["quizzes"]

    assert set(quizzes) == {"chunk_01", "chunk_02"}
    q = quizzes["chunk_01"]
    assert q["quizId"] == "quiz_s1_chunk_01"
    assert q["type"] == "ox"
    assert isinstance(q["answer"], bool)
    assert q["statement"] and q["sourceChunkId"] == "chunk_01"
    # 프론트 공용 shape(QuizData): question + options["O","X"]
    assert q["question"] == q["statement"]
    assert q["options"] == ["O", "X"]


def test_prebuild_skips_too_short_paragraph():
    state = create_initial_state(
        session_id="s1", user_id="u1", document_id="doc1", raw_text="x"
    )
    state["chunks"] = [{"chunk_id": "c1", "original_text": "짧음"}]  # < 8자 → 스킵
    state = prebuild_quizzes(state)
    assert state["quizzes"] == {}


# ── pick_quiz 트리거 ──────────────────────────────────────


def test_pick_quiz_none_when_focus_high_and_progress_low():
    state = prebuild_quizzes(_state_with_chunks())
    state["focus_score"] = 90.0
    state["reading_events"] = [{"type": "scroll", "timestamp_ms": 1000, "position": 0.2}]
    assert pick_quiz(state) is None


def test_pick_quiz_focus_drop_trigger():
    state = prebuild_quizzes(_state_with_chunks())
    state["focus_score"] = 20.0  # < 30 → focus_drop
    state["reading_events"] = [{"type": "scroll", "timestamp_ms": 5000, "position": 0.3}]

    quiz = pick_quiz(state)
    assert quiz is not None
    assert quiz["trigger"] == "focus_drop"
    assert state["asked_quiz_ids"] == [quiz["quizId"]]
    assert state["last_quiz_at_ms"] == 5000


def test_pick_quiz_progress_floor_trigger_even_when_focused():
    state = prebuild_quizzes(_state_with_chunks())
    state["focus_score"] = 95.0  # 집중 좋아도
    state["reading_events"] = [{"type": "scroll", "timestamp_ms": 9000, "position": 0.95}]

    quiz = pick_quiz(state)
    assert quiz is not None
    assert quiz["trigger"] == "progress_floor"


def test_pick_quiz_cooldown_blocks_immediate_second():
    state = prebuild_quizzes(_state_with_chunks())
    state["focus_score"] = 10.0
    state["reading_events"] = [{"type": "scroll", "timestamp_ms": 1000, "position": 0.3}]
    assert pick_quiz(state) is not None
    # 쿨다운(25s) 안에서 다시 → None
    state["reading_events"].append({"type": "blur", "timestamp_ms": 2000})
    assert pick_quiz(state) is None


def test_pick_quiz_respects_max_quizzes():
    state = prebuild_quizzes(_state_with_chunks())
    state["asked_quiz_ids"] = ["a", "b", "c"]  # MAX_QUIZZES=3
    state["focus_score"] = 5.0
    state["reading_events"] = [{"type": "scroll", "timestamp_ms": 99000, "position": 0.5}]
    assert pick_quiz(state) is None


# ── apply_pick_quiz 주입 ──────────────────────────────────


def test_apply_pick_quiz_promotes_intervention_to_quiz():
    state = prebuild_quizzes(_state_with_chunks())
    state["focus_score"] = 15.0
    state["reading_events"] = [{"type": "scroll", "timestamp_ms": 3000, "position": 0.3}]
    state["intervention"] = {"level": "none", "type": "none", "message": ""}

    state = apply_pick_quiz(state)
    assert state["intervention"]["type"] == "quiz"
    assert state["intervention"]["quiz_data"]["type"] == "ox"
    assert state["intervention_needed"] is True


# ── submit 채점 ───────────────────────────────────────────


def test_submit_ox_quiz_records_answer_and_recovers_focus():
    state = prebuild_quizzes(_state_with_chunks())
    state["focus_score"] = 20.0
    quiz = state["quizzes"]["chunk_01"]
    correct_option = "O" if quiz["answer"] else "X"

    result = submit_ox_quiz(state, quiz["quizId"], correct_option)
    assert result["correct"] is True
    assert result["explanation"]
    assert result["xpEarned"] == 10
    assert result["focusRecovered"] == 15.0
    assert state["focus_score"] == 35.0  # 20 + 15 회복
    assert state["quiz_answers"][0]["correct"] is True
    assert state["quiz_answers"][0]["sourceChunkId"] == "chunk_01"


def test_submit_ox_quiz_wrong_answer_no_reward():
    state = prebuild_quizzes(_state_with_chunks())
    quiz = state["quizzes"]["chunk_02"]
    wrong_option = "X" if quiz["answer"] else "O"

    result = submit_ox_quiz(state, quiz["quizId"], wrong_option)
    assert result["correct"] is False
    assert result["xpEarned"] == 0
    assert result["focusRecovered"] == 0
    assert state["quiz_answers"][0]["correct"] is False


def test_submit_ox_quiz_unknown_id_returns_none():
    state = prebuild_quizzes(_state_with_chunks())
    assert submit_ox_quiz(state, "quiz_does_not_exist", "O") is None


# ── 확장 API 경로 (start → events(집중하락) → quiz/submit) ──


def test_extension_quiz_appears_and_scores_end_to_end():
    start = client.post(
        "/api/session/start",
        json={
            "userId": "u1",
            "articleId": "doc-ox",
            "content": [
                "엑스선의 파장은 가시광선보다 짧아서 물체를 투과할 수 있다.",
                "가시광선은 사람의 눈으로 인지할 수 있는 좁은 파장 대역이다.",
            ],
        },
    )
    assert start.status_code == 200
    session_id = start.json()["sessionId"]
    assert SESSION_STORE[session_id]["quizzes"]  # 프리젠됨

    # 집중을 크게 떨어뜨려 focus_drop 트리거(blur 반복)
    events = client.post(
        f"/api/session/{session_id}/events",
        json={
            "events": [
                {"type": "scroll", "timestamp_ms": 1000, "position": 0.4},
                {"type": "blur", "timestamp_ms": 2000, "duration_ms": 800},
                {"type": "blur", "timestamp_ms": 3000, "duration_ms": 800},
                {"type": "blur", "timestamp_ms": 4000, "duration_ms": 800},
                {"type": "blur", "timestamp_ms": 5000, "duration_ms": 800},
            ]
        },
    )
    assert events.status_code == 200
    cmd = events.json()
    assert cmd["type"] == "quiz"
    quiz = cmd["payload"]["quiz"]
    assert quiz["quizId"]
    assert quiz["question"]  # 프론트 QuizCard가 렌더
    assert quiz["options"] == ["O", "X"]  # O/X 2버튼 모드
    assert "answer" not in quiz  # 정답 미노출(서버 채점)
    assert "explanation" not in quiz  # 해설도 미노출(정답 노출 방지)

    # 정답 제출 → 채점 응답에 해설 포함
    stored = SESSION_STORE[session_id]["quizzes"][quiz["sourceChunkId"]]
    correct_option = "O" if stored["answer"] else "X"
    submit = client.post(
        f"/api/session/{session_id}/quiz/submit",
        json={"quizId": quiz["quizId"], "selectedOption": correct_option},
    )
    assert submit.status_code == 200
    body = submit.json()
    assert body["correct"] is True
    assert body["explanation"]

    # 세션 종료 → 이해도 실측 반영(measured=True)
    result = client.get(f"/api/session/{session_id}/result")
    assert result.status_code == 200
    breakdown = SESSION_STORE[session_id]["score_breakdown"]
    assert breakdown["comprehension_measured"] is True
    assert breakdown["quiz_count"] == 1


def test_extension_quiz_submit_missing_fields_422():
    start = client.post(
        "/api/session/start",
        json={"userId": "u1", "articleId": "d", "content": ["충분히 긴 본문 문단입니다."]},
    )
    session_id = start.json()["sessionId"]
    resp = client.post(f"/api/session/{session_id}/quiz/submit", json={"quizId": "x"})
    assert resp.status_code == 422
