from __future__ import annotations

from backend.app.orchestrator.graph import run_reading_session
from backend.app.orchestrator.quiz import apply_quiz_result
from backend.app.orchestrator.routing import decide_intervention
from backend.app.orchestrator.score import calculate_literacy_score
from backend.app.orchestrator.state import create_initial_state


def _raising_step(state):
    raise RuntimeError("forced failure")


def _neutral_care_step(state):
    state["focus_score"] = 60.0
    state["engagement_score"] = 60.0
    return state


def test_run_reading_session_returns_m0_final_state():
    state = create_initial_state(
        session_id="s1",
        user_id="u1",
        document_id="doc1",
        raw_text="This is a sample article for the M0 orchestrator demo.",
        profile={"previous_literacy_score": 65.0},
    )
    state["reading_events"] = [
        {"type": "scroll", "timestamp_ms": 1000, "position": 0.2, "duration_ms": 250},
        {"type": "pause", "timestamp_ms": 2500, "duration_ms": 1200},
    ]
    apply_quiz_result(
        state,
        {"quiz_id": "q1", "correct_count": 4, "total_count": 5, "answers": []},
    )

    result = run_reading_session(state)

    assert result["chunks"]
    assert result["focus_score"] == 68.0
    assert result["intervention_level"] == "soft"
    assert result["intervention"]["type"] == "highlight"
    assert result["intervention"]["target_chunk_id"] == "chunk_01"
    assert result["literacy_score"] == 66.1
    assert result["reward"]["xp"] == 99
    assert result["updated_profile"]["trend"] == "stable"
    assert [entry["step"] for entry in result["trace"]] == [
        "content_reducer",
        "cognitive_care",
        "routing_decision",
        "score_engine",
        "reward",
        "profile_update",
        "self_correction",
    ]
    assert all(entry["status"] == "success" for entry in result["trace"])
    assert result["warnings"] == []


def test_content_reducer_failure_uses_fallback_and_flow_continues():
    state = create_initial_state(
        session_id="s1",
        user_id="u1",
        document_id="doc1",
        raw_text="Fallback text should still become a chunk.",
    )
    state["quiz_result"] = {
        "quiz_id": "q1",
        "correct_count": 3,
        "total_count": 5,
        "answers": [],
    }

    result = run_reading_session(
        state,
        steps=(
            ("content_reducer", _raising_step),
            ("cognitive_care", _neutral_care_step),
            ("routing_decision", decide_intervention),
            ("score_engine", calculate_literacy_score),
        ),
    )

    assert result["chunks"][0]["chunk_id"] == "chunk_fallback_01"
    assert result["difficulty_score"] == 50.0
    assert result["literacy_score"] == 52.5
    assert result["trace"][0]["status"] == "fallback"
    assert result["errors"][0]["step"] == "content_reducer"


def test_optional_reward_and_profile_failures_do_not_block_result():
    state = create_initial_state(
        session_id="s1",
        user_id="u1",
        document_id="doc1",
        raw_text="Sample",
    )

    result = run_reading_session(
        state,
        steps=(
            ("score_engine", calculate_literacy_score),
            ("reward", _raising_step),
            ("profile_update", _raising_step),
        ),
    )

    # 퀴즈·이벤트 없음 → 이해도는 상수 70이 아니라 완독률 프록시 0 → 0*0.5+60*0.35+50*0.15 = 28.5
    assert result["literacy_score"] == 18.0
    assert "reward" not in result
    assert "updated_profile" not in result
    assert [entry["status"] for entry in result["trace"]] == [
        "success",
        "fallback",
        "fallback",
    ]
    assert [error["step"] for error in result["errors"]] == ["reward", "profile_update"]
