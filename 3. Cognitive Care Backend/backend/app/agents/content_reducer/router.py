"""
router.py — LLM 난이도 기반 모델 라우팅 (M1)

difficulty_score와 전문 용어 수를 기반으로
Claude Sonnet(고성능) 또는 Claude Haiku(경량)를 선택한다.

라우팅 기준:
  difficulty_score >= THRESHOLD  또는  term_count >= 3
    → Claude Sonnet (고품질, 고비용)
  그 외
    → Claude Haiku (경량, 저비용)
"""
from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# 모델 식별자 상수
# ---------------------------------------------------------------------------

MODEL_HEAVY = "gemini-2.0-flash"   # 고성능 / 고난도 (Gemini 무료 티어)
MODEL_LIGHT = "gemini-2.0-flash"   # 경량 / 단순 변환 (Gemini 무료 티어)

# 환경 변수로 임계값 조정 가능 (기본값: 55)
_THRESHOLD = float(os.getenv("DIFFICULTY_THRESHOLD_FOR_HEAVY_LLM", "55"))


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------

def select_model(difficulty_score: float, term_count: int = 0) -> str:
    """
    난이도 점수와 전문 용어 수에 따라 LLM 모델을 선택한다.

    Args:
        difficulty_score: 0~100, 높을수록 어려운 텍스트
        term_count: 청크 내 전문 용어 수

    Returns:
        모델 식별자 문자열 (MODEL_HEAVY 또는 MODEL_LIGHT)

    Examples:
        >>> select_model(70.0) == MODEL_HEAVY
        True
        >>> select_model(30.0) == MODEL_LIGHT
        True
    """
    if difficulty_score >= _THRESHOLD or term_count >= 3:
        return MODEL_HEAVY
    return MODEL_LIGHT


def get_routing_reason(
    difficulty_score: float, term_count: int, model: str
) -> str:
    """라우팅 결정 이유를 반환한다 (trace 기록용)."""
    if model == MODEL_HEAVY:
        reasons = []
        if difficulty_score >= _THRESHOLD:
            reasons.append(
                f"difficulty({difficulty_score:.1f}) >= threshold({_THRESHOLD})"
            )
        if term_count >= 3:
            reasons.append(f"term_count({term_count}) >= 3")
        return f"heavy_model_selected: {', '.join(reasons)}"
    return (
        f"light_model_selected: difficulty({difficulty_score:.1f}) < "
        f"threshold({_THRESHOLD}), terms({term_count}) < 3"
    )
