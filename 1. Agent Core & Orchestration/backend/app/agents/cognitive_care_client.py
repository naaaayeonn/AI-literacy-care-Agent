"""Adapter for the Cognitive Care agent."""

from __future__ import annotations

from backend.app.agents.config import run_agent
from backend.app.agents.real.cognitive_care_service import (
    _scroll_velocity,
    calculate_focus_score,
    determine_intervention,
)
from backend.app.agents.stubs.cognitive_care_stub import cognitive_care_stub
from backend.app.orchestrator.state import ReadingSessionState


def _sanitize_events(events: list) -> list:
    """vendored `calculate_focus_score`가 크래시나지 않도록 이벤트를 방어한다(CP-1/H1).

    3번 원본은 `event.get("duration_ms", 1000)`을 쓰는데, 키가 **있고 값이 None**이면
    default가 먹지 않아 `None / 1000.0`(blur)·`None < 300`(scroll)에서 TypeError로 죽는다.
    정상 경로(`_normalize_events`)는 이미 None 키를 제거하지만, 정규화를 거치지 않은
    인입이나 3번 원본 교체 시에도 데모가 끊기지 않도록 어댑터에서 한 번 더 막는다.
    (원본 `cognitive_care_service.py`는 정책상 verbatim 유지 → 방어는 여기에 둔다.)
    """
    safe: list = []
    for event in events:
        if isinstance(event, dict) and "duration_ms" in event and event["duration_ms"] is None:
            event = {k: v for k, v in event.items() if k != "duration_ms"}
        safe.append(event)
    return safe


def _cognitive_care_real(state: ReadingSessionState) -> ReadingSessionState:
    """3번 실제 모듈을 ReadingSessionState 계약으로 매핑한다.

    3번 `cognitive_care_service`는 순수 함수만 제공하므로, reading_events를
    넘겨 focus_score를 받고 계약 필드(focus/engagement/intervention_needed)를 채운다.

    주의:
    - 3번 모듈은 engagement_score를 산출하지 않는다. 스텁과 동일한 관례로
      engagement_score = focus_score 로 둔다(별도 신호가 생기면 교체).
    - 최종 intervention 명령(level/type/message)은 orchestrator의 routing.py가
      단독 결정한다. 여기서는 intervention_needed 플래그까지만 채운다.
    - duration_ms=None 방어는 `_sanitize_events`가 담당한다(CP-1).
    """
    events = _sanitize_events(state.get("reading_events", []))
    focus_score = calculate_focus_score(events)
    needed, _level, _message = determine_intervention(focus_score)

    state["focus_score"] = focus_score
    state["engagement_score"] = focus_score
    state["intervention_needed"] = needed
    return state


# 실제 3번 모듈 연결 완료 — LITERACY_COGNITIVE_CARE_IMPL=real 로 전환.
_REAL_IMPL = _cognitive_care_real


def run_cognitive_care(state: ReadingSessionState) -> ReadingSessionState:
    """Run the configured Cognitive Care implementation."""
    return run_agent("cognitive_care", state, stub=cognitive_care_stub, real=_REAL_IMPL)


# 개입 컷오프(3번 `determine_intervention`과 동일). 디버그 모니터 색상 기준.
INTERVENTION_CUTOFFS = {"soft": 75.0, "medium": 50.0, "hard": 30.0}

# 3번 calculate_focus_score와 동일한 파라미터(디버그 감점 분해를 점수와 일치시키기 위함).
FOCUS_WINDOW = 12  # 최근 이벤트 창 크기
DEFAULT_SCROLL_THRESHOLD = 1.5  # px/ms (baseline 미적용 시 디폴트)


def calculate_focus_breakdown(events: list) -> dict:
    """집중도 점수의 **감점 내역**을 산출한다(디버그/모니터용).

    실제 점수는 3번 `calculate_focus_score`가 계산하므로 여기서 재계산하지 않고 그대로
    호출한다. 이 함수는 "왜 그 점수가 나왔는지"를 설명하는 파생값만 만든다.
    3번 원본과 동일하게 **최근 12개 이벤트 창(window)** 기준으로 감점을 분해하므로,
    penalty.total ≈ 100 - focusScore 가 성립한다(0/100 클램프 구간 제외).

    반환(camelCase, 프론트/모니터 계약):
      {
        focusScore, interventionLevel, interventionNeeded, windowSize,
        eventCounts: {scroll, blur, focus, pause, dwell, fastInterval, highVelocity, other, total, window},
        penalty: {blur, skimScroll, pause, dwell, total},
        cutoffs: {soft, medium, hard},
      }
    """
    safe = _sanitize_events(events or [])
    window = safe[-FOCUS_WINDOW:]  # 점수와 동일한 최근 창

    counts = {
        "scroll": 0,
        "blur": 0,
        "focus": 0,
        "pause": 0,
        "dwell": 0,
        "fastInterval": 0,  # 간격 < 250ms
        "highVelocity": 0,  # velocity > 임계(1.5)
        "other": 0,
    }
    blur_penalty = 0.0
    skim_penalty = 0.0
    pause_penalty = 0.0
    dwell_penalty = 0.0

    for event in window:
        if not isinstance(event, dict):
            counts["other"] += 1
            continue
        etype = event.get("type")
        if etype == "blur":
            counts["blur"] += 1
            duration = event.get("duration_ms")
            if duration is None:
                duration = 3000
            blur_penalty += 20.0 + min((duration / 1000.0) * 2.0, 15.0)
        elif etype == "scroll":
            counts["scroll"] += 1
            duration = event.get("duration_ms")
            velocity = _scroll_velocity(event)
            fast_interval = duration is not None and duration < 250
            high_velocity = velocity > DEFAULT_SCROLL_THRESHOLD
            if fast_interval:
                counts["fastInterval"] += 1  # 참고용 카운트(감점엔 미반영)
            if high_velocity:
                counts["highVelocity"] += 1
            if high_velocity:
                # 3번과 동일: 스키밍 감점은 velocity(>임계)만 기준. 간격(<250ms)은
                # 스로틀 오검출이라 제외(cognitive_care_service와 일치).
                skim_penalty += 8.0
        elif etype == "pause":
            counts["pause"] += 1
            pause_penalty += 18.0
        elif etype == "dwell":
            counts["dwell"] += 1
            meta = event.get("metadata") or {}
            payload = meta.get("payload") if isinstance(meta, dict) else None
            dwell_ms = payload.get("dwellMs") if isinstance(payload, dict) else None
            if dwell_ms is None:
                dwell_ms = event.get("duration_ms") or 0
            if dwell_ms > 20000:
                dwell_penalty += 12.0
        elif etype in counts:
            counts[etype] += 1
        else:
            counts["other"] += 1

    counts["total"] = len(safe)
    counts["window"] = len(window)

    focus_score = calculate_focus_score(safe)
    needed, level, _message = determine_intervention(focus_score)

    return {
        "focusScore": focus_score,
        "interventionLevel": level,
        "interventionNeeded": needed,
        "windowSize": len(window),
        "eventCounts": counts,
        "penalty": {
            "blur": round(blur_penalty, 1),
            "skimScroll": round(skim_penalty, 1),
            "pause": round(pause_penalty, 1),
            "dwell": round(dwell_penalty, 1),
            "total": round(blur_penalty + skim_penalty + pause_penalty + dwell_penalty, 1),
        },
        "cutoffs": dict(INTERVENTION_CUTOFFS),
    }
