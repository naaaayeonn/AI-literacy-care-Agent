"""Literacy Score v2 계산 — 근거 있는 가중식.

리터러시 점수 = 이해도(0.45) + 집중도(0.30) + 도전성취(0.25) − 교차검증 감점

- 이해도(comprehension): O/X 퀴즈 정답률 실측(없으면 완독률 프록시).
- 집중도(engagement): 이벤트 기반 focus.
- 도전성취(challenge_achievement): **이해한 만큼 × 글이 어려운 만큼**.
    글난이도(text_challenge) = 0.6·난이도(difficulty) + 0.4·비이독성(100−readability).
    → 2번의 **난이도**와 **이독성**을 둘 다 반영. 쉬운 글 완독보다 어려운 글 이해를 높게 평가.
- 교차검증 감점: 비정상 읽기(스키밍/이탈/무동작).

문해 5대 지표(compute_literacy_domains)와 글 프로필(compute_text_profile)도 함께 산출한다.
"""

from __future__ import annotations

import math

from .quiz import quiz_correct_rate
from .state import ReadingEvent, ReadingSessionState, ScoreBreakdown

# 가중치(합 1.0). 이해도 우선, 집중, 도전성취 순.
COMPREHENSION_WEIGHT = 0.45
ENGAGEMENT_WEIGHT = 0.30
CHALLENGE_WEIGHT = 0.25


def calculate_literacy_score(state: ReadingSessionState) -> ReadingSessionState:
    """Fill comprehension_score, literacy_score, score_breakdown, literacy_domains, text_profile."""
    focus_score = float(state.get("focus_score", 60.0))
    difficulty_score = float(state.get("difficulty_score", 50.0))
    readability_score = float(state.get("readability_score", 50.0))
    penalty, penalty_breakdown = abnormal_reading_penalty(state.get("reading_events", []))

    comp_rate, measured, confidence, quiz_count = _comprehension_rate(state)

    literacy_score, breakdown = compute_score(
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
    state["literacy_score"] = literacy_score
    state["score_breakdown"] = breakdown
    state["literacy_domains"] = domains
    state["text_profile"] = text_profile
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
    readability_score: float = 50.0,
    abnormal_reading_penalty: float = 0.0,
    penalty_breakdown: dict | None = None,
) -> tuple[float, ScoreBreakdown]:
    """Compute a reproducible 0-100 literacy score and its evidence (v2, 난이도·이독성 반영)."""
    comp_rate = _clamp(_finite(quiz_correct_rate, default=0.0), 0.0, 1.0)
    comprehension_score = comp_rate * 100.0
    engagement_score = _clamp(_finite(focus_score, default=60.0), 0.0, 100.0)
    difficulty = _clamp(_finite(difficulty_score, default=50.0), 0.0, 100.0)
    readability = _clamp(_finite(readability_score, default=50.0), 0.0, 100.0)
    penalty = _clamp(_finite(abnormal_reading_penalty, default=0.0), 0.0, 100.0)

    # 글이 얼마나 도전적이었나: 난이도(전문성)↑ + 비이독성(문장 어려움)↑ = 더 어려움.
    text_challenge = _clamp(0.6 * difficulty + 0.4 * (100.0 - readability), 0.0, 100.0)
    # 도전 성취: 이해한 만큼 × 도전적인 만큼. (쉬운 글 완독 < 어려운 글 이해)
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
            f"Literacy = comprehension({comprehension_score:.1f})*{COMPREHENSION_WEIGHT} "
            f"+ engagement({engagement_score:.1f})*{ENGAGEMENT_WEIGHT} "
            f"+ challenge({challenge_achievement:.1f})*{CHALLENGE_WEIGHT} "
            f"- penalty({penalty:.1f}). "
            f"challenge = comp_rate({comp_rate:.2f}) x text_challenge({text_challenge:.1f}"
            f"=0.6*diff{difficulty:.0f}+0.4*(100-read{readability:.0f}))."
        ),
    )
    return literacy_score, breakdown


# ──────────────────────────────────────────────
# 문해 5대 지표 (v2) — 전부 실측 신호 파생
# ──────────────────────────────────────────────


def compute_literacy_domains(state: ReadingSessionState, breakdown: ScoreBreakdown) -> dict:
    """레이더용 5대 지표(각 0~100). 라벨은 프론트가 매핑.

    - comprehension 이해도       : 퀴즈 정답률
    - focus         집중 유지     : engagement(focus)
    - closeReading  정독 충실도   : 본문 완독률(§4 position max)
    - challenge     난이도 도전력 : 이해도 × 난이도(difficulty)  ← 어려운 글 이해할수록↑
    - stability     읽기 안정성   : 100 − 감점(이독성 낮은 글은 완화)  ← readability 반영
    """
    comp = _num(breakdown.get("comprehension_score"), 0.0)
    eng = _num(breakdown.get("engagement_score"), 0.0)
    difficulty = _num(breakdown.get("difficulty_score"), 50.0)
    readability = _num(breakdown.get("readability_score"), 50.0)
    penalty = _num(breakdown.get("cross_validation_penalty"), 0.0)

    close_reading = _completion_rate(state.get("reading_events", [])) * 100.0
    challenge = (comp / 100.0) * difficulty

    # 이독성이 낮은(어려운) 글에서 느리게·재독하는 건 자연스러우니 감점을 완화한다.
    penalty_pct = min(100.0, penalty * 5.0)  # penalty(0~20) → 0~100
    softener = 0.5 + 0.5 * (readability / 100.0)  # read 0→0.5, 100→1.0
    stability = _clamp(100.0 - penalty_pct * softener, 0.0, 100.0)

    return {
        "comprehension": round(_clamp(comp, 0.0, 100.0), 1),
        "focus": round(_clamp(eng, 0.0, 100.0), 1),
        "closeReading": round(_clamp(close_reading, 0.0, 100.0), 1),
        "challenge": round(_clamp(challenge, 0.0, 100.0), 1),
        "stability": round(stability, 1),
    }


def compute_text_profile(state: ReadingSessionState) -> dict:
    """글 자체의 프로필(사용자 역량 아님) — 이독성/난이도 + 라벨. 4번 게이지·뇌아이콘용."""
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
    # 높을수록 읽기 쉬움.
    if r < 40:
        return "복잡"
    if r < 70:
        return "보통"
    return "매끄러움"


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


def _num(value: object, default: float = 0.0) -> float:
    return _finite(value, default=default)


def _finite(value: float, *, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
