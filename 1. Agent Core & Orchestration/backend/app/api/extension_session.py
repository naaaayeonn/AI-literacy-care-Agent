"""확장(크롬) 인입 alias 라우트 — API_CONTRACT §9, ADR-001/002.

확장은 **camelCase + `content[]` + REST(event-driven)**로 들어온다. 이 모듈은 그 경계를
내부 snake_case state로 잇는 **얇은 어댑터**다. 세션 저장소·오케스트레이터 함수는
`reading_session`의 것을 그대로 재사용한다(중복 store 금지).

경로(`main.py`가 `prefix="/api"`로 mount):
  POST /api/session/start           content[] → 세션 시작
  POST /api/session/{id}/events     이벤트 배치 → 개입 명령(to_intervention_command)
  GET  /api/session/{id}/result     세션 종료 → 최종 결과(to_session_result)

전송방식은 REST(ADR-001) — WS 없음. userId는 설치별 익명 UUID(ADR-002).
CORS(chrome-extension:// 오리진 허용)는 3번 인프라 몫이라 여기서 다루지 않는다.
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException

from backend.app.agents.cognitive_care_client import (
    calculate_focus_breakdown,
    run_cognitive_care,
)
from backend.app.agents.content_reducer_client import run_content_reducer
from backend.app.api.frontend_contract import to_intervention_command, to_session_result
from backend.app.api.reading_session import SESSION_STORE, _normalize_events
from backend.app.orchestrator.graph import run_reading_session
from backend.app.agents.qa_eval_client import run_qa_eval_agent
from backend.app.orchestrator.routing import decide_intervention
from backend.app.orchestrator.state import ReadingSessionState, create_initial_state

router = APIRouter(prefix="/session", tags=["extension"])


@router.post("/start")
def start_session(payload: dict) -> dict:
    """확장 본문(`content[]`)으로 세션을 시작한다.

    필드 매핑(API_CONTRACT §9-1): userId→user_id, articleId→document_id,
    content[]→raw_text("\\n\\n".join). source.url은 articleId 미제공 시 문서 식별자 폴백.
    """
    raw_text = _content_to_raw_text(payload.get("content"))

    user_id = str(payload.get("userId") or "anonymous")
    source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
    document_id = str(payload.get("articleId") or source.get("url") or "document_unknown")
    session_id = str(uuid4())
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
        "sessionId": session_id,
        "chunks": state.get("chunks", []),
        "simplifiedText": state.get("simplified_text", ""),
        "terms": state.get("terms", []),
        "difficultyScore": state.get("difficulty_score", 50.0),
    }


@router.post("/{session_id}/events")
def push_events(session_id: str, payload: dict) -> dict:
    """이벤트 배치를 반영하고 **개입 명령**(프론트 계약)을 반환한다.

    이벤트는 확장이 내부 스키마로 정규화해 보낸다(§9-2): {type, timestamp_ms, position, duration_ms}.
    """
    state = _get_state(session_id)
    events = payload.get("events", [])
    if not isinstance(events, list):
        raise HTTPException(status_code=422, detail="events must be a list")

    state["reading_events"].extend(_normalize_events(events))
    state = run_cognitive_care(state)
    state = decide_intervention(state)
    SESSION_STORE[session_id] = state

    command = to_intervention_command(state)
    # 디버그 모니터용 감점 내역(집중도 파라미터 실시간 확인). 프론트 계약과 무관한
    # 추가 키라 4번 render()는 무시한다. 누적 reading_events 기준 서버 진실값.
    command["debug"] = calculate_focus_breakdown(state.get("reading_events", []))
    return command


@router.get("/{session_id}/result")
def get_result(session_id: str) -> dict:
    """세션 종료 시 전체 오케스트레이터를 돌려 **최종 결과**(성장 그래프용)를 반환한다."""
    state = _get_state(session_id)
    state = run_reading_session(state)
    state = run_qa_eval_agent(state)  # 5번 QA: 세션 종료 시 품질 평가
    SESSION_STORE[session_id] = state
    return to_session_result(state)


def _content_to_raw_text(content: object) -> str:
    if not isinstance(content, list):
        raise HTTPException(status_code=422, detail="content must be a list of strings")
    paragraphs = [p.strip() for p in content if isinstance(p, str) and p.strip()]
    if not paragraphs:
        raise HTTPException(status_code=422, detail="content must contain at least one non-empty string")
    return "\n\n".join(paragraphs)


def _get_state(session_id: str) -> ReadingSessionState:
    try:
        return SESSION_STORE[session_id]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="session not found") from exc
