# 3. Cognitive Care Backend 딜리버리 플랜

## 1. 개요
이 문서는 3번 역할(Cognitive Care Backend)의 구현 계획 및 완료 현황을 추적합니다. 코어 시스템(실시간 이벤트→집중도→개입→최종점수)과 1번/4번 연동은 완료되었고, **계획 외 추가 기능인 크롬 확장(웹페이지 + pdf.js 뷰어) 인입 계약**의 3번 몫(alias·CORS·REST 전환)도 대부분 반영되었습니다. 남은 것은 **단어 뜻 hover lookup·배포 주소 확정·데이터 삭제**와 **2번/5번 실제 모듈 최종 통합**입니다.

- 아키텍처 정본: [`3_ARCHITECTURE.md`](./3_ARCHITECTURE.md)
- 확장 계약 정본: [`docs/EXTENSION_DESIGN.md`](./docs/EXTENSION_DESIGN.md) §10·§13-6, [`docs/EXTENSION_INTEGRATION_FIXES.md`](./docs/EXTENSION_INTEGRATION_FIXES.md) 3번 절, [`docs/API_CONTRACT.md`](./docs/API_CONTRACT.md) §9

### 일정 요약 (오늘 = 2026-07-06)
| 구간 | 기간 | 내용 |
|---|---|---|
| **개발 완주** | **7/6 → 7/10** | 아래 M3·M4 모든 항목 구현·테스트 완료. 7/10 기능 프리즈(feature freeze) |
| **버그 수정·검토** | 7/11 → 7/14 | 신규 기능 추가 금지. 통합 버그 수정·회귀 테스트·데모 리허설만 |
| **제출** | 7/15 | 최종 제출 |

---

## 2. 마일스톤 및 완료 현황

### Phase 1 (M0): 인프라 및 프로젝트 스캐폴딩 (✅ 완료)
- [x] FastAPI 백엔드 프로젝트 기본 골격 구성
- [x] PostgreSQL 데이터베이스 스키마 및 SQLAlchemy ORM 모델 세팅 (`models.py`)
- [x] Redis 연결 설정 및 비동기 클라이언트 구성 (`redis.py`)

### Phase 2 (M1): Cognitive Care 핵심 엔진 구현 (✅ 완료)
- [x] 실시간 이벤트 기반 집중도 점수(`focus_score`) 계산 로직 구현
- [x] 점수에 따른 개입(Intervention) 단계 판별 로직 추가 (`determine_intervention`)
- [x] 관련 로직에 대한 단위 테스트(`pytest`) 작성 및 통과 확인

### Phase 3 (M2): 핵심 모듈 통합 (Core Integration) (✅ 완료)
- [x] **1번 오케스트레이터 연동**: `frontend_contract.py` 및 `state.py` 이식 완료
- [x] **4번 프론트엔드 REST API 동기화**: `/start` 및 `/result` 스키마 갱신 및 어댑터 부착
- [x] 통합 테스트 및 `main` 브랜치 배포 완료
- [x] 실시간 개입 왕복 REST 전환 확정 (ADR-001) — 신규 WS 서빙 불요

### Phase 4 (M2.5): 크롬 확장 인입 계약 — 3번 몫 (🔄 대부분 완료)
> 계획 외 추가 기능. 확장(웹페이지 + pdf.js 뷰어)이 새 입력원으로 붙는 경계 계약.
- [x] **[G4/G5] WS 서빙 제외 확정 (ADR-001)** — 기존 `POST .../events`가 이벤트→개입 동기 반환하는지 검증. `@app.websocket` 신설 보류(후속)
- [x] **[start] `/api/session/start` alias — `content[]` 수용 (웹·PDF 공통)** — `extension_session.py`. camelCase 요청/응답, `content[] → raw_text("\n\n".join)`, `run_content_reducer` 재사용
- [x] **[events] `/api/session/{id}/events` REST 개입 반환** — 정규화 이벤트 배치 → `run_cognitive_care` → `decide_intervention` → `to_intervention_command`
- [x] **[result] `/api/session/{id}/result` alias** — 전체 오케스트레이터 실행 → `to_session_result`
- [x] **[CORS] chrome-extension:// + 임의 사이트 오리진 허용** — `main.py` `CORSMiddleware(allow_origins=*, allow_credentials=False)`
- [x] **[식별] 익명 userId 수용 (ADR-002)** — 미제공 시 `anonymous` 폴백
- [x] **[테스트] 확장 alias 단위 테스트** — `test_extension_session.py` 7 pass
- [x] **[문서] API_CONTRACT §9 "확장 인입 계약" 정합** — 세션/이벤트/결과 매핑표

