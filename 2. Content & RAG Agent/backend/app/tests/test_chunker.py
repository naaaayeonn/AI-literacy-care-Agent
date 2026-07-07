"""
test_chunker.py — 의미 단위 청킹 모듈 단위 테스트 (M0)

pytest로 실행:
  python -m pytest backend/app/tests/test_chunker.py -v
"""
import pytest

from backend.app.agents.content_reducer.chunker import semantic_chunk


# ---------------------------------------------------------------------------
# 기본 동작 테스트
# ---------------------------------------------------------------------------

class TestSemanticChunk:

    def test_returns_list_of_chunks(self):
        """결과가 list 타입이어야 한다."""
        result = semantic_chunk("안녕하세요.\n\n반갑습니다.", "doc001")
        assert isinstance(result, list)

    def test_chunk_id_format(self):
        """chunk_id가 'chunk_{document_id}_{2자리 순번}' 형식이어야 한다."""
        chunks = semantic_chunk("문단1입니다.\n\n문단2입니다.", "doc001")
        assert len(chunks) >= 1
        assert chunks[0]["chunk_id"] == "chunk_doc001_01"

    def test_chunk_id_sequential(self):
        """여러 chunk의 순번이 순서대로 증가해야 한다."""
        text = "문단1.\n\n문단2.\n\n문단3."
        chunks = semantic_chunk(text, "docABC")
        for i, chunk in enumerate(chunks, start=1):
            expected_id = f"chunk_docABC_{i:02d}"
            assert chunk["chunk_id"] == expected_id

    def test_chunk_has_required_fields(self):
        """각 chunk에 필수 필드가 포함되어야 한다."""
        chunks = semantic_chunk("텍스트입니다.", "doc002")
        required_fields = {"chunk_id", "original_text", "char_start", "char_end", "difficulty"}
        for chunk in chunks:
            missing = required_fields - set(chunk.keys())
            assert not missing, f"필드 누락: {missing}"

    def test_char_start_end_within_text(self):
        """char_start, char_end가 원문 범위 내에 있어야 한다."""
        text = "첫 번째 문단입니다.\n\n두 번째 문단입니다."
        chunks = semantic_chunk(text, "doc003")
        for chunk in chunks:
            assert chunk["char_start"] >= 0
            assert chunk["char_end"] <= len(text) + 5  # 약간의 여유

    def test_difficulty_in_range(self):
        """difficulty가 0~100 범위에 있어야 한다."""
        text = "인공지능 LLM 레이턴시 최적화 알고리즘 파인튜닝.\n\n날씨가 좋습니다."
        chunks = semantic_chunk(text, "doc004")
        for chunk in chunks:
            assert 0.0 <= chunk["difficulty"] <= 100.0, (
                f"difficulty 범위 초과: {chunk['difficulty']}"
            )

    def test_empty_text_returns_empty_list(self):
        """빈 텍스트는 빈 목록을 반환해야 한다."""
        assert semantic_chunk("", "doc005") == []

    def test_whitespace_only_returns_empty_list(self):
        """공백만 있는 텍스트는 빈 목록을 반환해야 한다."""
        assert semantic_chunk("   \n\n  ", "doc006") == []

    def test_original_text_preserved(self):
        """original_text가 원문 내용을 보존해야 한다."""
        text = "이것은 테스트 문단입니다."
        chunks = semantic_chunk(text, "doc007")
        assert len(chunks) >= 1
        assert text in chunks[0]["original_text"] or chunks[0]["original_text"] in text

    def test_same_input_same_chunk_ids(self):
        """같은 입력은 항상 같은 chunk_id를 생성해야 한다 (안정성)."""
        text = "문단 A.\n\n문단 B.\n\n문단 C."
        ids1 = [c["chunk_id"] for c in semantic_chunk(text, "docStable")]
        ids2 = [c["chunk_id"] for c in semantic_chunk(text, "docStable")]
        assert ids1 == ids2

    def test_long_text_creates_multiple_chunks(self):
        """긴 텍스트는 여러 chunk로 분할되어야 한다 (MAX_CHUNK_CHARS=600 초과)."""
        # 각 단락을 최소 200자 이상으로 작성하여 전체 > 600자가 되도록 구성
        long_text = "\n\n".join([
            (
                f"이것은 {i}번째 문단입니다. 이 문단에는 인공지능(AI) 기술과 관련된 내용이 포함되어 있습니다. "
                f"특히 LLM 기반 시스템과 RAG 아키텍처를 활용하면 환각 현상 없이 신뢰할 수 있는 정보를 제공할 수 있습니다. "
                f"또한 메타인지와 문해력 향상을 위한 맞춤형 학습 경험을 설계하는 것이 이 시스템의 핵심 목표입니다."
            )
            for i in range(1, 5)
        ])
        chunks = semantic_chunk(long_text, "docLong")
        assert len(chunks) >= 2, f"긴 텍스트가 {len(chunks)}개 chunk로만 분할됨"

    def test_different_document_ids_produce_different_chunk_ids(self):
        """같은 텍스트라도 document_id가 다르면 다른 chunk_id를 생성한다."""
        text = "테스트 문단."
        chunks_a = semantic_chunk(text, "docA")
        chunks_b = semantic_chunk(text, "docB")
        assert chunks_a[0]["chunk_id"] != chunks_b[0]["chunk_id"]
