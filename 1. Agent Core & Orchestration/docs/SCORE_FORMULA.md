# Literacy Score Formula

Implementation: `backend/app/orchestrator/score.py`

## Formula

```text
comprehension_score = quiz_correct_rate * 100
engagement_score    = focus_score
difficulty_score    = normalized document difficulty

literacy_score =
  comprehension_score * 0.50
  + engagement_score  * 0.35
  + difficulty_score  * 0.15
  - cross_validation_penalty
```

The final score is clamped to `0..100` and rounded to one decimal place.

## Missing / Invalid Inputs

The score function is defensive so a session always produces an explainable number:

- **No quiz result** (or `total_count <= 0`): `quiz_correct_rate` falls back to `0.7`
  (a neutral assumption), so `comprehension_score = 70`. Self-Correction records a
  `quiz_missing` (info) warning so this assumption is visible.
- **Missing `focus_score`**: defaults to `60`.
- **Missing `difficulty_score`**: defaults to `50`.
- **NaN / non-numeric**: replaced with the defaults above; the score never becomes `NaN`.

## Cross Validation Penalty

Reading behavior can reduce the final score when it conflicts with quiz or focus signals.

```text
blur_count        * 2.0
fast_scroll_count * 1.5
zero_dwell_count  * 2.5
long_idle_count   * 3.0
```

The applied penalty is capped at `20.0`.

## Score Breakdown

`score_breakdown` returns:

- `comprehension_score`
- `engagement_score`
- `difficulty_score`
- `cross_validation_penalty`
- `penalty_breakdown`
- `reason`

This makes the score reproducible and explainable without asking an LLM to grade the user.
