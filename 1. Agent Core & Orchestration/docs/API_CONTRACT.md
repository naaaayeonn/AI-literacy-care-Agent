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
{ "user_id": "u1", "document_id": "doc1", "literacy_score": 76.4, "score_breakdown": {}, "reading_events": [], "quiz_result": {},
  "profile": { "previous_literacy_score": 64.0, "score_history": [] } }
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
- `trend` ∈ `improving | stable | declining | baseline`(히스토리 없음 = cold start).
- 현재(v0)는 `profile.previous_literacy_score` 단일 값으로 비교.
- **시계열 확장(제안, 추가 필드만)** — 상세는 `docs/TIMESERIES_DESIGN.md`:
  - 입력: `profile.score_history`(세션별 점수 누적, 없으면 `[]`).
  - 출력 추가: `previous_scores`(그래프용 list[float]), `recommended_difficulty`(다음 글 난이도 추천).
  - 확정은 M2(7/5~), 동결은 M3(7/10). 기존 `trend` 동작은 그대로 유지.

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

**세션 최종 결과** — 데모 핵심 화면(성장 그래프)용. (`POST /finish`, `GET /result`)
```json
{
  "session_id": "s1",
  "chunks": [],
  "intervention": { "level": "medium", "type": "nudge", "message": "...", "target_chunk_id": "chunk_03" },
  "literacy_score": 76.4,
  "score_breakdown": { "comprehension_score": 82.0, "engagement_score": 71.0, "difficulty_score": 68.0, "cross_validation_penalty": 4.5, "penalty_breakdown": {}, "reason": "..." },
  "reward": { "xp": 120, "badge": "집중 리더", "message": "..." },
  "updated_profile": { "trend": "improving", "weaknesses": ["technical_terms"] },
  "warnings": [ { "code": "quiz_missing", "severity": "info", "message": "..." } ],
  "trace": [ { "step": "score_engine", "status": "success", "latency_ms": 1 } ],
  "errors": []
}
```
- `warnings`는 **Self-Correction 검토 결과**(비정상 점수·빈 출력·fallback 감지). 사용자 흐름은 막지 않으며 QA/관리자/발표 근거로 사용. 정상 세션이면 `[]`.
- `severity` ∈ `info | warning | critical`. code 목록은 `backend/app/orchestrator/self_correction.py`.

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

## 8. 에러 / 모듈 전환

- 입력 검증 실패: `422` (`{"detail": "raw_text is required"}` 등).
- 없는 세션: `404` (`{"detail": "session not found"}`).
- 서브 에이전트 실패는 **HTTP 에러로 새지 않는다** — orchestrator가 fallback을 적용하고 `trace.status="fallback"` + `errors[]`로 기록한다.
- stub ↔ real 모듈 전환은 환경변수로 제어한다. 자세한 내용은 `docs/INTEGRATION_CHECKLIST.md`.

## 9. 확장(크롬) 인입 계약 — 외부 입력원 어댑터

> 확장은 **새 입력원**이다. 웹앱은 사전 업로드된 `articleId`로 시작하지만, 확장은
> **페이지에서 추출한 본문 `content[]`**를 넘긴다. 이 절은 확장의 **camelCase + REST**
> 경계를 내부 **snake_case state**로 잇는 어댑터 계약이다.
> 전송방식은 **REST(event-driven)** — `EXTENSION_INTEGRATION_FIXES.md`의 **ADR-001** 확정.
> 정본: `EXTENSION_DESIGN.md`(§9 pdf.js, §12 ADR) · `EXTENSION_INTEGRATION_FIXES.md`.
>
> **상태: 계약 확정 / 구현 보류.** 아래 `/api/session/*` alias·필드 매핑은 통합 재개 시 붙인다
> (내부 `/api/reading-sessions/*`는 이미 구현·테스트 완료).

### 9-1. 세션 시작 — `POST /api/session/start` (확장 alias)

**요청(확장)**
```json
{
  "userId": "demo_user",
  "articleId": "https://example.com/article",
  "source": { "url": "https://example.com/article", "title": "글 제목", "type": "web" },
  "content": ["문단1", "문단2", "..."]
}
```
- `source.type` ∈ `web | pdf`. 본문 출처: 웹=Readability, **PDF=pdf.js `getTextContent()`**(§9-4).

**필드 매핑 (확장 → 내부 state)**

| 확장(요청) | 내부(state) | 변환 |
|---|---|---|
| `userId` | `user_id` | 그대로 |
| `articleId` | `document_id` | 그대로(확장은 URL을 문서 식별자로 사용) |
| `content[]` (문단 배열) | `raw_text` (str) | `"\n\n".join(content)` |
| `source{url,title,type}` | (메타·선택) | 로그/세션 메타로 보관 |
| `profile`(있으면) | `profile` | 그대로 |

