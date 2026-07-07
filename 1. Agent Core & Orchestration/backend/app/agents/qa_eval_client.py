"""Adapter for the QA/Evaluation agent."""

from __future__ import annotations

from backend.app.orchestrator.state import ReadingSessionState


def run_qa_eval_agent(state: ReadingSessionState) -> ReadingSessionState:
    """No-op QA adapter until the QA module is integrated."""
    return state
