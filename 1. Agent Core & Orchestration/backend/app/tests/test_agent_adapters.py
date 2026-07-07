from __future__ import annotations

from backend.app.agents.cognitive_care_client import run_cognitive_care
from backend.app.agents.content_reducer_client import run_content_reducer
from backend.app.agents.literacy_profile_client import run_literacy_profile_agent
from backend.app.agents.qa_eval_client import run_qa_eval_agent
from backend.app.agents.reward_client import run_reward_agent
from backend.app.orchestrator.score import calculate_literacy_score
from backend.app.orchestrator.state import create_initial_state


def test_content_reducer_adapter_fills_contract_fields():
    state = create_initial_state(
        session_id="s1",
        user_id="u1",
        document_id="doc1",
        raw_text="Sample text",
    )

    result = run_content_reducer(state)

    assert result["chunks"]
    assert result["simplified_text"] == "Sample text"
    assert result["terms"] == []
    assert result["difficulty_score"] == 60.0


def test_cognitive_care_adapter_fills_focus_fields():
    state = create_initial_state(
        session_id="s1",
        user_id="u1",
        document_id="doc1",
        raw_text="Sample text",
    )
    state["reading_events"] = [{"type": "blur", "timestamp_ms": 1000, "duration_ms": 500}]

    result = run_cognitive_care(state)

    assert result["focus_score"] == 58.0
    assert result["engagement_score"] == 58.0
    assert result["intervention_needed"] is True


def test_reward_and_profile_adapters_fill_optional_outputs():
    state = create_initial_state(
        session_id="s1",
        user_id="u1",
        document_id="doc1",
        raw_text="Sample text",
        profile={"previous_literacy_score": 50},
    )
    state["focus_score"] = 70.0
    state["difficulty_score"] = 60.0
    calculate_literacy_score(state)

    run_reward_agent(state)
    run_literacy_profile_agent(state)

    assert state["reward"]["badge"] == "steady_reader"
    assert state["updated_profile"]["trend"] == "improving"


def test_qa_eval_adapter_is_noop_until_real_module_is_connected():
    state = create_initial_state(
        session_id="s1",
        user_id="u1",
        document_id="doc1",
        raw_text="Sample text",
    )

    assert run_qa_eval_agent(state) is state
