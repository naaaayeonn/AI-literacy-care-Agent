"""
restructurer.py — 문단별 요약 생성 모듈 (M1/M2 개편)

각 청크의 original_text를 받아 독자의 문해력 수준(1~5레벨)에 맞춰서
1~2문장의 핵심 요약문(summary)을 생성한다. 이 요약문은 3번 백엔드에서 OX 퀴즈를 출제하는 근거로 사용된다.

SnowChat API(무료 Gemini 2.5 Flash)를 활용하여 요금을 차단하며, 
API 키가 없거나 데모 모드일 때는 결정론적인 더미 요약(앞부분 100자 + 요약 태그)을 제공하여 환각을 차단한다.
"""
from __future__ import annotations

import os
from backend.app.agents.content_reducer.snowchat_client import (
    is_snowchat_available,
    _call_llm_via_snowchat,
)

# ---------------------------------------------------------------------------
# 요약 생성 시스템 프롬프트
# ---------------------------------------------------------------------------
SUMMARY_SYSTEM_PROMPT = """당신은 한국어 문단을 독자의 문해력 수준에 맞춰서 1~2문장으로 압축 요약하는 전문가입니다.

요약 원칙:
1. 원문의 핵심 팩트, 숫자, 인과관계를 절대 왜곡하지 마세요.
2. 1~2문장으로 명확하게 요약하여, 독자가 글의 골자를 한눈에 이해하게 하세요.
3. 이 요약문은 향후 O/X 퀴즈의 출제 근거가 되므로 정보가 구체적이어야 합니다.
4. 설명이나 서두("이 글은~", "요약하자면~") 없이 오직 요약된 문장만 출력하세요.

독자 수준 가이드:
- 레벨 1 (초급): 아주 쉬운 단어와 비유를 사용. 
- 레벨 3 (중급): 고등학생 수준. 일반적인 시사 어휘 수준 유지.
- 레벨 5 (전문가): 전공 지식을 그대로 반영한 조밀한 요약."""


def summarize_chunk(original_text: str, user_literacy_level: int) -> str:
    """
    단일 문단을 독자 수준에 맞춰 1~2문장으로 요약한다.
    """
    if not original_text or not original_text.strip():
        return ""

    level_desc = {
        1: "레벨 1 (아주 쉬운 어휘와 초등 수준 비유 사용)",
        2: "레벨 2 (쉬운 어휘와 중등 수준 설명)",
        3: "레벨 3 (보통 난이도, 고등 수준)",
        4: "레벨 4 (성인 교양 수준, 다소 학술적)",
        5: "레벨 5 (전문 전공 수준, 전문용어 그대로 사용)"
    }.get(user_literacy_level, "레벨 3 (보통 난이도)")

    prompt = f"""[독자 수준]: {level_desc}
[요약할 원문]:
{original_text}

[요약문]:"""

    try:
        if is_snowchat_available():
            # gemini-2.5-flash 모델을 사용하여 무료로 고속 요약 수행
            summary = _call_llm_via_snowchat(
                model="gemini-2.5-flash",
                prompt=prompt,
                system_instruction=SUMMARY_SYSTEM_PROMPT
            )
            if summary:
                return summary
    except Exception:
        pass

    # Fallback: API 호출이 불가능하거나 에러 시 앞부분 일부를 잘라 요약문 대체
    sentences = original_text.replace("\n", " ").split(".")
    fallback_parts = [s.strip() for s in sentences if s.strip()]
    if len(fallback_parts) >= 2:
        return f"[요약] {fallback_parts[0]}. {fallback_parts[1]}."
    elif len(fallback_parts) == 1:
        return f"[요약] {fallback_parts[0]}."
    return f"[요약] {original_text[:100]}..."


def summarize_chunks(
    chunks: list[dict],
    profile: dict,
) -> list[dict]:
    """
    청크 목록을 돌며 각 청크에 'summary' 필드를 생성하여 주입한다.
    """
    user_literacy_level = int(profile.get("user_literacy_level", 3))

    for chunk in chunks:
        original = chunk.get("original_text", "")
        chunk["summary"] = summarize_chunk(original, user_literacy_level)

    return chunks
