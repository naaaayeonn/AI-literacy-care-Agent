# Shared State 필드 설명

`backend/app/orchestrator/state.py`의 `ReadingSessionState`를 사람이 읽기 쉽게
정리한 설명서다. **단일 진실 소스(SSOT)는 코드(state.py)** 이며, 이 문서는
"누가 읽고 / 누가 쓰고 / 언제 채워지는지"를 빠르게 파악하기 위한 참고용이다.

> 점수는 모두 **0~100 정규화**, 스크롤 `position`은 **0.0~1.0**,
> `timestamp_ms`는 **세션 시작 기준 ms**.

## 필드 표

| 필드 | 타입 | 쓰는 주체 | 읽는 주체 | 채워지는 시점 |
|---|---|---|---|---|
| `session_id` | str | API | 전체 | 세션 시작 |
| `user_id` | str | API | profile(5번) | 세션 시작 |
| `document_id` | str | API | profile(5번) | 세션 시작 |
| `raw_text` | str | API | content_reducer(2번) | 세션 시작 |
| `profile` | dict | API | content_reducer(2번), profile(5번) | 세션 시작 (이전 누적, 없으면 `{}`) |
| `chunks` | list[dict] | content_reducer(2번) | routing(1번), 프론트(4번) | content_reducer 단계 |
| `simplified_text` | str | content_reducer(2번) | 프론트(4번), QA(6번) | content_reducer 단계 |
| `terms` | list[dict] | content_reducer(2번) | 프론트(4번), QA(6번) | content_reducer 단계 |
| `difficulty_score` | float | content_reducer(2번) | score_engine(1번) | content_reducer 단계 |
| `reading_events` | list[ReadingEvent] | API(프론트 4번) | cognitive_care(3번), score_engine(1번) | events 수신 시 누적 |
| `focus_score` | float | cognitive_care(3번) | routing(1번), score_engine(1번) | cognitive_care 단계 |
| `engagement_score` | float | cognitive_care(3번) | reward(4번) | cognitive_care 단계 |
| `intervention_needed` | bool | cognitive_care(3번)/routing(1번) | 프론트(4번) | cognitive_care/routing 단계 |
| `intervention_level` | `none\|soft\|medium\|hard` | routing(1번) | 프론트(4번) | routing 단계 |
| `intervention_message` | str | routing(1번) | 프론트(4번) | routing 단계 |
| `intervention` | InterventionCommand | routing(1번) | 프론트(4번) | routing 단계 |
| `quiz_result` | QuizResult | API(프론트 4번) | score_engine(1번) | 퀴즈 제출 시 |
| `comprehension_score` | float | score_engine(1번) | profile(5번) | score 단계 |
| `literacy_score` | float | score_engine(1번) | reward(4번), profile(5번), 프론트 | score 단계 |
| `score_breakdown` | ScoreBreakdown | score_engine(1번) | 프론트(4번), QA(6번) | score 단계 |
| `reward` | dict | reward(4번) | 프론트(4번) | reward 단계 |
| `updated_profile` | dict | profile(5번) | 프론트(4번), 다음 세션 | profile 단계 |
| `trace` | list[TraceEntry] | orchestrator(1번) | QA(6번), 발표 | 매 단계 |
| `errors` | list[dict] | orchestrator(1번) | QA(6번), 디버깅 | 단계 실패 시 |
| `warnings` | list[QualityWarning] | self_correction(1번) | QA(6번), 발표 | self_correction 단계 |

## 보조 타입

- **`ReadingEvent`**: `{type, timestamp_ms, position?, duration_ms?, metadata?}`
  - `type` ∈ `scroll | pause | blur | focus | click`
- **`QuizResult`**: `{quiz_id, correct_count, total_count, answers}`
- **`ScoreBreakdown`**: `{comprehension_score, engagement_score, difficulty_score, cross_validation_penalty, penalty_breakdown?, reason?}`
- **`InterventionCommand`**: `{level, type, message, target_chunk_id?, reason?}`
  - `type` ∈ `none | highlight | nudge | quiz`
- **`TraceEntry`**: `{step, status, latency_ms?, detail?}`
  - `status` ∈ `success | fallback | error`
- **`QualityWarning`**: `{code, severity, message, field?, detail?}`
  - `severity` ∈ `info | warning | critical` (자세한 code 목록은 `self_correction.py`)

## 실행 순서로 본 필드 채워짐

```text
create_state   : session_id, user_id, document_id, raw_text, profile, (빈) reading_events/trace/errors/warnings
content_reducer: chunks, simplified_text, terms, difficulty_score
cognitive_care : focus_score, engagement_score, intervention_needed
routing        : intervention, intervention_level, intervention_message
score_engine   : comprehension_score, literacy_score, score_breakdown
reward         : reward
profile_update : updated_profile
self_correction: warnings
```
