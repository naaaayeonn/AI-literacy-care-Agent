from backend.evaluation.quality_report import (
    generate_quality_report
)


def evaluate_sample():

    # (임시) Ragas 점수라고 가정
    faithfulness = 0.92
    relevance = 0.87

    report = generate_quality_report(
        faithfulness=faithfulness,
        relevance=relevance,
    )

    return report