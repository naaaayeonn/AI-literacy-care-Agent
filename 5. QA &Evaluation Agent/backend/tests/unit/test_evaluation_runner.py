from backend.evaluation.evaluation_runner import evaluate_sample


def test_evaluation_runner():
    report = evaluate_sample()

    assert report["faithfulness"] == 0.92
    assert report["relevance"] == 0.87
    assert report["passed"] is True