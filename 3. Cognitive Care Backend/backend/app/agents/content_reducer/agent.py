"""
agent.py — Content Reducer 에이전트 진입점 (M1)

1번 Orchestrator에서 호출하는 메인 함수: run_content_reducer(state)

M1 구현 상태:
  - readability + chunking: 실제 동작
  - RAG 용어풀이: 신뢰 출처 JSON 기반 키워드 매칭
  → M2에서 퀴즈 생성기 추가 예정

Note: 문장 재구성(restructure) 기능은 설계 변경으로 제거됨.
      대신 문단별 난이도 + 문해력 RAG 로 대체 예정.

CONTENT_REDUCER_MODE 환경 변수:
  "real"  → 실제 모듈 사용 (기본값)
  "stub"  → content_reducer_stub.py 경유 (1번 E2E 테스트용)
"""
from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

from backend.app.agents.content_reducer.chunker import semantic_chunk
from backend.app.agents.content_reducer.fallbacks import (
    fallback_chunks,
    fallback_content_reducer_response,
    fallback_readability,
)
from backend.app.agents.content_reducer.rag_engine import (
    collect_all_terms,
    get_faithfulness_summary,
    inject_rag_terms,
)
from backend.app.agents.content_reducer.readability import (
    analyze_readability,
    calculate_difficulty_score,
    get_readability_label,
    get_technical_term_density,
)
from backend.app.agents.content_reducer.restructurer import summarize_chunks

if TYPE_CHECKING:
    from backend.app.agents.content_reducer.contracts import ReadingSessionState

# 모드 평가는 실행 시 동적으로 처리하도록 변경함


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------

def _collect_simplified_text(chunks: list) -> str:
    """청크의 요약 텍스트를 전체 문서 단위로 합쳐 전체 요약본을 제공한다."""
    parts = []
    for chunk in chunks:
        text = chunk.get("summary") or chunk.get("original_text", "")
        if text:
            parts.append(text)
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# 공개 API — 1번 Orchestrator에서 호출
# ---------------------------------------------------------------------------

def run_content_reducer(state: "ReadingSessionState") -> "ReadingSessionState":
    """
    Content Reducer 에이전트 메인 진입점 (M1).

    파이프라인:
      1. 가독성 분석 → difficulty_score
      2. 의미 단위 청킹 → chunks + chunk_id
      3. RAG 용어풀이 주입 → terms + faithfulness_score
      4. 결과 조합 → state 업데이트

    실패 시 절대 예외를 외부로 전파하지 않는다.
    각 서브모듈 실패 시 fallback 값을 사용한다.

    Args:
        state: ReadingSessionState (1번 Orchestrator에서 제공)

    Returns:
        chunks / terms / difficulty_score / simplified_text가 채워진 state
    """
    # Stub 모드: 전체를 stub으로 위임
    mode = os.getenv("CONTENT_REDUCER_MODE", "real").lower()
    if mode == "stub":
        from backend.app.agents.stubs.content_reducer_stub import (
            content_reducer_stub,
        )
        return content_reducer_stub(state)

    session_id = state.get("session_id", "unknown")
    document_id = state.get("document_id", "doc")
    raw_text = state.get("raw_text", "")
    profile = state.get("profile", {})

    if "trace" not in state:
        state["trace"] = []
    if "errors" not in state:
        state["errors"] = []

    t_start = time.monotonic()
    step_trace: dict = {
        "step": "content_reducer",
        "status": "success",
        "mode": "real",
    }

    try:
        # ─────────────────────────────────────────
        # Step 1: 가독성 및 난이도 분석
        # ─────────────────────────────────────────
        try:
            readability_score = analyze_readability(raw_text)
            tech_density = get_technical_term_density(raw_text)
            difficulty_score = calculate_difficulty_score(raw_text)
        except Exception as e:
            readability_score, difficulty_score = fallback_readability()
            tech_density = 0.0
            step_trace["readability_fallback"] = str(e)

        state["readability_score"] = round(readability_score, 2)
        state["difficulty_score"] = round(difficulty_score, 2)
        step_trace["readability_score"] = readability_score
        step_trace["difficulty_score"] = difficulty_score
        step_trace["technical_term_density"] = tech_density
        step_trace["readability_label"] = get_readability_label(readability_score)

        # ─────────────────────────────────────────
        # Step 2: 의미 단위 청킹
        # ─────────────────────────────────────────
        try:
            chunks = semantic_chunk(raw_text, document_id)
            if not chunks:
                chunks = fallback_chunks(raw_text, document_id)
        except Exception as e:
            chunks = fallback_chunks(raw_text, document_id)
            step_trace["chunking_fallback"] = str(e)

        step_trace["chunk_count"] = len(chunks)

        # ─────────────────────────────────────────
        # Step 3: RAG 용어풀이 주입
        # ─────────────────────────────────────────
        try:
            chunks = inject_rag_terms(chunks)
        except Exception as e:
            for chunk in chunks:
                chunk.setdefault("terms", [])
            step_trace["rag_fallback"] = str(e)

        # ─────────────────────────────────────────
        # Step 4: 문단별 요약 생성 (3번 OX 퀴즈용)
        # ─────────────────────────────────────────
        try:
            chunks = summarize_chunks(chunks, profile)
        except Exception as e:
            # 요약 실패 시 폴백으로 원문 앞부분 자동 세팅
            for chunk in chunks:
                chunk["summary"] = chunk["original_text"][:120] + "..."
            step_trace["summary_fallback"] = str(e)

        # ─────────────────────────────────────────
        # Step 5: 결과 조합
        # ─────────────────────────────────────────
        all_terms = collect_all_terms(chunks)
        simplified_text = _collect_simplified_text(chunks)

        # 프론트엔드로 나가는 term에 디버그 메타(_meta)가 노출되지 않도록 제거
        for chunk in chunks:
            if "terms" in chunk:
                for t in chunk["terms"]:
                    t.pop("_meta", None)
        for t in all_terms:
            t.pop("_meta", None)

        state["chunks"] = chunks
        state["simplified_text"] = simplified_text
        state["terms"] = all_terms

        # Faithfulness 요약 (5번 QA용)
        faith_summary = get_faithfulness_summary(all_terms)
        step_trace["faithfulness_summary"] = faith_summary
        step_trace["term_count"] = len(all_terms)

    except Exception as exc:
        # 전체 실패: 안전한 fallback 응답
        step_trace["status"] = "fallback"
        step_trace["error"] = str(exc)

        fallback = fallback_content_reducer_response(
            session_id, raw_text, document_id
        )
        state["readability_score"] = fallback["readability_score"]
        state["difficulty_score"] = fallback["difficulty_score"]
        state["chunks"] = fallback["chunks"]
        state["simplified_text"] = fallback["simplified_text"]
        state["terms"] = fallback["terms"]

        state["errors"].append(
            {"step": "content_reducer", "error": str(exc)}
        )

    # latency 기록
    step_trace["latency_ms"] = round((time.monotonic() - t_start) * 1000)
    state["trace"].append(step_trace)

    return state


