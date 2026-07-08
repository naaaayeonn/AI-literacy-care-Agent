# 3. Cognitive Care Backend 아키텍처

## 1. 문서 목적
본 문서는 AI 리터러시 케어 앱에서 **3번 역할 (Cognitive Care Backend)**의 시스템 구조와 핵심 모듈의 동작 방식을 정의합니다. 사용자의 실시간 읽기 행동 데이터를 수집하고 분석하여 집중도 점수를 계산하며, 오케스트레이터(1번)와 프론트엔드(4번)를 이어주는 중추적인 백엔드 서버 역할을 수행합니다.

> **범위 확장 (2026-07)**: 초기 설계는 "웹앱(apps/web) → 백엔드" 단일 인입 경로만 가정했으나,
> 계획 외 추가 기능인 **크롬 확장(웹페이지 + pdf.js 뷰어)**이 새 입력원으로 붙었다.
> 확장은 **파일 업로드 없이 크롬에서 읽는 모든 글**의 읽기 행동을 측정·개입·점수화한다.
> 3번 백엔드는 이 확장이 붙을 수 있도록 **인입 계약(alias)·CORS·전송방식(REST)**을
> 담당한다. 상세 근거·계약은 [`docs/EXTENSION_DESIGN.md`](./docs/EXTENSION_DESIGN.md),
> [`docs/EXTENSION_INTEGRATION_FIXES.md`](./docs/EXTENSION_INTEGRATION_FIXES.md),
> [`docs/API_CONTRACT.md`](./docs/API_CONTRACT.md) §9를 정본으로 한다. 아래 §7~§10에서
> 3번 관점의 구현 구조를 상세히 기술한다.

## 2. 기술 스택
- **Web Framework**: FastAPI (Python 3.13+)
- **In-Memory Cache**: Redis (실시간 행동 데이터 버퍼링 및 TTL 관리)
- **Database**: PostgreSQL (최종 읽기 세션 및 이벤트 영구 저장)
- **Communication**: **REST API(이벤트 구동)** — 세션 시작 / 이벤트→개입 왕복 / 최종 리포트.
  WebSocket 실시간 스트리밍은 **후속 선택**(ADR-001로 MVP에서는 REST 확정, §7-3 참조).
- **Cross-Origin**: FastAPI `CORSMiddleware` — 확장(임의 웹사이트 오리진 + `chrome-extension://` 뷰어)의 직접 fetch 허용.

## 3. 핵심 시스템 아키텍처

### 3.1. 이벤트 처리 파이프라인 (`app/api/reading_session.py`)
프론트엔드/확장으로부터 `scroll`, `dwell`, `blur`, `focus` 등의 이벤트를 수신하여 내부 규격(`pause`, `position`)으로 변환합니다(`_normalize_events`). 수신된 이벤트는 세션 상태(`reading_events`)에 적재되며, 데이터가 들어올 때마다 Focus Score Engine을 가동합니다.

> **전송방식 결정(ADR-001)**: 초기 설계는 WebSocket `/ws/reading/{id}`를 가정했으나, 개입(넛지·퀴즈·하이라이트)이 전부 **행동 반응형**이라 서버 선제 push가 불필요하다. 따라서 MVP는 **REST 이벤트 구동**으로 확정: 이벤트 발생 시 `POST .../events`(배치 flush) → **응답에 실린 개입 명령**을 클라이언트가 렌더한다. 고정주기 폴링이 아니라 이벤트 구동 요청/응답이므로 체감 실시간을 유지하면서 WS 수명관리 복잡성을 회피한다.

