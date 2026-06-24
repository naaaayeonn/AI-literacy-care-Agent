"""조건부 라우팅 — 집중도(focus_score)에 따라 개입 수준 결정.

[구현 예정: 6/24 집중도 기반 개입 라우팅]

기준 (ARCHITECTURE §6.6):
    focus_score >= 75      -> none
    50 <= focus_score < 75 -> soft   (핵심 문장 하이라이트)
    30 <= focus_score < 50 -> medium (넛지 메시지)
    focus_score < 30       -> hard   (즉석 퀴즈 카드)

출력은 프론트(4번)가 intervention.type / level / message 만 보고 UI를 그릴 수
있는 형태여야 한다.
"""

from __future__ import annotations

from .state import InterventionLevel, ReadingSessionState


def decide_intervention(state: ReadingSessionState) -> ReadingSessionState:
    """focus_score를 읽어 intervention_level / message를 채운다.

    TODO(6/24): 위 기준을 코드로 구현하고 프론트용 intervention command 반환.
    """
    raise NotImplementedError("6/24 라우팅 구현 예정")


def level_for_focus(focus_score: float) -> InterventionLevel:
    """focus_score → 개입 단계 매핑 (순수 함수, test_routing 대상).

    TODO(6/24): 경계값 포함 구현 + 단위 테스트.
    """
    raise NotImplementedError("6/24 구현 예정")
