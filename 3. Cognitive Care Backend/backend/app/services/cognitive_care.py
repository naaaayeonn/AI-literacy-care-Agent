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


def _personalized_scroll_threshold(baseline: Dict[str, Any] = None, difficulty_score: float = None) -> float:
    """온보딩 캘리브레이션 + 글 난이도로 개인화한 스키밍 임계값(px/ms). 1번 canonical과 동일 로직.

    개인의 "난이도별 편안한 읽기 속도" 직선을 두 캘리브레이션 점(easy/hard)으로 세우고,
    지금 글 난이도 D에서 예상 속도 × 여유계수 K를 임계값으로 쓴다.
    → 어려운 글일수록 임계값↓(일찍 스키밍 판정), 쉬운 글일수록 임계값↑. 온보딩만이면 기본 1.5와 블렌딩.
    baseline: {easy, hard, d_easy(기본20), d_hard(기본75), n_sessions}
    """
    DEFAULT = 1.5
    FLOOR = 0.4
    K = 1.8
    if not baseline:
        return DEFAULT
    v_easy = baseline.get("easy")
    v_hard = baseline.get("hard")
    if v_easy is None or v_hard is None:
        return DEFAULT
    try:
        v_easy = float(v_easy)
        v_hard = float(v_hard)
        d_easy = float(baseline.get("d_easy", 20.0))
        d_hard = float(baseline.get("d_hard", 75.0))
        D = float(difficulty_score) if difficulty_score is not None else (d_easy + d_hard) / 2.0
    except (TypeError, ValueError):
        return DEFAULT

    if d_hard != d_easy:
        slope = (v_hard - v_easy) / (d_hard - d_easy)
        expected = v_easy + slope * (D - d_easy)
    else:
        expected = (v_easy + v_hard) / 2.0
    expected = max(0.1, expected)
    personal = max(FLOOR, expected * K)

    try:
        n = int(baseline.get("n_sessions", 0) or 0)
    except (TypeError, ValueError):
        n = 0
    w = min(1.0, 0.5 + 0.1 * n)
    threshold = w * personal + (1.0 - w) * DEFAULT
    return max(FLOOR, threshold)


def _skim_threshold(baseline: Dict[str, Any] = None, difficulty_score: float = None) -> float:
    """스키밍(즉시 감점) 임계값(px/ms) = 개인의 난이도별 예상 읽기 속도 + 0.4.

    7/15: 기존 _personalized_scroll_threshold는 개인값을 기본 1.5와 블렌딩해 임계값이
    너무 높아, 실제 빠른 스크롤도 임계값 아래로 판정되어 오히려 회복(+2)되던 문제를 고친다.
    "내 속도보다 0.4 px/ms 이상 빠르면 스키밍"으로 판정하여 예민하게 감점시킨다.
    """
    FALLBACK = 0.7
    if not baseline:
        return FALLBACK
    v_easy = baseline.get("easy")
    v_hard = baseline.get("hard")
    if v_easy is None or v_hard is None:
        return FALLBACK
    try:
        v_easy = float(v_easy)
        v_hard = float(v_hard)
        d_easy = float(baseline.get("d_easy", 20.0))
        d_hard = float(baseline.get("d_hard", 75.0))
        D = float(difficulty_score) if difficulty_score is not None else (d_easy + d_hard) / 2.0
    except (TypeError, ValueError):
        return FALLBACK

    # 개인 속도-난이도 직선으로 이 난이도에서의 "편안한 읽기 속도" 예측.
    if d_hard != d_easy:
        slope = (v_hard - v_easy) / (d_hard - d_easy)
        expected = v_easy + slope * (D - d_easy)
    else:
        expected = (v_easy + v_hard) / 2.0
    expected = max(0.1, expected)
    # 7/15: 임계값 상한(cap) 1.2. 온보딩에서 빠르게 스크롤하면 baseline이 커져 임계값이 치솟는데,
    # 상한이 2.5면 실제 마우스휠 빠른 스크롤(~1.5~2.5 px/ms)도 임계값을 못 넘어 감점이 안 걸렸다.
    # 정상 읽기 스크롤은 대개 <1 px/ms이므로, 1.2 px/ms 이상은 baseline과 무관하게 스키밍으로 본다.
    return min(expected + 0.4, 1.2)  # 내 속도 + 0.4 초과 = 스키밍, 단 1.2 상한



def calculate_focus_score(events: List[Dict[str, Any]], baseline: Dict[str, Any] = None, difficulty_score: float = None) -> float:
    """
    행동 이벤트 리스트를 분석하여 0~100 사이의 실시간 집중도(Focus Score)를 계산합니다.
    """
    if not events:
        return 100.0

    # 7/15: "지금" 집중도 = 100 − 최근 10개 이벤트의 감점 합. 창을 작게(10) 두어 빠른 스크롤이
    # ~1.5초 안에 확 떨어지고, 정상 읽기(스크롤)를 이어가면 감점 이벤트가 창 밖으로 밀려 회복된다.
    # (정상 스크롤 +2 회복은 감점을 상쇄해 100에 붙이고 감점 반영을 지연시켜 제거함.)
    recent = events[-10:]
    score = 100.0

    # 7/15: 스키밍 임계값 = 개인 예상 읽기 속도 + 1.0 px/ms (블렌딩 폐기).
    scroll_threshold = _skim_threshold(baseline, difficulty_score)

    for i, event in enumerate(recent):
        etype = event.get("type")

        if etype == "blur":
            # 세션 시작 직후 3초 이내의 blur는 팝업 조작으로 인한 것이므로 무시
            if event.get("timestamp_ms", 0) < 3000:
                continue
                
            duration = event.get("duration_ms")
            if duration is None:
                if i + 1 < len(recent):
                    duration = recent[i+1].get("timestamp_ms", event.get("timestamp_ms", 0)) - event.get("timestamp_ms", 0)
                else:
                    duration = 3000
            
            score -= 20.0 + min((duration / 1000.0) * 3.0, 30.0)

        elif etype == "scroll":
            velocity = _scroll_velocity(event)
            # 임계값(개인 속도, 상한 2.5) 초과 = 스키밍 → 감점. 정상 속도 스크롤은 감점 없음(0).
            # 회복은 스키밍 이벤트가 최근 10개 창 밖으로 밀려나며 자연스럽게 이뤄진다.
            if velocity > scroll_threshold:
                score -= 8.0

        elif etype == "pause":
            score -= 2.0

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
