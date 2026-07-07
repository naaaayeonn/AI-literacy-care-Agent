"""
restructurer.py — LLM 기반 텍스트 재구성 모듈 (M1)

사용자의 리터러시 프로필과 텍스트 난이도에 따라
Claude API를 호출하여 쉬운 문장으로 변환한다.

동작 모드:
  CONTENT_REDUCER_MODE=real (기본):
    → ANTHROPIC_API_KEY가 있으면 실제 Claude API 호출
    → API 키 없으면 DEMO 모드로 자동 전환

  CONTENT_REDUCER_MODE=stub:
    → 원문 앞에 [레벨 수준] 접두사 추가 (API 없이 빠른 테스트용)

  DEMO_MODE=true:
    → API 없이 데모용 텍스트 반환

실패 시 Fallback: 원문 텍스트를 그대로 반환 (절대 예외 전파 안 함)
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from backend.app.agents.content_reducer.contracts import ChunkDict
from backend.app.agents.content_reducer.prompts import (
    RESTRUCTURE_SYSTEM_PROMPT,
    build_restructure_prompt,
)
from backend.app.agents.content_reducer.router import get_routing_reason, select_model

# ---------------------------------------------------------------------------
# 환경 설정
# ---------------------------------------------------------------------------
# 실행 시점에 환경 변수를 동적으로 읽도록 변경함


# ---------------------------------------------------------------------------
# 고품질 데모 폴백 데이터 로드
# ---------------------------------------------------------------------------

def _load_fallback_data() -> dict:
    try:
        root = Path(__file__).resolve().parents[4]
        path = root / "data" / "demo_fallback_data.json"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

_FALLBACK_DATA = _load_fallback_data()


# ---------------------------------------------------------------------------
# Gemini 클라이언트 초기화 (Google AI Studio 무료)
# ---------------------------------------------------------------------------

def _get_client():
    """Gemini 클라이언트를 반환한다. 키가 없거나 패키지가 없으면 None."""
    try:
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key or api_key.startswith("your_"):
            return None
        return genai.Client(api_key=api_key)
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# 데모 / Stub 재구성
# ---------------------------------------------------------------------------

_LEVEL_LABELS = {
    1: "초급",
    2: "초중급",
    3: "중급",
    4: "중고급",
    5: "전문가",
}


def _demo_restructure(text: str, level: int) -> str:
    """API 없이 동작하는 데모용 재구성."""
    # 1. 고품질 데모 캐시 데이터 매칭 시도
    if _FALLBACK_DATA and "chunks" in _FALLBACK_DATA:
        normalized_text = text.replace(" ", "").replace("\n", "")
        for entry in _FALLBACK_DATA["chunks"]:
            ref_text = entry["original_text"].replace(" ", "").replace("\n", "")
            if normalized_text in ref_text or ref_text in normalized_text:
                return entry["restructured_text"]

    # 2. 매칭 실패 시 단순 시뮬레이션
    label = _LEVEL_LABELS.get(level, "중급")
    sentences = re.split(r"(?<=[다요했됩습])[.]\s*|(?<=[.!?])\s+", text)
    simplified = " ".join(s.strip() for s in sentences if s.strip())
    return f"[{label} 수준 재구성] {simplified}"

from backend.app.agents.content_reducer.snowchat_client import is_snowchat_available, _call_llm_via_snowchat

# ---------------------------------------------------------------------------
# 데모 / Stub 재구성
# ---------------------------------------------------------------------------

_LEVEL_LABELS = {
    1: "초급",
    2: "초중급",
    3: "중급",
    4: "중고급",
    5: "전문가",
}


def _demo_restructure(text: str, level: int) -> str:
    """API 없이 동작하는 데모용 재구성."""
    # 1. 고품질 데모 캐시 데이터 매칭 시도
    if _FALLBACK_DATA and "chunks" in _FALLBACK_DATA:
        normalized_text = text.replace(" ", "").replace("\n", "")
        for entry in _FALLBACK_DATA["chunks"]:
            ref_text = entry["original_text"].replace(" ", "").replace("\n", "")
            if normalized_text in ref_text or ref_text in normalized_text:
                return entry["restructured_text"]

    # 2. 매칭 실패 시 단순 시뮬레이션
    label = _LEVEL_LABELS.get(level, "중급")
    sentences = re.split(r"(?<=[다요했됩습])[.]\s*|(?<=[.!?])\s+", text)
    simplified = " ".join(s.strip() for s in sentences if s.strip())
    return f"[{label} 수준 재구성] {simplified}"


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------

def restructure_text(
    chunks: list[ChunkDict],
    profile: dict,
    difficulty_score: float,
    domain: str = "일반",
) -> list[ChunkDict]:
    """
    청크 목록을 사용자 수준에 맞게 재구성한다.

    Args:
        chunks: ChunkDict 목록 (chunker.py 출력)
        profile: 사용자 프로필
        difficulty_score: 전체 문서 난이도
        domain: 도메인 힌트

    Returns:
        restructured_text가 추가된 ChunkDict 목록
    """
    # 리터러시 수준 결정
    level = profile.get("user_literacy_level", 3)
    if isinstance(profile.get("reading_level"), str):
        _map = {
            "beginner": 1, "elementary": 2, "intermediate": 3,
            "advanced": 4, "expert": 5,
        }
        level = _map.get(profile.get("reading_level", "intermediate"), 3)

    mode = os.getenv("CONTENT_REDUCER_MODE", "real").lower()
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    # Stub / Demo 모드 → 빠른 반환
    if mode == "stub" or demo_mode:
        for chunk in chunks:
            chunk["restructured_text"] = _demo_restructure(
                chunk["original_text"], level
            )
        return chunks

    # 실제 LLM 호출 시도
    if not is_snowchat_available():
        # API 키 없으면 demo로 폴백
        for chunk in chunks:
            chunk["restructured_text"] = _demo_restructure(
                chunk["original_text"], level
            )
        return chunks

    model_used = "gemini-2.5-flash"

    for chunk in chunks:
        chunk_difficulty = chunk.get("difficulty", difficulty_score)
        term_count = len(chunk.get("terms", []))

        try:
            prompt = build_restructure_prompt(chunk["original_text"], level, domain)
            restructured = _call_llm_via_snowchat(
                model=model_used,
                prompt=prompt,
                system_instruction=RESTRUCTURE_SYSTEM_PROMPT
            )
            chunk["restructured_text"] = restructured
            # routing 메타 정보 (trace용)
            reason = get_routing_reason(chunk_difficulty, term_count, model_used)
            chunk.setdefault("_meta", {})["routing"] = reason
            chunk.setdefault("_meta", {})["model"] = model_used

        except Exception as exc:
            # LLM 실패 → 원문 반환 (Fallback)
            chunk["restructured_text"] = chunk["original_text"]
            chunk.setdefault("_meta", {})["routing"] = f"fallback: {exc}"

        # Rate limit 방지
        time.sleep(0.05)

    return chunks