### Phase 5 (M3): 남은 외부 모듈 연동 + 확장 마감 (⏳ 진행 예정 — 7/10까지 완료)

**A. 확장 백엔드 잔여 (EXTENSION_DESIGN §10 3번·§13-6)**
- [ ] **[단어뜻] hover 단어 뜻 lookup 엔드포인트** — `GET /api/terms/lookup?word=...`(또는 세션 스코프).
      세션 시작 `terms[]`에 없던 단어 hover 대응. **무료 경로만**(기존 RAG 용어풀이/로컬 사전/stub), 유료 사전 API 금지. → 7/8까지
- [ ] **[배포] 데모 배포 주소 확정 + config 정합** — localhost:8000 외 배포 주소(있으면) 확정,
      확장 `config.js`의 `API_BASE`와 CORS 정합 확인. 없으면 "로컬 기동 데모"로 확정·문서화. → 7/9까지
- [ ] **[삭제] 데이터 삭제 요청 처리(ADR-002)** — 익명 `userId` 기준 세션/이벤트 삭제 엔드포인트
      `DELETE /api/user/{userId}/data`(개인정보 동의 고지의 "언제든 삭제" 대응). → 7/9까지

**B. 코어 실제 모듈 통합 (원 계획 M3)**
- [ ] **[2번] Content & RAG 연동** — `/start`의 목업 아티클을 실제 2번 요약/terms API 응답으로 교체.
      stub↔real 토글(`agents/config.py`)로 데모 안전망 유지. → 7/9까지
- [ ] **[5번] QA & Evaluation 연동** — `/result` 최종 점수 산출 시 목업 퀴즈 점수(85점)를
      실제 5번 퀴즈 모듈 결과로 교체. stub 폴백 유지. → 7/10까지

**C. 통합 검증 (7/10 기능 프리즈 직전)**
- [ ] **[E2E] 서버 기동 + 확장 실왕복 검증** — `uvicorn backend.app.main:app --reload` →
      확장 로드 → 실제 기사/PDF에서 세션 시작·이벤트·넛지·결과 왕복을 콘솔(`[ALC]`)로 확인.
      (지금까지 코드 정적 대조로만 확인 → 런타임 검증으로 승격) → 7/10
- [ ] **[회귀] 전체 pytest green** — 신규 엔드포인트 포함 전체 통과 유지 → 7/10

### Phase 6: 버그 수정·검토 (7/11 → 7/14, 기능 동결)
> **신규 기능 추가 금지.** 아래만 수행.
- [ ] 통합 시나리오 버그 수정(웹앱·확장·PDF 뷰어 3경로)
- [ ] 엣지 케이스 방어: 빈 content[], 세션 만료/404, 잘못된 이벤트 스키마(422) 응답 점검
- [ ] CORS/배포 주소 실환경 재확인
- [ ] 데모 리허설 & 회귀 테스트 반복(스크립트: `docs/DEMO_SCENARIO.md`)

### 제출 (7/15)
- [ ] 최종 제출

---

## 3. 최종 제출 체크리스트 (3번 역할 기준)
**코어**
- [x] 실시간 이벤트 스트리밍 처리 (REST 이벤트 구동, ADR-001)
- [x] 인메모리 버퍼링 및 RDBMS 영구 저장 파이프라인
- [x] 오케스트레이터 규격에 맞춘 어댑터 패턴 적용
- [x] 집중도 하락 시 클라이언트에 개입(Nudge) 명령 전송

**확장 인입 (추가)**
- [x] `/api/session/start` content[] 수용 (웹·PDF 공통)
- [x] `/api/session/{id}/events` · `/result` alias
- [x] CORS(임의 사이트 + chrome-extension://) 허용
- [x] 익명 userId 폴백
- [ ] 단어 뜻 hover lookup 엔드포인트 (무료 경로)
- [ ] 데이터 삭제 요청 처리
- [ ] 배포 주소 확정 + config/CORS 정합

**최종 통합**
- [ ] 2번(실제 요약/terms)·5번(실제 퀴즈) 모듈 최종 통합
- [ ] E2E 실왕복 검증(웹·확장·PDF) + 전체 pytest green

> **완료 목표: 7/10** — 이후 7/11~14 버그 수정·검토, 7/15 제출.
