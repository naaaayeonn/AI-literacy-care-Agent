def calculate_literacy_score(
    comprehension_score,
    engagement_score,
    difficulty_score
):
    """
    Literacy Score 계산

    Parameters
    ----------
    comprehension_score : float
    engagement_score : float
    difficulty_score : float

    Returns
    -------
    float
    """

    score = (
        comprehension_score * 0.5
        + engagement_score * 0.3
        + difficulty_score * 0.2
    )

    return round(score, 2)