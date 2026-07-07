"""Adapter for the Reward agent."""

from __future__ import annotations

from backend.app.agents.config import run_agent
from backend.app.agents.stubs.reward_stub import reward_stub
from backend.app.orchestrator.state import ReadingSessionState

# 실제 4번 모듈이 준비되면 real=<real_fn>을 채운다.
_REAL_IMPL = None


def run_reward_agent(state: ReadingSessionState) -> ReadingSessionState:
    """Run the configured Reward implementation."""
    return run_agent("reward", state, stub=reward_stub, real=_REAL_IMPL)
