"""Literacy Score v2 — 근거 있는 가중식 (1번 canonical과 동일 로직).

리터러시 = 이해도(0.45) + 집중도(0.30) + 도전성취(0.25) − 교차검증 감점
  - 도전성취 = 이해율 × 글난이도(0.6·난이도 + 0.4·비이독성)  → 2번 난이도·이독성 반영.
  - 이해도: quiz_answers/quiz_result 실측, 없으면 완독률 프록시(상수 0.7 폐기).

문해 5대 지표(compute_literacy_domains)·글 프로필(compute_text_profile)도 함께 산출.
"""

from __future__ import annotations

import math

from .state import ReadingSessionState, ScoreBreakdown

COMPREHENSION_WEIGHT = 0.45
ENGAGEMENT_WEIGHT = 0.30
CHALLENGE_WEIGHT = 0.25


def calculate_literacy_score(state: ReadingSessionState) -> ReadingSessionState:
    """state의 quiz/focus/difficulty/readability를 읽어 literacy_score·5대 지표·글 프로필을 채운다."""
    focus_score = float(state.get("focus_score", 60.0))
    difficulty_score = float(state.get("difficulty_score", 50.0))
    readability_score = float(state.get("readability_score", 50.0))
    penalty, penalty_breakdown = abnormal_reading_penalty(state.get("reading_events", []))

    comp_rate, measured, confidence, quiz_count = _comprehension_rate(state)

    literacy, breakdown = compute_score(
        quiz_correct_rate=comp_rate,
        focus_score=focus_score,
        difficulty_score=difficulty_score,
        readability_score=readability_score,
        abnormal_reading_penalty=penalty,
        penalty_breakdown=penalty_breakdown,
    )
    breakdown["comprehension_measured"] = measured
    breakdown["comprehension_confidence"] = confidence
    breakdown["quiz_count"] = quiz_count

    domains = compute_literacy_domains(state, breakdown)
    text_profile = compute_text_profile(state)
    breakdown["literacy_domains"] = domains
    breakdown["text_profile"] = text_profile

    state["comprehension_score"] = breakdown["comprehension_score"]
    state["engagement_score"] = breakdown["engagement_score"]
    state["literacy_score"] = literacy
    state["score_breakdown"] = breakdown
    state["literacy_domains"] = domains
    state["text_profile"] = text_profile

    state.setdefault("trace", []).append({
        "step": "score_engine",
        "status": "success",
        "detail": {"literacy_score": literacy, "measured": measured, "penalty": penalty},
    })
    return state


def _comprehension_rate(state: ReadingSessionState) -> tuple[float, bool, str, int]:
    """이해도 비율(0~1). 우선순위: quiz_answers → quiz_result → 완독률 프록시. (상수 0.7 폐기)"""
    answers = state.get("quiz_answers")
    if isinstance(answers, list) and answers:
        correct = sum(1 for a in answers if isinstance(a, dict) and a.get("correct"))
        rate = correct / len(answers)
        confidence = "high" if len(answers) >= 2 else "medium"
        return _clamp(rate, 0.0, 1.0), True, confidence, len(answers)

    quiz = state.get("quiz_result")
    total = quiz.get("total_count", 0) if isinstance(quiz, dict) else 0
    if isinstance(total, (int, float)) and total > 0:
        rate = _clamp(_num(quiz.get("correct_count"), 0.0) / total, 0.0, 1.0)
        return rate, True, "medium", int(total)

    return _completion_rate(state.get("reading_events", [])), False, "low", 0


def _completion_rate(events: list) -> float:
    positions = [
        _num(e.get("position"), 0.0)
        for e in events
        if isinstance(e, dict) and e.get("position") is not None
    ]
    return _clamp(max(positions), 0.0, 1.0) if positions else 0.0


