from __future__ import annotations

from backend.app.orchestrator.routing import (
    build_intervention_command,
    decide_intervention,
    level_for_focus,
)
from backend.app.orchestrator.state import create_initial_state


def test_level_for_focus_boundaries():
    assert level_for_focus(75) == "none"
    assert level_for_focus(74.9) == "soft"
    assert level_for_focus(50) == "soft"
    assert level_for_focus(49.9) == "medium"
    assert level_for_focus(30) == "medium"
    assert level_for_focus(29.9) == "hard"


def test_decide_intervention_fills_frontend_command_fields():
    state = create_initial_state(
        session_id="s1",
        user_id="u1",
        document_id="doc1",
        raw_text="sample",
    )
    state["focus_score"] = 45.0
    state["chunks"] = [{"chunk_id": "chunk_02", "text": "sample"}]

    result = decide_intervention(state)

    assert result["intervention_level"] == "medium"
    assert result["intervention_needed"] is True
    assert result["intervention_message"]
    assert result["intervention"] == {
        "level": "medium",
        "type": "nudge",
        "message": "Show a short nudge and ask the user to reread the key sentence.",
        "reason": "focus_score=45.0",
        "target_chunk_id": "chunk_02",
    }


def test_build_intervention_command_for_each_level():
    state = create_initial_state(
        session_id="s1",
        user_id="u1",
        document_id="doc1",
        raw_text="sample",
    )

    state["focus_score"] = 80
    assert build_intervention_command(state)["type"] == "none"

    state["focus_score"] = 60
    assert build_intervention_command(state)["type"] == "highlight"

    state["focus_score"] = 40
    assert build_intervention_command(state)["type"] == "nudge"

    state["focus_score"] = 20
    assert build_intervention_command(state)["type"] == "quiz"


def test_invalid_or_missing_focus_defaults_to_soft():
    # 비숫자/누락 focus는 _safe_focus_score가 60.0으로 처리 → soft
    assert level_for_focus("bad") == "soft"

    state = create_initial_state(
        session_id="s1",
        user_id="u1",
        document_id="doc1",
        raw_text="sample",
    )
    result = decide_intervention(state)  # focus_score 없음
    assert result["intervention_level"] == "soft"
    assert result["intervention_needed"] is True


def test_none_level_omits_target_chunk_id_even_with_chunks():
    state = create_initial_state(
        session_id="s1",
        user_id="u1",
        document_id="doc1",
        raw_text="sample",
    )
    state["focus_score"] = 90.0
    state["chunks"] = [{"chunk_id": "chunk_01", "text": "sample"}]

    command = build_intervention_command(state)

    assert command["level"] == "none"
    assert "target_chunk_id" not in command
