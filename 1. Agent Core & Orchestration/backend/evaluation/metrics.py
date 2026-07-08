from typing import List


def calculate_average(scores: List[float]) -> float:
    """
    여러 평가 점수의 평균을 계산한다.
    """
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 4)


def calculate_faithfulness_score(expected: str, actual: str) -> float:
    """
    기대 문장과 실제 생성 문장의 단어 겹침 비율로 충실도를 계산한다.
    무료 평가용 간단 휴리스틱이다.
    """
    if not expected or not actual:
        return 0.0

    expected_words = set(expected.lower().split())
    actual_words = set(actual.lower().split())

    if not expected_words:
        return 0.0

    matched_words = expected_words.intersection(actual_words)
    score = len(matched_words) / len(expected_words)

    return round(score, 4)


def calculate_relevance_score(question: str, answer: str) -> float:
    """
    질문과 답변의 단어 겹침 비율로 관련성을 계산한다.
    """
    if not question or not answer:
        return 0.0

    question_words = set(question.lower().split())
    answer_words = set(answer.lower().split())

    if not question_words:
        return 0.0

    matched_words = question_words.intersection(answer_words)
    score = len(matched_words) / len(question_words)

    return round(score, 4)


def calculate_accuracy(correct_count: int, total_count: int) -> float:
    """
    퀴즈 정답률을 계산한다.
    """
    if total_count == 0:
        return 0.0

    return round(correct_count / total_count, 4)


def is_passed(score: float, threshold: float = 0.8) -> bool:
    """
    기준 점수 이상이면 통과로 판단한다.
    """
    return score >= threshold

def calculate_literacy_score(
    comprehension_score: float,
    engagement_score: float,
    difficulty_score: float
) -> float:
    """
    이해도, 집중도, 난이도를 가중합하여 Literacy Score를 계산한다.
    """
    score = (
        comprehension_score * 0.5
        + engagement_score * 0.3
        + difficulty_score * 0.2
    ) #Literacy Score = 이해도 50% + 집중도 30% + 난이도 20%

    return round(score, 1)