# 3번(Cognitive Care Backend) 코드 리뷰 피드백 — from 1번(오케스트레이션)

> 검토일: 2026-07-06 · 대상: `naaaayeonn/AI-literacy-care-Agent` main → 실제 코드는 **최상위 `backend/`**
> (폴더 `3. Cognitive Care Backend/`엔 문서 2개뿐, 코드는 루트 `backend/app/`에 있음).
> 검토 범위: `main.py · api/endpoints.py · api/ws.py · api/frontend_contract.py · services/cognitive_care.py ·
> orchestrator/{graph,score,routing,state}.py · models/models.py · schemas/schemas.py · core/{db,redis}.py ·
> run.py · resolve.py · requirements.txt · docker-compose.yml`
>
> WS 파이프라인·Redis 버퍼링·DB Flush·계약 어댑터의 뼈대는 잘 잡혀 있습니다. 다만 **최종 결과
> 경로(/finish·/result)에 확실한 크래시 버그**가 있고, **확장(ADR-001 REST · content[]) 계약이
> 아직 미반영**입니다. 심각도 순으로 정리했습니다.

---

## 🔴 High — 실제 크래시 / 통합 차단

### H1. `/finish`·`/result`가 blur·scroll 이벤트에서 **확실히 500으로 죽음** (TypeError)
- **위치**: `orchestrator/graph.py:36~41` + `services/cognitive_care.py:19, 26`
- **증상/원인**:
  - `graph.run_reading_session`이 이벤트를 정규화할 때 `duration_ms`가 없으면 **명시적으로 `None`을 넣는다**:
    ```python
    "duration_ms": metadata.get("duration_ms")   # 없으면 None
    ```
  - `cognitive_care.calculate_focus_score`는 `None`을 못 막는다:
    ```python
    duration = event.get("duration_ms", 1000)     # 키가 있고 값이 None → None 반환 (default 1000 안 먹음)
    penalty += 20.0 + (duration / 1000.0) * 2.0    # None / 1000.0 → TypeError  (blur)
    if duration < 300:                             # None < 300  → TypeError    (scroll)
    ```
  - 프론트의 **blur/scroll 이벤트는 대개 `dwellMs`가 없어** `duration_ms` 자체가 안 실린다 → graph가 `None` 주입 → **계산 함수 크래시**.
- **영향**: 대시보드/확장이 최종 점수를 받는 `GET /api/session/{id}/result`가 **blur 한 번만 있어도 500**. `/finish`도 동일. 즉 정상 시나리오에서 최종 결과 경로가 사실상 항상 실패.
- **수정안**(둘 다 권장):
  ```python
  # cognitive_care.py — None-안전 가드
  duration = event.get("duration_ms")
  if duration is None:
      duration = 1000
  ```
  ```python
  # graph.py — None을 넣지 말고 생략하거나 기본값
  "duration_ms": metadata.get("duration_ms") or 1000,
  ```

### H2. 확장 REST `/events` 엔드포인트 부재 — **ADR-001 위반, 확장과 통신 불가**
- **위치**: `api/ws.py`(WS만 존재), `api/endpoints.py`(start/finish/result만)
- **증상**: 이벤트/개입 왕복이 **WebSocket `/ws/reading/{id}`로만** 구현됨. 그러나 `EXTENSION_INTEGRATION_FIXES.md` **ADR-001**로 확장↔백엔드는 **REST 이벤트 구동**(`POST /api/session/{id}/events` → 응답 개입)으로 확정됐고, 4번 확장은 이미 배치 flush POST로 전환됨.
- **영향**: 현재 backend는 확장(REST)과 **통신 자체가 안 됨**. WS 클라이언트가 붙는 4번 웹앱(데모 폴백)만 동작.
- **수정안**: `POST /api/session/{session_id}/events` 추가. 바디 `{ events:[{type,timestamp_ms,position,duration_ms}] }` → focus 계산 → `to_intervention_command` 동기 반환. (WS 로직을 함수로 빼서 재사용.) 1번 로컬 레포에 참고 구현(`extension_session.py`)이 있으니 정합 맞추면 됨.

