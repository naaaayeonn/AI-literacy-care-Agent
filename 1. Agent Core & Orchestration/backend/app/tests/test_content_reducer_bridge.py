"""content_reducer 임시 브릿지(1번) 검증.

Gemini 호출은 네트워크·quota에 의존하므로 테스트에서는 `_restructure`를 막아
오프라인 경로(청킹·용어검색·난이도·원문 폴백)의 결정론과 계약만 검증한다.
"""

from __future__ import annotations

import pytest

from backend.app.agents import content_reducer_client
from backend.app.agents.real import content_reducer_bridge
from backend.app.agents.real.content_reducer_bridge import content_reducer_bridge as bridge
from backend.app.orchestrator.contracts import validate_state_output
from backend.app.orchestrator.graph import run_reading_session
from backend.app.orchestrator.state import create_initial_state

SAMPLE_TEXT = (
    "인공지능은 인간의 학습과 추론을 모방한다. 머신러닝은 데이터를 통해 스스로 학습한다.\n\n"
    "딥러닝은 인공 신경망을 여러 층으로 쌓아 복잡한 패턴을 학습하는 기법이다."
)


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """모든 테스트에서 Gemini 호출을 막고 원문 폴백을 강제한다."""
    monkeypatch.setattr(content_reducer_bridge, "_restructure", lambda text: None)


def _state(raw_text: str):
    return create_initial_state(
        session_id="s1", user_id="u1", document_id="doc001", raw_text=raw_text, profile={}
    )


def test_bridge_fills_contract_fields():
    out = bridge(_state(SAMPLE_TEXT))
    assert out["chunks"] and all("chunk_id" in c for c in out["chunks"])
    assert all("original_text" in c and "char_start" in c for c in out["chunks"])
    assert 0.0 <= out["difficulty_score"] <= 100.0
    assert out["simplified_text"] == SAMPLE_TEXT  # Gemini 폴백 → 원문 그대로
    validate_state_output("content_reducer", out)


def test_bridge_finds_trusted_terms():
    out = bridge(_state(SAMPLE_TEXT))
    found = {t["term"] for t in out["terms"]}
    assert {"인공지능", "머신러닝", "딥러닝"} <= found
    # 검색(생성 아님) → 출처가 실려 있고 faithfulness=1.0
    assert all(t["source"] and t["faithfulness_score"] == 1.0 for t in out["terms"])


def test_bridge_is_deterministic():
    a = bridge(_state(SAMPLE_TEXT))
    b = bridge(_state(SAMPLE_TEXT))
    assert a["chunks"] == b["chunks"]
    assert a["difficulty_score"] == b["difficulty_score"]
    assert a["terms"] == b["terms"]


def test_bridge_empty_text_is_contract_safe():
    out = bridge(_state(""))
    assert len(out["chunks"]) == 1
    assert out["terms"] == []
    validate_state_output("content_reducer", out)


def test_restructure_returns_none_without_key(monkeypatch):
    monkeypatch.setattr(content_reducer_bridge, "_load_dotenv_key", lambda name: None)
    assert content_reducer_bridge._restructure("아무 텍스트나") is None


def test_closed_loop_runs_with_real_content_reducer(monkeypatch):
    monkeypatch.setenv("LITERACY_CONTENT_REDUCER_IMPL", "real")
    state = _state(SAMPLE_TEXT)
    # 확장 시작 경로처럼 content_reducer를 real로 실행 → 계약 통과해야 한다.
    state = content_reducer_client.run_content_reducer(state)
    assert state["chunks"] and state["terms"]

    result = run_reading_session(state)
    assert 0.0 <= result["literacy_score"] <= 100.0
    assert any(t.get("step") == "content_reducer" for t in result["trace"])
