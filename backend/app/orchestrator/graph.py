"""Orchestrator flow — 에이전트 실행 순서와 상태 전이.

[구현 예정: 6/22 M0 / 6/23 상태 전이]

초기 버전은 LangGraph 없이 단순 Python 함수 체인으로 만든다. 중요한 것은
호출 순서와 state 변경이 명확하고, 각 단계가 trace에 기록되며, 한 에이전트
실패가 전체를 멈추지 않는 것이다. (LangGraph StateGraph 전환은 그 이후.)

최소 흐름:
    create_state
    → content_reducer
    → cognitive_care
    → routing_decision
    → score_engine
    → reward
    → profile_update
    → final_result
"""

from __future__ import annotations

from .state import ReadingSessionState


def run_reading_session(state: ReadingSessionState) -> ReadingSessionState:
    """한 세션을 시작부터 결과까지 실행한다.

    TODO(6/22): stub 에이전트를 순서대로 호출하고 각 단계를 trace에 기록.
    TODO(6/23): 단계별 fallback(errors.py) 연결.
    """
    raise NotImplementedError("M0(6/22)에서 stub 흐름 구현 예정")
