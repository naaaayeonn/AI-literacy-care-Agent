from __future__ import annotations

from backend.app.orchestrator.quiz import (
    apply_quiz_result,
    normalize_quiz_result,
    quiz_correct_rate,
)
from backend.app.orchestrator.state import create_initial_state


def test_normalize_quiz_result_clamps_counts_and_answers():
    result = normalize_quiz_result(
        {
            "quiz_id": 123,
            "correct_count": 9,
            "total_count": 5,
            "answers": {"not": "a-list"},
        }
    )

    assert result == {
        "quiz_id": "123",
        "correct_count": 5,
        "total_count": 5,
        "answers": [],
    }


def test_normalize_quiz_result_handles_missing_payload():
    result = normalize_quiz_result(None)

    assert result == {
        "quiz_id": "quiz_unknown",
        "correct_count": 0,
        "total_count": 0,
        "answers": [],
    }


def test_apply_quiz_result_updates_state():
    state = create_initial_state(
        session_id="s1",
        user_id="u1",
        document_id="doc1",
        raw_text="sample",
    )

    result = apply_quiz_result(
        state,
        {
            "quiz_id": "q1",
            "correct_count": "2",
            "total_count": "4",
            "answers": [{"id": "a"}],
        },
    )

    assert result["quiz_result"] == {
        "quiz_id": "q1",
        "correct_count": 2,
        "total_count": 4,
        "answers": [{"id": "a"}],
    }


def test_quiz_correct_rate_uses_default_when_quiz_is_missing_or_empty():
    assert quiz_correct_rate(None) == 0.7
    assert quiz_correct_rate({"correct_count": 0, "total_count": 0}) == 0.7
    assert quiz_correct_rate({"correct_count": 3, "total_count": 5}) == 0.6
