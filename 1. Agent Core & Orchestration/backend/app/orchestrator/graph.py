"""M0 orchestrator flow for the AI literacy care agent."""

from __future__ import annotations

from collections.abc import Callable
from time import perf_counter

from backend.app.agents.cognitive_care_client import run_cognitive_care
from backend.app.agents.content_reducer_client import run_content_reducer
from backend.app.agents.literacy_profile_client import run_literacy_profile_agent
from backend.app.agents.reward_client import run_reward_agent

from .errors import apply_fallback
from .routing import decide_intervention
from .score import calculate_literacy_score
from .self_correction import review_session
from .state import ReadingSessionState

Step = Callable[[ReadingSessionState], ReadingSessionState]
FlowStep = tuple[str, Step]

DEFAULT_STEPS: tuple[FlowStep, ...] = (
    ("content_reducer", run_content_reducer),
    ("cognitive_care", run_cognitive_care),
    ("routing_decision", decide_intervention),
    ("score_engine", calculate_literacy_score),
    ("reward", run_reward_agent),
    ("profile_update", run_literacy_profile_agent),
    ("self_correction", review_session),
)


def run_reading_session(
    state: ReadingSessionState, steps: tuple[FlowStep, ...] = DEFAULT_STEPS
) -> ReadingSessionState:
    """Run the stub-backed session from raw text to final result fields."""
    for step_name, step in steps:
        state = _run_step(state, step_name, step)
    return state


def _run_step(state: ReadingSessionState, step_name: str, step: Step) -> ReadingSessionState:
    started = perf_counter()
    try:
        state = step(state)
    except Exception as exc:
        latency_ms = int((perf_counter() - started) * 1000)
        state["errors"].append(
            {
                "step": step_name,
                "error": str(exc),
                "error_type": type(exc).__name__,
            }
        )
        state = apply_fallback(step_name, state, exc)
        state["trace"].append(
            {
                "step": step_name,
                "status": "fallback",
                "latency_ms": latency_ms,
                "detail": {"error": str(exc), "error_type": type(exc).__name__},
            }
        )
        return state

    latency_ms = int((perf_counter() - started) * 1000)
    state["trace"].append({"step": step_name, "status": "success", "latency_ms": latency_ms})
    return state