### 3.2. Focus Score Engine (`app/services/cognitive_care.py` / `app/agents/real/cognitive_care_service.py`)
누적된 행동 데이터를 기반으로 사용자의 실시간 집중도를 계산합니다.
- **감점 요인**: 비정상적인 스크롤(찍기·과속), 잦은 화면 이탈(Blur), 무동작(idle pause)
- **개입 결정 (Intervention)**: Focus Score 구간에 따라 `none`, `soft(highlight)`, `medium(nudge)`, `hard(quiz)` 단계로 분류하여 클라이언트에 즉각적인 피드백을 전달합니다.
- **구현 토글**: stub(`stubs/cognitive_care_stub.py`) ↔ real(`real/cognitive_care_service.py`)을 `agents/config.py`로 전환. 데모/테스트는 stub로 비용 0 동작, 실연산은 real 서비스.

### 3.3. Orchestrator 통합 (`app/api/frontend_contract.py`)
1번 역할(오케스트레이터)이 정의한 Shared State 규격을 준수합니다. 백엔드 내부 연산 결과를 `ReadingSessionState`로 구성한 뒤, 어댑터를 통해 프론트엔드/확장이 렌더링할 수 있는 규격화된 JSON 명령으로 변환합니다.
- `to_intervention_command(state)`: 실시간 개입 명령(넛지 레벨·메시지·focusScore·highlight/quiz).
- `to_session_result(state)`: 세션 종료 시 최종 리터러시 점수·성장 데이터(대시보드용).

### 3.4. REST API Endpoints — 두 계열
백엔드는 **① 웹앱 계열(snake_case, 원문 계약)**과 **② 확장 계열(camelCase alias, §7)** 두 라우터를 함께 mount한다(`main.py`가 각각 `prefix="/api"`).

**① 웹앱 계열 (`app/api/reading_session.py`, `/api/reading-sessions/*`)**
- **`POST /api/reading-sessions/start`**: 새 세션 발급 + 초기 아티클(chunks·simplified·terms·difficulty) 제공.
- **`POST /api/reading-sessions/{id}/events`**: 이벤트 배치 → 개입 명령 반환.
- **`POST /api/reading-sessions/{id}/quiz`**: 퀴즈 응답 채점 반영.
- **`POST /api/reading-sessions/{id}/finish`**: Redis 버퍼 → PostgreSQL Flush + 최종 계산 엔진 가동.
- **`GET /api/reading-sessions/{id}/result`**: 최종 Literacy Score·세션 결과 반환.

**② 확장 계열 (`app/api/extension_session.py`, `/api/session/*`)** — §7 상세.

## 4. 데이터 흐름도 (Data Flow)
1. User reads article (웹앱 또는 **확장/PDF 뷰어**) -> 클라이언트가 raw 이벤트 방출.
2. Backend parses events (`_normalize_events`) -> 세션 상태 버퍼에 적재.
3. Backend runs Cognitive Care Engine -> Focus Score 계산.
4. If score drops -> Determines Intervention (e.g., Nudge/Quiz).
5. State passed to Orchestrator adapter(`to_intervention_command`) -> Returns strict JSON format.
6. **클라이언트가 `POST .../events`의 응답으로 개입 수신 -> UI Nudge 트리거** (REST 이벤트 구동, ADR-001).
7. User finishes -> `GET .../result` (확장) / `POST .../finish` (웹앱) -> Flush & Compute Final Literacy Score.

---

## 5. 시스템 구성도 (확장 인입 포함)

```
[웹앱 apps/web] ──(articleId, snake_case)──┐
                                          ├─→ [3번 백엔드 FastAPI]
[크롬 확장 (웹페이지 + pdf.js 뷰어)] ──┐    │      main.py
   content script / viewer.js       │    │      ├─ CORSMiddleware (allow_origins=*)
   POST /api/session/start (content[])├────┘      ├─ reading_session router (/api/reading-sessions/*)
   POST /api/session/{id}/events     │            └─ extension_session router (/api/session/*)  ← alias
   GET  /api/session/{id}/result     ┘                    │
                                                          ▼
                            [1번 오케스트레이터] ──→ [2번 Content Reducer] ──→ [5번 QA/Quiz]
                            state.py · graph.py · routing.py · score.py · frontend_contract.py
```

