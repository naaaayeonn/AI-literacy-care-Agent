"""Orchestrator flow — 에이전트 실행 순서와 상태 전이.

[구현 예정: 6/22 M0 / 6/23 상태 전이]

초기 버전은 LangGraph 없이 단순 Python 함수 체인으로 만든다. 중요한 것은
호출 순서와 state 변경이 명확하고, 각 단계가 trace에 기록되며, 한 에이전트
실패가 전체를 멈추지 않는 것이다. (LangGraph StateGraph 전환은 그 이후.)

최소 흐름:
    create_state
    → content_reducer
    → cognitive_care
    → routing_decision
    → score_engine
    → reward
    → profile_update
    → final_result
"""

from __future__ import annotations

from .state import ReadingSessionState


from ..services.cognitive_care import calculate_focus_score, determine_intervention

def run_reading_session(state: ReadingSessionState) -> ReadingSessionState:
    """한 세션을 시작부터 결과까지 실행한다.
    Role 1 오케스트레이터 파이프라인에서 Role 3(Cognitive Care) 엔진을 호출합니다.
    """
    # 1. Cognitive Care Node 실행
    # state['reading_events'] 에서 계산 엔진 호환 형태로 변환
    events_data = []
    for e in state.get("reading_events", []):
        metadata = e.get("metadata", {})
        events_data.append({
            "timestamp_ms": e.get("timestamp_ms", 0),
            "type": e.get("type", "unknown"),
            "position": e.get("position", metadata.get("position")),
            "duration_ms": e.get("duration_ms", metadata.get("duration_ms")) or 1000
        })
        
    focus_score = calculate_focus_score(events_data)
    intervention_needed, intervention_level = determine_intervention(focus_score)
    
    state["focus_score"] = focus_score
    state["intervention_needed"] = intervention_needed
    state["intervention_level"] = intervention_level
    
    state["trace"].append({
        "step": "cognitive_care",
        "status": "success",
        "detail": {"focus_score": focus_score, "intervention_level": intervention_level}
    })
    
    # 2. Score Engine Stub (1번 역할 추가 구현 예정)
    state["literacy_score"] = 85.0
    state["score_breakdown"] = {
        "comprehension_score": 90.0,
        "engagement_score": focus_score,
        "difficulty_score": 50.0
    }
    
    state["trace"].append({
        "step": "score_engine",
        "status": "success",
        "detail": {"literacy_score": 85.0}
    })
    
    return state
