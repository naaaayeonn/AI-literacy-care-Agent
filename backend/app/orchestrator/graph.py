"""Orchestrator flow - 에이전트 간 전체 파이프라인.

[구현: 6/22 M0 / 6/23 기본 구조 / 7/5 전체 연결 완성]

초기에는 LangGraph 대신 순수 Python 함수 체인 방식.
각 단계는 state를 받아 채우고, 예외 발생 시 fallback 적용.

전체 흐름:
    create_state
    → content_reducer (스텁 - RAG 팀 담당)
    → cognitive_care
    → routing_decision  
    → score_engine
    → reward
    → profile_update (비동기 DB 접근이 필요하므로 별도 처리)
    → final_result
"""

from __future__ import annotations
from .state import ReadingSessionState
from ..services.cognitive_care import calculate_focus_score, determine_intervention
from .score import calculate_literacy_score
from .routing import decide_intervention as route_intervention
from .errors import (
    apply_content_reducer_fallback,
    apply_cognitive_care_fallback,
    apply_score_fallback,
    apply_reward_fallback,
)
from ..services.reward_service import calculate_xp, check_badges


def run_reading_session(state: ReadingSessionState) -> ReadingSessionState:
    """전체 읽기 세션 파이프라인을 실행한다.
    Role 1 오케스트레이터가 모든 Role(2~5번)을 순차 호출합니다.
    """
    
    # 1. Content Reducer (2번 역할 - 스텁/RAG 팀 담당)
    try:
        state = _run_content_reducer(state)
    except Exception as e:
        state = apply_content_reducer_fallback(state, e)
    
    # 2. Cognitive Care (3번 역할 - 집중도 분석)
    try:
        state = _run_cognitive_care(state)
    except Exception as e:
        state = apply_cognitive_care_fallback(state, e)
    
    # 3. Routing Decision (개입 판별)
    try:
        state = route_intervention(state)
    except Exception as e:
        # 라우팅 실패 시 개입 없음으로 처리
        state["intervention_needed"] = False
        state["intervention_level"] = "none"
        state["trace"].append({"step": "routing", "status": "fallback", "detail": {"error": str(e)}})
    
    # 4. Score Engine (1번 핵심 - Literacy Score 산출)
    try:
        state = calculate_literacy_score(state)
    except Exception as e:
        state = apply_score_fallback(state, e)
    
    # 5. Reward (4번 역할 - XP/배지)
    try:
        state = _run_reward(state)
    except Exception as e:
        state = apply_reward_fallback(state, e)
    
    return state


def _run_content_reducer(state: ReadingSessionState) -> ReadingSessionState:
    """Content Reducer 스텁 (2번 RAG 팀 담당, 현재는 raw_text 그대로 사용)."""
    raw = state.get("raw_text", "")
    paragraphs = [p.strip() for p in raw.split("\n\n") if p.strip()]
    
    if not paragraphs:
        paragraphs = [raw] if raw else ["(빈 문서)"]
    
    state["chunks"] = [
        {"index": i, "text": p, "type": "paragraph"}
        for i, p in enumerate(paragraphs)
    ]
    state["simplified_text"] = raw
    state["terms"] = []  # RAG 팀이 채울 영역
    state["difficulty_score"] = state.get("difficulty_score", 50.0)
    
    state["trace"].append({
        "step": "content_reducer",
        "status": "success",
        "detail": {"chunk_count": len(paragraphs)}
    })
    
    return state


def _run_cognitive_care(state: ReadingSessionState) -> ReadingSessionState:
    """Cognitive Care Node 실행 (3번 역할)."""
    events_data = []
    for e in state.get("reading_events", []):
        metadata = e.get("metadata", {})
        events_data.append({
            "timestamp_ms": e.get("timestamp_ms", 0),
            "type": e.get("type", "unknown"),
            "position": metadata.get("position"),
            "duration_ms": metadata.get("duration_ms")
        })
    
    focus_score = calculate_focus_score(events_data)
    intervention_needed, intervention_level, intervention_msg = determine_intervention(focus_score)
    
    state["focus_score"] = focus_score
    state["engagement_score"] = focus_score
    state["intervention_needed"] = intervention_needed
    state["intervention_level"] = intervention_level
    state["intervention_message"] = intervention_msg
    
    state["trace"].append({
        "step": "cognitive_care",
        "status": "success",
        "detail": {"focus_score": focus_score, "intervention_level": intervention_level}
    })
    
    return state


def _run_reward(state: ReadingSessionState) -> ReadingSessionState:
    """Reward 계산 (4번 역할)."""
    literacy = state.get("literacy_score", 0.0)
    xp = calculate_xp(literacy_score=literacy, completed=True)
    
    profile = state.get("profile", {})
    total_sessions = profile.get("total_sessions", 0) + 1
    engagement = state.get("engagement_score", 0.0)
    
    new_badges = check_badges(
        total_sessions=total_sessions,
        literacy_score=literacy,
        engagement_score=engagement,
        existing_badge_ids=profile.get("badges", []),
    )
    
    state["reward"] = {
        "xp": xp,
        "badges": new_badges,
        "message": f"+{xp} XP 획득!" if xp > 0 else "",
    }
    
    state["trace"].append({
        "step": "reward",
        "status": "success",
        "detail": {"xp": xp, "new_badges_count": len(new_badges)}
    })
    
    return state
