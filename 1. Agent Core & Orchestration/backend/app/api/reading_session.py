"""Reading session API routes for the orchestrator core."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException

from backend.app.agents.cognitive_care_client import run_cognitive_care
from backend.app.agents.content_reducer_client import run_content_reducer
from backend.app.orchestrator.graph import run_reading_session
from backend.app.agents.qa_eval_client import run_qa_eval_agent
from backend.app.orchestrator.quiz import (
    apply_pick_quiz,
    apply_quiz_result,
    prebuild_quizzes,
    submit_ox_quiz,
)
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
    state = prebuild_quizzes(state)  # 각 chunk O/X 프리젠 → state["quizzes"]
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
    state = apply_pick_quiz(state)  # 트리거 A/B면 intervention에 O/X quiz_data 주입
    SESSION_STORE[session_id] = state

    return {
        "session_id": session_id,
        "focus_score": state.get("focus_score"),
        "engagement_score": state.get("engagement_score"),
        "intervention": state.get("intervention"),
    }


@router.post("/{session_id}/quiz")
def submit_quiz(session_id: str, payload: dict) -> dict:
    """Attach quiz result to the session state (집계형·하위호환)."""
    state = _get_state(session_id)
    state = apply_quiz_result(state, payload)
    SESSION_STORE[session_id] = state

    return {"session_id": session_id, "quiz_result": state["quiz_result"]}


@router.post("/{session_id}/quiz/submit")
def submit_ox(session_id: str, payload: dict) -> dict:
    """O/X 문항 채점 (편지 §5-4). quiz_answers에 기록 + 정답 시 집중 회복/XP."""
    state = _get_state(session_id)
    quiz_id = payload.get("quizId") or payload.get("quiz_id")
    selected = payload.get("selectedOption") or payload.get("selected_option")
    if not quiz_id or selected is None:
        raise HTTPException(status_code=422, detail="quizId and selectedOption are required")

    result = submit_ox_quiz(state, str(quiz_id), str(selected))
    if result is None:
        raise HTTPException(status_code=404, detail="quiz not found")

    SESSION_STORE[session_id] = state
    return result


@router.post("/{session_id}/finish")
def finish_session(session_id: str) -> dict:
    """Run the full orchestrator and return final session result."""
    state = _get_state(session_id)
    state = run_reading_session(state)
    state = run_qa_eval_agent(state)  # 5번 QA: 세션 종료 시 품질 평가
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
        # readChunkIndex: 확장 본문 기준 진행률(§4)이 싣는 "지금 읽는 문단 인덱스".
        # 3번이 "어느 문단?"을 알 때 쓰는 신호라 계약에서 통과시킨다(bool 제외).
        read_chunk_index = event.get("readChunkIndex")
        if isinstance(read_chunk_index, int) and not isinstance(read_chunk_index, bool):
            normalized_event["readChunkIndex"] = max(0, read_chunk_index)
        # velocity: 확장 tracker가 계산한 스크롤 속도(px/ms). 3번 calculate_focus_score가
        # event.velocity 를 읽어 비정상 스크롤(>1.5)을 감점하므로 계약에서 통과시킨다(bool 제외).
        velocity = event.get("velocity")
        if isinstance(velocity, (int, float)) and not isinstance(velocity, bool):
            normalized_event["velocity"] = max(0.0, float(velocity))
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
