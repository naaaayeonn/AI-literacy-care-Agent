"""
chunker.py — 의미 단위 청킹 모듈 (M0)

원문 텍스트를 의미 연결성 기준으로 Chunk 단위로 분할한다.

chunk_id 규칙: chunk_{document_id}_{순번(2자리 zero-padding)}
  예시: chunk_doc001_01, chunk_doc001_02, chunk_doc001_10

중요:
  - chunk_id는 3번(행동 데이터), 4번(UI 하이라이트), 퀴즈 생성 모두에서 사용
  - 같은 document_id + 같은 텍스트 = 항상 같은 chunk_id (안정성 보장)
"""
from __future__ import annotations

import re

from backend.app.agents.content_reducer.contracts import ChunkDict
from backend.app.agents.content_reducer.readability import analyze_readability


# ---------------------------------------------------------------------------
# 청킹 설정
# ---------------------------------------------------------------------------

MIN_CHUNK_CHARS = 80     # 너무 짧은 청크 방지
MAX_CHUNK_CHARS = 600    # 너무 긴 청크 방지
_DOUBLE_NEWLINE_RE = re.compile(r"\n{2,}")


# ---------------------------------------------------------------------------
# 내부 구현
# ---------------------------------------------------------------------------

def _try_langchain_chunker(text: str) -> list[str] | None:
    """LangChain RecursiveCharacterTextSplitter 시도. 없으면 None."""
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=MAX_CHUNK_CHARS,
            chunk_overlap=0,  # overlap을 0으로 설정하여 청크 순차성을 확보
            separators=["\n\n", "\n", ". ", "다. ", "요. ", " ", ""],
        )
        result = splitter.split_text(text)
        return [c.strip() for c in result if c.strip()]
    except ImportError:
        return None


def _paragraph_split(text: str) -> list[str]:
    """
    이중 개행(\n\n)으로 단락을 분리한다.
    단락이 없으면 문장 기반 분리를 수행한다.
    단락이 너무 짧으면 인접 단락과 병합한다.
    """
    paragraphs = [p.strip() for p in _DOUBLE_NEWLINE_RE.split(text) if p.strip()]

    # 단락 구분이 없으면 문장 기반 분리
    if len(paragraphs) <= 1:
        sentence_re = re.compile(r"(?<=[다요했됩습])[.]\s+|(?<=[.!?])\s+")
        sentences = sentence_re.split(text.strip())
        paragraphs = []
        buf = ""
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            if len(buf) + len(sent) > MAX_CHUNK_CHARS and buf:
                paragraphs.append(buf)
                buf = sent
            else:
                buf = (buf + " " + sent).strip() if buf else sent
        if buf:
            paragraphs.append(buf)

    # 너무 짧은 단락만 다음 단락과 병합한다.
    # 단락 자체가 충분히 길면 독립 chunk로 유지한다.
    merged: list[str] = []
    buf = ""
    for para in paragraphs:
        # buf가 없으면 현재 단락으로 시작
        if not buf:
            buf = para
        # 현재 단락이 충분히 길면 buf를 저장하고 새로 시작
        elif len(para) >= MIN_CHUNK_CHARS:
            merged.append(buf)
            buf = para
        # 현재 단락이 짧고 buf+para가 MAX보다 작으면 병합
        elif len(buf) + len(para) < MAX_CHUNK_CHARS:
            buf = (buf + " " + para).strip()
        # MAX를 초과하면 buf를 저장하고 새로 시작
        else:
            merged.append(buf)
            buf = para
    if buf:
        merged.append(buf)

    return merged if merged else [text.strip()]


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------

def semantic_chunk(text: str, document_id: str) -> list[ChunkDict]:
    """
    원문 텍스트를 의미 단위 Chunk로 분할한다.

    Args:
        text: 원문 텍스트
        document_id: 문서 식별자 (chunk_id 생성에 사용)

    Returns:
        ChunkDict 목록. 각 항목에 chunk_id, original_text,
        char_start, char_end, difficulty 포함.

    Examples:
        >>> chunks = semantic_chunk("문단1입니다.\\n\\n문단2입니다.", "doc001")
        >>> chunks[0]["chunk_id"]
        'chunk_doc001_01'
        >>> 0 <= chunks[0]["difficulty"] <= 100
        True
    """
    if not text or not text.strip():
        return []

    # LangChain 시도 → 실패 시 단락 기반 폴백
    raw_chunks = _try_langchain_chunker(text) or _paragraph_split(text)

    result: list[ChunkDict] = []
    cursor = 0

    for idx, chunk_text in enumerate(raw_chunks, start=1):
        # 원문에서 청크의 위치 탐색
        start = text.find(chunk_text, cursor)
        if start == -1:
            start = text.find(chunk_text)  # cursor 기준 탐색 실패 시 전체 탐색 시도
        
        if start == -1:
            # 완전히 매칭되지 않는 엣지케이스 대응
            start_pos = -1
            end_pos = -1
        else:
            start_pos = start
            end_pos = start + len(chunk_text)
            cursor = end_pos

        chunk_id = f"chunk_{document_id}_{idx:02d}"
        difficulty = float(max(0.0, min(100.0, 100.0 - analyze_readability(chunk_text))))

        result.append(
            ChunkDict(
                chunk_id=chunk_id,
                original_text=chunk_text,
                char_start=start_pos,
                char_end=end_pos,
                difficulty=round(difficulty, 2),
            )
        )

    return result