핵심: 오케스트레이터·Content Reducer·score 코어는 **입력원을 가리지 않는다.** 확장 인입은
"코어 교체"가 아니라 **얇은 alias 어댑터 한 겹**(camelCase↔snake_case, content[]↔raw_text)만 추가한 것이다.

---

## 6. 세션 저장소·수명

- **단일 세션 저장소**: `reading_session.SESSION_STORE`(session_id → `ReadingSessionState`)를
  웹앱·확장 두 계열이 **공유**한다. 확장 alias는 별도 store를 만들지 않고 이 딕셔너리를 재사용한다(중복 store 금지). MVP는 인메모리, 운영 시 Redis 백엔드로 승격.
- **세션 경계(확장)**: PDF/웹 문서를 열어 읽기 판정 통과 → `/start`로 세션 발급,
  탭 이탈·닫기·visibility hidden 지속 → 클라이언트가 `/result` 호출로 종료. 업로드가 없는
  환경이므로 "문서 열기~닫기"를 한 세션으로 본다(EXTENSION_DESIGN §5).
- **사용자 식별(ADR-002)**: 확장은 설치 시 생성한 **익명 UUID**(`chrome.storage`)를 `userId`로 보낸다.
  로그인/회원가입 없음. 백엔드는 `userId` 미제공 시 `anonymous`로 폴백한다.

---

## 7. 확장 인입 alias 라우트 (`app/api/extension_session.py`) — 상세

> 확장은 **camelCase + `content[]`(본문 배열) + REST(이벤트 구동)**로 들어온다. 웹앱의 원문
> 계약(snake_case + `raw_text` 문자열)과 형태가 다르므로, 이를 내부 state로 잇는 **얇은
> 어댑터 라우터**를 둔다. 라우터는 `prefix="/session"` + mount `prefix="/api"` = `/api/session/*`.

### 7-1. `POST /api/session/start` — 본문(content[])으로 세션 시작
웹앱은 업로드된 `articleId`로 시작하지만, 확장은 **추출한 본문 배열**을 넘긴다. 한 엔드포인트가
둘 다(택일) 받는다.

- **요청(확장)**: `{ userId, source:{url,title,type}, content:["문단1","문단2",...], (articleId?) }`
- **필드 매핑(API_CONTRACT §9-1)**:
  - `userId → user_id` (미제공 시 `anonymous`, ADR-002)
  - `articleId → document_id`, 없으면 `source.url` 폴백, 그것도 없으면 `document_unknown`
  - `content[] → raw_text` : `"\n\n".join(문단)` (빈/비문자 문단 제거, 최소 1개 검증 — 실패 시 422)
- **처리**: `create_initial_state()` → `run_content_reducer(state)`(2번: chunks/simplified/terms/difficulty) → `SESSION_STORE`에 저장
- **응답(camelCase)**: `{ sessionId, chunks, simplifiedText, terms, difficultyScore }`.
  `wsEndpoint`는 ADR-001(REST 확정)로 **미포함**.

> **웹=Readability / PDF=pdf.js** 두 소스가 **동일한 `content[]` 형태**로 정규화되어 오므로,
> 백엔드 관점에선 "웹이든 PDF든 content[] 받으면 끝" — PDF 전용 신규 계약이 없다(§9-5 EXTENSION_DESIGN).

### 7-2. `POST /api/session/{id}/events` — 이벤트 배치 → 개입 명령
- **요청**: `{ events:[{ type, timestamp_ms, position(0~1), duration_ms }, ...] }` (확장이 내부 스키마로 정규화해 전송)
- **처리**: `_normalize_events` → `reading_events`에 append → `run_cognitive_care(state)`(focus score) → `decide_intervention(state)`(개입 단계) → 저장
- **응답**: `to_intervention_command(state)` — `{ type, payload:{ nudgeLevel, nudgeMessage, focusScore, ... } }`.
  즉 이벤트 왕복 한 번에 개입 명령이 **동기 반환**(ADR-001, 이벤트 구동).