### H3. `/api/session/start`가 확장 `content[]`를 못 받음
- **위치**: `api/endpoints.py:17~53`, `schemas/schemas.py:4~6`
- **증상**: `SessionStartRequest = {userId, articleId}`만 받고 **항상 `mock_article` 반환**. 확장은 추출 본문 `content[]`(camelCase)를 넘김(EXTENSION_DESIGN §4-2).
- **영향**: 확장/PDF 인입(웹=Readability·PDF=pdf.js → content[]) 미지원. 2번 실제 요약 연동도 막힘.
- **수정안**: 요청에 `content: list[str] | None`, `source: dict | None` 추가. `content[]` → `"\n\n".join` → 2번 content_reducer 투입 → chunks/simplified/terms 반환. `articleId`는 옵션 폴백.

### H4. 최종 결과 계약 불일치 — **프론트에 comprehension/engagement가 0으로 나감**
- **위치**: `api/frontend_contract.py:89~90` vs `orchestrator/graph.py:57~59`
- **증상**: `to_session_result`는 **`score_breakdown` 중첩 딕셔너리**에서 값을 읽는다:
  ```python
  "comprehensionScore": round(_num(breakdown.get("comprehension_score")), 1),
  "engagementScore":    round(_num(breakdown.get("engagement_score")), 1),
  ```
  그런데 `graph.py`는 `score_breakdown`을 채우지 않고 **flat 키**만 세팅한다:
  ```python
  state["comprehension_score"] = 90.0   # score_breakdown 아님!
  state["engagement_score"] = focus_score
  ```
  → `breakdown = state.get("score_breakdown") or {}` = `{}` → **comprehensionScore=0.0, engagementScore=0.0, difficultyBonus=0**.
- **추가**: `graph.py`는 `literacy_score`를 **하드코딩 85.0**, `comprehension` 90.0으로 고정하고 `quiz_result`·difficulty를 무시함(`score.py`의 실제 계산 함수는 `NotImplementedError` 스텁). 즉 **데모의 핵심 지표 Literacy Score가 상수**.
- **영향**: 대시보드 전후 비교/이해도/집중도 카드가 0 또는 상수로 표시 → 데모 설득력 붕괴.
- **수정안**: (a) `graph.py`가 `state["score_breakdown"] = {"comprehension_score":..., "engagement_score": focus_score, "difficulty_score":...}`를 채우도록, (b) 하드코딩 대신 **1번의 실제 score 엔진**과 동기화(현재 배포본 graph/score가 오래된 스텁으로 보임).

---

## 🟡 Medium — 정합성 / 설계 결합

### M1. CORS `allow_credentials=True` + `allow_origins=["*"]`
- **위치**: `main.py:27~33`. 2번과 동일 이슈. 쿠키 인증 안 쓰므로 **`allow_credentials=False`**로. (모든 오리진에 자격증명 허용은 불필요한 노출.)

### M2. 이벤트 스키마가 경로마다 다름 — 3형태 공존
- **위치**: `ws.py`(top-level position/duration) · `endpoints.py:/finish`(metadata 중첩만) · `/result`(둘 다) · `graph.py`(metadata에서 읽음) · `cognitive_care.py`/`frontend_contract.py`(top-level에서 읽음)
- **증상**: 저장·전달 형태가 3가지, 읽는 쪽 규약이 2가지라 H1 같은 버그의 온상.
- **수정안**: 내부 표준 1개로 통일 — 예: 항상 top-level `{type, timestamp_ms, position, duration_ms}`. graph도 top-level에서 읽게 바꾸고 metadata 의존 제거.

### M3. `calculate_focus_score` 로직/문서 불일치 + idle 미반영
- **위치**: `cognitive_care.py:3~30`
- 문서엔 "체류 시간은 **가점** 요소"라 했으나 **가점 코드가 없음**(감점만). "빠른 스크롤 <300ms 감점"도 scroll 이벤트에 duration이 거의 안 실려 **사실상 발동 안 함**. `pause`(dwell)·`focus` 타입은 점수에 미반영 → **ADR-001의 idle 넛지**(무동작 → pause → 넛지)가 이 엔진에선 트리거되지 않음.
- **수정안**: dwell/pause를 집중 신호로 반영하거나, 문서에서 "가점" 문구 제거. idle 넛지 규칙을 pause 이벤트 기반으로 명시 구현.

