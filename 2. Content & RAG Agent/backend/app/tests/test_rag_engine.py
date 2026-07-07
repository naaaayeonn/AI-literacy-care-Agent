"""
test_rag_engine.py — RAG 용어풀이 엔진 단위 테스트 (M1)

pytest로 실행:
  python -m pytest backend/app/tests/test_rag_engine.py -v
"""
import pytest

from backend.app.agents.content_reducer.rag_engine import (
    _find_terms,
    _keyword_score,
    _TERM_DICT,
    collect_all_terms,
    get_faithfulness_summary,
    inject_rag_terms,
)
from backend.app.agents.content_reducer.contracts import ChunkDict


# ---------------------------------------------------------------------------
# 픽스처
# ---------------------------------------------------------------------------

@pytest.fixture
def it_text_chunk() -> ChunkDict:
    return ChunkDict(
        chunk_id="chunk_test_01",
        original_text=(
            "인공지능(AI)과 LLM 기반 시스템은 레이턴시 최적화를 위해 "
            "RAG 아키텍처를 활용한다. 이 접근법은 환각 현상을 줄이는 데 효과적이다."
        ),
        restructured_text=(
            "AI와 LLM 시스템은 빠른 응답 속도를 위해 RAG 구조를 씁니다. "
            "이 방법은 AI가 잘못된 정보를 만들어 내는 문제를 줄여줍니다."
        ),
        char_start=0,
        char_end=100,
        difficulty=62.5,
    )


@pytest.fixture
def edu_text_chunk() -> ChunkDict:
    return ChunkDict(
        chunk_id="chunk_test_02",
        original_text=(
            "메타인지와 문해력은 자기주도 학습에서 핵심적인 역할을 한다. "
            "인지부하를 줄이면 학습 효율이 높아진다."
        ),
        restructured_text=(
            "내 생각을 스스로 살피는 능력(메타인지)과 글 읽는 능력(문해력)은 "
            "혼자 공부할 때 매우 중요합니다. 뇌의 부담을 줄이면 더 잘 배울 수 있어요."
        ),
        char_start=100,
        char_end=200,
        difficulty=45.0,
    )


# ---------------------------------------------------------------------------
# _keyword_score 테스트
# ---------------------------------------------------------------------------

class TestKeywordScore:

    def test_direct_term_match_returns_high_score(self):
        """텍스트에 용어가 직접 포함되면 높은 점수를 반환해야 한다."""
        entry = {"term": "레이턴시", "aliases": ["latency"], "definition": "지연 시간"}
        score = _keyword_score("시스템 레이턴시가 중요하다.", entry)
        assert score >= 0.9

    def test_alias_match_also_returns_high_score(self):
        """별칭(alias)이 텍스트에 포함되어도 높은 점수를 반환해야 한다."""
        entry = {"term": "레이턴시", "aliases": ["latency", "지연 시간"], "definition": "..."}
        score = _keyword_score("API latency 최적화", entry)
        assert score >= 0.9

    def test_no_match_returns_low_score(self):
        """매칭되는 용어가 없으면 낮은 점수를 반환해야 한다."""
        entry = {"term": "퀀텀컴퓨팅", "aliases": ["quantum computing"], "definition": "..."}
        score = _keyword_score("오늘 날씨가 좋습니다.", entry)
        assert score < 0.5


# ---------------------------------------------------------------------------
# 용어집 로드 테스트
# ---------------------------------------------------------------------------

class TestTermDictionary:

    def test_term_dict_loaded(self):
        """용어집이 로드되어야 한다."""
        assert len(_TERM_DICT) > 0, "term_dictionary.json이 로드되지 않았습니다"

    def test_term_dict_has_required_fields(self):
        """각 용어에 필수 필드가 있어야 한다."""
        required = {"term", "definition", "source"}
        for entry in _TERM_DICT:
            missing = required - set(entry.keys())
            assert not missing, f"용어 '{entry.get('term')}' 필드 누락: {missing}"

    def test_term_dict_has_it_terms(self):
        """IT 도메인 용어가 포함되어야 한다."""
        it_terms = {e["term"] for e in _TERM_DICT if e.get("domain") == "IT"}
        assert len(it_terms) >= 5, f"IT 용어가 너무 적습니다: {it_terms}"


# ---------------------------------------------------------------------------
# _find_terms 테스트
# ---------------------------------------------------------------------------

class TestFindTerms:

    def test_finds_terms_in_it_text(self):
        """IT 텍스트에서 관련 용어를 찾아야 한다."""
        text = "인공지능과 LLM, RAG는 현대 IT 시스템의 핵심이다."
        results = _find_terms(text)
        assert len(results) >= 1

    def test_returns_list_of_tuples(self):
        """결과가 (dict, float) 튜플 목록이어야 한다."""
        results = _find_terms("AI와 머신러닝을 활용한다.")
        for entry, score in results:
            assert isinstance(entry, dict)
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0

    def test_top_k_limit(self):
        """top_k 이하의 결과만 반환해야 한다."""
        results = _find_terms("인공지능 LLM RAG 메타인지 문해력 알고리즘", top_k=3)
        assert len(results) <= 3

    def test_empty_text_returns_empty(self):
        """빈 텍스트는 빈 목록을 반환해야 한다."""
        results = _find_terms("")
        assert results == []


