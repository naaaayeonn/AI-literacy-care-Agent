"""계약 검증 테스트 — 실제 모듈 교체(M2) 시 계약 위반을 잡는지 확인."""

from __future__ import annotations

import pytest

from backend.app.agents.config import run_agent
from backend.app.agents.stubs.cognitive_care_stub import cognitive_care_stub
from backend.app.orchestrator.contracts import (
    ContractError,
    validate_contract,
    validate_state_output,
)
from backend.app.orchestrator.state import create_initial_state


def _state():
    return create_initial_state(
        session_id="s1",
        user_id="u1",
        document_id="doc1",
        raw_text="sample",
    )


# --- validate_contract ---------------------------------------------------


def test_valid_content_reducer_payload_passes():
    payload = {
        "chunks": [{"chunk_id": "chunk_01"}],
        "simplified_text": "easy",
        "terms": [],
        "difficulty_score": 60.0,
    }
    assert validate_contract("content_reducer", payload) is None


def test_missing_required_field_raises_with_field_name():
    payload = {"chunks": [], "simplified_text": "x", "terms": []}  # difficulty_score 없음
    with pytest.raises(ContractError, match="difficulty_score"):
        validate_contract("content_reducer", payload)


def test_score_field_out_of_range_raises():
    payload = {
        "focus_score": 140.0,  # 0~100 벗어남
        "engagement_score": 50.0,
        "intervention_needed": False,
    }
    with pytest.raises(ContractError, match="focus_score"):
        validate_contract("cognitive_care", payload)


def test_bool_is_not_accepted_as_score():
    payload = {
        "focus_score": True,  # bool은 점수로 인정 안 함
        "engagement_score": 50.0,
        "intervention_needed": False,
    }
    with pytest.raises(ContractError, match="focus_score"):
        validate_contract("cognitive_care", payload)


def test_intervention_needed_false_is_valid_required_field():
    # False는 "누락"이 아니다(None만 누락 취급).
    payload = {"focus_score": 50.0, "engagement_score": 50.0, "intervention_needed": False}
    assert validate_contract("cognitive_care", payload) is None


def test_non_dict_payload_raises():
    with pytest.raises(ContractError):
        validate_contract("reward", ["not", "a", "dict"])


def test_unknown_contract_name_raises():
    with pytest.raises(ContractError, match="알 수 없는"):
        validate_contract("mystery_agent", {})


# --- validate_state_output (중첩 source 포함) ----------------------------


def test_validate_state_output_reads_nested_reward():
    state = _state()
    state["reward"] = {"xp": 100, "badge": "steady", "message": "ok"}
    assert validate_state_output("reward", state) is None


def test_validate_state_output_missing_nested_reward_raises():
    state = _state()  # reward 없음
    with pytest.raises(ContractError, match="reward"):
        validate_state_output("reward", state)


def test_stub_output_satisfies_contract():
    # 우리 stub은 계약을 지켜야 한다(자기 점검).
    state = cognitive_care_stub(_state())
    assert validate_state_output("cognitive_care", state) is None


# --- run_agent: real 모듈만 검증 -----------------------------------------


def _good_real(state):
    state["focus_score"] = 55.0
    state["engagement_score"] = 55.0
    state["intervention_needed"] = False
    return state


def _bad_real(state):
    return state  # 필수 필드 채우지 않음 → 계약 위반


def test_run_agent_validates_real_output(monkeypatch):
    monkeypatch.setenv("LITERACY_COGNITIVE_CARE_IMPL", "real")
    with pytest.raises(ContractError):
        run_agent("cognitive_care", _state(), stub=cognitive_care_stub, real=_bad_real)


def test_run_agent_accepts_valid_real_output(monkeypatch):
    monkeypatch.setenv("LITERACY_COGNITIVE_CARE_IMPL", "real")
    result = run_agent("cognitive_care", _state(), stub=cognitive_care_stub, real=_good_real)
    assert result["focus_score"] == 55.0


def test_run_agent_skips_validation_for_stub(monkeypatch):
    # stub 모드(기본)에서는 real이 잘못돼도 검증하지 않고 stub을 쓴다.
    monkeypatch.delenv("LITERACY_COGNITIVE_CARE_IMPL", raising=False)
    monkeypatch.delenv("LITERACY_AGENT_IMPL", raising=False)
    result = run_agent("cognitive_care", _state(), stub=cognitive_care_stub, real=_bad_real)
    assert "focus_score" in result  # stub이 채움
