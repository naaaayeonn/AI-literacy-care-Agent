"""ReadingSessionState 스키마 테스트.

오늘은 create_initial_state가 필수 필드를 채우는지만 가볍게 확인한다.
(나머지 테스트는 6/22~26에 채움)
"""

from __future__ import annotations

from backend.app.orchestrator.state import create_initial_state


def test_create_initial_state_has_required_fields():
    state = create_initial_state(
        session_id="s1",
        user_id="u1",
        document_id="doc1",
        raw_text="긴 원문...",
    )
    assert state["session_id"] == "s1"
    assert state["reading_events"] == []
    assert state["trace"] == []
    assert state["errors"] == []
    assert state["profile"] == {}
