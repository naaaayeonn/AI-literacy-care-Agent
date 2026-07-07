"""Self-Correction v0 — 세션 결과 품질 검토와 경고 생성 (7/1 작업).

폐루프가 끝난 결과 state를 읽어 '비정상 점수'나 '빈 출력' 같은 품질 이상을
감지하고 `warnings`로 남긴다. 사용자 흐름을 막지 않는 검토 층이며, QA(6번)와
발표용 '검증 가능한 시스템' 근거, 디버깅에 사용한다.

v0 범위: 감지 + 경고. 실제 단계 재실행(self-correction loop)은 통합 이후
확장한다. 지금은 순수 함수로 결정론적 검토만 수행한다.

검토 항목
- empty_chunks            : Content Reducer 산출 chunks가 비어 있음
- empty_simplified_text   : 쉬운 설명 텍스트가 비어 있음
- missing_focus_score     : 집중도 점수가 없음
- missing_literacy_score  : 최종 점수가 없음
- score_out_of_range      : 점수가 0~100 범위를 벗어남(또는 NaN)
- quiz_missing            : 퀴즈 결과가 없어 이해도가 기본값으로 계산됨
- high_abnormal_penalty   : 비정상 읽기 감점이 임계치 이상
- agent_fallback          : 한 개 이상 단계가 fallback으로 처리됨
"""

from __future__ import annotations

import math

from .state import QualityWarning, ReadingSessionState

# 비정상 읽기 감점이 이 값 이상이면 품질 경고를 남긴다.
HIGH_PENALTY_THRESHOLD = 15.0


def review_session(state: ReadingSessionState) -> ReadingSessionState:
    """결과 state를 검토하고 감지된 경고를 state['warnings']에 누적한다."""
    state.setdefault("warnings", [])
    state["warnings"].extend(collect_warnings(state))
    return state


def collect_warnings(state: ReadingSessionState) -> list[QualityWarning]:
    """결과 품질 이상을 결정론적으로 수집한다(순수 함수)."""
    warnings: list[QualityWarning] = []

    if not state.get("chunks"):
        warnings.append(
            {
                "code": "empty_chunks",
                "severity": "warning",
                "message": "Content Reducer가 chunk를 생성하지 못했습니다.",
                "field": "chunks",
            }
        )

    if not str(state.get("simplified_text", "")).strip():
        warnings.append(
            {
                "code": "empty_simplified_text",
                "severity": "warning",
                "message": "쉬운 설명 텍스트가 비어 있습니다.",
                "field": "simplified_text",
            }
        )

    if "focus_score" not in state:
        warnings.append(
            {
                "code": "missing_focus_score",
                "severity": "warning",
                "message": "집중도 점수가 계산되지 않았습니다.",
                "field": "focus_score",
            }
        )

    warnings.extend(_check_literacy_score(state))
    warnings.extend(_check_quiz(state))
    warnings.extend(_check_penalty(state))
    warnings.extend(_check_fallback(state))

    return warnings


def _check_literacy_score(state: ReadingSessionState) -> list[QualityWarning]:
    if "literacy_score" not in state:
        return [
            {
                "code": "missing_literacy_score",
                "severity": "critical",
                "message": "최종 Literacy Score가 산출되지 않았습니다.",
                "field": "literacy_score",
            }
        ]

    score = state.get("literacy_score")
    try:
        value = float(score)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        value = math.nan

    if not math.isfinite(value) or not 0.0 <= value <= 100.0:
        return [
            {
                "code": "score_out_of_range",
                "severity": "critical",
                "message": "Literacy Score가 0~100 범위를 벗어났습니다.",
                "field": "literacy_score",
                "detail": {"literacy_score": score},
            }
        ]
    return []


def _check_quiz(state: ReadingSessionState) -> list[QualityWarning]:
    quiz_result = state.get("quiz_result")
    total_count = (quiz_result or {}).get("total_count", 0)
    if not quiz_result or total_count <= 0:
        return [
            {
                "code": "quiz_missing",
                "severity": "info",
                "message": "퀴즈 결과가 없어 이해도가 기본값으로 계산되었습니다.",
                "field": "quiz_result",
            }
        ]
    return []


def _check_penalty(state: ReadingSessionState) -> list[QualityWarning]:
    breakdown = state.get("score_breakdown") or {}
    penalty = breakdown.get("cross_validation_penalty", 0.0)
    try:
        penalty_value = float(penalty)
    except (TypeError, ValueError):
        return []

    if penalty_value >= HIGH_PENALTY_THRESHOLD:
        return [
            {
                "code": "high_abnormal_penalty",
                "severity": "warning",
                "message": "비정상 읽기 감점이 높습니다. 행동 데이터를 확인하세요.",
                "field": "score_breakdown",
                "detail": {"cross_validation_penalty": penalty_value},
            }
        ]
    return []


def _check_fallback(state: ReadingSessionState) -> list[QualityWarning]:
    fallback_steps = [
        entry.get("step")
        for entry in state.get("trace", [])
        if entry.get("status") == "fallback"
    ]
    if fallback_steps:
        return [
            {
                "code": "agent_fallback",
                "severity": "warning",
                "message": "한 개 이상 단계가 fallback으로 처리되었습니다.",
                "detail": {"steps": fallback_steps},
            }
        ]
    return []
