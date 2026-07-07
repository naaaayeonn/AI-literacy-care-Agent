"""
test_stub_e2e.py — Stub 기반 E2E 흐름 테스트 (M0)

1번 Orchestrator가 stub을 사용해 전체 폐루프를 돌릴 수 있음을 검증한다.

pytest로 실행:
  python -m pytest backend/app/tests/test_stub_e2e.py -v
"""
import pytest

from backend.app.agents.stubs.content_reducer_stub import content_reducer_stub
from backend.app.agents.content_reducer.agent import run_content_reducer


# ---------------------------------------------------------------------------
# 공통 테스트 상태 픽스처
# ---------------------------------------------------------------------------

@pytest.fixture
def base_state():
    """기본 ReadingSessionState 픽스처."""
    return {
        "session_id": "test_session_001",
        "user_id": "user_001",
        "document_id": "doc_test",
        "raw_text": (
            "인공지능(AI)은 컴퓨터 과학의 한 분야로, 인간의 지능을 모방하는 기술이다.\n\n"
            "특히 LLM(대규모 언어 모델)은 방대한 텍스트 데이터를 학습하여 "
            "자연스러운 언어를 생성할 수 있다. 레이턴시 최적화는 실서비스에서 중요한 과제다.\n\n"
            "메타인지와 문해력은 효과적인 학습의 핵심 요소로, "
            "RAG 기반 시스템을 통해 환각 없는 정보를 제공할 수 있다."
        ),
        "profile": {
            "reading_level": "intermediate",
            "user_literacy_level": 3,
            "weaknesses": ["technical_terms"],
        },
        "trace": [],
        "errors": [],
    }


# ---------------------------------------------------------------------------
# content_reducer_stub 테스트
# ---------------------------------------------------------------------------

class TestContentReducerStub:

    def test_stub_returns_state(self, base_state):
        """stub이 state를 반환해야 한다."""
        result = content_reducer_stub(base_state)
        assert result is not None
        assert isinstance(result, dict)

    def test_stub_fills_difficulty_score(self, base_state):
        """difficulty_score가 0~100 범위로 채워져야 한다."""
        result = content_reducer_stub(base_state)
        assert "difficulty_score" in result
        assert 0.0 <= result["difficulty_score"] <= 100.0

    def test_stub_fills_readability_score(self, base_state):
        """readability_score가 0~100 범위로 채워져야 한다."""
        result = content_reducer_stub(base_state)
        assert "readability_score" in result
        assert 0.0 <= result["readability_score"] <= 100.0

    def test_stub_fills_chunks(self, base_state):
        """chunks가 비어 있지 않아야 한다."""
        result = content_reducer_stub(base_state)
        assert "chunks" in result
        assert len(result["chunks"]) >= 1

    def test_stub_chunks_have_required_fields(self, base_state):
        """각 chunk에 필수 필드가 있어야 한다."""
        result = content_reducer_stub(base_state)
        required = {"chunk_id", "original_text", "char_start", "char_end", "difficulty"}
        for chunk in result["chunks"]:
            missing = required - set(chunk.keys())
            assert not missing, f"chunk 필드 누락: {missing}"

    def test_stub_fills_simplified_text(self, base_state):
        """simplified_text가 비어 있지 않아야 한다."""
        result = content_reducer_stub(base_state)
        assert "simplified_text" in result
        assert len(result["simplified_text"]) > 0

    def test_stub_fills_terms(self, base_state):
        """terms 필드가 존재해야 한다 (빈 배열도 허용)."""
        result = content_reducer_stub(base_state)
        assert "terms" in result
        assert isinstance(result["terms"], list)

    def test_stub_records_trace(self, base_state):
        """trace에 content_reducer 스텝이 기록되어야 한다."""
        result = content_reducer_stub(base_state)
        assert len(result["trace"]) >= 1
        steps = [t["step"] for t in result["trace"]]
        assert "content_reducer" in steps

    def test_stub_trace_has_required_fields(self, base_state):
        """trace 항목에 필수 필드가 있어야 한다."""
        result = content_reducer_stub(base_state)
        cr_trace = next(t for t in result["trace"] if t["step"] == "content_reducer")
        assert "status" in cr_trace
        assert "chunk_count" in cr_trace
        assert "latency_ms" in cr_trace

    def test_stub_chunk_id_follows_convention(self, base_state):
        """chunk_id가 'chunk_{document_id}_{순번}' 형식을 따라야 한다."""
        result = content_reducer_stub(base_state)
        document_id = base_state["document_id"]
        for chunk in result["chunks"]:
            assert chunk["chunk_id"].startswith(f"chunk_{document_id}_")

    def test_stub_does_not_raise_on_empty_text(self):
        """빈 raw_text에서도 예외 없이 동작해야 한다."""
        state = {
            "session_id": "s",
            "user_id": "u",
            "document_id": "d",
            "raw_text": "",
            "profile": {},
            "trace": [],
            "errors": [],
        }
        result = content_reducer_stub(state)
        assert "chunks" in result


# ---------------------------------------------------------------------------
# run_content_reducer (M0 agent.py 뼈대) 테스트
# ---------------------------------------------------------------------------

class TestRunContentReducer:

    def test_agent_fills_required_fields(self, base_state):
        """agent가 모든 필수 필드를 채워야 한다."""
        result = run_content_reducer(base_state)
        for field in ["difficulty_score", "readability_score", "chunks", "simplified_text", "terms"]:
            assert field in result, f"필드 누락: {field}"

    def test_agent_records_trace(self, base_state):
        """agent의 trace에 content_reducer 스텝이 기록되어야 한다."""
        result = run_content_reducer(base_state)
        steps = [t["step"] for t in result["trace"]]
        assert "content_reducer" in steps

    def test_agent_does_not_raise_on_empty_text(self):
        """빈 raw_text에서도 예외 없이 동작해야 한다."""
        state = {
            "session_id": "s",
            "user_id": "u",
            "document_id": "d",
            "raw_text": "",
            "profile": {},
            "trace": [],
            "errors": [],
        }
        result = run_content_reducer(state)
        assert "chunks" in result
