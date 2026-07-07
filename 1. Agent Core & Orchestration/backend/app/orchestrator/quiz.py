"""Quiz result normalization and state integration."""

from __future__ import annotations

from .state import QuizResult, ReadingSessionState


DEFAULT_QUIZ_ID = "quiz_unknown"


def apply_quiz_result(state: ReadingSessionState, payload: dict) -> ReadingSessionState:
    """Normalize a quiz payload and attach it to shared state."""
    state["quiz_result"] = normalize_quiz_result(payload)
    return state


def normalize_quiz_result(payload: dict | None) -> QuizResult:
    """Return a safe QuizResult shape from frontend/API input."""
    payload = payload or {}
    total_count = _non_negative_int(payload.get("total_count", 0))
    correct_count = _non_negative_int(payload.get("correct_count", 0))
    correct_count = min(correct_count, total_count)

    answers = payload.get("answers", [])
    if not isinstance(answers, list):
        answers = []

    quiz_id = payload.get("quiz_id") or DEFAULT_QUIZ_ID

    return QuizResult(
        quiz_id=str(quiz_id),
        correct_count=correct_count,
        total_count=total_count,
        answers=answers,
    )


def quiz_correct_rate(quiz_result: QuizResult | dict | None, *, default: float = 0.7) -> float:
    """Calculate correct_count / total_count with a default for missing quiz data."""
    if not quiz_result:
        return default

    normalized = normalize_quiz_result(dict(quiz_result))
    if normalized["total_count"] <= 0:
        return default

    return normalized["correct_count"] / normalized["total_count"]


def _non_negative_int(value: object) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, number)
