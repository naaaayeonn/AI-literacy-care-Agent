from backend.evaluation.metrics import (
    calculate_faithfulness_score,
    calculate_relevance_score,
    calculate_average,
    is_passed,
)


def run_evaluation(sample: dict) -> dict:
    """
    Golden Dataset 한 개를 평가한다.
    """

    raw_text = sample.get("raw_text", "")
    expected_quiz = sample.get("expected_quiz", "")
    expected_answer = sample.get("expected_answer", "")

    faithfulness = calculate_faithfulness_score(
        expected=raw_text,
        actual=expected_answer,
    )

    relevance = calculate_relevance_score(
        question=expected_quiz,
        answer=expected_answer,
    )

    average_score = calculate_average([faithfulness, relevance])

    return {
        "faithfulness": faithfulness,
        "relevance": relevance,
        "average_score": average_score,
        "passed": is_passed(average_score, threshold=0.2),
    }