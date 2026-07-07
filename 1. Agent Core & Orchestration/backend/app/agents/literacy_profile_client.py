"""Adapter for the Literacy Profile agent."""

from __future__ import annotations

from backend.app.agents.config import run_agent
from backend.app.agents.stubs.literacy_profile_stub import literacy_profile_stub
from backend.app.orchestrator.state import ReadingSessionState

# 실제 5번 모듈이 준비되면 real=<real_fn>을 채운다.
_REAL_IMPL = None


def run_literacy_profile_agent(state: ReadingSessionState) -> ReadingSessionState:
    """Run the configured Literacy Profile implementation."""
    return run_agent("literacy_profile", state, stub=literacy_profile_stub, real=_REAL_IMPL)
