from typing import List, Dict, Any, Tuple

def calculate_focus_score(events: List[Dict[str, Any]]) -> float:
    """
    행동 이벤트 리스트를 분석하여 0~100 사이의 실시간 집중도(Focus Score)를 계산합니다.
    - 화면 이탈(blur) 1회당 기본 20점 감점 + 이탈 시간에 따른 비례 감점
    - 너무 빠른 스크롤(300ms 미만 간격 혹은 duration) 시 5점 감점
    """
    if not events:
        return 100.0

    base_score = 100.0
    penalty = 0.0
    
    # 1. 이벤트에 duration_ms가 직접 명시된 경우 (단위 테스트 규격)
    has_duration = any("duration_ms" in e for e in events if e.get("type") in ("blur", "scroll"))
    
    if has_duration:
        for event in events:
            etype = event.get("type")
            if etype == "blur":
                duration = event.get("duration_ms", 1000)
                if duration is None:
                    duration = 1000
                # 이탈 1회당 20점 기본 감점 + 1초당 2점 추가 감점
                penalty += 20.0 + (duration / 1000.0) * 2.0
            elif etype == "scroll":
                duration = event.get("duration_ms", 1000)
                if duration is None:
                    duration = 1000
                # 빠른 스크롤 (300ms 미만) 1회당 5점 감점
                if duration < 300:
                    penalty += 5.0
            
    else:
        # 2. 실시간 스트리밍 모드: 타임스탬프 기반 페어링 계산
        sorted_events = sorted(events, key=lambda x: x.get("timestamp", x.get("timestamp_ms", 0)))
        last_blur_time = None
        last_scroll_time = None
        
        for event in sorted_events:
            etype = event.get("type")
            ts = event.get("timestamp", event.get("timestamp_ms", 0))
            
            if etype == "blur":
                last_blur_time = ts
                penalty += 20.0  # 이탈 1회당 20점 기본 감점
            elif etype == "focus":
                if last_blur_time is not None:
                    duration_ms = ts - last_blur_time
                    if duration_ms > 0:
                        penalty += (duration_ms / 1000.0) * 2.0
                    last_blur_time = None
            elif etype == "scroll":
                if last_scroll_time is not None:
                    interval = ts - last_scroll_time
                    # 300ms 이내에 연속 스크롤이 일어나면 빠른 스크롤로 간주
                    if interval < 300:
                        penalty += 5.0
                last_scroll_time = ts
                
        # 진행 중인 blur 처리 (아직 포커스가 돌아오지 않은 상태면 3초 경과한 것으로 임시 감점)
        if last_blur_time is not None:
            penalty += 6.0
            
    final_score = base_score - penalty
    return round(max(0.0, min(100.0, final_score)), 1)

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
