"""에이전트 입출력 계약 (런타임 검증).

각 팀원 모듈(2~5번)의 출력이 계약을 지키는지 코드로 검증한다. 실제 모듈을
stub 자리에 끼울 때(M2 통합) 계약 위반을 **명확한 에러**로 잡아, 잘못된
출력이 Shared State로 조용히 새어 들어가는 것을 막는다.

문서 버전은 docs/API_CONTRACT.md (SSOT는 state.py).

사용
- `validate_contract(name, payload)`: 평평한 출력 dict를 직접 검증.
- `validate_state_output(name, state)`: state에서 해당 에이전트 산출을 뽑아 검증.
  (agents/config.py의 run_agent가 real 모듈 출력에 대해 자동 호출)
"""

from __future__ import annotations

import math

from .state import ReadingSessionState


class ContractError(ValueError):
    """에이전트 출력이 계약을 위반했을 때 발생."""


# 각 에이전트 출력 계약.
# - required : 반드시 존재하고 None이 아니어야 하는 필드
# - scores   : 0~100 숫자여야 하는 필드
# - source   : state에서 payload를 뽑는 방식
#              "state"        → state 최상위에서 required 필드를 모음
#              "<key>"        → state[<key>] 중첩 dict가 곧 payload
_SPECS: dict[str, dict] = {
    "content_reducer": {
        "required": ("chunks", "simplified_text", "terms", "difficulty_score"),
        "scores": ("difficulty_score",),
        "source": "state",
    },
    "cognitive_care": {
        "required": ("focus_score", "engagement_score", "intervention_needed"),
        "scores": ("focus_score", "engagement_score"),
        "source": "state",
    },
    "reward": {
        "required": ("xp", "badge", "message"),
        "scores": (),
        "source": "reward",
    },
    "literacy_profile": {
        "required": ("reading_level", "trend", "weaknesses", "recommended_next_action"),
        "scores": (),
        "source": "updated_profile",
    },
}

# 문서/참조용 평탄 필드 목록 (기존 호환 유지).
CONTENT_REDUCER_OUTPUT_FIELDS = _SPECS["content_reducer"]["required"]
COGNITIVE_CARE_OUTPUT_FIELDS = _SPECS["cognitive_care"]["required"]
REWARD_OUTPUT_FIELDS = _SPECS["reward"]["required"]
PROFILE_OUTPUT_FIELDS = _SPECS["literacy_profile"]["required"]
QA_OUTPUT_FIELDS = ("passed", "faithfulness", "answer_relevance", "warnings")


def validate_contract(name: str, payload: dict) -> None:
    """출력 payload가 `name` 에이전트 계약을 지키는지 검증한다.

    위반 시 ContractError를 던진다. 통과하면 None.
    """
    spec = _SPECS.get(name)
    if spec is None:
        raise ContractError(f"알 수 없는 계약 이름: {name!r}")
    if not isinstance(payload, dict):
        raise ContractError(
            f"{name} 출력이 dict가 아닙니다: {type(payload).__name__}"
        )

    missing = [f for f in spec["required"] if payload.get(f) is None]
    if missing:
        raise ContractError(f"{name} 출력에 필수 필드 누락: {missing}")

    for field in spec["scores"]:
        value = payload.get(field)
        if not _is_score(value):
            raise ContractError(
                f"{name}.{field}는 0~100 범위의 숫자여야 합니다: {value!r}"
            )


def validate_state_output(name: str, state: ReadingSessionState) -> None:
    """state에서 `name` 에이전트의 산출을 뽑아 계약을 검증한다."""
    spec = _SPECS.get(name)
    if spec is None:
        raise ContractError(f"알 수 없는 계약 이름: {name!r}")

    source = spec["source"]
    if source == "state":
        payload = {field: state.get(field) for field in spec["required"]}
    else:
        payload = state.get(source) or {}

    validate_contract(name, payload)


def _is_score(value: object) -> bool:
    # bool은 int 하위형이지만 점수로 인정하지 않는다.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    number = float(value)
    return math.isfinite(number) and 0.0 <= number <= 100.0
