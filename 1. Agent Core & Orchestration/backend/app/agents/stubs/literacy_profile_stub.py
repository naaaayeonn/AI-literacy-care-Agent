"""Literacy Profile stub for the M0 end-to-end flow."""

from __future__ import annotations

from ...orchestrator.state import ReadingSessionState


def literacy_profile_stub(state: ReadingSessionState) -> ReadingSessionState:
    """Create a small updated profile from score and breakdown data."""
    literacy_score = float(state.get("literacy_score", 0.0))
    previous_score = state.get("profile", {}).get("previous_literacy_score")

    if isinstance(previous_score, (int, float)):
        if literacy_score > previous_score + 3:
            trend = "improving"
        elif literacy_score < previous_score - 3:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "baseline"

    weaknesses = []
    breakdown = state.get("score_breakdown", {})
    if breakdown.get("comprehension_score", 100.0) < 60:
        weaknesses.append("comprehension")
    if breakdown.get("engagement_score", 100.0) < 60:
        weaknesses.append("focus")

    state["updated_profile"] = {
        "reading_level": "intermediate",
        "trend": trend,
        "weaknesses": weaknesses,
        "recommended_next_action": "Read one more short passage and answer a quick check quiz.",
    }
    return state
