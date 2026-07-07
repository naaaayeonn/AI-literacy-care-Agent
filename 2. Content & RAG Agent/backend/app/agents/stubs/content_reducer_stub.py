"""
content_reducer_stub.py — Content Reducer 더미 구현 (M0)

실제 LLM/RAG 없이 1번 Orchestrator E2E 흐름을 지원하는 stub.

사용 목적:
  - 1번 Orchestrator가 stub을 사용해 전체 폐루프를 먼저 테스트
  - LLM API 키 없이 CI/CD, 단위 테스트에서 사용
  - M2에서 실제 agent.py의 run_content_reducer()로 교체

교체 방법 (1번 Orchestrator 기준):
  # M0 Stub
  from backend.app.agents.stubs.content_reducer_stub import content_reducer_stub
  state = content_reducer_stub(state)

  # M2 실제 구현
  from backend.app.agents.content_reducer.agent import run_content_reducer
  state = run_content_reducer(state)
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.agents.content_reducer.contracts import ReadingSessionState

# Stub에서도 실제 readability / chunker는 사용 (LLM만 stub)
from backend.app.agents.content_reducer.chunker import semantic_chunk
from backend.app.agents.content_reducer.readability import (
    analyze_readability,
    calculate_difficulty_score,
)


def content_reducer_stub(state: "ReadingSessionState") -> "ReadingSessionState":
    """
    Content Reducer 더미 구현.

    실제 Claude API / Vector DB 없이 동작한다.
    readability + chunking은 실제 로직을 사용하고,
    재구성과 용어풀이는 미리 정의된 더미 데이터를 반환한다.

    Args:
        state: ReadingSessionState

    Returns:
        chunks / terms / difficulty_score가 채워진 state
    """
    if "trace" not in state:
        state["trace"] = []
    if "errors" not in state:
        state["errors"] = []

    raw_text = state.get("raw_text", "")
    document_id = state.get("document_id", "doc_stub")
    t0 = time.monotonic()

    # 실제 가독성 분석 + 청킹 (stub에서도 실제 사용)
    readability_score = analyze_readability(raw_text) if raw_text else 50.0
    difficulty_score = calculate_difficulty_score(readability_score)
    chunks = semantic_chunk(raw_text, document_id) if raw_text else []

    # 청크가 없으면 더미 청크 생성
    if not chunks:
        chunks = [
            {
                "chunk_id": f"chunk_{document_id}_01",
                "original_text": raw_text[:300] or "더미 텍스트",
                "char_start": 0,
                "char_end": min(len(raw_text), 300),
                "difficulty": difficulty_score,
            }
        ]

    # 더미 재구성 텍스트 주입
    for chunk in chunks:
        chunk["restructured_text"] = (
            f"[Stub 재구성] {chunk['original_text'][:120]}"
        )
        # 더미 용어 주입
        chunk["terms"] = [
            {
                "term": "인공지능",
                "definition": "인간의 학습, 추론, 문제 해결 능력을 컴퓨터가 모방할 수 있도록 만든 기술.",
                "source": "stub_source (표준국어대사전 기반)",
                "faithfulness_score": 1.0,
                "chunk_id": chunk["chunk_id"],
            }
        ]

    # 전체 simplified_text
    simplified_text = "\n\n".join(
        ch.get("restructured_text", ch["original_text"]) for ch in chunks
    )

    # terms 중복 제거
    seen: set[str] = set()
    all_terms = []
    for chunk in chunks:
        for t in chunk.get("terms", []):
            if t["term"] not in seen:
                seen.add(t["term"])
                all_terms.append(t)

    # state 업데이트
    state["readability_score"] = round(readability_score, 2)
    state["difficulty_score"] = round(difficulty_score, 2)
    state["chunks"] = chunks
    state["simplified_text"] = simplified_text
    state["terms"] = all_terms

    elapsed = round((time.monotonic() - t0) * 1000)
    state["trace"].append({
        "step": "content_reducer",
        "status": "stub",
        "readability_score": readability_score,
        "difficulty_score": difficulty_score,
        "chunk_count": len(chunks),
        "term_count": len(all_terms),
        "latency_ms": elapsed,
        "note": "Stub implementation — replace with run_content_reducer() at M2",
    })

    return state
