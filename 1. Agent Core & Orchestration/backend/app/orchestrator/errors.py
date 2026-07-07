"""Fallback behavior for orchestrator agent failures."""

from __future__ import annotations

from collections.abc import Callable

from .state import ReadingSessionState


class AgentError(Exception):
    """Base exception for sub-agent execution failures."""


Fallback = Callable[[ReadingSessionState, Exception], ReadingSessionState]


def apply_fallback(step_name: str, state: ReadingSessionState, error: Exception) -> ReadingSessionState:
    """Apply the registered fallback for a failed step."""
    fallback = FALLBACKS.get(step_name, apply_generic_fallback)
    return fallback(state, error)


def apply_content_reducer_fallback(
    state: ReadingSessionState, error: Exception
) -> ReadingSessionState:
    """Keep the flow alive with a single raw-text chunk."""
    raw_text = state.get("raw_text", "")
    state["chunks"] = [
        {
            "chunk_id": "chunk_fallback_01",
            "text": raw_text,
            "summary": raw_text[:80],
            "difficulty": 50,
        }
    ]
    state["simplified_text"] = raw_text
    state["terms"] = []
    state["difficulty_score"] = 50.0
    return state


def apply_cognitive_care_fallback(
    state: ReadingSessionState, error: Exception
) -> ReadingSessionState:
    """Use neutral focus defaults when behavior analysis fails."""
    state["focus_score"] = 60.0
    state["engagement_score"] = 60.0
    state["intervention_needed"] = False
    state["intervention_level"] = "none"
    state["intervention_message"] = ""
    state["intervention"] = {
        "level": "none",
        "type": "none",
        "message": "",
        "reason": "fallback_cognitive_care",
    }
    return state


def apply_routing_fallback(state: ReadingSessionState, error: Exception) -> ReadingSessionState:
    """Avoid interrupting the user if intervention routing fails."""
    state["intervention_needed"] = False
    state["intervention_level"] = "none"
    state["intervention_message"] = ""
    state["intervention"] = {
        "level": "none",
        "type": "none",
        "message": "",
        "reason": "fallback_routing",
    }
    return state


def apply_score_fallback(state: ReadingSessionState, error: Exception) -> ReadingSessionState:
    """Return a neutral, explainable score when score calculation fails."""
    state["comprehension_score"] = 60.0
    state["literacy_score"] = 60.0
    state["score_breakdown"] = {
        "comprehension_score": 60.0,
        "engagement_score": float(state.get("focus_score", 60.0)),
        "difficulty_score": float(state.get("difficulty_score", 50.0)),
        "cross_validation_penalty": 0.0,
        "reason": "Fallback score was used because score calculation failed.",
    }
    return state


def apply_reward_fallback(state: ReadingSessionState, error: Exception) -> ReadingSessionState:
    """Reward is optional for M0, so preserve score results only."""
    state.pop("reward", None)
    return state


def apply_profile_fallback(state: ReadingSessionState, error: Exception) -> ReadingSessionState:
    """Profile update is optional for M0, so preserve session results only."""
    state.pop("updated_profile", None)
    return state


def apply_self_correction_fallback(
    state: ReadingSessionState, error: Exception
) -> ReadingSessionState:
    """Quality review is non-blocking; keep results and note the failure."""
    state.setdefault("warnings", [])
    state["warnings"].append(
        {
            "code": "self_correction_failed",
            "severity": "warning",
            "message": "결과 품질 검토 단계가 실패했습니다.",
            "detail": {"error": str(error)},
        }
    )
    return state


def apply_generic_fallback(state: ReadingSessionState, error: Exception) -> ReadingSessionState:
    """Default fallback for non-critical future steps."""
    return state


FALLBACKS: dict[str, Fallback] = {
    "content_reducer": apply_content_reducer_fallback,
    "cognitive_care": apply_cognitive_care_fallback,
    "routing_decision": apply_routing_fallback,
    "score_engine": apply_score_fallback,
    "reward": apply_reward_fallback,
    "profile_update": apply_profile_fallback,
    "self_correction": apply_self_correction_fallback,
}
