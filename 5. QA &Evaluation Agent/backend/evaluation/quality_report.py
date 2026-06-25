def generate_quality_report(
    faithfulness: float,
    relevance: float
):
    """
    품질 평가 결과 생성
    """

    overall_score = round(
        (faithfulness + relevance) / 2,
        2
    )

    passed = overall_score >= 0.8

    report = {
        "faithfulness": faithfulness,
        "relevance": relevance,
        "overall_score": overall_score,
        "passed": passed
    }

    return report

def generate_quality_report(faithfulness: float, relevance: float):
    overall_score = round((faithfulness + relevance) / 2, 2)
    passed = overall_score >= 0.8

    return {
        "faithfulness": faithfulness,
        "relevance": relevance,
        "overall_score": overall_score,
        "passed": passed,
    }