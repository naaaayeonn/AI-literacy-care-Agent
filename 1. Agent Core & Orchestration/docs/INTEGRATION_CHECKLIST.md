# Integration Checklist

## Current Adapter Entry Points

The orchestrator calls adapter/client functions, not stub modules directly.

- `backend/app/agents/content_reducer_client.py`
- `backend/app/agents/cognitive_care_client.py`
- `backend/app/agents/reward_client.py`
- `backend/app/agents/literacy_profile_client.py`
- `backend/app/agents/qa_eval_client.py`

## Replacement Rule

When a real team module is ready, register it as the `real` implementation inside the matching client file (set `_REAL_IMPL = <real_fn>`) while keeping the public function name stable:

- `run_content_reducer(state)`
- `run_cognitive_care(state)`
- `run_reward_agent(state)`
- `run_literacy_profile_agent(state)`
- `run_qa_eval_agent(state)`

## Stub / Real Toggle

Each client resolves its implementation via `backend/app/agents/config.py::resolve_impl`.
Selection priority (highest first):

1. Per-agent env var `LITERACY_<AGENT>_IMPL` (e.g. `LITERACY_CONTENT_REDUCER_IMPL=real`)
2. Global env var `LITERACY_AGENT_IMPL`
3. Default `stub`

Agent keys: `content_reducer`, `cognitive_care`, `reward`, `literacy_profile`.

Safety rule: if `real` is selected but no real implementation is registered
(`_REAL_IMPL = None`), the client falls back to the stub so the demo never breaks.

```bash
# Run everything with real modules once they are registered:
LITERACY_AGENT_IMPL=real python -m pytest

# Flip only one agent to real:
LITERACY_COGNITIVE_CARE_IMPL=real uvicorn backend.app.main:app --reload
```

## Contract Requirements

- Preserve `ReadingSessionState` as the shared input/output shape.
- Do not let a sub-agent exception escape the orchestrator; `graph.py` applies fallback.
- Return only JSON-serializable data in state fields.
- Keep frontend-facing `intervention`, `score_breakdown`, `reward`, and `updated_profile` stable.

## Contract Validation (M2)

`backend/app/orchestrator/contracts.py` checks that an agent's output honors its
contract (required fields present + score fields in `0..100`).

- `run_agent` (in `agents/config.py`) validates **real module output only** — stubs
  are trusted, so current stub-based behavior is unchanged.
- A real module that violates its contract raises `ContractError`. Inside the
  orchestrator flow `graph.py` catches it and applies the fallback (the demo never
  breaks). On the direct API paths (`/start`, `/events`) a `ContractError` surfaces
  as a 500 — wrap if a softer response is needed when wiring real modules.

Required output per agent:

| agent | required fields | 0..100 score fields | state location |
|---|---|---|---|
| `content_reducer` | chunks, simplified_text, terms, difficulty_score | difficulty_score | top-level |
| `cognitive_care` | focus_score, engagement_score, intervention_needed | focus_score, engagement_score | top-level |
| `reward` | xp, badge, message | — | `state["reward"]` |
| `literacy_profile` | reading_level, trend, weaknesses, recommended_next_action | — | `state["updated_profile"]` |

## Verification

```bash
python -m pytest backend/app/tests/test_agent_adapters.py
python -m pytest backend/app/tests/test_m1_demo_smoke.py
python -m pytest backend/app/tests
```
