from backend.evaluation.evaluation_pipeline import (
    run_evaluation_pipeline
)


def test_evaluation_pipeline():

    report = run_evaluation_pipeline()

    assert report["passed"] is True