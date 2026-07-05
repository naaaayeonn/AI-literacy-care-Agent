"""Adapter for the Content Reducer agent."""

from __future__ import annotations

from backend.app.agents.config import run_agent
from backend.app.agents.real.content_reducer_bridge import content_reducer_bridge
from backend.app.agents.stubs.content_reducer_stub import content_reducer_stub
from backend.app.orchestrator.state import ReadingSessionState

# 임시 브릿지(1번) — 오프라인 chunks/terms/difficulty + Gemini 무료 재구성.
# 2번 실구현이 오면 이 한 줄만 교체한다(HANDOFF_TO_ROLE2_GEMINI_BRIDGE.md).
# 활성화: LITERACY_CONTENT_REDUCER_IMPL=real
_REAL_IMPL = content_reducer_bridge


def run_content_reducer(state: ReadingSessionState) -> ReadingSessionState:
    """Run the configured Content Reducer implementation."""
    return run_agent("content_reducer", state, stub=content_reducer_stub, real=_REAL_IMPL)
