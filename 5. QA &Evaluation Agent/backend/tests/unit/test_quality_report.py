from backend.evaluation.quality_report import generate_quality_report


def test_generate_quality_report_pass():

    report = generate_quality_report(
        faithfulness=0.91,
        relevance=0.88,
        threshold=0.30,
    )

    assert report["passed"] is True

def test_generate_quality_report_fail():

    report = generate_quality_report(
        faithfulness=0.10,
        relevance=0.20,
        threshold=0.30,
    )

    assert report["passed"] is False