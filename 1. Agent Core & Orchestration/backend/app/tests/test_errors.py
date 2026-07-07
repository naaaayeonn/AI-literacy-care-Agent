"""Fallback 안전망 단위 테스트 — 에이전트 실패해도 데모가 끊기지 않아야 한다."""

from __future__ import annotations

from backend.app.orchestrator.errors import (
    apply_cognitive_care_fallback,
    apply_content_reducer_fallback,
    apply_fallback,
    apply_profile_fallback,
    apply_reward_fallback,
    apply_routing_fallback,
    apply_score_fallback,
    apply_self_correction_fallback,
)
from backend.app.orchestrator.state import create_initial_state


def _state():
    return create_initial_state(
        session_id="s1",
        user_id="u1",
        document_id="doc1",
        raw_text="원문 텍스트 샘플",
    )


def test_content_reducer_fallback_keeps_one_chunk():
    state = apply_content_reducer_fallback(_state(), Exception("boom"))

    assert state["chunks"][0]["chunk_id"] == "chunk_fallback_01"
    assert state["chunks"][0]["text"] == "원문 텍스트 샘플"
    assert state["difficulty_score"] == 50.0
    assert state["simplified_text"] == "원문 텍스트 샘플"
    assert state["terms"] == []


def test_cognitive_care_fallback_uses_neutral_focus():
    state = apply_cognitive_care_fallback(_state(), Exception("boom"))

    assert state["focus_score"] == 60.0
    assert state["intervention_needed"] is False
    assert state["intervention"]["level"] == "none"
    assert state["intervention"]["reason"] == "fallback_cognitive_care"


def test_routing_fallback_does_not_interrupt_user():
    state = apply_routing_fallback(_state(), Exception("boom"))

    assert state["intervention_level"] == "none"
    assert state["intervention_needed"] is False
    assert state["intervention"]["type"] == "none"


def test_score_fallback_returns_neutral_explainable_score():
    state = _state()
    state["focus_score"] = 72.0
    state["difficulty_score"] = 65.0

    state = apply_score_fallback(state, Exception("boom"))

    assert state["literacy_score"] == 60.0
    assert state["comprehension_score"] == 60.0
    assert state["score_breakdown"]["engagement_score"] == 72.0
    assert state["score_breakdown"]["difficulty_score"] == 65.0
    assert state["score_breakdown"]["reason"]


def test_reward_fallback_drops_partial_reward():
    state = _state()
    state["reward"] = {"xp": 1}

    state = apply_reward_fallback(state, Exception("boom"))

    assert "reward" not in state


def test_profile_fallback_drops_partial_profile():
    state = _state()
    state["updated_profile"] = {"trend": "improving"}

    state = apply_profile_fallback(state, Exception("boom"))

    assert "updated_profile" not in state


def test_self_correction_fallback_records_warning():
    state = apply_self_correction_fallback(_state(), Exception("boom"))

    codes = [w["code"] for w in state["warnings"]]
    assert "self_correction_failed" in codes


def test_apply_fallback_dispatches_by_step_name():
    state = apply_fallback("content_reducer", _state(), Exception("boom"))
    assert state["chunks"][0]["chunk_id"] == "chunk_fallback_01"


def test_apply_fallback_unknown_step_is_noop():
    state = _state()
    result = apply_fallback("mystery_step", state, Exception("boom"))
    assert result is state
    assert "chunks" not in result
