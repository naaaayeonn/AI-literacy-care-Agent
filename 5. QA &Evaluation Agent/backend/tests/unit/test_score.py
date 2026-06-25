from backend.evaluation.metrics import calculate_literacy_score


def test_calculate_score():
    score = calculate_literacy_score(
        comprehension_score=90,
        engagement_score=80,
        difficulty_score=70,
    )

    assert score == 83.0

def test_zero_score():
    score = calculate_literacy_score(
        comprehension_score=0,
        engagement_score=0,
        difficulty_score=0,
    )

    assert score == 0

def test_negative_score():
    score = calculate_literacy_score(
        comprehension_score=-10,
        engagement_score=20,
        difficulty_score=30,
    )

    assert score == 7.0