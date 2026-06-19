"""Literacy Score 계산 엔진 — 1번 역할의 핵심 산출물.

[구현 예정: 6/25 퀴즈 연결 / 6/26 Score v1]

점수는 LLM에 맡기지 않고 재현 가능한 순수 함수로 계산한다. 같은 입력이면
항상 같은 출력이어야 하고, 근거를 score_breakdown으로 남긴다.

초기 계산식 (ARCHITECTURE §6.5):
    comprehension_score = quiz_correct_rate * 100
    engagement_score    = focus_score
    difficulty_adjustment = difficulty_score * 0.15
    penalty             = abnormal_reading_penalty

    literacy_score =
        comprehension_score * 0.50
        + engagement_score   * 0.35
        + difficulty_adjustment
        - penalty
    -> 0~100 으로 clamp

예외 처리: total_count == 0, NaN, 누락 필드.
"""

from __future__ import annotations

from .state import ReadingSessionState, ScoreBreakdown


def calculate_literacy_score(state: ReadingSessionState) -> ReadingSessionState:
    """state에서 quiz/focus/difficulty를 읽어 literacy_score를 채운다.

    TODO(6/26): 가중합 + 교차검증 감점 + clamp + score_breakdown 구현.
    """
    raise NotImplementedError("6/26 Score v1 구현 예정")


def compute_score(
    *,
    quiz_correct_rate: float,
    focus_score: float,
    difficulty_score: float,
    abnormal_reading_penalty: float = 0.0,
) -> tuple[float, ScoreBreakdown]:
    """순수 계산 함수 (test_score 대상).

    TODO(6/26): 구현 + pytest. 입력 정규화/clamp/예외 처리 포함.
    """
    raise NotImplementedError("6/26 구현 예정")
