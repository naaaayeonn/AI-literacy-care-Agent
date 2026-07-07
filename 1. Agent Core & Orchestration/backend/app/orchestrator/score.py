"""Literacy Score v1 calculation for the orchestrator core."""

from __future__ import annotations

import math

from .quiz import quiz_correct_rate
from .state import ReadingEvent, ReadingSessionState, ScoreBreakdown


def calculate_literacy_score(state: ReadingSessionState) -> ReadingSessionState:
    """Fill comprehension_score, literacy_score, and score_breakdown."""
    focus_score = float(state.get("focus_score", 60.0))
    difficulty_score = float(state.get("difficulty_score", 50.0))
    penalty, penalty_breakdown = abnormal_reading_penalty(state.get("reading_events", []))

    literacy_score, breakdown = compute_score(
        quiz_correct_rate=quiz_correct_rate(state.get("quiz_result")),
        focus_score=focus_score,
        difficulty_score=difficulty_score,
        abnormal_reading_penalty=penalty,
        penalty_breakdown=penalty_breakdown,
    )
    state["comprehension_score"] = breakdown["comprehension_score"]
    state["literacy_score"] = literacy_score
    state["score_breakdown"] = breakdown
    return state


def compute_score(
    *,
    quiz_correct_rate: float,
    focus_score: float,
    difficulty_score: float,
    abnormal_reading_penalty: float = 0.0,
    penalty_breakdown: dict | None = None,
) -> tuple[float, ScoreBreakdown]:
    """Compute a reproducible 0-100 literacy score and its evidence."""
    quiz_correct_rate = _clamp(_finite(quiz_correct_rate, default=0.0), 0.0, 1.0)
    comprehension_score = quiz_correct_rate * 100.0
    engagement_score = _clamp(_finite(focus_score, default=60.0), 0.0, 100.0)
    normalized_difficulty_score = _clamp(_finite(difficulty_score, default=50.0), 0.0, 100.0)
    penalty = _clamp(_finite(abnormal_reading_penalty, default=0.0), 0.0, 100.0)

    literacy_score = (
        comprehension_score * 0.50
        + engagement_score * 0.35
        + normalized_difficulty_score * 0.15
        - penalty
    )
    literacy_score = round(_clamp(literacy_score, 0.0, 100.0), 1)

    breakdown = ScoreBreakdown(
        comprehension_score=round(comprehension_score, 1),
        engagement_score=round(engagement_score, 1),
        difficulty_score=round(normalized_difficulty_score, 1),
        cross_validation_penalty=round(penalty, 1),
        penalty_breakdown=penalty_breakdown or {},
        reason=(
            f"Literacy score = comprehension({comprehension_score:.1f})*0.50 "
            f"+ engagement({engagement_score:.1f})*0.35 "
            f"+ difficulty({normalized_difficulty_score:.1f})*0.15 "
            f"- penalty({penalty:.1f})."
        ),
    )
    return literacy_score, breakdown


def abnormal_reading_penalty(events: list[ReadingEvent]) -> tuple[float, dict]:
    """Apply deterministic penalties for low-signal reading behavior."""
    blur_count = sum(1 for event in events if event["type"] == "blur")
    fast_scroll_count = sum(
        1
        for event in events
        if event["type"] == "scroll" and event.get("duration_ms", 1000) < 300
    )
    zero_dwell_count = sum(
        1
        for event in events
        if event["type"] in {"pause", "click"} and event.get("duration_ms", 1) <= 0
    )
    long_idle_count = sum(
        1
        for event in events
        if event["type"] == "pause" and event.get("duration_ms", 0) >= 30_000
    )

    raw_penalty = (
        blur_count * 2.0
        + fast_scroll_count * 1.5
        + zero_dwell_count * 2.5
        + long_idle_count * 3.0
    )
    total_penalty = round(min(20.0, raw_penalty), 1)

    return total_penalty, {
        "blur_count": blur_count,
        "fast_scroll_count": fast_scroll_count,
        "zero_dwell_count": zero_dwell_count,
        "long_idle_count": long_idle_count,
        "max_penalty": 20.0,
        "applied_penalty": total_penalty,
    }


def _finite(value: float, *, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
