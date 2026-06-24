"""에이전트 입출력 계약 (런타임 검증용).

[초안: 6/20 / 구체화: 6/21~]

각 팀원 모듈의 입력/출력 JSON 형태를 코드로 고정해, 실제 모듈을 붙일 때
계약 위반을 명확한 에러로 잡는다. 문서 버전은 docs/API_CONTRACT.md.

오늘은 시그니처/필드명만 자리 잡고, Pydantic 모델 또는 검증 함수는 통합
단계(M2, 7/5~)에 채운다.
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
    "evidence",
)

# 4번 Reward
REWARD_OUTPUT_FIELDS = ("xp", "badge", "message")

# 5번 Literacy Profile
PROFILE_OUTPUT_FIELDS = ("reading_level", "trend", "weaknesses", "recommended_next_action")

# 6번 QA / Evaluation
QA_OUTPUT_FIELDS = ("passed", "faithfulness", "answer_relevance", "warnings")


def validate_contract(name: str, payload: dict) -> None:
    """필수 필드 누락 시 명확한 에러를 던진다.

    TODO(M2): 계약별 필수 필드 검증 구현. 지금은 자리만.
    """
    raise NotImplementedError("통합 단계에서 구현 예정")
