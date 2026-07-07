from __future__ import annotations

import pytest

from backend.app.agents import config
from backend.app.agents.content_reducer_client import run_content_reducer
from backend.app.orchestrator.state import create_initial_state


def _state():
    return create_initial_state(
        session_id="s1",
        user_id="u1",
        document_id="doc1",
        raw_text="Sample text",
    )


def _real_marker(state):
    state["difficulty_score"] = 99.0
    return state


def _stub_marker(state):
    state["difficulty_score"] = 1.0
    return state


@pytest.fixture(autouse=True)
def _clear_impl_env(monkeypatch):
    """각 테스트가 깨끗한 환경변수 상태에서 시작하도록 보장한다."""
    for key in ("LITERACY_AGENT_IMPL", "LITERACY_CONTENT_REDUCER_IMPL"):
        monkeypatch.delenv(key, raising=False)


def test_default_mode_is_stub():
    assert config.impl_mode("content_reducer") == "stub"


def test_global_env_selects_real():
    import os

    os.environ["LITERACY_AGENT_IMPL"] = "REAL"
    try:
        assert config.impl_mode("content_reducer") == "real"
    finally:
        del os.environ["LITERACY_AGENT_IMPL"]


def test_per_agent_env_overrides_global(monkeypatch):
    monkeypatch.setenv("LITERACY_AGENT_IMPL", "stub")
    monkeypatch.setenv("LITERACY_CONTENT_REDUCER_IMPL", "real")
    assert config.impl_mode("content_reducer") == "real"


def test_resolve_returns_stub_by_default():
    impl = config.resolve_impl("content_reducer", stub=_stub_marker, real=_real_marker)
    assert impl is _stub_marker


def test_resolve_returns_real_when_selected_and_registered(monkeypatch):
    monkeypatch.setenv("LITERACY_CONTENT_REDUCER_IMPL", "real")
    impl = config.resolve_impl("content_reducer", stub=_stub_marker, real=_real_marker)
    assert impl is _real_marker


def test_resolve_falls_back_to_stub_when_real_missing(monkeypatch):
    """real을 골랐지만 실제 구현이 없으면 stub으로 폴백한다(데모 보호)."""
    monkeypatch.setenv("LITERACY_CONTENT_REDUCER_IMPL", "real")
    impl = config.resolve_impl("content_reducer", stub=_stub_marker, real=None)
    assert impl is _stub_marker


def test_client_uses_real_bridge_when_selected(monkeypatch):
    """content_reducer는 이제 real 브릿지(1번 임시)가 등록돼 있어, real 선택 시 브릿지가 실행된다.

    (Gemini 호출은 막고 오프라인 경로만 확인 — 스텁의 chunk_01이 아니라
    2번 ChunkDict 형태 chunk_{document_id}_NN을 낸다.)
    """
    from backend.app.agents.real import content_reducer_bridge

    monkeypatch.setenv("LITERACY_CONTENT_REDUCER_IMPL", "real")
    monkeypatch.setattr(content_reducer_bridge, "_restructure", lambda text: None)
    result = run_content_reducer(_state())
    assert result["chunks"][0]["chunk_id"].startswith("chunk_doc1_")
    assert result["simplified_text"] == "Sample text"  # Gemini 폴백 → 원문
