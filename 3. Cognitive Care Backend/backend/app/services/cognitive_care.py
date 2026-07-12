from typing import List, Dict, Any, Tuple

def _scroll_velocity(event: Dict[str, Any]) -> float:
    """스크롤 속도(px/s)를 이벤트에서 정규화해 읽는다.
    - 확장(tracker.js): 최상위 velocity 미제공(대신 duration_ms=스크롤 간격)
    - 웹(ReadingPane): metadata.payload.scrollVelocity 에 담겨 옴
    """
    v = event.get("velocity")
    if v is None:
        meta = event.get("metadata") or {}
        payload = meta.get("payload") if isinstance(meta, dict) else None
        if isinstance(payload, dict):
            v = payload.get("scrollVelocity")
    try:
        return float(v) if v is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def calculate_focus_score(events: List[Dict[str, Any]], baseline: Dict[str, int] = None) -> float:
    """
    행동 이벤트 리스트를 분석하여 0~100 사이의 실시간 집중도(Focus Score)를 계산합니다.
    """
    if not events:
        return 100.0

    recent = events[-500:]
    score = 100.0

    scroll_threshold = 1.5
    if baseline and "easy" in baseline and "hard" in baseline:
        avg_speed = (baseline["easy"] + baseline["hard"]) / 2.0
        scroll_threshold = max(0.4, avg_speed * 2.0)

    for i, event in enumerate(recent):
        etype = event.get("type")

        if etype == "blur":
            duration = event.get("duration_ms")
            if duration is None:
                if i + 1 < len(recent):
                    duration = recent[i+1].get("timestamp_ms", event.get("timestamp_ms", 0)) - event.get("timestamp_ms", 0)
                else:
                    duration = 3000
            
            score -= 20.0 + min((duration / 1000.0) * 3.0, 30.0)

        elif etype == "scroll":
            velocity = _scroll_velocity(event)
            too_fast_velocity = velocity > scroll_threshold
            if too_fast_velocity:
                score -= 8.0

        elif etype == "pause":
            score -= 25.0

        elif etype == "dwell":
            meta = event.get("metadata") or {}
            payload = meta.get("payload") if isinstance(meta, dict) else None
            dwell_ms = None
            if isinstance(payload, dict):
                dwell_ms = payload.get("dwellMs")
            if dwell_ms is None:
                dwell_ms = event.get("duration_ms") or 0
            if dwell_ms > 20000:
                score -= 15.0

    return round(max(0.0, min(100.0, score)), 1)

def determine_intervention(focus_score: float) -> Tuple[bool, str, str]:
    """
    Focus Score에 따라 개입(Intervention) 여부 및 피드백 메시지를 결정합니다.
    """
    if focus_score >= 75.0:
        return False, "none", ""
    elif 50.0 <= focus_score < 75.0:
        return True, "soft", "핵심 문장을 다시 한번 살펴볼까요? 📌"
    elif 30.0 <= focus_score < 50.0:
        return True, "medium", "잠깐! 조금 쉬었다가 다시 읽어보는 건 어때요? ☕"
    else:
        return True, "hard", "집중이 필요해요! 간단한 퀴즈로 내용을 확인해봐요! 📝"
