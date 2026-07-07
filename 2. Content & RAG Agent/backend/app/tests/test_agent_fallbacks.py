"""
test_agent_fallbacks.py — 가독성 분석, 청커, 재구성, RAG 모듈 개별 실패 시의 Fallback 동작 테스트 (M1)

pytest로 실행:
  python -m pytest backend/app/tests/test_agent_fallbacks.py -v
"""
import pytest
from unittest.mock import patch

from backend.app.agents.content_reducer.agent import run_content_reducer
from backend.app.agents.content_reducer.contracts import ReadingSessionState


@pytest.fixture
def error_state():
    """테스트용 ReadingSessionState."""
    return {
        "session_id": "session_fallback_test",
        "user_id": "user_tester",
        "document_id": "doc_fallback_test",
        "raw_text": "인공지능 기술의 미래와 LLM 기반 교육에 대해 알아보겠습니다.",
        "profile": {
            "reading_level": "intermediate",
            "user_literacy_level": 3,
            "target_domain": "IT",
        },
        "trace": [],
        "errors": [],
    }


def test_readability_fallback(error_state):
    """가독성 분석 함수가 예외를 발생시키더라도, fallback_readability가 호출되어 기본값이 적용되어야 한다."""
    with patch("backend.app.agents.content_reducer.agent.analyze_readability", side_effect=Exception("Readability analysis error")):
        result = run_content_reducer(error_state)
        # default difficulty와 readability가 들어갔는지 확인 (기본값 50.0)
        assert result["readability_score"] == 50.0
        assert result["difficulty_score"] == 50.0
        assert len(result["trace"]) >= 1
        assert "readability_fallback" in result["trace"][-1]
        assert result["trace"][-1]["readability_fallback"] == "Readability analysis error"


def test_chunker_fallback(error_state):
    """청커가 예외를 발생시키더라도, fallback_chunks가 호출되어 원문 단일 청크가 정상 반환되어야 한다."""
    with patch("backend.app.agents.content_reducer.agent.semantic_chunk", side_effect=Exception("Chunker error")):
        result = run_content_reducer(error_state)
        # fallback으로 1개의 청크가 구성되어야 함
        assert len(result["chunks"]) == 1
        assert result["chunks"][0]["chunk_id"] == "chunk_doc_fallback_test_01"
        assert len(result["trace"]) >= 1
        assert "chunking_fallback" in result["trace"][-1]
        assert result["trace"][-1]["chunking_fallback"] == "Chunker error"


def test_restructure_fallback(error_state):
    """LLM 재구성 모듈(restructure_text)이 예외를 발생시키더라도, restructured_text에 original_text가 그대로 매핑되어야 한다."""
    with patch("backend.app.agents.content_reducer.agent.restructure_text", side_effect=Exception("LLM API restructure error")):
        result = run_content_reducer(error_state)
        assert len(result["chunks"]) >= 1
        for chunk in result["chunks"]:
            # LLM 실패 시 원문 텍스트를 그대로 반환
            assert chunk["restructured_text"] == chunk["original_text"]
        assert len(result["trace"]) >= 1
        assert "restructure_fallback" in result["trace"][-1]
        assert result["trace"][-1]["restructure_fallback"] == "LLM API restructure error"


def test_rag_fallback(error_state):
    """RAG 용어풀이 주입 모듈(inject_rag_terms)이 예외를 발생시키더라도, terms = [] 로 처리되어야 한다."""
    with patch("backend.app.agents.content_reducer.agent.inject_rag_terms", side_effect=Exception("RAG DB connection error")):
        result = run_content_reducer(error_state)
        assert len(result["chunks"]) >= 1
        for chunk in result["chunks"]:
            assert chunk["terms"] == []
        assert len(result["trace"]) >= 1
        assert "rag_fallback" in result["trace"][-1]
        assert result["trace"][-1]["rag_fallback"] == "RAG DB connection error"


def test_entire_pipeline_critical_failure(error_state):
    """에이전트 전체 파이프라인에서 복합 혹은 예상치 못한 최상위 오류 발생 시, fallback_content_reducer_response가 호출되어 예외가 외부로 전파되지 않아야 한다."""
    # semantic_chunk가 예외를 내고, fallback_chunks조차 예외를 내는 극단적 상황 시뮬레이션
    with patch("backend.app.agents.content_reducer.agent.semantic_chunk", side_effect=Exception("Critical chunker error")), \
         patch("backend.app.agents.content_reducer.agent.fallback_chunks", side_effect=RuntimeError("Fatal fallback error")):
        
        result = run_content_reducer(error_state)
        # 응답이 크래시하지 않고, 기본 fallback 구조를 반환해야 한다.
        assert result["readability_score"] == 50.0
        assert result["difficulty_score"] == 50.0
        assert len(result["chunks"]) == 1
        assert result["chunks"][0]["chunk_id"] == "chunk_doc_fallback_test_01"
        assert result["simplified_text"] != ""
        assert result["terms"] == []
        assert len(result["errors"]) >= 1
        assert result["trace"][-1]["status"] == "fallback"