# ---------------------------------------------------------------------------
# inject_rag_terms 테스트
# ---------------------------------------------------------------------------

class TestInjectRagTerms:

    def test_adds_terms_field_to_chunks(self, it_text_chunk):
        """inject_rag_terms가 각 chunk에 terms 필드를 추가해야 한다."""
        chunks = inject_rag_terms([it_text_chunk])
        assert "terms" in chunks[0]
        assert isinstance(chunks[0]["terms"], list)

    def test_terms_have_required_fields(self, it_text_chunk):
        """각 term에 필수 필드가 있어야 한다."""
        chunks = inject_rag_terms([it_text_chunk])
        required = {"term", "definition", "source", "chunk_id"}
        for term in chunks[0].get("terms", []):
            missing = required - set(term.keys())
            assert not missing, f"term 필드 누락: {missing}"

    def test_terms_faithfulness_score_in_range(self, it_text_chunk):
        """faithfulness_score가 0~1 범위에 있어야 한다."""
        chunks = inject_rag_terms([it_text_chunk])
        for term in chunks[0].get("terms", []):
            score = term.get("faithfulness_score")
            if score is not None:
                assert 0.0 <= score <= 1.0

    def test_terms_chunk_id_matches(self, it_text_chunk):
        """term의 chunk_id가 원본 chunk_id와 일치해야 한다."""
        chunks = inject_rag_terms([it_text_chunk])
        for term in chunks[0].get("terms", []):
            assert term["chunk_id"] == chunks[0]["chunk_id"]

    def test_it_text_finds_relevant_terms(self, it_text_chunk):
        """IT 텍스트에서 AI, LLM, RAG 등 관련 용어가 검색되어야 한다."""
        chunks = inject_rag_terms([it_text_chunk])
        term_names = {t["term"] for t in chunks[0].get("terms", [])}
        # AI 관련 용어 중 하나 이상 매칭 기대
        it_expected = {"인공지능", "LLM", "RAG", "레이턴시", "환각"}
        assert len(term_names & it_expected) >= 1, (
            f"IT 용어가 매칭되지 않았습니다. 매칭된 용어: {term_names}"
        )

    def test_multiple_chunks_processed(self, it_text_chunk, edu_text_chunk):
        """여러 chunk를 처리해도 각각 terms가 추가되어야 한다."""
        chunks = inject_rag_terms([it_text_chunk, edu_text_chunk])
        assert len(chunks) == 2
        for chunk in chunks:
            assert "terms" in chunk

    def test_does_not_raise_on_empty_chunks(self):
        """빈 청크 목록에서도 예외 없이 동작해야 한다."""
        result = inject_rag_terms([])
        assert result == []

    def test_no_duplicate_terms_in_chunk(self, it_text_chunk):
        """같은 chunk에 동일 용어가 중복 포함되지 않아야 한다."""
        chunks = inject_rag_terms([it_text_chunk])
        term_names = [t["term"] for t in chunks[0].get("terms", [])]
        assert len(term_names) == len(set(term_names)), "중복 용어 발견"


# ---------------------------------------------------------------------------
# collect_all_terms 테스트
# ---------------------------------------------------------------------------

class TestCollectAllTerms:

    def test_collects_unique_terms_across_chunks(
        self, it_text_chunk, edu_text_chunk
    ):
        """여러 chunk에서 중복 없이 용어를 수집해야 한다."""
        chunks = inject_rag_terms([it_text_chunk, edu_text_chunk])
        all_terms = collect_all_terms(chunks)
        term_names = [t["term"] for t in all_terms]
        assert len(term_names) == len(set(term_names)), "중복 용어 발견"

    def test_returns_list(self, it_text_chunk):
        """결과가 list 타입이어야 한다."""
        chunks = inject_rag_terms([it_text_chunk])
        result = collect_all_terms(chunks)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# get_faithfulness_summary 테스트
# ---------------------------------------------------------------------------

class TestFaithfulnessSummary:

    def test_empty_terms_returns_zero_stats(self):
        """빈 목록은 zero 통계를 반환해야 한다."""
        summary = get_faithfulness_summary([])
        assert summary["total"] == 0
        assert summary["avg_faithfulness"] == 0.0

    def test_summary_has_required_fields(self, it_text_chunk):
        """summary에 필수 필드가 있어야 한다."""
        chunks = inject_rag_terms([it_text_chunk])
        all_terms = collect_all_terms(chunks)
        summary = get_faithfulness_summary(all_terms)
        for field in ["total", "avg_faithfulness", "below_threshold", "threshold"]:
            assert field in summary

    def test_avg_faithfulness_in_range(self, it_text_chunk):
        """평균 faithfulness가 0~1 범위에 있어야 한다."""
        chunks = inject_rag_terms([it_text_chunk])
        all_terms = collect_all_terms(chunks)
        summary = get_faithfulness_summary(all_terms)
        if summary["total"] > 0:
            assert 0.0 <= summary["avg_faithfulness"] <= 1.0
