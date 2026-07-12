"""
quiz_generator.py — 문맥 맞춤형 퀴즈 생성기 (M2) (v2 O/X 스펙 적용)
"""
from __future__ import annotations

import json
import os
import re

from backend.app.agents.content_reducer.contracts import QuizDict
from backend.app.agents.content_reducer.prompts import QUIZ_SYSTEM_PROMPT, build_quiz_prompt

def validate_quiz(quiz: dict) -> bool:
    """O/X 퀴즈 유효성 검증"""
    try:
        if not isinstance(quiz.get("statement"), str) or not quiz["statement"].strip():
            return False
        if not isinstance(quiz.get("answer"), bool):
            return False
        if not isinstance(quiz.get("explanation"), str) or not quiz["explanation"].strip():
            return False
        return True
    except Exception:
        return False

def fallback_ox_quiz(chunk_id: str, summary: str) -> QuizDict:
    """키가 없거나 실패 시 결정론적 해시 폴백(홀짝)"""
    h = hash(chunk_id)
    if h % 2 == 0:
        return QuizDict(
            quizId="",
            type="ox",
            statement=summary if summary.strip() else "이 문단은 올바른 정보를 제공합니다.",
            answer=True,
            explanation="요약과 일치합니다.",
            sourceChunkId=chunk_id
        )
    else:
        # 간단한 반대말(없다/않다 추가) - 데모용이므로 간단히 처리
        return QuizDict(
            quizId="",
            type="ox",
            statement=summary + " (반대)" if summary.strip() else "이 문단은 올바르지 않은 정보를 제공합니다.",
            answer=False,
            explanation="원문과 반대되는 서술입니다.",
            sourceChunkId=chunk_id
        )

def generate_ox_quiz(summary: str, paragraph: str, chunk_id: str = "") -> QuizDict:
    """
    주어진 텍스트 문맥을 분석하여 독해력 확인 O/X 퀴즈를 생성한다.
    """
    if not paragraph or not paragraph.strip():
        return fallback_ox_quiz(chunk_id, summary)

    # 1. Stub 또는 Demo 모드일 경우 API 없이 시뮬레이션
    mode = os.getenv("CONTENT_REDUCER_MODE", "real").lower()
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
    if mode == "stub" or demo_mode:
        return fallback_ox_quiz(chunk_id, summary)

    try:
        from backend.app.agents.content_reducer.snowchat_client import is_snowchat_available, _call_llm_via_snowchat
        
        if not is_snowchat_available():
            return fallback_ox_quiz(chunk_id, summary)

        model = "gemini-2.5-flash"
        prompt = build_quiz_prompt(summary, paragraph)

        raw_content = _call_llm_via_snowchat(
            model=model,
            prompt=prompt,
            system_instruction=QUIZ_SYSTEM_PROMPT
        )
        
        json_match = re.search(r"\{.*\}", raw_content, re.DOTALL)
        if json_match:
            quiz_data = json.loads(json_match.group(0))
        else:
            quiz_data = json.loads(raw_content)

        if validate_quiz(quiz_data):
            return QuizDict(
                quizId="",
                type="ox",
                statement=quiz_data["statement"],
                answer=quiz_data["answer"],
                explanation=quiz_data["explanation"],
                sourceChunkId=chunk_id
            )
        else:
            print(f"[quiz_generator] WARNING: 퀴즈 유효성 실패. Fallback 적용. Raw: {raw_content}")
            return fallback_ox_quiz(chunk_id, summary)

    except Exception as exc:
        print(f"[quiz_generator] 퀴즈 생성 예외 발생, fallback 반환. 원인: {exc}")
        return fallback_ox_quiz(chunk_id, summary)