def compute_score(
    *,
    quiz_correct_rate: float,
    focus_score: float,
    difficulty_score: float,
    readability_score: float = 50.0,
    abnormal_reading_penalty: float = 0.0,
    penalty_breakdown: dict | None = None,
) -> tuple[float, ScoreBreakdown]:
    comp_rate = _clamp(_num(quiz_correct_rate, 0.0), 0.0, 1.0)
    comprehension_score = comp_rate * 100.0
    engagement_score = _clamp(_num(focus_score, 60.0), 0.0, 100.0)
    difficulty = _clamp(_num(difficulty_score, 50.0), 0.0, 100.0)
    readability = _clamp(_num(readability_score, 50.0), 0.0, 100.0)
    penalty = _clamp(_num(abnormal_reading_penalty, 0.0), 0.0, 100.0)

    text_challenge = _clamp(0.6 * difficulty + 0.4 * (100.0 - readability), 0.0, 100.0)
    challenge_achievement = _clamp(comp_rate * text_challenge, 0.0, 100.0)

    literacy_score = (
        comprehension_score * COMPREHENSION_WEIGHT
        + engagement_score * ENGAGEMENT_WEIGHT
        + challenge_achievement * CHALLENGE_WEIGHT
        - penalty
    )
    literacy_score = round(_clamp(literacy_score, 0.0, 100.0), 1)

    breakdown = ScoreBreakdown(
        comprehension_score=round(comprehension_score, 1),
        engagement_score=round(engagement_score, 1),
        difficulty_score=round(difficulty, 1),
        readability_score=round(readability, 1),
        text_challenge=round(text_challenge, 1),
        challenge_achievement=round(challenge_achievement, 1),
        cross_validation_penalty=round(penalty, 1),
        penalty_breakdown=penalty_breakdown or {},
        reason=(
            f"Literacy = comp({comprehension_score:.1f})*{COMPREHENSION_WEIGHT} "
            f"+ eng({engagement_score:.1f})*{ENGAGEMENT_WEIGHT} "
            f"+ challenge({challenge_achievement:.1f})*{CHALLENGE_WEIGHT} - pen({penalty:.1f})."
        ),
    )
    return literacy_score, breakdown


def compute_literacy_domains(state: ReadingSessionState, breakdown: ScoreBreakdown) -> dict:
    """문해 5대 지표(각 0~100): comprehension/focus/closeReading/challenge/stability."""
    comp = _num(breakdown.get("comprehension_score"), 0.0)
    eng = _num(breakdown.get("engagement_score"), 0.0)
    difficulty = _num(breakdown.get("difficulty_score"), 50.0)
    readability = _num(breakdown.get("readability_score"), 50.0)
    penalty = _num(breakdown.get("cross_validation_penalty"), 0.0)

    close_reading = _completion_rate(state.get("reading_events", [])) * 100.0
    challenge = (comp / 100.0) * difficulty
    penalty_pct = min(100.0, penalty * 5.0)
    softener = 0.5 + 0.5 * (readability / 100.0)
    stability = _clamp(100.0 - penalty_pct * softener, 0.0, 100.0)

    return {
        "comprehension": round(_clamp(comp, 0.0, 100.0), 1),
        "focus": round(_clamp(eng, 0.0, 100.0), 1),
        "closeReading": round(_clamp(close_reading, 0.0, 100.0), 1),
        "challenge": round(_clamp(challenge, 0.0, 100.0), 1),
        "stability": round(stability, 1),
    }


def compute_text_profile(state: ReadingSessionState) -> dict:
    readability = _clamp(_num(state.get("readability_score"), 50.0), 0.0, 100.0)
    difficulty = _clamp(_num(state.get("difficulty_score"), 50.0), 0.0, 100.0)
    return {
        "readability": round(readability, 1),
        "difficulty": round(difficulty, 1),
        "readabilityLabel": _readability_label(readability),
        "difficultyLabel": _difficulty_label(difficulty),
    }


def _difficulty_label(d: float) -> str:
    if d < 25:
        return "쉬움"
    if d < 50:
        return "보통"
    if d < 75:
        return "어려움"
    return "전문"


def _readability_label(r: float) -> str:
    if r < 40:
        return "복잡"
    if r < 70:
        return "보통"
    return "매끄러움"


def abnormal_reading_penalty(events: list) -> tuple[float, dict]:
    """비정상 읽기 감점(결정론, 1번과 동일)."""
    blur_count = sum(1 for e in events if e.get("type") == "blur")
    fast_scroll_count = sum(
        1 for e in events if e.get("type") == "scroll" and _num(e.get("duration_ms"), 1000) < 300
    )
    zero_dwell_count = sum(
        1 for e in events if e.get("type") in {"pause", "click"} and _num(e.get("duration_ms"), 1) <= 0
    )
    long_idle_count = sum(
        1 for e in events if e.get("type") == "pause" and _num(e.get("duration_ms"), 0) >= 30_000
    )
    raw = blur_count * 2.0 + fast_scroll_count * 1.5 + zero_dwell_count * 2.5 + long_idle_count * 3.0
    total = round(min(20.0, raw), 1)
    return total, {
        "blur_count": blur_count,
        "fast_scroll_count": fast_scroll_count,
        "zero_dwell_count": zero_dwell_count,
        "long_idle_count": long_idle_count,
        "max_penalty": 20.0,
        "applied_penalty": total,
    }


def _num(value: object, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))
