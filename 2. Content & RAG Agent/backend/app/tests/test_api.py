"""
test_api.py — FastAPI API 엔드포인트 통합 테스트 (M2)

pytest로 실행:
  python -m pytest backend/app/tests/test_api.py -v
"""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    """헬스 체크 엔드포인트가 정상 작동하는지 확인."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Content & RAG Reducer Agent" in data["agent"]


def test_reduce_content_endpoint():
    """Content Reduction REST API가 정상적으로 입력을 받아 스키마를 돌려주는지 검증."""
    req_payload = {
        "session_id": "api_test_session_01",
        "raw_text": (
            "인공지능(AI)과 머신러닝 기술은 대형 모델의 레이턴시(지연 시간) 문제를 해결해야 합니다.\n\n"
            "특히 RAG(검색 증강 생성) 아키텍처는 신뢰 가능한 문서를 기반으로 답변을 생성하여 환각을 없앱니다."
        ),
        "user_literacy_level": 3,
        "target_domain": "IT",
        "profile": {
            "user_id": "api_user"
        }
    }
    
    response = client.post("/api/content-reducer/reduce", json=req_payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["session_id"] == "api_test_session_01"
    assert "readability_score" in data
    assert "difficulty_score" in data
    assert len(data["chunks"]) >= 1
    assert "simplified_text" in data
    assert isinstance(data["terms"], list)
    
    # 각 청크와 용어 구조 확인
    first_chunk = data["chunks"][0]
    assert "chunk_id" in first_chunk
    assert "original_text" in first_chunk
    assert "restructured_text" in first_chunk


def test_get_quiz_endpoint():
    """Quiz 생성 API가 정상 작동하며 QuizDict 형태를 반환하는지 검증."""
    req_payload = {
        "session_id": "api_test_session_01",
        "chunk_id": "chunk_doc1_01",
        "context": "인공지능과 머신러닝의 활용 방안에 대해 논의합니다.",
        "user_literacy_level": 3
    }
    
    response = client.post("/api/content-reducer/quiz", json=req_payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["chunk_id"] == "chunk_doc1_01"
    assert "question" in data
    assert len(data["options"]) == 4
    assert data["correct_option"] in [1, 2, 3, 4]
    assert "explanation" in data
