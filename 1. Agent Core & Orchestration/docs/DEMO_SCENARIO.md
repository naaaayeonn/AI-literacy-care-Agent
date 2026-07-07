# M1 Demo Scenario

Implementation: `backend/app/demo/m1_scenario.py`

## Purpose

This fixed scenario proves the core loop can run repeatedly with the same input:

```text
raw_text
-> content chunks
-> reading behavior analysis
-> intervention command
-> quiz-based score
-> reward
-> updated profile
-> self-correction review (quality warnings)
```

## Canonical Smoke Command

```bash
python -m pytest backend/app/tests/test_m1_demo_smoke.py
```

## Expected Outcome

- `focus_score`: `39.0`
- `intervention.level`: `medium`
- `intervention.type`: `nudge`
- `literacy_score`: `55.6`
- `reward.badge`: `needs_support`
- `updated_profile.trend`: `declining`
- `warnings`: `[]` (clean run, no quality issues detected)
- all 7 orchestrator trace entries are `success`

This scenario is intentionally deterministic so it can be reused during M1 integration.
