"""Fixed M1 demo scenario for the orchestrator core."""

from __future__ import annotations

from backend.app.orchestrator.graph import run_reading_session
from backend.app.orchestrator.quiz import apply_quiz_result
from backend.app.orchestrator.state import ReadingSessionState, create_initial_state

DEMO_RAW_TEXT = (
    "Artificial intelligence systems can summarize long articles, but reading "
    "support should do more than shorten text. A useful literacy care agent "
    "observes how a learner reads, notices when attention drops, offers a small "
    "intervention, checks comprehension, and updates a profile for the next "
    "session. This makes the system different from a simple chatbot summary."
)

DEMO_READING_EVENTS = [
    {"type": "scroll", "timestamp_ms": 1_000, "position": 0.18, "duration_ms": 260},
    {"type": "pause", "timestamp_ms": 3_000, "position": 0.30, "duration_ms": 1_400},
    {"type": "scroll", "timestamp_ms": 5_200, "position": 0.68, "duration_ms": 220},
    {"type": "blur", "timestamp_ms": 8_000, "duration_ms": 1_500},
    {"type": "blur", "timestamp_ms": 9_700, "duration_ms": 800},
]

DEMO_QUIZ_RESULT = {
    "quiz_id": "m1_demo_quiz",
    "correct_count": 4,
    "total_count": 5,
    "answers": [
        {"question_id": "q1", "selected": "measure_reading_behavior", "is_correct": True},
        {"question_id": "q2", "selected": "intervene_when_focus_drops", "is_correct": True},
        {"question_id": "q3", "selected": "profile_update", "is_correct": True},
        {"question_id": "q4", "selected": "only_summarize_text", "is_correct": False},
        {"question_id": "q5", "selected": "score_with_quiz_and_focus", "is_correct": True},
    ],
}

DEMO_PROFILE = {
    "reading_level": "intermediate",
    "previous_literacy_score": 64.0,
    "weaknesses": ["technical_terms"],
}


def build_m1_demo_state() -> ReadingSessionState:
    """Build the canonical M1 demo input state."""
    state = create_initial_state(
        session_id="demo_m1_session",
        user_id="demo_user",
        document_id="demo_doc_ai_literacy",
        raw_text=DEMO_RAW_TEXT,
        profile=DEMO_PROFILE,
    )
    state["reading_events"] = list(DEMO_READING_EVENTS)
    apply_quiz_result(state, DEMO_QUIZ_RESULT)
    return state


def run_m1_demo() -> ReadingSessionState:
    """Run the canonical M1 demo through the orchestrator."""
    return run_reading_session(build_m1_demo_state())
