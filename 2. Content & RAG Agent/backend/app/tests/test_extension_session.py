"""
test_extension_session.py — 크롬 확장 및 PDF 인입 통합 테스트 (Phase E)

pytest로 실행:
  python -m pytest backend/app/tests/test_extension_session.py -v
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from backend.app.main import app
from backend.app.agents.content_reducer.extension_session import _content_to_raw_text, remove_repeated_lines
from backend.app.agents.content_reducer.rag_engine import lookup_term

client = TestClient(app)


def test_repeated_lines_removal():
    """여러 문단에 걸쳐 반복되는 머리말/꼬리말(쪽번호, 반복 문서명)이 올바르게 필터링되는지 검증."""
    content = [
        "2026 AI 경진대회 논문\n이 연구는 인공지능 리터러시를 다룹니다.\nPage 1",
        "2026 AI 경진대회 논문\n두 번째 문단에서는 메타인지를 설명합니다.\nPage 2",
        "2026 AI 경진대회 논문\n세 번째 문단은 RAG 기법의 유용성을 입증합니다.\nPage 3"
    ]
    
    # "2026 AI 경진대회 논문"이 모든 문단에 반복 등장하므로 제거 대상이 되어야 함.
    # "Page X"는 각 문단 내에서 고유하므로(빈도 1) 제거되면 안 됨.
    cleaned = remove_repeated_lines(content)
    
    assert len(cleaned) == 3
    for p in cleaned:
        assert "2026 AI 경진대회 논문" not in p
        assert "Page" in p


def test_content_to_raw_text_normalization():
    """content[] 문단 리스트가 올바르게 정규화되고 이중 개행으로 병합되는지 검증."""
    content = [
        "   문단1입니다.   ",
        "",  # 빈 문단 필터링 대상
        "문단2입니다."
    ]
    raw_text = _content_to_raw_text(content)
    assert raw_text == "문단1입니다.\n\n문단2입니다."


def test_lookup_term_exact_and_alias():
    """단건 단어 lookup 시 정확 매칭 및 별칭 매칭 검증."""
    # 용어집에 존재하는 "레이턴시" 단어 테스트
    term_res = lookup_term("레이턴시")
    assert term_res["term"] == "레이턴시"
    assert term_res["source"] != "not_found"
    assert term_res["definition"] != ""
    
    # 대소문자 무관 및 별칭(latency) 테스트
    term_alias = lookup_term("latency")
    assert term_alias["term"] == "레이턴시"
    assert term_alias["source"] != "not_found"
    
    # 미존재 단어 테스트
    with patch("backend.app.agents.content_reducer.rag_engine.is_snowchat_available") as mock_avail:
        mock_avail.return_value = False
        term_missing = lookup_term("없는단어입니다")
        assert term_missing["source"] == "not_found"
        assert term_missing["definition"] == ""



def test_start_session_api_endpoint():
    """POST /api/session/start 엔드포인트의 통합 연동 및 camelCase 응답 정합성 검증."""
    payload = {
        "userId": "user_chrome_ext_99",
        "source": {
            "url": "https://example.com/article",
            "title": "테스트 뉴스 기사",
            "type": "web"
        },
        "content": [
            "인공지능과 머신러닝의 활용이 본격화되고 있습니다.",
            "RAG 시스템은 신뢰성 있는 답변 생성을 위해 필수적입니다."
        ]
    }
    
    # demo_mode=True 강제하여 실제 LLM 호출 우회
    with patch.dict("os.environ", {"CONTENT_REDUCER_MODE": "real", "DEMO_MODE": "true"}):
        response = client.post("/api/session/start", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        # camelCase 키 존재 확인
        assert "sessionId" in data
        assert "chunks" in data
        assert "simplifiedText" in data
        assert "terms" in data
        assert "difficultyScore" in data
        
        # 호환용 snake_case 키 존재 확인 (chunks 내)
        first_chunk = data["chunks"][0]
        assert "chunkId" in first_chunk
        assert "chunk_id" in first_chunk
        assert "originalText" in first_chunk
        assert "original_text" in first_chunk


def test_terms_lookup_api_endpoint():
    """POST /api/terms/lookup 엔드포인트 동작 및 호환 필드 검증."""
    payload = {
        "word": "RAG",
        "sessionId": "sess_test_123"
    }
    
    response = client.post("/api/terms/lookup", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["term"] == "RAG"
    assert data["source"] != "not_found"
    assert "faithfulnessScore" in data
    assert "faithfulness_score" in data


@patch("backend.app.agents.content_reducer.rag_engine._query_woorimalsem_api")
def test_lookup_term_woorimalsem_api(mock_query_api):
    """우리말샘 오픈 API 응답을 통해 용어 정의를 조회하는지 검증."""
    mock_query_api.return_value = {
        "term": "우리말단어",
        "definition": "우리말샘에서 정의한 단어의 뜻입니다.",
        "source": "우리말샘 (국립국어원)"
    }

    res = lookup_term("우리말단어")
    assert res["term"] == "우리말단어"
    assert res["definition"] == "우리말샘에서 정의한 단어의 뜻입니다."
    assert res["source"] == "우리말샘 (국립국어원)"
    assert res["faithfulness_score"] == 1.0


def test_clean_korean_josa():
    """조사 제거 함수가 한국어 조사를 올바르게 제거하는지 검증."""
    from backend.app.agents.content_reducer.rag_engine import _clean_korean_josa
    assert _clean_korean_josa("주가를") == "주가"
    assert _clean_korean_josa("방지법을") == "방지법"
    assert _clean_korean_josa("메타인지는") == "메타인지"
    assert _clean_korean_josa("사람에게는") == "사람에게"  # 조사 '는' 제거됨
    assert _clean_korean_josa("가게") == "가게"  # '게'는 조사가 아니므로 제거되지 않음


@patch("backend.app.agents.content_reducer.rag_engine._query_llm_definition")
@patch("backend.app.agents.content_reducer.rag_engine._query_woorimalsem_api")
def test_lookup_term_llm_fallback(mock_query_api, mock_query_llm):
    """DB와 우리말샘 모두 없을 때 LLM 실시간 의미 유추로 폴백하는지 검증."""
    mock_query_api.return_value = None
    mock_query_llm.return_value = "문맥에서 유추한 실시간 단어 정의입니다."

    res = lookup_term("미등록단어을", context="이 기사에는 미등록단어을 사용하는 문맥이 있습니다.")
    assert res["term"] == "미등록단어"  # 조사 '을' 제거됨
    assert res["definition"] == "문맥에서 유추한 실시간 단어 정의입니다."
    assert res["source"] == "LLM 실시간 유추"
    assert res["faithfulness_score"] == 1.0


def test_lookup_term_meta_tracing():
    """lookup_term 수행 시 _meta 필드에 tried 및 errors가 올바르게 기입되는지 검증."""
    # 1. 로컬 매칭 성공 시
    res_local = lookup_term("RAG")
    assert "_meta" in res_local
    assert "local" in res_local["_meta"]["tried"]
    
    # 2. 미등록 단어 매칭 실패 시 (전체 스텝 시도 후 error 가드 작동)
    with patch("backend.app.agents.content_reducer.rag_engine.is_snowchat_available") as mock_avail:
        mock_avail.return_value = False
        res_missing = lookup_term("없는단어임")
        assert "_meta" in res_missing
        assert "local" in res_missing["_meta"]["tried"]
        assert "llm_skipped_no_key" in res_missing["_meta"]["tried"]


def test_disambiguate_homonyms_with_llm():
    """동음이의어가 여러 개 검색되었을 때 LLM을 이용하여 문맥에 맞는 정의를 정밀 판별하는지 검증."""
    from backend.app.agents.content_reducer.rag_engine import _disambiguate_homonyms_with_llm
    
    mock_items = [
        {"word": "주가", "sense": {"definition": "주식 시장에서 거래되는 주식의 가격."}},
        {"word": "주가", "sense": {"definition": "주인집. 또는 주인의 집."}}
    ]
    
    # LLM이 1번 정의(주식 가격)를 선택하도록 모의
    with patch("backend.app.agents.content_reducer.rag_engine._call_llm_via_snowchat") as mock_call, \
         patch("backend.app.agents.content_reducer.rag_engine.is_snowchat_available") as mock_avail:
        mock_avail.return_value = True
        mock_call.return_value = "1"
        
        best = _disambiguate_homonyms_with_llm(
            word="주가",
            items=mock_items,
            context="최근 IT 기술주의 주가가 폭락했습니다."
        )
        assert best["sense"]["definition"] == "주식 시장에서 거래되는 주식의 가격."
        
    # LLM이 2번 정의(주인집)를 선택하도록 모의
    with patch("backend.app.agents.content_reducer.rag_engine._call_llm_via_snowchat") as mock_call, \
         patch("backend.app.agents.content_reducer.rag_engine.is_snowchat_available") as mock_avail:
        mock_avail.return_value = True
        mock_call.return_value = "2"
        
        best = _disambiguate_homonyms_with_llm(
            word="주가",
            items=mock_items,
            context="그는 마당이 넓은 주가로 이사를 했다."
        )
        assert best["sense"]["definition"] == "주인집. 또는 주인의 집."


