"""
main.py — Content Reducer FastAPI 서버 진입점 (M2)

Orchestrator(1번), 백엔드(3번), 프론트엔드(4번)가 호출할 수 있는 REST API 엔드포인트를 제공한다.

실행 방법:
  uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import os
import re
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 환경 변수 로드
load_dotenv()

from backend.app.agents.content_reducer.contracts import (
    ReadingSessionState,
    ContentReducerRequest,
    ContentReducerResponse,
    QuizGenerationRequest,
    QuizDict
)
from backend.app.agents.content_reducer.agent import run_content_reducer
from backend.app.agents.content_reducer.quiz_generator import generate_quiz

app = FastAPI(
    title="AI Literacy Care - Content Reducer API",
    description="가독성 분석, 의미 청킹, LLM 기반 쉬운 문장 재구성 및 RAG 용어풀이를 담당하는 2번 에이전트 서비스",
    version="1.0.0"
)

# CORS 설정 (프론트엔드 연동 지원)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic 스키마 정의 (FastAPI 자동 문서화 및 타입 검증용)
# ---------------------------------------------------------------------------

class ContentReducerRequestModel(BaseModel):
    session_id: str = Field(..., description="세션 식별자")
    raw_text: str = Field(..., description="분석할 원문 텍스트")
    user_literacy_level: int = Field(3, ge=1, le=5, description="사용자 문해력 수준 (1~5)")
    target_domain: str | None = Field("일반", description="도메인 영역")
    profile: dict | None = Field(default_factory=dict, description="사용자 세부 프로필")
    user_id: str | None = Field(None, description="사용자 식별자")
    document_id: str | None = Field(None, description="문서 식별자")


class QuizGenerationRequestModel(BaseModel):
    session_id: str = Field(..., description="세션 식별자")
    chunk_id: str = Field(..., description="문제를 생성할 청크 ID")
    context: str = Field(..., description="청크의 재구성된 텍스트")
    user_literacy_level: int | None = Field(3, ge=1, le=5, description="사용자 문해력 수준")


class SessionStartRequestModel(BaseModel):
    userId: str = Field(..., description="사용자 익명 식별자")
    source: dict = Field(..., description="출처 정보 (url, title, type)")
    content: list[str] = Field(..., description="Readability 또는 pdf.js에서 추출한 본문 문단 배열")


class TermLookupRequestModel(BaseModel):
    word: str = Field(..., description="조회할 단어")
    sessionId: str | None = Field(None, description="세션 식별자")
    context: str | None = Field(None, description="단어가 등장한 문맥")


# ---------------------------------------------------------------------------
# 엔드포인트 구현
# ---------------------------------------------------------------------------

@app.get("/health")
def health_check():
    """서버 헬스 체크."""
    return {
        "status": "healthy",
        "agent": "Content & RAG Reducer Agent (Role 2)",
        "mode": os.getenv("CONTENT_REDUCER_MODE", "real"),
        "rag_mode": os.getenv("RAG_MODE", "memory")
    }


@app.post("/api/content-reducer/reduce", response_model=dict)
def reduce_content(req: ContentReducerRequestModel):
    """
    원문을 입력받아 가독성 점수, 의미 단위 청킹, 쉬운 문장 재구성 및 RAG 용어풀이를 일괄 수행한다.
    Orchestrator 혹은 프론트엔드에서 세션 로드 시 호출.
    """
    user_id = req.user_id or (req.profile.get("user_id") if req.profile else None) or "default_user"
    document_id = req.document_id or (req.profile.get("document_id") if req.profile else None) or "default_doc"

    # ReadingSessionState 스키마로 가공하여 에이전트 진입점 호출
    state: ReadingSessionState = {
        "session_id": req.session_id,
        "user_id": user_id,
        "document_id": document_id,
        "raw_text": req.raw_text,
        "profile": {
            "user_literacy_level": req.user_literacy_level,
            "target_domain": req.target_domain,
            **(req.profile or {})
        },
        "trace": [],
        "errors": []
    }
    
    try:
        updated_state = run_content_reducer(state)
        
        # API Response 규격에 맞춰 추출
        return {
            "session_id": updated_state.get("session_id"),
            "readability_score": updated_state.get("readability_score", 50.0),
            "difficulty_score": updated_state.get("difficulty_score", 50.0),
            "chunks": updated_state.get("chunks", []),
            "simplified_text": updated_state.get("simplified_text", ""),
            "terms": updated_state.get("terms", []),
            "trace": updated_state.get("trace", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content reduction failed: {str(e)}")


@app.post("/api/content-reducer/quiz", response_model=dict)
def get_quiz(req: QuizGenerationRequestModel):
    """
    특정 청크 텍스트에 대한 맞춤형 독해력 확인 퀴즈를 생성한다.
    개입 트리거(3번 에이전트 신호) 수신 후 Orchestrator에서 호출.
    """
    try:
        quiz = generate_quiz(req.chunk_id, req.context)
        return quiz
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")


@app.post("/api/session/start")
def start_session(req: SessionStartRequestModel):
    """
    크롬 확장 프로그램에서 전송한 본문 content[] 배열을 가공하여 세션을 시작한다.
    """
    from backend.app.agents.content_reducer.extension_session import _content_to_raw_text
    import uuid

    # 1. content[] 문단 배열 정규화 (머리말/꼬리말 제거 포함)
    raw_text = _content_to_raw_text(req.content)
    
    # 2. 세션 아이디 생성
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    document_id = req.source.get("title", "doc")
    # 특수문자 제거 및 정제
    document_id = re.sub(r"[^a-zA-Z0-9가-힣]", "_", document_id)[:30]
    if not document_id:
        document_id = "doc"

    # 3. ReadingSessionState 구성
    state: ReadingSessionState = {
        "session_id": session_id,
        "user_id": req.userId,
        "document_id": document_id,
        "raw_text": raw_text,
        "profile": {
            "user_literacy_level": 3,
            "target_domain": "일반"
        },
        "trace": [],
        "errors": []
    }

    try:
        updated_state = run_content_reducer(state)
        
        # 4. camelCase와 snake_case 호환성을 위해 둘 다 지원하는 맵핑 수행
        def map_term(t):
            return {
                "term": t["term"],
                "definition": t["definition"],
                "source": t["source"],
                "faithfulnessScore": t.get("faithfulness_score", 1.0),
                "faithfulness_score": t.get("faithfulness_score", 1.0),
                "chunkId": t["chunk_id"],
                "chunk_id": t["chunk_id"],
                "_meta": t.get("_meta", {})
            }

        def map_chunk(c):
            return {
                "chunkId": c["chunk_id"],
                "chunk_id": c["chunk_id"],
                "originalText": c["original_text"],
                "original_text": c["original_text"],
                "difficulty": c["difficulty"],
                "charStart": c["char_start"],
                "char_start": c["char_start"],
                "charEnd": c["char_end"],
                "char_end": c["char_end"],
                "terms": [map_term(t) for t in c.get("terms", [])]
            }

        chunks_mapped = [map_chunk(c) for c in updated_state.get("chunks", [])]
        terms_mapped = [map_term(t) for t in updated_state.get("terms", [])]

        return {
            "sessionId": session_id,
            "chunks": chunks_mapped,
            "simplifiedText": updated_state.get("simplified_text", ""),
            "terms": terms_mapped,
            "difficultyScore": updated_state.get("difficulty_score", 50.0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


@app.post("/api/terms/lookup")
def lookup_term_api(req: TermLookupRequestModel):
    """
    단어 단건에 대한 무료 용어풀이 결과를 반환한다.
    """
    from backend.app.agents.content_reducer.rag_engine import lookup_term
    try:
        t = lookup_term(req.word, req.context)
        return {
            "term": t["term"],
            "definition": t["definition"],
            "source": t["source"],
            "faithfulnessScore": t.get("faithfulness_score", 0.0),
            "faithfulness_score": t.get("faithfulness_score", 0.0),
            "chunkId": t.get("chunk_id", ""),
            "chunk_id": t.get("chunk_id", ""),
            "_meta": t.get("_meta", {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lookup failed: {str(e)}")

