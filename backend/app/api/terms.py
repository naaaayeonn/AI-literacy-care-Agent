from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..agents.content_reducer.rag_engine import lookup_term

router = APIRouter(prefix="/api/terms", tags=["Terms Lookup"])

@router.get("/lookup")
async def lookup_term_api(word: str, sessionId: Optional[str] = None, context: Optional[str] = None):
    """
    단어 단건에 대한 용어풀이 결과를 반환한다.
    2번 모듈의 RAG 엔진(rag_engine.py)을 활용하여 환각 없는 정확한 정의를 제공.
    """
    if not word:
        raise HTTPException(status_code=400, detail="word is required")
        
    try:
        t = lookup_term(word, context)
        return {
            "term": t["term"],
            "definition": t["definition"],
            "source": t["source"],
            "faithfulnessScore": t.get("faithfulness_score", 0.0),
            "chunkId": t.get("chunk_id", "")
        }
    except Exception as e:
        # 검색 실패 또는 예외 발생 시 기본 응답 폴백
        return {
            "term": word,
            "definition": f"'{word}'에 대한 사전 뜻을 찾을 수 없습니다. ({str(e)})",
            "source": "Local Fallback",
            "faithfulnessScore": 0.0,
            "chunkId": ""
        }
