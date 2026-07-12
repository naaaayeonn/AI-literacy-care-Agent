"""오케스트레이터 출력 → 프론트(4번) 계약 변환 어댑터.

1번 역할의 산출물 중 하나: "프론트가 바로 렌더링할 수 있는 JSON 제공".
프론트(apps/web)는 camelCase + 중첩(type/payload) 구조를 쓰는데, 내부 state는
snake_case + flat 구조다. 이 모듈이 그 경계를 변환한다.

3번 백엔드는 이 함수를 import해서 그대로 프론트에 전달하면 된다:
- WebSocket 응답(③→④):  to_intervention_command(state)
- 세션 결과 REST 응답:    to_session_result(state)

프론트 계약 출처:
  apps/web/src/lib/api.ts  (InterventionCommand, SessionResultResponse)
  feature/frontend-setup 브랜치

내부 state에 없는 필드(scoreSeries, level, totalXp, completionRate, badges[])는
합리적 기본값으로 파생한다. 각 파생 규칙은 주석으로 명시했고, 실제 누적값
(누적 XP/레벨, 장기 시계열)은 3번 DB·5번 프로필이 채우면 교체하면 된다.
"""

from __future__ import annotations

from typing import Any

from backend.app.orchestrator.state import ReadingSessionState

# --- 내 intervention.type → 프론트 InterventionType 매핑 ---
# 내부: none/highlight/nudge/quiz  →  프론트: nudge/quiz/highlight/score_update/session_end
_FRONT_INTERVENTION_TYPE = {
    "highlight": "highlight",
    "nudge": "nudge",
    "quiz": "quiz",
    "none": "score_update",  # 개입 없음 = 점수만 실시간 갱신
}

# --- reward.badge(문자열) → 프론트 BadgeData(객체) 카탈로그 ---
# 새 배지가 생기면 여기만 추가한다. 미등록 배지는 기본 이모지로 폴백.
_BADGE_CATALOG: dict[str, dict[str, str]] = {
    "first_read": {"name": "첫 완독", "emoji": "📚", "description": "첫 글을 끝까지 읽었어요!"},
    "steady_focus": {"name": "집중 유지", "emoji": "🎯", "description": "흔들림 없이 끝까지 집중했어요."},
    "comeback": {"name": "다시 집중", "emoji": "🔄", "description": "집중이 흐트러져도 끝까지 읽었어요."},
    "needs_support": {"name": "함께 성장", "emoji": "🌱", "description": "케어와 함께 읽기를 마쳤어요."},
}


def to_intervention_command(state: ReadingSessionState) -> dict[str, Any]:
    """WS(③→④) InterventionCommand 로 변환.

    프론트 NudgeController가 `command.type` 과 `command.payload` 를 읽는다.
    """
    intervention = state.get("intervention") or {}
    level = intervention.get("level", "none")
    internal_type = intervention.get("type", "none")
    front_type = _FRONT_INTERVENTION_TYPE.get(internal_type, "score_update")

    focus_score = _num(state.get("focus_score"), default=0.0)
    progress = _completion_rate(state)

    payload: dict[str, Any] = {
        "focusScore": round(focus_score, 1),
        "progress": progress,
    }

    if level != "none":
        payload["nudgeLevel"] = level
        payload["nudgeMessage"] = intervention.get("message", "")
        if "summary_text" in intervention:
            payload["summaryText"] = intervention["summary_text"]

    if front_type == "highlight":
        payload["highlights"] = _highlights(state, intervention)
    elif front_type == "quiz" and "quiz_data" in intervention:
        payload["quizzes"] = intervention["quiz_data"]

    return {"type": front_type, "payload": payload}


