"""Intervention routing based on focus score."""

from __future__ import annotations

from .state import InterventionCommand, InterventionLevel, InterventionType, ReadingSessionState


# 사용자에게 그대로 보이는 개입 오버레이 문구(한국어). 확장 오버레이 폴백 톤과 일관되게 유지.
INTERVENTION_MESSAGES: dict[InterventionLevel, str] = {
    "none": "",
    "soft": "이 문단의 핵심 문장에 잠시 집중해볼까요?",
    "medium": "잠깐 멈추고 방금 읽은 핵심 문장을 다시 읽어볼까요?",
    "hard": "계속하기 전에 방금 읽은 내용을 짧은 퀴즈로 확인해볼까요?",
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
