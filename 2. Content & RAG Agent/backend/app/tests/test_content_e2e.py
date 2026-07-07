"""
test_content_e2e.py — Content Reducer 전체 파이프라인 E2E 통합 테스트 (M2)

수행 단계:
  1. 원문 입력 → 가독성 분석 → 청킹 → 재구성 → RAG 용어풀이 주입 실행 (agent.py)
  2. 생성된 chunks 배열 및 terms 배열의 정합성 검증 ( contracts.py 스키마 일치 여부)
  3. 청크 중 하나를 지정해 퀴즈 생성 호출 (quiz_generator.py)
  4. stub/real 토글 설정 동작 확인
  5. trace 및 오류 목록 적재 검증

pytest로 실행:
  python -m pytest backend/app/tests/test_content_e2e.py -v
"""
import pytest
import os
from unittest.mock import patch

from backend.app.agents.content_reducer.contracts import ReadingSessionState
from backend.app.agents.content_reducer.agent import run_content_reducer
from backend.app.agents.content_reducer.quiz_generator import generate_quiz


@pytest.fixture
def sample_state() -> ReadingSessionState:
    """E2E 테스트용 입력 ReadingSessionState."""
    return {
        "session_id": "session_e2e_001",
        "user_id": "user_e2e_tester",
        "document_id": "doc_e2e_test",
        "raw_text": (
            "최근 대규모 언어 모델(LLM)의 급격한 발전은 교육용 인공지능 에이전트 설계에 혁신을 가져왔으며, "
            "다양한 학업 도메인에서 널리 활용되고 있습니다. 이 연구는 최신 기술의 현황을 설명합니다. "
            "과거에는 정적인 학습 교재만 사용했던 반면, 오늘날은 개인 맞춤형 대화 학습이 가능해졌습니다.\n\n"
            "특히 RAG(검색 증강 생성) 아키텍처는 신뢰할 수 있는 외부 출처를 검색하여 할루시네이션(환각) 현상을 획기적으로 줄여줍니다. "
            "이로 인해 AI 기술에 대한 신뢰도와 설명 가능성이 급격히 향상되었습니다. 교육 현장에서도 신뢰도 보장이 필수적입니다.\n\n"
            "학습자의 인지부하를 효율적으로 관리하고 메타인지 능력을 기르는 방향으로 시스템 인터랙션과 퀴즈가 유기적으로 설계되어야 합니다. "
            "개인화 학습 지도는 향후 리터러시 케어 시스템 개발에 매우 중요한 초석이 될 것입니다. 메타인지는 학습의 효율성을 크게 증가시킵니다.\n\n"
            "또한 학습 수준에 따른 라우팅 기능은 복잡한 작업에는 대형 고성능 모델을, 단순 작업에는 경량 모델을 매칭하여 "
            "비용과 레이턴시를 획기적으로 낮추는 역할을 감당합니다. 이러한 하이브리드 아키텍처는 필수적인 엔지니어링 기법입니다.\n\n"
            "마지막으로 데이터셋 구축과 정교한 모델 평가는 시스템의 안정적 운영을 보장하는 핵심 조건입니다. "
            "모델이 특정 자료에만 과도하게 최적화되는 오버피팅 현상을 방지하기 위해 다양한 도메인의 대규모 텍스트를 균형 있게 학습시켜야 합니다. "
            "최신 트랜스포머 기반 아키텍처를 적절히 활용하면 한글 문맥의 미묘한 의미 차이까지 포착하여 자연스러운 읽기 지도를 제공할 수 있습니다."
        ),
        "profile": {
            "reading_level": "intermediate",
            "user_literacy_level": 3,
            "target_domain": "IT/Education",
        },
        "trace": [],
        "errors": [],
    }


def test_full_pipeline_e2e_real_mode_demo(sample_state):
    """실제 모드(Claude API 호출 대신 데모 시뮬레이션 활용)에서 전체 파이프라인 흐름 동작 검증."""
    # ANTHROPIC_API_KEY가 설정되어 있지 않아도 데모로 자동 전환되어 전체 파이프라인이 크래시 없이 끝나야 한다.
    with patch.dict("os.environ", {"CONTENT_REDUCER_MODE": "real", "DEMO_MODE": "true"}):
        # 1. Content Reducer 에이전트 실행
        processed_state = run_content_reducer(sample_state)
        
        # 2. 전반적 반환 스키마 점검
        assert processed_state["session_id"] == "session_e2e_001"
        assert 0.0 <= processed_state["readability_score"] <= 100.0
        assert 0.0 <= processed_state["difficulty_score"] <= 100.0
        assert abs(processed_state["readability_score"] + processed_state["difficulty_score"] - 100.0) < 0.1
        
        # 3. 청크 확인
        chunks = processed_state["chunks"]
        assert len(chunks) >= 2, f"청크 분할 개수 부족: {len(chunks)}"
        
        for i, chunk in enumerate(chunks, start=1):
            assert chunk["chunk_id"] == f"chunk_doc_e2e_test_{i:02d}"
            assert len(chunk["original_text"]) > 0
            assert "restructured_text" in chunk
            assert len(chunk["restructured_text"]) > 0
            assert 0.0 <= chunk["difficulty"] <= 100.0
            assert chunk["char_start"] < chunk["char_end"]
            assert "terms" in chunk
            
        # 4. 세션 전체 terms(용어집) 수집 검증
        terms = processed_state["terms"]
        assert isinstance(terms, list)
        if len(terms) > 0:
            for term in terms:
                assert "term" in term
                assert "definition" in term
                assert "source" in term
                assert "faithfulness_score" in term
                assert term["chunk_id"].startswith("chunk_doc_e2e_test_")
        
        # 5. 텍스트 재구성 결합본 검증
        assert len(processed_state["simplified_text"]) > 0
        assert "\n\n" in processed_state["simplified_text"]
        
        # 6. trace 기록 확인
        assert len(processed_state["trace"]) == 1
        assert processed_state["trace"][0]["step"] == "content_reducer"
        assert processed_state["trace"][0]["status"] == "success"
        
        # 7. 개입 퀴즈 생성 호출 검증 (첫 번째 청크 기준)
        target_chunk = chunks[0]
        quiz = generate_quiz(target_chunk["chunk_id"], target_chunk["restructured_text"])
        
        assert quiz["chunk_id"] == target_chunk["chunk_id"]
        assert len(quiz["question"]) > 0
        assert len(quiz["options"]) == 4
        assert quiz["correct_option"] in [1, 2, 3, 4]
        assert len(quiz["explanation"]) > 0


def test_stub_toggle_mode(sample_state):
    """CONTENT_REDUCER_MODE 환경변수가 'stub'일 때 content_reducer_stub으로 온전히 전환되는지 검증."""
    with patch.dict("os.environ", {"CONTENT_REDUCER_MODE": "stub"}):
        processed_state = run_content_reducer(sample_state)
        
        # stub 실행 여부를 trace로 검증
        assert len(processed_state["trace"]) == 1
        assert processed_state["trace"][0]["status"] == "stub"
        assert "Stub implementation" in processed_state["trace"][0]["note"]
        
        # stub 응답 검증
        assert len(processed_state["chunks"]) >= 1
        assert "[Stub 재구성]" in processed_state["simplified_text"]