- `userId`는 **설치별 익명 UUID**(`chrome.storage`, 로그인 없음) — ADR-002. 기본값 `anonymous` 허용.

**응답**
```json
{ "sessionId": "s1", "chunks": [], "simplifiedText": "...", "terms": [], "difficultyScore": 72.0 }
```
- `sessionId` = 내부 `session_id`. 나머지는 내부 §6 세션 시작 응답과 동일(확장은 선택 사용).
- ⚠️ **`wsEndpoint`는 ADR-001로 미사용** — 반환하지 않거나 `null`. 이벤트는 REST(§9-2)로 보낸다.

### 9-2. 이벤트 전송 — `POST /api/session/{id}/events` (확장 alias, REST)

ADR-001: WS 대신 **이벤트 구동 배치 flush**. 확장은 이벤트 큐를 1~2초 창(또는 blur 등
중요 이벤트)마다 아래 형태로 보내고, **응답에 실린 개입을 즉시 렌더**한다(고정주기 폴링 아님).

**요청(확장)** — 내부 §7 스키마로 정규화해 전송
```json
{ "session_id": "s1",
  "events": [ { "type": "scroll", "timestamp_ms": 12000, "position": 0.42, "duration_ms": 180 } ] }
```

**이벤트 필드 매핑 (확장 원형 → 내부 event)**

| 확장 원형 | 내부 event | 변환 |
|---|---|---|
| `type` | `type` | `scroll \| pause \| blur \| focus \| click` |
| `timestamp`(epoch ms) | `timestamp_ms` | **세션 시작 기준 ms**로 환산(`now - sessionStart`) |
| `payload.progress`(0~100) | `position`(0.0~1.0) | `progress / 100` |
| `payload.dwellMs` | `duration_ms` | 그대로(int, 직전 스크롤 간격 → "찍기 감점"에 사용) |

**응답** = 개입 명령(프론트 계약, `to_intervention_command` 출력)
```json
{ "type": "nudge",
  "payload": { "focusScore": 63.0, "progress": 42, "nudgeLevel": "soft", "nudgeMessage": "잠시 멈춰 핵심 문장을 다시 볼까요?" } }
```
- `type` ∈ `nudge | highlight | quiz | score_update`. 개입 없음이면 `score_update`(점수만 갱신).
- `session_end`는 클라이언트가 세션 종료 시 자체 처리(서버가 push하지 않음).
- **idle 넛지**: 확장이 N초 무동작 감지 시 `pause` 이벤트를 보내면 서버가 넛지를 응답으로 반환.

### 9-3. 결과 조회 — `GET /api/session/{id}/result` (확장 alias)

내부 `GET /api/reading-sessions/{id}/result`와 동일 응답(내부 §6 최종 결과, camelCase는 프론트
어댑터 `to_session_result` 사용). 확장은 세션 종료 시 호출해 대시보드에 성장 그래프를 기록.

### 9-4. 본문 소스 (웹 / PDF 공통 `content[]`)

| 출처 | 추출 | 결과 |
|---|---|---|
| 웹페이지 | Readability(또는 `<p>` 휴리스틱) | `content[]` |
| **PDF** | **pdf.js `getTextContent()`** → 줄 병합·하이픈·머리말/꼬리말 정리 | `content[]` |

두 경로 모두 **동일한 `content[]`** 로 정규화 → 백엔드는 출처를 구분하지 않는다(2번 담당, §9-1).

---

## 변경 이력
- v0 (6/20): ARCHITECTURE.md §4 계약을 문서로 추출. 필드명은 state.py와 1:1.
- v1 (6/21): 필드 표는 `docs/SHARED_STATE.md`로 분리·확정. intervention.type ∈ `none|highlight|nudge|quiz`.
- v2 (7/2): 최종 응답에 `warnings`(Self-Correction)·`trace`·`errors` 반영, 에러/모듈 전환 절 추가.
- v3 (7/3): Profile 시계열 확장(안) 반영 — `score_history` 입력, `previous_scores`/`recommended_difficulty` 출력(추가 필드). 상세는 `docs/TIMESERIES_DESIGN.md`. **제안 단계**(미동결).
- v4 (7/3): §9 확장(크롬) 인입 계약 추가 — `content[]` 세션 시작, camelCase↔snake_case·이벤트 필드 매핑, REST 전송(ADR-001), 웹/PDF 공통 `content[]`. **계약 확정·구현 보류**. 정본: `EXTENSION_INTEGRATION_FIXES.md`/`EXTENSION_DESIGN.md`.
