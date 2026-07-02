# 확장 ↔ 백엔드 통합 수정 목록 (보류 — 기록용)

> 작성일 2026-07-03 · 상태 **보류(defer)**. 오늘은 추가 기획 진행, 아래는 나중에 손볼 항목.
> 근거: 확장 MVP 골격(커밋 45bc809)이 **가정한 계약**과 현재 백엔드가 **실제 구현한 계약**이
> 어긋나 있어, 지금 상태로는 확장을 켜도 백엔드와 통신되지 않는다.
> (백엔드 테스트 82개는 전부 통과 — 코어 자체는 정상, 문제는 "확장이 붙는 경계"뿐)

관련 문서: [EXTENSION_DESIGN.md](./EXTENSION_DESIGN.md) · [API_CONTRACT.md](./API_CONTRACT.md) · [FRONTEND_INTEGRATION_GUIDE.md](./FRONTEND_INTEGRATION_GUIDE.md)

---

## ADR-001 — 확장↔백엔드 실시간 전송: REST(event-driven) 채택, WS 후속

- **상태**: 채택(Accepted) · 2026-07-03 · 결정자 1번(이소희) · **본 문서가 정본**
- **적용 범위**: 확장(웹·PDF 뷰어) ↔ 백엔드 읽기행동 이벤트/개입 왕복. M1~M3 MVP.

**맥락(Context)**
- 확장 골격은 WS `/ws/reading/{id}`를 가정(G4/G5)했으나 백엔드엔 WS 라우트가 없음.
- 백엔드는 이미 `POST /events`가 이벤트를 받아 개입까지 **동기 반환**(구현·82 tests 통과).
- 개입(넛지·퀴즈·하이라이트)은 전부 **행동 반응형**. 서버가 클라 이벤트 없이 먼저 push할
  시나리오가 사실상 없음(idle 넛지도 클라가 `pause` 이벤트로 전송 가능).

**결정(Decision)**
- **MVP 전송 = REST.** 확장은 이벤트 발생 시 `POST /events`(배치 flush)하고 **그 응답에 실린
  개입**을 렌더한다. 고정주기 폴링이 아니라 **이벤트 구동 요청/응답**.
- **WS는 후속(선택).** 여유 시 "실시간 스트리밍" 폴리시로 업그레이드. 계약
  (`to_intervention_command`)이 전송무관이라 저비용 전환.

**근거(Rationale)**
- 백엔드 신규작업 0 → M2(7/6)·개인일정·비용0 제약 충족.
- 서버 push 불요 → WS 강점 미사용. MV3 수명/재연결 복잡성 회피.
- 지연: 로컬 왕복 수십 ms → 체감 실시간. 스크롤 간격도 이벤트에 실려 "찍기 감점" 유지.

