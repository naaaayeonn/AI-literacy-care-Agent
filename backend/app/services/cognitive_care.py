from typing import List, Dict, Any, Tuple

def calculate_focus_score(events: List[Dict[str, Any]]) -> float:
    """
    행동 이벤트 리스트를 분석하여 0~100 사이의 실시간 집중도(Focus Score)를 계산합니다.
    - 화면 이탈(blur) 이벤트의 지속 시간에 따른 감점
    - 너무 잦은 빠른 스크롤에 따른 감점
    """
    if not events:
        return 100.0

    base_score = 100.0
    penalty = 0.0
    
    # 1. 이벤트에 duration_ms가 직접 명시된 경우 (기존 테스트 및 단위 케이스)
    # 2. 명시되지 않고 blur/focus가 페어링되어 timestamp 차이로 계산해야 하는 경우 (실시간 스트리밍)
    has_duration = any("duration_ms" in e for e in events if e.get("type") == "blur")
    
    if has_duration:
        for event in events:
            etype = event.get("type")
            if etype == "blur":
                duration = event.get("duration_ms", 1000)
                penalty += (duration / 1000.0) * 2.0
            elif etype == "scroll":
                # 스크롤 감점
                pass
        # 기존 스크롤 개수 감점 처리 추가
        scroll_count = sum(1 for e in events if e.get("type") == "scroll")
        if scroll_count > 5:
            penalty += (scroll_count - 5) * 1.0
            
    else:
        # 실시간 스트리밍 모드: 타임스탬프 기반 페어링 계산
        sorted_events = sorted(events, key=lambda x: x.get("timestamp", x.get("timestamp_ms", 0)))
        last_blur_time = None
        fast_scroll_count = 0
        
        for event in sorted_events:
            etype = event.get("type")
            ts = event.get("timestamp", event.get("timestamp_ms", 0))
            
            if etype == "blur":
                last_blur_time = ts
            elif etype == "focus":
                if last_blur_time is not None:
                    duration_ms = ts - last_blur_time
                    if duration_ms > 0:
                        penalty += (duration_ms / 1000.0) * 2.0
                    last_blur_time = None
            elif etype == "scroll":
                fast_scroll_count += 1
                if fast_scroll_count > 5:
                    penalty += 1.0
                    
        # 진행 중인 blur 처리 (아직 포커스가 돌아오지 않은 상태면 3초 경과한 것으로 임시 감점)
        if last_blur_time is not None:
            penalty += 6.0
            
    final_score = base_score - penalty
    if final_score < 0:
        return 0.0
    if final_score > 100:
        return 100.0
        
    return round(final_score, 1)

def determine_intervention(focus_score: float) -> Tuple[bool, str, str]:
    """
    Focus Score에 따라 개입(Intervention) 여부 및 피드백 메시지를 결정합니다.
    """
    if focus_score >= 80.0:
        return False, "none", ""
    elif 60.0 <= focus_score < 80.0:
        return True, "soft", "핵심 문장을 다시 한번 살펴볼까요? 📌"
    elif 40.0 <= focus_score < 60.0:
        return True, "medium", "잠깐! 조금 쉬었다가 다시 읽어보는 건 어때요? ☕"
    else:
        return True, "hard", "집중이 필요해요! 간단한 퀴즈로 내용을 확인해봐요! 📝"
