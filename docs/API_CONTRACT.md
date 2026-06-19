# API Contract (초안 v0 · 6/20)

> 이 문서는 **1번(오케스트레이션)이 팀원에게 주는 입출력 계약**이다.
> 2~6번 팀원은 이 JSON 형태만 보고 자기 모듈을 병렬로 구현할 수 있어야 한다.
> 모든 점수는 **0~100 정규화**, 스크롤 position은 **0.0~1.0**, timestamp는 **세션 시작 기준 ms**.
>
> 단일 진실 소스(SSOT)는 `backend/app/orchestrator/state.py`의 `ReadingSessionState`.
> 계약 변경은 **M3(7/10) 이후 금지** — 그 전까지 이 문서로 협의한다.

---

## 0. 연결 개요

```
프론트(4번) ──events/quiz──▶ API(reading_session.py) ──▶ Orchestrator(graph.py)
                                                              │  Shared State
        ┌─────────────────────────────────────────────────────┤
        ▼              ▼              ▼            ▼            ▼
   ContentReducer  CognitiveCare  ScoreEngine   Reward    LiteracyProfile
      (2번)           (3번)         (1번)        (4번)        (5번)
                                                              │
                                                          QA/Eval(6번) ◀ trace
```

각 에이전트는 `ReadingSessionState`(dict)를 받아 **자기 출력 필드만 채워** 돌려준다.

---

## 1. Content Reducer (2번)

**입력**
```json
{
  "raw_text": "원문 텍스트",
  "profile": { "reading_level": "intermediate", "weaknesses": ["long_sentence", "technical_terms"] }
}
```

**출력** (state에 merge)
```json
{
  "chunks": [
    { "chunk_id": "chunk_01", "text": "원문 문단", "summary": "핵심 요약", "difficulty": 72 }
  ],
  "simplified_text": "쉬운 설명 버전",
  "terms": [
    { "term": "인지부하", "definition": "정보를 이해할 때 처리해야 하는 부담", "source": "표준국어대사전" }
  ],
  "difficulty_score": 72.0
}
```
- `chunk_id`는 프론트 하이라이트·행동 로그 연결 키 → **안정적으로 생성** 필수.
- `terms[].source`는 QA Faithfulness 평가에 필요 → 비우지 말 것.

## 2. Cognitive Care (3번)

**입력**
```json
{ "session_id": "s1", "reading_events": [ { "type": "scroll", "timestamp_ms": 1000, "position": 0.35 } ], "chunks": [] }
```
**출력**
```json
{
  "focus_score": 63.0,
  "engagement_score": 67.5,
  "intervention_needed": true,
  "intervention_level": "soft",
  "evidence": { "fast_scroll_count": 3, "blur_count": 1, "low_dwell_chunks": ["chunk_02"] }
}
```
- `intervention_level` ∈ `none | soft | medium | hard`.
- 최종 개입 결정/메시지는 **1번 routing.py**가 확정 (3번은 신호·근거 제공).

## 3. Reward (4번)

**입력**
```json
{ "literacy_score": 76.4, "focus_score": 71.0, "quiz_result": { "correct_count": 4, "total_count": 5 } }
```
**출력**
```json
{ "reward": { "xp": 120, "badge": "집중 리더", "message": "집중도와 이해도가 안정적으로 유지되었습니다." } }
```

## 4. Literacy Profile (5번)

**입력**
```json
{ "user_id": "u1", "document_id": "doc1", "literacy_score": 76.4, "score_breakdown": {}, "reading_events": [], "quiz_result": {} }
```
**출력**
```json
{
  "updated_profile": {
    "reading_level": "intermediate", "trend": "improving",
    "weaknesses": ["technical_terms"], "recommended_next_action": "전문용어 툴팁을 켠 채 다음 글 읽기"
  }
}
```
- `trend` ∈ `improving | stable | declining`.

## 5. QA / Evaluation (6번)

**입력**
```json
{ "trace": [], "generated_outputs": { "simplified_text": "...", "quiz": [], "terms": [] } }
```
**출력**
```json
{ "qa_result": { "passed": true, "faithfulness": 0.91, "answer_relevance": 0.87, "warnings": [] } }
```
- QA는 **런타임 흐름을 막지 않는다** (개발/검증 층). 결과는 trace/admin으로 노출.

---

## 6. 프론트(4번)가 받는 최종 응답

**세션 시작 응답**
```json
{ "session_id": "s1", "chunks": [], "simplified_text": "...", "terms": [], "difficulty_score": 72.0 }
```

**개입(intervention) 명령** — 프론트는 이것만 보고 UI를 그린다.
```json
{ "intervention": { "level": "medium", "type": "nudge", "message": "잠시 멈춰서 핵심 문장을 다시 확인해보세요.", "target_chunk_id": "chunk_03" } }
```

**세션 최종 결과** — 데모 핵심 화면(성장 그래프)용.
```json
{
  "session_id": "s1",
  "literacy_score": 76.4,
  "score_breakdown": { "comprehension_score": 82.0, "engagement_score": 71.0, "difficulty_score": 68.0, "cross_validation_penalty": 4.5 },
  "reward": { "xp": 120, "badge": "집중 리더", "message": "..." },
  "updated_profile": { "trend": "improving", "weaknesses": ["technical_terms"] }
}
```

---

## 7. 행동 이벤트 schema (3번·4번 합의)

```json
{
  "session_id": "s1",
  "events": [
    { "type": "scroll", "timestamp_ms": 12000, "position": 0.42, "metadata": { "viewport_height": 900 } },
    { "type": "blur",   "timestamp_ms": 18000, "duration_ms": 5000 }
  ]
}
```
- `type` ∈ `scroll | pause | blur | focus | click`.

---

## 변경 이력
- v0 (6/20): ARCHITECTURE.md §4 계약을 문서로 추출. 필드명은 state.py와 1:1.
- TODO(6/21): 필수/선택 필드 표, 에러 응답 형식, intervention.type 목록 확정.
