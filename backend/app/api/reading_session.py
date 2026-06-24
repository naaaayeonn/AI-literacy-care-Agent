"""읽기 세션 API 라우터 — 프론트(4번)와 오케스트레이터 사이 계층.

[골격: 6/20 / 연결: M0~M1]

역할:
- 프론트에서 받은 원문/행동 이벤트/퀴즈 결과를 검증
- ReadingSessionState로 변환
- orchestrator.graph 호출
- 프론트가 사용할 응답 JSON 반환

엔드포인트 (ARCHITECTURE §4):
- POST /api/reading-sessions/start
- POST /api/reading-sessions/{session_id}/events
- POST /api/reading-sessions/{session_id}/quiz
- POST /api/reading-sessions/{session_id}/finish
- GET  /api/reading-sessions/{session_id}/result

NOTE: FastAPI 의존성은 6/22 이후 추가. 지금은 시그니처/계약만 자리 잡는다.
"""

from __future__ import annotations


def start_session(payload: dict) -> dict:
    """POST /start — 원문 입력으로 세션 생성, 읽기 화면 구성 데이터 반환."""
    raise NotImplementedError("M0~M1 구현 예정")


def push_events(session_id: str, payload: dict) -> dict:
    """POST /{id}/events — reading_events 누적, intervention command 반환."""
    raise NotImplementedError("M1 구현 예정")


def submit_quiz(session_id: str, payload: dict) -> dict:
    """POST /{id}/quiz — quiz_result 반영."""
    raise NotImplementedError("M1 구현 예정")


def finish_session(session_id: str) -> dict:
    """POST /{id}/finish — Score/Reward/Profile 실행 후 최종 결과 반환."""
    raise NotImplementedError("M1 구현 예정")


def get_result(session_id: str) -> dict:
    """GET /{id}/result — 세션 결과 JSON 조회."""
    raise NotImplementedError("M1 구현 예정")
