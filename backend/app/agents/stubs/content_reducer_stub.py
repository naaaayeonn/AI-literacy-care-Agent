"""Content Reducer (2번) 더미 구현. [구현 예정: 6/22]"""

from __future__ import annotations

from ...orchestrator.state import ReadingSessionState


def content_reducer_stub(state: ReadingSessionState) -> ReadingSessionState:
    """raw_text를 단순 분할해 chunks/difficulty_score를 채운다.

    TODO(6/22): 더미 chunk 1~N개 생성 + difficulty_score 기본값.
    """
    raise NotImplementedError("6/22 stub 구현 예정")
