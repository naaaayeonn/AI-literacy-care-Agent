"""Cognitive Care stub for the M0 end-to-end flow."""

from __future__ import annotations

from ...orchestrator.state import ReadingSessionState


def cognitive_care_stub(state: ReadingSessionState) -> ReadingSessionState:
    """Derive a simple focus score from reading events."""
    events = state.get("reading_events", [])
    blur_count = sum(1 for event in events if event["type"] == "blur")
    fast_scroll_count = sum(
        1
        for event in events
        if event["type"] == "scroll" and event.get("duration_ms", 1000) < 300
    )
    pause_count = sum(1 for event in events if event["type"] == "pause")

    focus_score = 70.0 - blur_count * 12.0 - fast_scroll_count * 5.0 + min(pause_count, 3) * 3.0
    focus_score = max(0.0, min(100.0, focus_score))

    state["focus_score"] = focus_score
    state["engagement_score"] = focus_score
    state["intervention_needed"] = focus_score < 75.0
    return state
