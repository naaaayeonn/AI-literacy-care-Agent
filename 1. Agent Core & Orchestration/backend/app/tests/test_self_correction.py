from __future__ import annotations

from backend.app.orchestrator.self_correction import collect_warnings, review_session
from backend.app.orchestrator.state import create_initial_state


def _healthy_state():
    state = create_initial_state(
        session_id="s1",
        user_id="u1",
        document_id="doc1",
        raw_text="Sample article",
    )
    state["chunks"] = [{"chunk_id": "chunk_01", "text": "Sample article"}]
    state["simplified_text"] = "Sample article made simple."
    state["focus_score"] = 70.0
    state["literacy_score"] = 72.0
    state["quiz_result"] = {"quiz_id": "q1", "correct_count": 4, "total_count": 5, "answers": []}
    state["score_breakdown"] = {"cross_validation_penalty": 3.0}
    return state


def _codes(state):
    return {w["code"] for w in collect_warnings(state)}


def test_healthy_session_has_no_warnings():
    assert collect_warnings(_healthy_state()) == []


def test_empty_chunks_is_flagged():
    state = _healthy_state()
    state["chunks"] = []
    assert "empty_chunks" in _codes(state)


def test_empty_simplified_text_is_flagged():
    state = _healthy_state()
    state["simplified_text"] = "   "
    assert "empty_simplified_text" in _codes(state)


def test_missing_focus_score_is_flagged():
    state = _healthy_state()
    del state["focus_score"]
    assert "missing_focus_score" in _codes(state)


def test_missing_literacy_score_is_critical():
    state = _healthy_state()
    del state["literacy_score"]
    warnings = collect_warnings(state)
    missing = [w for w in warnings if w["code"] == "missing_literacy_score"]
    assert missing and missing[0]["severity"] == "critical"


def test_score_out_of_range_is_critical():
    state = _healthy_state()
    state["literacy_score"] = 140.0
    warnings = collect_warnings(state)
    out = [w for w in warnings if w["code"] == "score_out_of_range"]
    assert out and out[0]["severity"] == "critical"


def test_missing_quiz_is_info():
    state = _healthy_state()
    del state["quiz_result"]
    warnings = collect_warnings(state)
    quiz = [w for w in warnings if w["code"] == "quiz_missing"]
    assert quiz and quiz[0]["severity"] == "info"


def test_high_penalty_is_flagged():
    state = _healthy_state()
    state["score_breakdown"] = {"cross_validation_penalty": 18.0}
    assert "high_abnormal_penalty" in _codes(state)


def test_fallback_in_trace_is_flagged():
    state = _healthy_state()
    state["trace"] = [
        {"step": "content_reducer", "status": "fallback"},
        {"step": "cognitive_care", "status": "success"},
    ]
    warnings = collect_warnings(state)
    fallback = [w for w in warnings if w["code"] == "agent_fallback"]
    assert fallback and fallback[0]["detail"]["steps"] == ["content_reducer"]


def test_review_session_accumulates_into_state():
    state = _healthy_state()
    state["chunks"] = []
    result = review_session(state)
    assert result is state
    assert any(w["code"] == "empty_chunks" for w in result["warnings"])
