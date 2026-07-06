"""개입 판별 엔진 - 집중도(focus_score)에 따라 개입 수준을 결정한다.

[구현: 6/24 집중도 개입 판별 구현]

규칙 (ARCHITECTURE §6.6):
    focus_score >= 75      -> none
    50 <= focus_score < 75 -> soft   (다시 한 하이라이트)
    30 <= focus_score < 50 -> medium (격려 메시지)
    focus_score < 30       -> hard   (강제 퀴즈 카드)

프론트엔드(4번)는 intervention.type / level / message 값을 받아 UI를 그리는 데
사용하는 역할만 한다.
"""

from __future__ import annotations
from .state import InterventionLevel, ReadingSessionState


# 개입 메시지 템플릿
INTERVENTION_MESSAGES = {
    "none": "",
    "soft": "핵심 문단을 다시 한번 살펴볼까요? 📌",
    "medium": "잠깐! 조금 쉬었다가 다시 읽어보는 건 어때요? ☕",
    "hard": "집중이 필요해요! 간단한 퀴즈로 내용을 확인해봐요! 📝",
}


def decide_intervention(state: ReadingSessionState) -> ReadingSessionState:
    """focus_score를 읽어서 intervention_level / message를 채운다."""
    focus = state.get("focus_score", 75.0)
    level = level_for_focus(focus)
    
    state["intervention_needed"] = level != "none"
    state["intervention_level"] = level
    state["intervention_message"] = INTERVENTION_MESSAGES.get(level, "")
    
    state["trace"].append({
        "step": "routing",
        "status": "success",
        "detail": {
            "focus_score": focus,
            "intervention_level": level,
        }
    })
    
    return state


def level_for_focus(focus_score: float) -> InterventionLevel:
    """focus_score 기준 개입 단계 결정 (순수 함수, test_routing 용)."""
    if focus_score >= 75.0:
        return "none"
    elif focus_score >= 50.0:
        return "soft"
    elif focus_score >= 30.0:
        return "medium"
    else:
        return "hard"
