"""Literacy Score 산출 엔진 - 1번 역할 핵심 산출물.

[구현: 6/25 퀴즈 연동 / 6/26 Score v1]

최종 공식 (ARCHITECTURE §6.5):
    comprehension_score = quiz_correct_rate * 100
    engagement_score    = focus_score
    difficulty_adjustment = difficulty_score * 0.15
    penalty             = abnormal_reading_penalty

    literacy_score =
        comprehension_score * 0.50
        + engagement_score   * 0.35
        + difficulty_adjustment
        - penalty
    -> 0~100 범위 clamp

예외 처리: total_count == 0, NaN, 누락 필드.
"""

from __future__ import annotations
from .state import ReadingSessionState, ScoreBreakdown


def calculate_literacy_score(state: ReadingSessionState) -> ReadingSessionState:
    """state의 quiz/focus/difficulty를 읽어서 literacy_score를 채운다."""
    
    # 퀴즈 결과에서 정답률 추출
    quiz = state.get("quiz_result")
    if quiz and quiz.get("total_count", 0) > 0:
        quiz_correct_rate = quiz["correct_count"] / quiz["total_count"]
    else:
        # 퀴즈 없으면 기본 70% (중립값)
        quiz_correct_rate = 0.7
    
    comprehension = quiz_correct_rate * 100.0
    engagement = state.get("focus_score", 70.0)
    difficulty = state.get("difficulty_score", 50.0)
    
    # 비정상 읽기 패널티 (blur 과다, 너무 빠른 완독 등)
    penalty = _calculate_penalty(state)
    
    literacy, breakdown = compute_score(
        quiz_correct_rate=quiz_correct_rate,
        focus_score=engagement,
        difficulty_score=difficulty,
        abnormal_reading_penalty=penalty,
    )
    
    state["comprehension_score"] = comprehension
    state["engagement_score"] = engagement
    state["literacy_score"] = literacy
    state["score_breakdown"] = breakdown
    
    state["trace"].append({
        "step": "score_engine",
        "status": "success",
        "detail": {
            "literacy_score": literacy,
            "comprehension": comprehension,
            "engagement": engagement,
            "penalty": penalty,
        }
    })
    
    return state


def compute_score(
    *,
    quiz_correct_rate: float,
    focus_score: float,
    difficulty_score: float,
    abnormal_reading_penalty: float = 0.0,
) -> tuple[float, ScoreBreakdown]:
    """순수 계산 함수 (테스트용).
    
    입력 정규화 후 가중합 + clamp 0~100.
    """
    # 입력 정규화 (0~100 범위로)
    comprehension = _clamp(quiz_correct_rate * 100.0)
    engagement = _clamp(focus_score)
    difficulty = _clamp(difficulty_score)
    penalty = max(0.0, abnormal_reading_penalty)
    
    difficulty_adjustment = difficulty * 0.15
    
    raw_score = (
        comprehension * 0.50
        + engagement * 0.35
        + difficulty_adjustment
        - penalty
    )
    
    final_score = _clamp(raw_score)
    
    breakdown = ScoreBreakdown(
        comprehension_score=round(comprehension, 1),
        engagement_score=round(engagement, 1),
        difficulty_score=round(difficulty, 1),
        cross_validation_penalty=round(penalty, 1),
        reason=f"comp={comprehension:.0f}*0.5 + eng={engagement:.0f}*0.35 + diff={difficulty:.0f}*0.15 - pen={penalty:.0f}",
    )
    
    return round(final_score, 1), breakdown


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """값을 [lo, hi] 범위로 제한."""
    if value != value:  # NaN check
        return (lo + hi) / 2
    return max(lo, min(hi, value))


def _calculate_penalty(state: ReadingSessionState) -> float:
    """비정상 읽기 패턴 감점 계산."""
    events = state.get("reading_events", [])
    if not events:
        return 0.0
    
    blur_count = sum(1 for e in events if e.get("type") == "blur")
    total_events = len(events)
    
    # blur 비율이 30% 이상이면 감점
    if total_events > 0:
        blur_ratio = blur_count / total_events
        if blur_ratio > 0.3:
            return min((blur_ratio - 0.3) * 30, 15.0)  # 최대 15점 감점
    
    return 0.0