# ---------------------------------------------------------------------------
# 직접 실행 — 데모 & Smoke Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    sample_text = (
        "인공지능(AI)의 LLM 기반 하이브리드 라우팅은 레이턴시 최적화를 위해 "
        "고난도 추론 작업과 단순 처리 작업을 분리하여 처리하는 기법이다.\n\n"
        "이 방식은 비용 효율성을 높이면서도 전체 시스템의 응답 품질을 "
        "유지할 수 있다는 장점이 있다. 특히 대규모 언어 모델에서 "
        "파인튜닝과 프롬프트 엔지니어링을 조합하면 더욱 효과적이다.\n\n"
        "메타인지와 문해력 향상을 위한 RAG 기반 시스템을 활용하면 "
        "환각 없이 신뢰할 수 있는 정보를 독자에게 제공할 수 있다."
    )

    demo_state: ReadingSessionState = {
        "session_id": "demo_m1_001",
        "user_id": "user_demo",
        "document_id": "doc_demo",
        "raw_text": sample_text,
        "profile": {
            "reading_level": "intermediate",
            "user_literacy_level": 3,
            "target_domain": "IT/AI",
        },
        "trace": [],
        "errors": [],
    }

    print("=" * 60)
    print("Content Reducer M1 데모")
    print("=" * 60)

    result = run_content_reducer(demo_state)

    print(f"readability_score : {result['readability_score']}")
    print(f"difficulty_score  : {result['difficulty_score']}")
    print(f"chunk 수          : {len(result['chunks'])}")
    print(f"term 수           : {len(result['terms'])}")
    print()

    for ch in result["chunks"]:
        print(f"[{ch['chunk_id']}]")
        print(f"  원문     : {ch['original_text'][:80]}...")
        terms_in_chunk = ch.get("terms", [])
        if terms_in_chunk:
            print(f"  용어     : {', '.join(t['term'] for t in terms_in_chunk)}")
        print()

    print("--- 전체 용어 ---")
    for t in result["terms"]:
        print(
            f"  [{t['term']}] {t['definition'][:60]}... "
            f"(출처: {t['source']}, faithfulness: {t.get('faithfulness_score', '-')})"
        )

    print()
    print("--- Trace ---")
    print(json.dumps(result["trace"], ensure_ascii=False, indent=2))
