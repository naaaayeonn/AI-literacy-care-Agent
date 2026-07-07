"""Reward stub for the M0 end-to-end flow."""

from __future__ import annotations

from ...orchestrator.state import ReadingSessionState


def reward_stub(state: ReadingSessionState) -> ReadingSessionState:
    """Create deterministic reward data from the final score."""
    literacy_score = float(state.get("literacy_score", 0.0))

    if literacy_score >= 80:
        badge = "focused_reader"
    elif literacy_score >= 60:
        badge = "steady_reader"
    else:
        badge = "needs_support"

    state["reward"] = {
        "xp": int(round(literacy_score * 1.5)),
        "badge": badge,
        "message": "Session completed. Keep reading with steady focus.",
    }
    return state
