"""3번(Cognitive Care) 실제 모듈 연결 검증.

stub↔real 토글로 3번 구현이 붙는지, 계약 필드를 채우는지, 전체 폐루프가
real 모드에서도 깨지지 않는지 확인한다.
"""

from __future__ import annotations

import pytest

from backend.app.agents.cognitive_care_client import run_cognitive_care
from backend.app.agents.real.cognitive_care_service import calculate_focus_score
from backend.app.demo.m1_scenario import build_m1_demo_state, DEMO_READING_EVENTS
from backend.app.orchestrator.contracts import validate_state_output
from backend.app.orchestrator.graph import run_reading_session


@pytest.fixture
def _real_cognitive_care(monkeypatch):
    monkeypatch.setenv("LITERACY_COGNITIVE_CARE_IMPL", "real")


def test_real_cognitive_care_fills_contract_fields(_real_cognitive_care):
    state = build_m1_demo_state()
    out = run_cognitive_care(state)

    # 3번 원본 함수 결과와 일치해야 한다(어댑터가 값을 변형하지 않음).
    assert out["focus_score"] == calculate_focus_score(DEMO_READING_EVENTS)
    assert out["engagement_score"] == out["focus_score"]
    assert isinstance(out["intervention_needed"], bool)

    # 계약 검증을 통과해야 한다(필수 필드 + 0..100 범위).
    validate_state_output("cognitive_care", out)


def test_real_cognitive_care_empty_events_is_full_focus(_real_cognitive_care):
    state = build_m1_demo_state()
    state["reading_events"] = []
    out = run_cognitive_care(state)
    assert out["focus_score"] == 100.0
    assert out["intervention_needed"] is False


def test_none_duration_events_do_not_crash(_real_cognitive_care):
    """CP-1: duration_ms=None인 blur/scroll이 들어와도 어댑터가 크래시를 막는다.

    3번 원본 함수는 None을 못 막고 TypeError로 죽지만(H1), 어댑터의 _sanitize_events가
    None 키를 제거해 vendored 함수의 기본값(1000)이 살아나야 한다.
    """
    state = build_m1_demo_state()
    state["reading_events"] = [
        {"type": "blur", "timestamp_ms": 1000, "duration_ms": None},
        {"type": "scroll", "timestamp_ms": 2000, "duration_ms": None},
    ]
    out = run_cognitive_care(state)
    assert 0.0 <= out["focus_score"] <= 100.0
    validate_state_output("cognitive_care", out)


def test_closed_loop_runs_with_real_cognitive_care(_real_cognitive_care):
    """real cognitive_care를 끼운 채 전체 폐루프가 끝까지 돈다."""
    result = run_reading_session(build_m1_demo_state())

    assert 0.0 <= result["literacy_score"] <= 100.0
    assert "intervention" in result
    assert result["score_breakdown"]["engagement_score"] == result["focus_score"]
    # trace에 cognitive_care 단계가 기록된다.
    assert any(t.get("step") == "cognitive_care" for t in result["trace"])
