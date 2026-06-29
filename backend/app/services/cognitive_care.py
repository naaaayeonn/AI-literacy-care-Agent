from typing import List, Dict, Any, Tuple

def calculate_focus_score(events: List[Dict[str, Any]]) -> float:
    """
    행동 이벤트 리스트를 분석하여 0~100점 사이의 집중도(Focus Score)를 계산한다.
    - 잦은 blur 이벤트는 큰 감점 요소
    - 빠른 스크롤(찍기 의심)도 감점 요소
    - 체류 시간은 가점 요소
    """
    if not events:
        return 100.0  # 기본 만점

    base_score = 100.0
    penalty = 0.0
    
    blur_count = 0
    total_blur_duration = 0
    fast_scroll_count = 0
    
    # 간단한 휴리스틱 분석 로직
    for event in events:
        etype = event.get("type")
        if etype == "blur":
            blur_count += 1
            duration = event.get("duration_ms", 1000)
            total_blur_duration += duration
            penalty += (duration / 1000) * 2.0  # 1초 이탈 당 2점 감점
            
        elif etype == "scroll":
            # 스크롤 속도 로직 (더미 로직: 연속 발생 시 감점)
            fast_scroll_count += 1
            if fast_scroll_count > 5:
                penalty += 1.0 # 잦은 스크롤마다 1점 감점
                
    # 점수 제한
    final_score = base_score - penalty
    if final_score < 0:
        return 0.0
    if final_score > 100:
        return 100.0
        
    return round(final_score, 1)

def determine_intervention(focus_score: float) -> Tuple[bool, str, str]:
    """
    Focus Score에 따라 개입(Intervention) 여부와 수준을 결정한다.
    return: (개입 필요 여부, 개입 레벨, 넛지 메시지)
    """
    if focus_score >= 80.0:
        return False, "none", ""
    elif 60.0 <= focus_score < 80.0:
        return True, "soft", "핵심 문장을 하이라이트 해볼까요?"
    elif 40.0 <= focus_score < 60.0:
        return True, "medium", "잠시 멈춰서 다시 읽어보는 건 어떨까요?"
    else:
        return True, "hard", "방금 읽은 내용을 퀴즈로 확인해보세요!"
