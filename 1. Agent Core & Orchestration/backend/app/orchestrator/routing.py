"""Intervention routing based on focus score."""

from __future__ import annotations

from .state import InterventionCommand, InterventionLevel, InterventionType, ReadingSessionState


INTERVENTION_MESSAGES: dict[InterventionLevel, str] = {
    "none": "",
    "soft": "Highlight the key sentence in the current chunk.",
    "medium": "Show a short nudge and ask the user to reread the key sentence.",
    "hard": "Show a quick quiz card before continuing.",
}

INTERVENTION_TYPES: dict[InterventionLevel, InterventionType] = {
    "none": "none",
    "soft": "highlight",
    "medium": "nudge",
    "hard": "quiz",
}


def decide_intervention(state: ReadingSessionState) -> ReadingSessionState:
    """Fill frontend-ready intervention command fields from focus_score."""
    command = build_intervention_command(state)

    state["intervention"] = command
    state["intervention_level"] = command["level"]
    state["intervention_needed"] = command["level"] != "none"
    state["intervention_message"] = command["message"]
    return state


def build_intervention_command(state: ReadingSessionState) -> InterventionCommand:
    """Build the JSON command consumed by the frontend."""
    focus_score = _safe_focus_score(state.get("focus_score", 60.0))
    level = level_for_focus(focus_score)
    command = InterventionCommand(
        level=level,
        type=INTERVENTION_TYPES[level],
        message=INTERVENTION_MESSAGES[level],
        reason=f"focus_score={focus_score:.1f}",
    )

    target_chunk_id = _target_chunk_id(state)
    if target_chunk_id and level != "none":
        command["target_chunk_id"] = target_chunk_id

    return command


def level_for_focus(focus_score: float) -> InterventionLevel:
    """Map focus score to none/soft/medium/hard intervention levels."""
    focus_score = _safe_focus_score(focus_score)
    if focus_score >= 75:
        return "none"
    if focus_score >= 50:
        return "soft"
    if focus_score >= 30:
        return "medium"
    return "hard"


def _target_chunk_id(state: ReadingSessionState) -> str | None:
    chunks = state.get("chunks", [])
    if not chunks:
        return None

    first_chunk = chunks[0]
    chunk_id = first_chunk.get("chunk_id")
    return str(chunk_id) if chunk_id else None


def _safe_focus_score(value: object) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 60.0
    return max(0.0, min(100.0, score))