def to_session_result(state: ReadingSessionState) -> dict[str, Any]:
    """세션 최종 결과(REST) SessionResultResponse 로 변환."""
    breakdown = state.get("score_breakdown") or {}
    reward = state.get("reward") or {}
    profile = state.get("profile") or {}

    literacy = _num(state.get("literacy_score"), default=0.0)
    prev_literacy = _num(profile.get("previous_literacy_score"), default=literacy)

    xp_earned = int(_num(reward.get("xp"), default=0))
    prev_total_xp = int(_num(profile.get("total_xp"), default=0))
    total_xp = prev_total_xp + xp_earned

    return {
        "sessionId": state.get("session_id", ""),
        "literacyScore": round(literacy, 1),
        "comprehensionScore": round(_num(breakdown.get("comprehension_score")), 1),
        "engagementScore": round(_num(breakdown.get("engagement_score")), 1),
        # difficulty_score(0~100, 절대 난이도) → ±보정값. 50을 기준 0으로, ±5 범위.
        "difficultyBonus": round(_num(breakdown.get("difficulty_score"), default=50.0) / 10 - 5, 1),
        "completionRate": _completion_rate(state),
        "xpEarned": xp_earned,
        "totalXp": total_xp,
        # 레벨: 누적 XP 100당 1레벨 (3번 DB가 누적값을 주면 그대로 반영됨).
        "level": total_xp // 100 + 1,
        # 시계열: 누적 데이터가 없으므로 케어 전/후 2점으로 개선 스토리를 만든다.
        # (5번 프로필이 장기 시계열을 주면 교체)
        "scoreSeries": [
            {"label": "케어 전", "before": round(prev_literacy, 1), "after": round(prev_literacy, 1)},
            {"label": "케어 후", "before": round(prev_literacy, 1), "after": round(literacy, 1)},
        ],
        "badges": _badges(reward),
        "sessionDurationMs": _session_duration_ms(state),
    }


# ──────────────────────────────────────────────
# 파생 헬퍼
# ──────────────────────────────────────────────


def _num(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if result != result:  # NaN 방어
        return default
    return result


def _completion_rate(state: ReadingSessionState) -> int:
    """reading_events의 최대 스크롤 위치(0~1)를 완독률(%)로 환산. 없으면 0."""
    positions = [
        _num(e.get("position"))
        for e in state.get("reading_events", [])
        if e.get("position") is not None
    ]
    if not positions:
        return 0
    return min(100, max(0, int(round(max(positions) * 100))))


def _session_duration_ms(state: ReadingSessionState) -> int:
    """reading_events 타임스탬프 범위로 세션 길이(ms)를 추정. 없으면 0."""
    stamps = [int(_num(e.get("timestamp_ms"))) for e in state.get("reading_events", [])]
    if len(stamps) < 2:
        return 0
    return max(stamps) - min(stamps)


def _badges(reward: dict) -> list[dict[str, Any]]:
    """reward.badge(문자열 1개) → 프론트 BadgeData 배열."""
    badge_id = reward.get("badge")
    if not badge_id:
        return []
    meta = _BADGE_CATALOG.get(
        badge_id, {"name": badge_id, "emoji": "🏅", "description": ""}
    )
    return [
        {
            "id": badge_id,
            "name": meta["name"],
            "emoji": meta["emoji"],
            "description": meta["description"],
            # acquiredAt: 시각은 호출부(API 경계)에서 주입. 순수 변환에선 빈 문자열.
            "acquiredAt": "",
        }
    ]


def _highlights(state: ReadingSessionState, intervention: dict) -> list[dict[str, Any]]:
    """target_chunk_id → 단락 인덱스 기반 highlight 범위."""
    target = intervention.get("target_chunk_id")
    if not target:
        return []
    chunks = state.get("chunks", []) or []
    paragraph_index = 0
    for idx, chunk in enumerate(chunks):
        if str(chunk.get("chunk_id")) == str(target):
            paragraph_index = idx
            break
    # 문자 단위 위치는 2번 chunk 메타가 생기면 채운다. 지금은 단락 전체 강조.
    return [{"paragraphIndex": paragraph_index, "start": 0, "end": 0}]
