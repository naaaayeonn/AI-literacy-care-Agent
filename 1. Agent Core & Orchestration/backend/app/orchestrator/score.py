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

    comp_rate, measured, confidence, quiz_count = _comprehension_rate(state)

    literacy_score, breakdown = compute_score(
        quiz_correct_rate=comp_rate,
        focus_score=focus_score,
        difficulty_score=difficulty_score,
        abnormal_reading_penalty=penalty,
        penalty_breakdown=penalty_breakdown,
    )
    breakdown["comprehension_measured"] = measured
    breakdown["comprehension_confidence"] = confidence
    breakdown["quiz_count"] = quiz_count
    state["comprehension_score"] = breakdown["comprehension_score"]
    state["literacy_score"] = literacy_score
    state["score_breakdown"] = breakdown
    return state


def _comprehension_rate(state: ReadingSessionState) -> tuple[float, bool, str, int]:
    """이해도 비율(0~1)을 실측/추정으로 구한다. → (rate, measured, confidence, quiz_count)

    우선순위:
      1) quiz_answers(신규 O/X 문항별 정답 기록) — 실측
      2) quiz_result(기존 집계형, total_count>0) — 실측
      3) 둘 다 없으면 완독률(max position) 프록시 — 추정(measured=False)
    상수 0.7 default는 더 이상 쓰지 않는다(집중 잘한 사람의 이해도가 상수로 박제되던 문제).
    """
    answers = state.get("quiz_answers")
    if isinstance(answers, list) and answers:
        correct = sum(1 for a in answers if isinstance(a, dict) and a.get("correct"))
        rate = correct / len(answers)
        confidence = "high" if len(answers) >= 2 else "medium"
        return _clamp(rate, 0.0, 1.0), True, confidence, len(answers)

    quiz_result = state.get("quiz_result")
    total = quiz_result.get("total_count", 0) if isinstance(quiz_result, dict) else 0
    if isinstance(total, (int, float)) and total > 0:
        rate = _clamp(_finite(quiz_correct_rate(quiz_result), default=0.0), 0.0, 1.0)
        return rate, True, "medium", int(total)

    # 결측 → 완독률 프록시(추정)
    return _completion_rate(state.get("reading_events", [])), False, "low", 0


def _completion_rate(events: list) -> float:
    """reading_events의 최대 읽기 진행률(position, 0~1)을 이해도 프록시로 쓴다."""
    positions = [
        _finite(e.get("position"), default=0.0)
        for e in events
        if isinstance(e, dict) and e.get("position") is not None
    ]
    if not positions:
        return 0.0
    return _clamp(max(positions), 0.0, 1.0)


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