- **검증**: `events`가 list가 아니면 422, 세션 없으면 404.

### 7-3. `GET /api/session/{id}/result` — 세션 종료·최종 결과
- **처리**: `run_reading_session(state)`(전체 오케스트레이터 실행) → `to_session_result(state)`
- **응답**: 최종 Literacy Score·성장 그래프용 데이터(대시보드 GrowthDashboard 재사용).

### 7-4. WebSocket 서빙 — 제외(후속)
ADR-001에 따라 신규 WS 라우트를 열지 않는다. 기존 `POST .../events`가 이벤트→개입을 동기
반환하는 것으로 대체. 계약(`to_intervention_command`)이 전송무관이므로, 여유 시 "실시간
스트리밍" 폴리시로 저비용 업그레이드 여지만 남긴다.

---

## 8. CORS / 오리진 정책 (`app/main.py`)

확장은 **두 종류 오리진**에서 백엔드로 fetch한다:
1. **content script**: 사용자가 읽는 **임의 웹사이트** origin (예: `https://news.example.com`) — `chrome-extension`이 아님.
2. **pdf.js 뷰어 페이지**: `chrome-extension://<id>` origin.

임의 사이트에서 읽으므로 dev/demo에서는 **모든 Origin 허용**이 필요하다. 쿠키/세션 인증을 쓰지
않으므로(`allow_credentials=False`) 와일드카드 허용의 위험이 낮다.

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # 임의 사이트 + chrome-extension:// 뷰어
    allow_credentials=False,    # 쿠키/인증 미사용 → 와일드카드 안전
    allow_methods=["*"],
    allow_headers=["*"],
)
```

> **운영 강화(후속)**: fetch를 서비스워커(`chrome-extension` origin)로 라우팅해 화이트리스트로 좁힌다.

---

## 9. 단어 뜻(terms) 제공 경로

- **세션 시작 시 일괄 제공**: `/api/session/start` 응답의 `terms[]`(2번 Content Reducer가 추출한
  용어풀이). 확장 오버레이가 이를 캐시해 hover 시 즉시 툴팁 표시.
- **hover 실시간 lookup(추가 예정, §10)**: 세션 시작 때 없던 단어를 hover하면 단어 → 뜻을
  요청하는 경량 lookup 엔드포인트를 둔다. **무료 경로만**(기존 RAG 용어풀이/로컬 사전/stub) —
  유료 사전 API 신규 도입 금지(EXTENSION_DESIGN §11 비용 0 원칙).

---

## 10. 확장 추가로 인한 3번 작업 요약 (구현 상태)

| 항목 | 내용 | 상태 |
|---|---|---|
| `/api/session/start` content[] 수용 (웹·PDF 공통) | camelCase alias + raw_text 변환 | ✅ 구현 |
| `/api/session/{id}/events` REST 개입 반환 | 이벤트 구동, WS 제외(ADR-001) | ✅ 구현 |
| `/api/session/{id}/result` 최종 결과 | 오케스트레이터 실행 → to_session_result | ✅ 구현 |
| CORS (임의 사이트 + chrome-extension://) | `allow_origins=*`, credentials=False | ✅ 구현 |
| 익명 userId 수용 (ADR-002) | 미제공 시 `anonymous` 폴백 | ✅ 구현 |
| 단어 뜻 hover lookup 엔드포인트 | 무료 경로, terms 미포함 단어 대응 | ⏳ 예정(§9) |
| 데모 배포 주소 확정 + config 정합 | localhost 외 배포 · API_BASE/CORS | ⏳ 예정 |
| 데이터 삭제 요청 처리 (ADR-002) | 익명 userId 기준 삭제 | ⏳ 후속 |
| 2번(실제 요약)·5번(실제 퀴즈) 최종 통합 | 목업 → 실제 모듈 | ⏳ M3 |

> 딜리버리 일정·담당·검증은 `3_DELIVERY_PLAN.md`를 정본으로 한다.
