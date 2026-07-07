"""에이전트 실패 시 fallback — 한 단계 실패가 전체 데모를 멈추지 않게 한다.

[구현 예정: 6/23 상태 전이 / 6/26 이후 보강]

기본값 정책 (ARCHITECTURE §4 errors):
    Content Reducer 실패 : raw_text를 그대로 단일 chunk로, difficulty_score=50
    Cognitive Care 실패  : focus_score=60, intervention_level="none"
    Reward 실패          : reward 없이 score 결과만 반환
    Profile 실패         : updated_profile 없이 세션 결과 저장
    QA 실패              : 사용자 흐름 유지, trace에 warning 기록

모든 fallback은 trace에 status="fallback"으로 남긴다.
"""

from __future__ import annotations


class AgentError(Exception):
    """서브 에이전트 실행 실패를 나타내는 기본 예외."""


# TODO(6/23): 단계별 fallback 적용 함수(apply_*_fallback) 구현.
