from backend.evaluation.evaluation_runner import evaluate_sample


def test_evaluation_runner():

    report = evaluate_sample()

    assert "faithfulness" in report
    assert "relevance" in report
    assert "overall_score" in report
    assert "passed" in report

    assert 0.0 <= report["faithfulness"] <= 1.0
    assert 0.0 <= report["relevance"] <= 1.0
    assert 0.0 <= report["overall_score"] <= 1.0