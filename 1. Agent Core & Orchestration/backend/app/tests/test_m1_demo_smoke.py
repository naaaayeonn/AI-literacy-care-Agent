from __future__ import annotations

from backend.app.demo.m1_scenario import build_m1_demo_state, run_m1_demo


def test_build_m1_demo_state_has_fixed_inputs():
    state = build_m1_demo_state()

    assert state["session_id"] == "demo_m1_session"
    assert state["user_id"] == "demo_user"
    assert state["document_id"] == "demo_doc_ai_literacy"
    assert len(state["reading_events"]) == 5
    assert state["quiz_result"]["correct_count"] == 4
    assert state["quiz_result"]["total_count"] == 5


def test_run_m1_demo_smoke_result_is_repeatable():
    result = run_m1_demo()

    assert result["chunks"][0]["chunk_id"] == "chunk_01"
    assert result["focus_score"] == 39.0
    assert result["intervention"] == {
        "level": "medium",
        "type": "nudge",
        "message": "잠깐 멈추고 방금 읽은 핵심 문장을 다시 읽어볼까요?",
        "reason": "focus_score=39.0",
        "target_chunk_id": "chunk_01",
    }
    assert result["literacy_score"] == 55.6
    assert result["score_breakdown"]["penalty_breakdown"] == {
        "blur_count": 2,
        "fast_scroll_count": 2,
        "zero_dwell_count": 0,
        "long_idle_count": 0,
        "max_penalty": 20.0,
        "applied_penalty": 7.0,
    }
    assert result["reward"]["badge"] == "needs_support"
    assert result["updated_profile"]["trend"] == "declining"
    assert [entry["status"] for entry in result["trace"]] == ["success"] * 7
    assert result["errors"] == []
    assert result["warnings"] == []
