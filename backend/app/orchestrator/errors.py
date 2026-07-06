"""에이전트 에러 fallback - 각 단계가 실패해도 전체 흐름이 멈추지 않게 한다.

[구현: 6/23 기본 구조 / 6/26 완성]

기본적 정책 (ARCHITECTURE §4 errors):
    Content Reducer 실패 : raw_text를 그대로 단일 chunk로, difficulty_score=50
    Cognitive Care 실패  : focus_score=60, intervention_level="none"
    Reward 실패          : reward 빈 dict 반환
    Profile 실패         : updated_profile 빈 dict 반환
    QA 실패              : 전체 흐름 유지, trace에 warning 추가

모든 fallback은 trace에 status="fallback"을 기록한다.
"""

from __future__ import annotations
from .state import ReadingSessionState


class AgentError(Exception):
    """특정 에이전트 단계 실패를 나타내는 기본 예외."""


def apply_content_reducer_fallback(state: ReadingSessionState, error: Exception) -> ReadingSessionState:
    """Content Reducer 실패 시: raw_text를 단일 chunk로 사용."""
    state["chunks"] = [{"index": 0, "text": state.get("raw_text", ""), "type": "paragraph"}]
    state["simplified_text"] = state.get("raw_text", "")
    state["terms"] = []
    state["difficulty_score"] = 50.0
    state["trace"].append({
        "step": "content_reducer",
        "status": "fallback",
        "detail": {"error": str(error)}
    })
    return state


def apply_cognitive_care_fallback(state: ReadingSessionState, error: Exception) -> ReadingSessionState:
    """Cognitive Care 실패 시: 기본 중립값."""
    state["focus_score"] = 60.0
    state["engagement_score"] = 60.0
    state["intervention_needed"] = False
    state["intervention_level"] = "none"
    state["intervention_message"] = ""
    state["trace"].append({
        "step": "cognitive_care",
        "status": "fallback",
        "detail": {"error": str(error)}
    })
    return state


def apply_score_fallback(state: ReadingSessionState, error: Exception) -> ReadingSessionState:
    """Score Engine 실패 시: 퀴즈 정답률 * 집중도 단순 평균."""
    quiz = state.get("quiz_result", {})
    focus = state.get("focus_score", 60.0)
    if quiz and quiz.get("total_count", 0) > 0:
        comp = (quiz["correct_count"] / quiz["total_count"]) * 100
    else:
        comp = 70.0
    state["literacy_score"] = round((comp + focus) / 2, 1)
    state["comprehension_score"] = round(comp, 1)
    state["engagement_score"] = round(focus, 1)
    state["trace"].append({
        "step": "score_engine",
        "status": "fallback",
        "detail": {"error": str(error)}
    })
    return state


def apply_reward_fallback(state: ReadingSessionState, error: Exception) -> ReadingSessionState:
    """Reward 실패 시: 빈 리워드."""
    state["reward"] = {"xp": 0, "badge": None, "message": ""}
    state["trace"].append({
        "step": "reward",
        "status": "fallback",
        "detail": {"error": str(error)}
    })
    return state


def apply_profile_fallback(state: ReadingSessionState, error: Exception) -> ReadingSessionState:
    """Profile 실패 시: 빈 프로필."""
    state["updated_profile"] = {}
    state["trace"].append({
        "step": "profile_update",
        "status": "fallback",
        "detail": {"error": str(error)}
    })
    return state


def apply_qa_fallback(state: ReadingSessionState, error: Exception) -> ReadingSessionState:
    """QA 실패 시: 경고만 추가하고 흐름 유지."""
    state["trace"].append({
        "step": "qa_eval",
        "status": "fallback",
        "detail": {"error": str(error), "warning": "QA evaluation skipped"}
    })
    return state
