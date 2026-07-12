"""
restructurer.py — (비활성화됨)

설계 변경에 따라 LLM 기반 문장 재구성 기능이 제거되었습니다.
대신 문단별 난이도 분석 + 문해력 수준 RAG로 대체 예정입니다.

이 파일은 하위 호환을 위해 유지하지만, 실제 호출되지 않습니다.
"""
from __future__ import annotations


def restructure_text(
    chunks: list,
    profile: dict,
    difficulty_score: float,
    domain: str = "일반",
) -> list:
    """
    (비활성화됨) 원문을 그대로 반환합니다.

    이 함수는 agent.py에서 더 이상 호출하지 않습니다.
    만약 실수로 호출되더라도 안전하게 원문을 반환합니다.
    """
    return chunks
