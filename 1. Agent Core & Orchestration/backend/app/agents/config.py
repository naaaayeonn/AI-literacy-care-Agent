"""에이전트 구현 전환(stub ↔ real) — M2 선행 작업.

각 어댑터(`*_client.py`)는 이 모듈의 `resolve_impl`로 실행할 구현을 고른다.
실제 팀원 모듈이 아직 없으므로, 기본값은 항상 stub이며 `real`을 골라도
실제 구현이 등록되지 않았으면 stub으로 안전하게 폴백한다(데모 보호).

전환 우선순위 (높은 쪽이 우선):
1. 에이전트별 환경변수  `LITERACY_<AGENT>_IMPL`  (예: LITERACY_CONTENT_REDUCER_IMPL=real)
2. 전역 환경변수        `LITERACY_AGENT_IMPL`
3. 기본값              "stub"

실제 모듈이 준비되면 통합 담당(1번)은 매칭되는 `*_client.py`에서
`resolve_impl(..., real=<real_fn>)` 인자만 채우면 된다. 함수 이름과
시그니처는 그대로 유지한다(INTEGRATION_CHECKLIST 규칙).
"""

from __future__ import annotations

import os
from collections.abc import Callable

from backend.app.orchestrator.state import ReadingSessionState

AgentFn = Callable[[ReadingSessionState], ReadingSessionState]

STUB = "stub"
REAL = "real"


def impl_mode(agent: str) -> str:
    """현재 설정된 구현 모드("stub" 또는 "real")를 반환한다."""
    specific = os.getenv(f"LITERACY_{agent.upper()}_IMPL")
    mode = specific or os.getenv("LITERACY_AGENT_IMPL") or STUB
    return mode.strip().lower()


def resolve_impl(agent: str, *, stub: AgentFn, real: AgentFn | None = None) -> AgentFn:
    """설정에 따라 stub 또는 real 구현을 반환한다.

    `real`을 선택했지만 실제 구현이 등록되지 않은 경우 stub으로 폴백한다.
    데모가 절대 끊기지 않도록 하기 위한 의도된 안전장치다.
    """
    if impl_mode(agent) == REAL and real is not None:
        return real
    return stub


def run_agent(
    agent: str, state: ReadingSessionState, *, stub: AgentFn, real: AgentFn | None = None
) -> ReadingSessionState:
    """에이전트를 실행하고, real 모듈이 쓰였으면 출력 계약을 검증한다.

    - stub은 우리가 신뢰하므로 검증을 건너뛴다(기존 동작 보존).
    - real 모듈은 계약 위반 시 ContractError를 던진다. orchestrator graph는
      이를 fallback으로 받아 흐름을 유지한다.
    """
    impl = resolve_impl(agent, stub=stub, real=real)
    state = impl(state)
    if real is not None and impl is real:
        # 늦은 import로 순환 의존을 피한다.
        from backend.app.orchestrator.contracts import validate_state_output

        validate_state_output(agent, state)
    return state