**영향(Consequences)**
- 4번: WS 클라이언트(`openSocket`) → **배치 flush POST + 응답 렌더**로 교체. idle 넛지용 클라 타이머 추가.
- 3번: 신규 WS 불요. `/events` 개입 반환 검증 + CORS(chrome-extension://)만.
- 1번: 경로 alias(`/api/session/*`) + 이벤트 스키마 정합(G6).
- 문서: 설계서 §4-1의 "WS 재사용" 전제는 본 ADR로 **대체(superseded)**.

**대안·기각(Rejected)**
- **A. WS 신설**: 기획안 §6 "WebSocket 스트리밍" 문구엔 부합하나, 백엔드 신규구축·수명관리
  비용이 일정 대비 과함. 전송계층은 심사 비노출 → "실시간"은 REST로도 유지. 후속으로 남김.
- **고정주기 폴링**: 불필요한 트래픽 → 기각. 이벤트 구동으로 대체.

---

## ADR-002 — 사용자 식별=익명 기기 UUID(로그인 없음), 문서=로컬 pdf.js(서버 저장 없음)

- **상태**: 채택(Accepted) · 2026-07-03 · 결정자 1번(이소희)
- **적용 범위**: 첫 실행 온보딩·사용자 식별·문서 열기. M1~M3 MVP.

**맥락(Context)**
- 누적 성장곡선(Dynamic Profile)엔 **지속 식별자**가 필요하나, 데모에 로그인 마찰·인증
  스코프·비번 보안책임은 과함. 문서를 서버에 보관하면 저장소·개인정보·비용 부담.

**결정(Decision)**
1. **사용자 = 설치 시 생성한 익명 UUID**(`chrome.storage.local.userId`). **로그인/회원가입 없음.**
2. **"문서 업로드" = 로컬 PDF를 파일 피커로 골라 pdf.js 뷰어로 렌더.** **서버 업로드·보관 없음**(브라우저 로컬 처리).
3. **온보딩(개인정보 동의 + ON/OFF)은 확장 팝업 최초 1회.**

**근거(Rationale)**
- 마찰 0·비용 0·PII 없음 → 심사위원 즉시 체험. 익명 UUID로도 "프로필 누적" 데모 성립.
- 문서 로컬 처리 → 업로드 서버 불요, 개인정보 최소.

**영향(Consequences)**
- `config.js`의 고정 `USER_ID:"demo_user"` → 설치별 UUID 생성 로직으로 교체.
- 4번: 팝업에 동의 화면 + 파일 피커 + UUID 생성. 3번: 익명 `userId` 수용(기본값 `anonymous` 이미 있음).
- 상세 설계·역할: `EXTENSION_DESIGN.md` §13.

**후속·기각(Rejected)**
- **구글 OAuth**: 기기간 동기화 필요 시 후속(무료, 비번 저장 안 함).
- **이메일+비번 자체구현**: 보안책임·스코프 → 기각.
- **서버 업로드·보관**: 저장소·개인정보·비용 → 기각.

---

## 0. 한눈에 보는 불일치 표

| # | 항목 | 확장이 호출 (extension) | 백엔드 실제 (backend) | 담당 |
|---|---|---|---|---|
| G1 | 세션 시작 경로 | `POST /api/session/start` | `POST /api/reading-sessions/start` | 1번/3번 |
| G2 | 시작 요청 바디 | `{ userId, articleId, source, content[] }` (camelCase, 본문 **배열**) | `{ raw_text(str), user_id, document_id, profile }` (snake_case, **문자열**) | 1번/3번 |
| G3 | 시작 응답 | `{ sessionId, wsEndpoint }` | `{ session_id, chunks, simplified_text, terms, difficulty_score }` | 1번/3번 |
| G4 | 이벤트 전송 방식 | **WebSocket** `/ws/reading/{id}` | **HTTP POST** `/api/reading-sessions/{id}/events` | 1번/3번 |
| G5 | WS 엔드포인트 존재 | 있다고 가정 | **없음** (코드 전체에 라우트 0개) | 1번/3번 |
| G6 | 이벤트 스키마 | `{ type, sessionId, timestamp, payload:{ progress, dwellMs } }` | `{ events:[{ type, timestamp_ms, position, duration_ms }] }` | 1번/4번 |
| G7 | 개입 응답 스키마 | `{ type, payload:{ nudgeLevel, nudgeMessage, focusScore } }` | `to_intervention_command()` 출력과 대체로 일치 ✅ | — |
| G8 | 결과 조회 | `GET /api/session/{id}/result` | `GET /api/reading-sessions/{id}/result` | 1번/4번 |
| G9 | 본문 추출 품질 | `<p>` 휴리스틱 (Readability 미적용) | (해당 없음) | 2번/4번 |

> G7만 사실상 맞는다. 나머지 G1~G6, G8은 실제로 어긋나 통신 실패 지점.

---

## 1번 (오케스트레이터 / 계약 / 백엔드 글루) — 담당자 결정 필요

핵심 판단: **WS를 실제로 열 것인가, 아니면 확장을 REST 폴링으로 돌릴 것인가.**
설계서(EXTENSION_DESIGN §4-1)는 "기존 WS 계약 재사용"을 전제로 썼지만, 이 레포 백엔드에는
WS가 구현돼 있지 않다. 둘 중 하나로 계약을 확정해야 한다.

- [x] **[결정] 통신 방식 확정 → REST(B) 채택** (ADR-001, 2026-07-03). WS는 후속 선택.
- [x] **[G4/G5] WS 엔드포인트 신설 불필요(ADR-001)** — 확장은 이벤트 발생 시 `POST /events`
      (배치 flush) → 응답에 실린 개입을 렌더(이벤트 구동, 폴링 아님). WS는 후속 업그레이드 여지로만 남김.
- [x] **[G1/G3] `/api/session/start` alias 신설** — `backend/app/api/extension_session.py` 구현.
      `content[]`를 `"\n\n".join` → `raw_text` 변환, 기존 SESSION_STORE·오케스트레이터 재사용.
      응답 camelCase(`sessionId`/`simplifiedText`/`difficultyScore`). `wsEndpoint`는 ADR-001로 미포함.
- [x] **[G2] 필드 매핑 확정** — `userId→user_id`, `articleId→document_id`(폴백 `source.url`),
      `content[]→raw_text`. API_CONTRACT §9-1 반영. userId 미제공 시 `anonymous`(ADR-002).
- [x] **[G8] 결과 경로 정합** — 확장 alias `GET /api/session/{id}/result` 신설(전체 오케스트레이터
      실행 → `to_session_result`). `POST /api/session/{id}/events`는 개입 명령 반환(REST, ADR-001).
- [x] **[문서] API_CONTRACT.md §9 "확장(크롬) 인입 계약" 절 추가** — 세션 시작·이벤트·결과
      매핑표 + 웹/PDF 공통 content[]. (v4)
- **검증**: `pytest backend/app/tests/test_extension_session.py` 6 pass, 전체 88 pass.

---

## 3번 (백엔드 구현: /api/session/start 확장 + WS 서빙)

> 설계서 §6에서 "확장↔백엔드 계약 구현·서빙"은 3번 몫으로 위임돼 있음. 1번이 계약을 확정하면
> 실제 라우트/배포는 3번이 붙인다.

- [x] **[G4/G5] WS 서빙 제외(ADR-001)** — 신규 WS 불필요. 기존 `POST /events`가 이벤트→개입을
      동기 반환하는지만 검증(이미 구현·테스트됨). `@app.websocket` 구현은 후속으로 보류.
- [ ] **[G1] `/api/session/start` 배포 경로 확정** — 로컬(localhost:8000) 외 데모 배포 주소도.
      확장 `config.js`의 `API_BASE`/`WS_BASE`와 CORS 정합.
- [ ] **[인프라] CORS / host 허용** — 확장은 임의 오리진에서 fetch. FastAPI CORSMiddleware 확인.

---

## 4번 (확장 UI: popup / 오버레이 / tracker)

> **ADR-001 REST + shared 공용화가 1번 글루로 선반영됨.** 아래 전송/스키마 항목은 해소,
> 4번의 남은 몫은 **UI(온보딩·퀴즈 모달·단어 툴팁)와 대시보드 기록**이다.

- [x] **[G6] 이벤트 스키마 정합** — `shared/tracker.js`가 정규화 스키마
      `{ type, timestamp_ms, position(0~1), duration_ms }`로 방출(progress/100·간격→duration_ms).
- [x] **[G4] WS → 배치 flush POST 전환(ADR-001)** — `shared/session_client.js`: 큐를
      `FLUSH_INTERVAL_MS`마다(또는 blur/pause 즉시) `POST /events` → 응답 개입 렌더.
      idle 넛지 타이머(`IDLE_NUDGE_MS` 무동작 → `pause`) 포함.
- [x] **[G1/G3] 경로·응답 필드 정합** — `session_client`가 `/api/session/start` 호출,
      `data.sessionId` 사용. `wsEndpoint` 참조 제거(ADR-001).
- [~] **[G8] 세션 종료 시 결과 반영** — `stop()`에서 `GET /result` 호출까지 구현.
      **대시보드 기록은 4번 후속**(응답을 GrowthDashboard로 전달).
- [x] **[개입] `score_update` 등 처리** — `session_client.render()`가
      nudge/highlight/quiz/score_update 정합.
- [ ] **[4번] 팝업 온보딩 UI** — 개인정보 동의 화면 + 문서 열기(로컬 pdf.js). EXTENSION_DESIGN §13.
- [ ] **[4번] 퀴즈 모달 · 단어 뜻 툴팁** — overlay 확장(현재 toast/badge까지).
- **참고**: `shared/tracker.js`·`overlay.js`·`session_client.js`는 웹·PDF 공용. content_script는
      웹 `extract()`/`getProgress()`만 주입하는 얇은 어댑터로 리팩터됨(검증: `node --check` 통과).

---

## 2번 (Content Reducer / 본문 추출)

- [ ] **[G9] Readability 통합** — 확장 본문추출을 `<p>` 휴리스틱 → `@mozilla/readability`로
      교체(광고·메뉴 제거). content_script `extractArticle()` 대상.
- [ ] **[계약] chunks/terms 메타 확장** — highlight 문자 단위 위치(`frontend_contract._highlights`
      TODO)를 위해 chunk에 문자 오프셋 메타 제공 검토. (후순위)

---

## 보류 사유 & 재개 조건

- **오늘**: 추가 기획 우선. 위 항목은 기록만 하고 코드는 건드리지 않음.
- **~~재개 시 첫 단추: 통신 방식 결정~~ → 완료**: REST 확정(ADR-001). 다음 단추는 경로 alias·이벤트 스키마(G6) 정합.
- **검증 방법(재개 후)**: `uvicorn backend.app.main:app --reload`로 서버 기동 →
  확장 로드 → 실제 기사 페이지에서 세션 시작·이벤트·넛지 왕복을 콘솔(`[ALC]`)로 확인.
  (오늘 서버 미기동 상태라 런타임 검증은 못 함 — 위 간극은 **코드 정적 대조**로 확인한 것.)
