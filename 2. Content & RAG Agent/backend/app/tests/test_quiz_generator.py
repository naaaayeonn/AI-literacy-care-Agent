"""
test_quiz_generator.py — 퀴즈 생성기 단위 테스트 (M2)

pytest로 실행:
  python -m pytest backend/app/tests/test_quiz_generator.py -v
"""
import pytest
from unittest.mock import patch, MagicMock

from backend.app.agents.content_reducer.quiz_generator import (
    validate_quiz,
    generate_quiz,
    _generate_demo_quiz
)
from backend.app.agents.content_reducer.fallbacks import fallback_quiz


class TestQuizValidation:

    def test_valid_quiz_returns_true(self):
        valid = {
            "question": "인공지능의 정의로 옳은 것은?",
            "options": [
                "1. 인간의 지능을 모방하는 기술",
                "2. 단순 계산용 하드웨어",
                "3. 수동 데이터 백업장치",
                "4. 인터넷 신호 전송 기기"
            ],
            "correct_option": 1,
            "explanation": "본문에서 인공지능은 인간의 지능을 모방하는 기술의 총칭으로 설명됩니다."
        }
        assert validate_quiz(valid) is True

    def test_missing_question_returns_false(self):
        invalid = {
            "options": ["1. A", "2. B", "3. C", "4. D"],
            "correct_option": 2,
            "explanation": "설명"
        }
        assert validate_quiz(invalid) is False

    def test_invalid_option_count_returns_false(self):
        invalid = {
            "question": "질문",
            "options": ["1. A", "2. B", "3. C"],  # 3개 선택지
            "correct_option": 1,
            "explanation": "설명"
        }
        assert validate_quiz(invalid) is False

    def test_out_of_range_correct_option_returns_false(self):
        invalid = {
            "question": "질문",
            "options": ["1. A", "2. B", "3. C", "4. D"],
            "correct_option": 5,  # 1~4 범위를 벗어남
            "explanation": "설명"
        }
        assert validate_quiz(invalid) is False

    def test_empty_explanation_returns_false(self):
        invalid = {
            "question": "질문",
            "options": ["1. A", "2. B", "3. C", "4. D"],
            "correct_option": 3,
            "explanation": "   "
        }
        assert validate_quiz(invalid) is False


class TestGenerateQuiz:

    def test_generate_demo_quiz_structure(self):
        """데모 퀴즈 생성 시 구조가 완벽해야 한다."""
        quiz = _generate_demo_quiz("chunk_01", "인공지능(AI)과 메타인지 능력은 중요합니다.")
        assert quiz["chunk_id"] == "chunk_01"
        assert "인공지능" in quiz["question"] or "메타인지" in quiz["question"]
        assert len(quiz["options"]) == 4
        assert quiz["correct_option"] == 2
        assert len(quiz["explanation"]) > 0

    def test_generate_quiz_fallback_on_empty_context(self):
        """빈 문맥이 들어왔을 때, 예외 없이 fallback_quiz를 반환한다."""
        quiz = generate_quiz("chunk_02", "")
        fb = fallback_quiz("chunk_02")
        assert quiz["question"] == fb["question"]
        assert quiz["correct_option"] == fb["correct_option"]

    @patch("backend.app.agents.content_reducer.quiz_generator._get_client")
    def test_generate_quiz_api_success(self, mock_get_client):
        """API 호출 성공 및 유효한 응답 수신 시의 동작 검증."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock response from Gemini
        mock_response = MagicMock()
        mock_response.text = """
        {
          "question": "RAG의 핵심 목적은 무엇인가요?",
          "options": [
            "1. 임의 데이터 가공",
            "2. 환각(Hallucination) 감소 및 최신 정보 검색",
            "3. CPU 성능 개선",
            "4. 메모리 용량 확보"
          ],
          "correct_option": 2,
          "explanation": "RAG는 외부 데이터베이스 검색을 결합해 AI의 환각을 줄여줍니다."
        }
        """
        mock_client.models.generate_content.return_value = mock_response

        # 환경 모드를 real로 강제
        with patch.dict("os.environ", {"CONTENT_REDUCER_MODE": "real", "DEMO_MODE": "false"}):
            quiz = generate_quiz("chunk_03", "RAG 기반 시스템은 환각(hallucination)을 줄이고 정확성을 높입니다.")
            assert quiz["chunk_id"] == "chunk_03"
            assert quiz["question"] == "RAG의 핵심 목적은 무엇인가요?"
            assert quiz["correct_option"] == 2
            assert "환각" in quiz["explanation"]

    @patch("backend.app.agents.content_reducer.quiz_generator._get_client")
    def test_generate_quiz_api_validation_failure_fallback(self, mock_get_client):
        """API 호출은 성공했으나 반환된 JSON이 규격에 맞지 않을 때 fallback_quiz가 적용되는지 검증."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # options 개수가 2개뿐인 규격 미달 응답
        mock_response = MagicMock()
        mock_response.text = """
        {
          "question": "문제",
          "options": ["1. A", "2. B"],
          "correct_option": 1,
          "explanation": "설명"
        }
        """
        mock_client.models.generate_content.return_value = mock_response

        with patch.dict("os.environ", {"CONTENT_REDUCER_MODE": "real", "DEMO_MODE": "false"}):
            quiz = generate_quiz("chunk_04", "본문 데이터")
            fb = fallback_quiz("chunk_04")
            assert quiz["question"] == fb["question"]
            assert quiz["correct_option"] == fb["correct_option"]
            assert quiz["chunk_id"] == "chunk_04"
