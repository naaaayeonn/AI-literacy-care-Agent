def generate_quality_report(faithfulness: float, relevance: float) -> dict:
    overall_score = round((faithfulness + relevance) / 2, 2)

    return {
        "faithfulness": faithfulness,
        "relevance": relevance,
        "overall_score": overall_score,
        "passed": faithfulness >= 0.8 and relevance >= 0.8,
    }