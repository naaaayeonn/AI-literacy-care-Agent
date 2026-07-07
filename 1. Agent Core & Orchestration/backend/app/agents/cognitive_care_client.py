"""Adapter for the Cognitive Care agent."""

from __future__ import annotations

from backend.app.agents.config import run_agent
from backend.app.agents.real.cognitive_care_service import (
    calculate_focus_score,
    determine_intervention,
)
from backend.app.agents.stubs.cognitive_care_stub import cognitive_care_stub
from backend.app.orchestrator.state import ReadingSessionState


def _sanitize_events(events: list) -> list:
    """vendored `calculate_focus_score`가 크래시나지 않도록 이벤트를 방어한다(CP-1/H1).

    3번 원본은 `event.get("duration_ms", 1000)`을 쓰는데, 키가 **있고 값이 None**이면
    default가 먹지 않아 `None / 1000.0`(blur)·`None < 300`(scroll)에서 TypeError로 죽는다.
    정상 경로(`_normalize_events`)는 이미 None 키를 제거하지만, 정규화를 거치지 않은
    인입이나 3번 원본 교체 시에도 데모가 끊기지 않도록 어댑터에서 한 번 더 막는다.
    (원본 `cognitive_care_service.py`는 정책상 verbatim 유지 → 방어는 여기에 둔다.)
    """
    safe: list = []
    for event in events:
        if isinstance(event, dict) and "duration_ms" in event and event["duration_ms"] is None:
            event = {k: v for k, v in event.items() if k != "duration_ms"}
        safe.append(event)
    return safe


def _cognitive_care_real(state: ReadingSessionState) -> ReadingSessionState:
    """3번 실제 모듈을 ReadingSessionState 계약으로 매핑한다.

    3번 `cognitive_care_service`는 순수 함수만 제공하므로, reading_events를
    넘겨 focus_score를 받고 계약 필드(focus/engagement/intervention_needed)를 채운다.

    주의:
    - 3번 모듈은 engagement_score를 산출하지 않는다. 스텁과 동일한 관례로
      engagement_score = focus_score 로 둔다(별도 신호가 생기면 교체).
    - 최종 intervention 명령(level/type/message)은 orchestrator의 routing.py가
      단독 결정한다. 여기서는 intervention_needed 플래그까지만 채운다.
    - duration_ms=None 방어는 `_sanitize_events`가 담당한다(CP-1).
    """
    events = _sanitize_events(state.get("reading_events", []))
    focus_score = calculate_focus_score(events)
    needed, _level, _message = determine_intervention(focus_score)

    state["focus_score"] = focus_score
    state["engagement_score"] = focus_score
    state["intervention_needed"] = needed
    return state


# 실제 3번 모듈 연결 완료 — LITERACY_COGNITIVE_CARE_IMPL=real 로 전환.
_REAL_IMPL = _cognitive_care_real


def run_cognitive_care(state: ReadingSessionState) -> ReadingSessionState:
    """Run the configured Cognitive Care implementation."""
    return run_agent("cognitive_care", state, stub=cognitive_care_stub, real=_REAL_IMPL)
