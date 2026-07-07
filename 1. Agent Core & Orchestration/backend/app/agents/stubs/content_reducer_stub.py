"""Content Reducer stub for the M0 end-to-end flow."""

from __future__ import annotations

from ...orchestrator.state import ReadingSessionState


def content_reducer_stub(state: ReadingSessionState) -> ReadingSessionState:
    """Split raw text into deterministic chunks and fill content fields."""
    raw_text = state["raw_text"].strip()
    chunk_size = 300
    chunks = []

    if raw_text:
        for index, start in enumerate(range(0, len(raw_text), chunk_size), start=1):
            text = raw_text[start : start + chunk_size]
            chunks.append(
                {
                    "chunk_id": f"chunk_{index:02d}",
                    "text": text,
                    "summary": text[:80],
                    "difficulty": 60,
                }
            )
    else:
        chunks.append(
            {
                "chunk_id": "chunk_01",
                "text": "",
                "summary": "",
                "difficulty": 50,
            }
        )

    state["chunks"] = chunks
    state["simplified_text"] = raw_text
    state["terms"] = []
    state["difficulty_score"] = 60.0 if raw_text else 50.0
    return state
