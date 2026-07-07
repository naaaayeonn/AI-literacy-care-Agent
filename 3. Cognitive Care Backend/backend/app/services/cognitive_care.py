from typing import List, Dict, Any, Tuple

def calculate_focus_score(events: List[Dict[str, Any]]) -> float:
    """
    행동 이벤트 리스트를 분석하여 0~100점 사이의 집중도(Focus Score)를 계산한다.
    - 잦은 blur 이벤트는 강력한 감점 요소 (1회당 기본 -20점, + 1초당 -2점)
    - 빠른 스크롤(찍기 의심)도 감점 요소 (duration < 300ms 일 때 -5점)
    - 체류 시간은 가점 요소
    """
    if not events:
        return 100.0  # 기본 만점

    base_score = 100.0
    penalty = 0.0
    
    for event in events:
        etype = event.get("type")
        if etype == "blur":
            duration = event.get("duration_ms")
            if duration is None:
                duration = 1000
            # 이탈 1회당 20점 기본 감점 + 1초당 2점 추가 감점
            penalty += 20.0 + (duration / 1000.0) * 2.0
            
        elif etype == "scroll":
            velocity = event.get("velocity", 0)
            # 빠른 스크롤 (예: 2000 px/s 이상) 1회당 0.5점 감점 (스크롤 이벤트가 자주 발생하므로 감점폭을 낮춤)
            if velocity > 2000:
                penalty += 0.5
                
        elif etype in ("pause", "dwell"):
            duration = event.get("duration_ms")
            if duration is None:
                duration = 1000
            # 체류 시간 1초당 0.5점 가점
            penalty -= (duration / 1000.0) * 0.5
                
    final_score = base_score - penalty
    return round(max(0.0, min(100.0, final_score)), 1)

def determine_intervention(focus_score: float) -> Tuple[bool, str, str]:
    """
    Focus Score에 따라 개입(Intervention) 여부와 수준을 결정한다.
    return: (개입 필요 여부, 개입 레벨, 넛지 메시지)
    """
    if focus_score >= 75.0:
        return False, "none", ""
    elif 50.0 <= focus_score < 75.0:
        return True, "soft", "핵심 문장을 하이라이트 해볼까요?"
    elif 30.0 <= focus_score < 50.0:
        return True, "medium", "잠시 멈춰서 다시 읽어보는 건 어떨까요?"
    else:
        return True, "hard", "방금 읽은 내용을 퀴즈로 확인해보세요!"
