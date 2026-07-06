"""에이전트 간 계약 (인터페이스 정의).

[초안: 6/20 / 구체화: 6/21~ / 검증 구현: M2]

각 역할의 입력/출력 JSON 형태를 코드로 명세하고, 누락 필드가 있으면
에러를 조기에 잡는다. 상세 명세는 docs/API_CONTRACT.md.
"""

from __future__ import annotations

# 2번 Content Reducer
CONTENT_REDUCER_OUTPUT_FIELDS = ("chunks", "simplified_text", "terms", "difficulty_score")

# 3번 Cognitive Care
COGNITIVE_CARE_OUTPUT_FIELDS = (
    "focus_score",
    "engagement_score",
    "intervention_needed",
    "intervention_level",
)

# 4번 Reward
REWARD_OUTPUT_FIELDS = ("xp", "badge", "message")

# 5번 Literacy Profile
PROFILE_OUTPUT_FIELDS = ("reading_level", "trend", "weaknesses", "recommended_next_action")

# 6번 QA / Evaluation
QA_OUTPUT_FIELDS = ("passed", "faithfulness", "answer_relevance", "warnings")


# 계약별 필수 필드 매핑
_CONTRACT_REGISTRY: dict[str, tuple[str, ...]] = {
    "content_reducer": CONTENT_REDUCER_OUTPUT_FIELDS,
    "cognitive_care": COGNITIVE_CARE_OUTPUT_FIELDS,
    "reward": REWARD_OUTPUT_FIELDS,
    "profile": PROFILE_OUTPUT_FIELDS,
    "qa": QA_OUTPUT_FIELDS,
}


def validate_contract(name: str, payload: dict) -> None:
    """필수 필드 존재 여부 확인.
    
    누락 필드가 있으면 ContractValidationError를 발생시킨다.
    """
    required = _CONTRACT_REGISTRY.get(name)
    if required is None:
        return  # 미등록 계약은 통과
    
    missing = [f for f in required if f not in payload]
    if missing:
        raise ContractValidationError(
            f"Contract '{name}' validation failed. Missing fields: {missing}"
        )


class ContractValidationError(Exception):
    """계약 검증 실패 예외."""
    pass
