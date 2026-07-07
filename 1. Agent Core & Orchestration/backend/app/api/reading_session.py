"""Reading session API routes for the orchestrator core."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException

from backend.app.agents.cognitive_care_client import run_cognitive_care
from backend.app.agents.content_reducer_client import run_content_reducer
from backend.app.orchestrator.graph import run_reading_session
from backend.app.orchestrator.quiz import apply_quiz_result
from backend.app.orchestrator.routing import decide_intervention
from backend.app.orchestrator.state import ReadingEvent, ReadingSessionState, create_initial_state

router = APIRouter(prefix="/reading-sessions", tags=["reading-sessions"])

SESSION_STORE: dict[str, ReadingSessionState] = {}


@router.post("/start")
def start_session(payload: dict) -> dict:
    """Create a session and return reader setup data."""
    raw_text = _required_str(payload, "raw_text")
    user_id = str(payload.get("user_id") or "anonymous")
    document_id = str(payload.get("document_id") or "document_unknown")
    session_id = str(payload.get("session_id") or uuid4())
    profile = payload.get("profile") if isinstance(payload.get("profile"), dict) else {}

    state = create_initial_state(
        session_id=session_id,
        user_id=user_id,
        document_id=document_id,
        raw_text=raw_text,
        profile=profile,
    )
    state = run_content_reducer(state)
    SESSION_STORE[session_id] = state

    return {
        "session_id": session_id,
        "chunks": state.get("chunks", []),
        "simplified_text": state.get("simplified_text", ""),
        "terms": state.get("terms", []),
        "difficulty_score": state.get("difficulty_score", 50.0),
    }


@router.post("/{session_id}/events")
def push_events(session_id: str, payload: dict) -> dict:
    """Append reading events and return the current intervention command."""
    state = _get_state(session_id)
    events = payload.get("events", [])
    if not isinstance(events, list):
        raise HTTPException(status_code=422, detail="events must be a list")

    state["reading_events"].extend(_normalize_events(events))
    state = run_cognitive_care(state)
    state = decide_intervention(state)
    SESSION_STORE[session_id] = state

    return {
        "session_id": session_id,
        "focus_score": state.get("focus_score"),
        "engagement_score": state.get("engagement_score"),
        "intervention": state.get("intervention"),
    }


@router.post("/{session_id}/quiz")
def submit_quiz(session_id: str, payload: dict) -> dict:
    """Attach quiz result to the session state."""
    state = _get_state(session_id)
    state = apply_quiz_result(state, payload)
    SESSION_STORE[session_id] = state

    return {"session_id": session_id, "quiz_result": state["quiz_result"]}


@router.post("/{session_id}/finish")
def finish_session(session_id: str) -> dict:
    """Run the full orchestrator and return final session result."""
    state = _get_state(session_id)
    state = run_reading_session(state)
    SESSION_STORE[session_id] = state
    return _final_response(state)


@router.get("/{session_id}/result")
def get_result(session_id: str) -> dict:
    """Return the latest stored session result."""
    state = _get_state(session_id)
    return _final_response(state)


def _get_state(session_id: str) -> ReadingSessionState:
    try:
        return SESSION_STORE[session_id]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="session not found") from exc


def _required_str(payload: dict, field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise HTTPException(status_code=422, detail=f"{field} is required")
    return value


def _normalize_events(events: list[dict]) -> list[ReadingEvent]:
    normalized: list[ReadingEvent] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        event_type = event.get("type")
        timestamp_ms = event.get("timestamp_ms")
        if event_type not in {"scroll", "pause", "blur", "focus", "click"}:
            continue
        if not isinstance(timestamp_ms, int):
            continue

        normalized_event: ReadingEvent = {"type": event_type, "timestamp_ms": timestamp_ms}
        if isinstance(event.get("position"), int | float):
            normalized_event["position"] = max(0.0, min(1.0, float(event["position"])))
        if isinstance(event.get("duration_ms"), int):
            normalized_event["duration_ms"] = max(0, event["duration_ms"])
        if isinstance(event.get("metadata"), dict):
            normalized_event["metadata"] = event["metadata"]
        normalized.append(normalized_event)
    return normalized


def _final_response(state: ReadingSessionState) -> dict:
    return {
        "session_id": state["session_id"],
        "chunks": state.get("chunks", []),
        "intervention": state.get("intervention"),
        "literacy_score": state.get("literacy_score"),
        "score_breakdown": state.get("score_breakdown"),
        "reward": state.get("reward"),
        "updated_profile": state.get("updated_profile"),
        "warnings": state.get("warnings", []),
        "trace": state.get("trace", []),
        "errors": state.get("errors", []),
    }
