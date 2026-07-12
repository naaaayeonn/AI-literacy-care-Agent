"""
fallbacks.py — 서브모듈 실패 시 기본값 처리 (M0)

각 서브모듈이 예외를 발생시켰을 때 전체 데모가 중단되지 않도록
기본값(fallback)을 정의한다.

원칙:
  - fallback은 최소 유효한 형태의 데이터를 반환해야 한다.
  - trace에 반드시 fallback 사유를 기록한다.
  - 1번 Orchestrator는 fallback 결과를 실제 결과와 동일하게 처리할 수 있어야 한다.
"""
from __future__ import annotations

from backend.app.agents.content_reducer.contracts import ChunkDict, QuizDict, TermDict


# ---------------------------------------------------------------------------
# 가독성 분석 실패
# ---------------------------------------------------------------------------

DEFAULT_READABILITY_SCORE: float = 50.0
DEFAULT_DIFFICULTY_SCORE: float = 50.0


def fallback_readability() -> tuple[float, float]:
    """
    가독성 분석 실패 시 반환할 기본값.
    Returns: (readability_score, difficulty_score)
    """
    return DEFAULT_READABILITY_SCORE, DEFAULT_DIFFICULTY_SCORE


# ---------------------------------------------------------------------------
# 청킹 실패
# ---------------------------------------------------------------------------

def fallback_chunks(raw_text: str, document_id: str) -> list[ChunkDict]:
    """
    Semantic Chunker 실패 시 원문을 단일 chunk로 반환한다.
    """
    return [
        ChunkDict(
            chunk_id=f"chunk_{document_id}_01",
            original_text=raw_text[:600] if raw_text else "",
            char_start=0,
            char_end=min(len(raw_text), 600),
            difficulty=DEFAULT_DIFFICULTY_SCORE,
        )
    ]


# ---------------------------------------------------------------------------
# LLM 재구성 — 설계 변경으로 제거됨
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# RAG 용어풀이 실패
# ---------------------------------------------------------------------------

def fallback_terms() -> list[TermDict]:
    """
    RAG 검색 실패 시 빈 용어 목록을 반환한다.
    프론트는 terms=[]이면 툴팁 없이 처리한다.
    """
    return []


# ---------------------------------------------------------------------------
# 퀴즈 생성 실패
# ---------------------------------------------------------------------------

def fallback_quiz(chunk_id: str) -> QuizDict:
    """
    퀴즈 생성 실패 시 반환할 기본 퀴즈.
    사전에 준비된 일반 독해력 확인 문제를 반환한다.
    """
    return QuizDict(
        chunk_id=chunk_id,
        question="방금 읽은 문단의 핵심 내용으로 가장 적절한 것은 무엇인가요?",
        options=[
            "1. 본문에서 언급된 개념을 처음 제안한 사람이 누구인지 설명한다.",
            "2. 본문의 핵심 개념과 그 의미를 이해했다.",
            "3. 본문과 무관한 배경 지식이 필요하다.",
            "4. 본문의 내용은 다른 분야에도 동일하게 적용된다.",
        ],
        correct_option=2,
        explanation="이 퀴즈는 기본 독해력 확인 문항입니다. 본문의 핵심 개념 이해 여부를 확인하세요.",
    )


# ---------------------------------------------------------------------------
# 전체 Content Reducer 실패 (최악의 경우)
# ---------------------------------------------------------------------------

def fallback_content_reducer_response(
    session_id: str, raw_text: str, document_id: str
) -> dict:
    """
    Content Reducer 전체 실패 시 Orchestrator에 반환할 최소 유효 응답.
    """
    chunks = fallback_chunks(raw_text, document_id)
    return {
        "session_id": session_id,
        "readability_score": DEFAULT_READABILITY_SCORE,
        "difficulty_score": DEFAULT_DIFFICULTY_SCORE,
        "chunks": chunks,
        "simplified_text": raw_text[:500] if raw_text else "",
        "terms": [],
    }
