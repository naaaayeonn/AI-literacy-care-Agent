import pytest
from app.services.cognitive_care import calculate_focus_score, determine_intervention

def test_calculate_focus_score_empty():
    assert calculate_focus_score([]) == 100.0

def test_calculate_focus_score_with_blurs():
    events = [
        {"type": "blur", "duration_ms": 2000}, # 4점 감점
        {"type": "blur", "duration_ms": 5000}  # 10점 감점
    ]
    score = calculate_focus_score(events)
    assert score == 86.0

def test_determine_intervention():
    # 80 이상
    needed, level, _ = determine_intervention(85.0)
    assert needed is False
    assert level == "none"
    
    # 60 ~ 80
    needed, level, _ = determine_intervention(70.0)
    assert needed is True
    assert level == "soft"
    
    # 40 ~ 60
    needed, level, _ = determine_intervention(50.0)
    assert needed is True
    assert level == "medium"
    
    # 40 미만
    needed, level, _ = determine_intervention(30.0)
    assert needed is True
    assert level == "hard"
