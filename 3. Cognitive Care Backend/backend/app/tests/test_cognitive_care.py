import pytest
from backend.app.services.cognitive_care import calculate_focus_score, determine_intervention

def test_calculate_focus_score_empty():
    assert calculate_focus_score([]) == 100.0

def test_calibration_focused():
    # 집중 시나리오: pause 위주, 이탈 없음
    events = [
        {"type": "pause", "duration_ms": 5000}, 
        {"type": "scroll", "duration_ms": 1000}
    ]
    score = calculate_focus_score(events)
    assert score >= 80.0

def test_calibration_distracted_demo():
    # 데모 산만 시나리오: blur 2회(약 2.3초) + 스키밍 scroll 2회
    # 스키밍은 스크롤 속도(velocity>1.5)로 판정한다(간격<250ms 조건 제거됨).
    events = [
        {"type": "blur", "duration_ms": 1000},              # -22점
        {"type": "blur", "duration_ms": 1300},              # -22.6점
        {"type": "scroll", "duration_ms": 200, "velocity": 2.0},  # 스키밍 -8점
        {"type": "scroll", "duration_ms": 100, "velocity": 2.5},  # 스키밍 -8점
    ]
    # 총 감점 60.6점 -> 39.4점 예상
    score = calculate_focus_score(events)
    assert 35.0 <= score <= 50.0

def test_calibration_very_distracted():
    # 매우 산만: blur 4회
    events = [{"type": "blur", "duration_ms": 1000} for _ in range(4)]
    score = calculate_focus_score(events)
    assert score <= 30.0

def test_determine_intervention():
    # 75 이상
    needed, level, _ = determine_intervention(80.0)
    assert needed is False
    assert level == "none"
    
    # 50 ~ 75
    needed, level, _ = determine_intervention(60.0)
    assert needed is True
    assert level == "soft"
    
    # 30 ~ 50
    needed, level, _ = determine_intervention(40.0)
    assert needed is True
    assert level == "medium"
    
    # 30 미만
    needed, level, _ = determine_intervention(20.0)
    assert needed is True
    assert level == "hard"
