from backend.evaluation.evaluation_runner import evaluate_sample


def run_evaluation_pipeline():
    """
    QA Evaluation Pipeline

    현재는 Dummy Runner를 사용한다.
    이후 Ragas가 연결되면 evaluate_sample()을
    실제 평가 함수로 교체한다.
    """

    report = evaluate_sample()

    return report