### M4. `/result`가 `/finish` 선행에 강결합 — 확장 경로에서 빈 점수
- **위치**: `endpoints.py:121~155` ("DB에 Flush 되었다고 가정")
- **증상**: `/result`는 **DB의 ReadingEvent만** 읽는다. 이벤트는 `/finish`에서만 DB로 flush된다. 확장 REST 경로는 세션 종료 시 `GET /result`만 호출(우리 설계) → **이벤트가 DB에 없어 near-zero 점수**.
- **수정안**: `/result`가 Redis 버퍼도 fallback으로 읽거나, `/events`→`/result` 경로에서 종료 시 flush를 보장. (H2 `/events` 도입과 함께 설계.)

### M5. 오케스트레이터 스텁이 실제 구현과 어긋남
- **위치**: `orchestrator/score.py`(`compute_score`/`calculate_literacy_score` → `NotImplementedError`), `routing.py`(`decide_intervention`/`level_for_focus` → `NotImplementedError`)
- **증상**: 배포본의 score/routing 실계산이 미구현(스텁). graph가 하드코딩으로 우회 중.
- **수정안**: 1번의 최신 orchestrator(score v1, routing)와 동기화. 안 되면 graph에서 최소 실제 가중합이라도 채워 H4 해소.

---

## 🟢 Low — 개선/위생

- **L1. DB `echo=True`** (`core/db.py:8`): SQL 전량 로깅. 성능·로그 소음. `echo=bool(os.getenv("SQL_ECHO"))`로 env 게이트.
- **L2. `get_redis()`가 매 호출 새 클라이언트 생성·미반납** (`core/redis.py:6~7`): WS 연결마다 새 클라이언트를 만들고 disconnect 시 안 닫음(`ws.py`) → 커넥션 누수. 싱글턴/풀 + `finally: aclose()`.
- **L3. `/finish`가 `get_redis()` 대신 자체 `redis.from_url` 생성 + 함수 내부 import** (`endpoints.py:61~63`): 일관성 저하. `get_redis()`로 통일.
- **L4. `resolve.py` 커밋됨** (머지 충돌 해소 스크립트): 리포지토리에 남아 있음. `README.md`에 `<<<<<<< HEAD` 마커가 남아 있지 않은지 확인하고 스크립트는 제거 권장.
- **L5. `/start` 신규 유저 생성 경합** (`endpoints.py:19~34`): 존재 확인 후 `add`+`commit`. 동시 요청 시 중복 PK IntegrityError 가능. upsert 또는 예외 처리.
- **L6. WS 견고성** (`ws.py`): 세션 검증 없음, disconnect 시 redis 미반납. 데모엔 무방하나 정리 권장.

---

## 통합(1번 관점) 우선순위

1. **H1 크래시** 즉시 수정 — 이거 없으면 최종 결과 경로가 데모에서 죽음. (한 줄 가드)
2. **H4 계약 불일치** — 대시보드 숫자가 0으로 나옴. `score_breakdown` 채우기 + 1번 score 동기화.
3. **H2 `/events` REST + H3 `content[]`** — 확장 통신의 전제(ADR-001). 이 둘이 없으면 확장은 아예 못 붙음.
4. **M1 CORS** 3번 정책 통일(False), **M4** `/result` Redis fallback.
5. 나머지 위생 항목.

> 참고: 1번 로컬 레포에 확장 REST alias(`/api/session/*` + content[] + /events)와 `to_session_result`/`score_breakdown`를 채우는 최신 orchestrator 구현이 있습니다. H2·H3·H4는 그 구현과 맞추면 빠릅니다. 계약(state/contract) 변경 시 1번에 공지 바랍니다.
