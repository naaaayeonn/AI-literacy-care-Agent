from backend.evaluation.quality_report import generate_quality_report


def test_generate_quality_report_pass():
    report = generate_quality_report(
        faithfulness=0.91,
        relevance=0.88,
    )

    assert report["faithfulness"] == 0.91
    assert report["relevance"] == 0.88
    assert report["overall_score"] == 0.9
    assert report["passed"] is True


def test_generate_quality_report_fail():
    report = generate_quality_report(
        faithfulness=0.5,
        relevance=0.6,
    )

    assert report["overall_score"] == 0.55
    assert report["passed"] is False