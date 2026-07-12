from __future__ import annotations

import math

from backend.app.orchestrator.score import (
    abnormal_reading_penalty,
    calculate_literacy_score,
    compute_score,
)
from backend.app.orchestrator.state import create_initial_state


def test_compute_score_is_deterministic_and_explainable():
    score, breakdown = compute_score(
        quiz_correct_rate=0.8,
        focus_score=70,
        difficulty_score=60,
        abnormal_reading_penalty=2.5,
    )

    assert score == 71.0
    assert breakdown["comprehension_score"] == 80.0
    assert breakdown["engagement_score"] == 70.0
    assert breakdown["difficulty_score"] == 60.0
    assert breakdown["cross_validation_penalty"] == 2.5
    assert breakdown["penalty_breakdown"] == {}
    assert breakdown["reason"]


def test_compute_score_clamps_invalid_values():
    score, breakdown = compute_score(
        quiz_correct_rate=math.nan,
        focus_score=150,
        difficulty_score=-10,
        abnormal_reading_penalty=200,
    )

    assert score == 0.0
    assert breakdown["comprehension_score"] == 0.0
    assert breakdown["engagement_score"] == 100.0
    assert breakdown["difficulty_score"] == 0.0
    assert breakdown["cross_validation_penalty"] == 100.0


def test_abnormal_reading_penalty_reports_evidence():
    penalty, evidence = abnormal_reading_penalty(
        [
            {"type": "blur", "timestamp_ms": 1000, "duration_ms": 1000},
            {"type": "scroll", "timestamp_ms": 2000, "duration_ms": 200},
            {"type": "pause", "timestamp_ms": 3000, "duration_ms": 0},
            {"type": "pause", "timestamp_ms": 4000, "duration_ms": 30_000},
        ]
    )

    assert penalty == 9.0
    assert evidence == {
        "blur_count": 1,
        "fast_scroll_count": 1,
        "zero_dwell_count": 1,
        "long_idle_count": 1,
        "max_penalty": 20.0,
        "applied_penalty": 9.0,
    }


def test_calculate_literacy_score_uses_quiz_result():
    state = create_initial_state(
        session_id="s1",
        user_id="u1",
        document_id="doc1",
        raw_text="sample",
    )
    state["quiz_result"] = {
        "quiz_id": "q1",
        "correct_count": 4,
        "total_count": 5,
        "answers": [],
    }
    state["focus_score"] = 70.0
    state["difficulty_score"] = 60.0

    result = calculate_literacy_score(state)

    assert result["literacy_score"] == 73.5
    assert result["comprehension_score"] == 80.0
    assert result["score_breakdown"]["engagement_score"] == 70.0
    assert result["score_breakdown"]["penalty_breakdown"]["applied_penalty"] == 0.0


def test_calculate_literacy_score_normalizes_invalid_quiz_result():
    state = create_initial_state(
        session_id="s1",
        user_id="u1",
        document_id="doc1",
        raw_text="sample",
    )
    state["quiz_result"] = {
        "quiz_id": "q1",
        "correct_count": 10,
        "total_count": 5,
        "answers": [],
    }
    state["focus_score"] = 70.0
    state["difficulty_score"] = 60.0

    result = calculate_literacy_score(state)

    assert result["literacy_score"] == 83.5
    assert result["comprehension_score"] == 100.0


def test_calculate_literacy_score_uses_completion_proxy_when_no_quiz():
    # 퀴즈(quiz_answers/quiz_result) 없음 → 이해도는 상수 70이 아니라 완독률 프록시(추정).
    # 이벤트도 없으면 완독률 0 → comprehension 0, measured=False.
    state = create_initial_state(
        session_id="s1",
        user_id="u1",
        document_id="doc1",
        raw_text="sample",
    )

    result = calculate_literacy_score(state)

    # 0*0.5 + 60*0.35 + 50*0.15 - 0 = 28.5
    assert result["literacy_score"] == 28.5
    assert result["comprehension_score"] == 0.0
    assert result["score_breakdown"]["comprehension_measured"] is False
    assert result["score_breakdown"]["comprehension_confidence"] == "low"
    assert result["score_breakdown"]["quiz_count"] == 0
    assert result["score_breakdown"]["engagement_score"] == 60.0
    assert result["score_breakdown"]["difficulty_score"] == 50.0


def test_calculate_literacy_score_completion_proxy_uses_max_position():
    # 퀴즈 없지만 본문 80%까지 읽음 → 이해도 프록시 = 0.8 → comprehension 80 (measured=False)
    state = create_initial_state(
        session_id="s1", user_id="u1", document_id="doc1", raw_text="sample",
    )
    state["reading_events"] = [
        {"type": "scroll", "timestamp_ms": 1000, "position": 0.4},
        {"type": "scroll", "timestamp_ms": 2000, "position": 0.8},
    ]
    state["focus_score"] = 60.0
    state["difficulty_score"] = 50.0

    result = calculate_literacy_score(state)

    assert result["comprehension_score"] == 80.0
    assert result["score_breakdown"]["comprehension_measured"] is False


def test_calculate_literacy_score_uses_quiz_answers_when_present():
    # 신규 O/X 흐름: quiz_answers 문항별 정답 → 실측(measured=True)
    state = create_initial_state(
        session_id="s1", user_id="u1", document_id="doc1", raw_text="sample",
    )
    state["quiz_answers"] = [
        {"quizId": "q1", "correct": True},
        {"quizId": "q2", "correct": True},
        {"quizId": "q3", "correct": False},
    ]
    state["focus_score"] = 70.0
    state["difficulty_score"] = 60.0

    result = calculate_literacy_score(state)

    # 2/3 = 0.6667 → comprehension 66.7
    assert result["comprehension_score"] == 66.7
    assert result["score_breakdown"]["comprehension_measured"] is True
    assert result["score_breakdown"]["comprehension_confidence"] == "high"
    assert result["score_breakdown"]["quiz_count"] == 3


def test_abnormal_reading_penalty_is_capped_at_20():
    events = [
        {"type": "blur", "timestamp_ms": i * 100, "duration_ms": 1000} for i in range(20)
    ]

    penalty, evidence = abnormal_reading_penalty(events)

    # 20 blurs * 2.0 = 40 → 상한 20.0으로 캡
    assert penalty == 20.0
    assert evidence["blur_count"] == 20
    assert evidence["applied_penalty"] == 20.0


def test_abnormal_reading_penalty_empty_events_is_zero():
    penalty, evidence = abnormal_reading_penalty([])

    assert penalty == 0.0
    assert evidence["applied_penalty"] == 0.0
