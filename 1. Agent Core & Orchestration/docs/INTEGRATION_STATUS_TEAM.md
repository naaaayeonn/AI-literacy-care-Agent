# 팀 통합 상태 요약 (Integration Status) — 2026-07-06

> 작성: 1번(오케스트레이션) · 근거: 2·3·4·5번 저장소 코드/문서 리뷰
> (`FEEDBACK_TO_ROLE{2,3,4,5}_FROM_ROLE1.md`)
> 일정: **7/10 전 기능 완성(기능 프리즈) → 7/11~14 버그 수정·검토 → 7/15 제출**

---

## 0. 한눈에 보는 현재 통합 상태

| 역할 | 코드 상태 | 데모 동작 | 통합 블로커 |
|---|---|---|---|
| **1번** 오케스트레이션 | 계약·확장 alias 있음, **score/routing 실계산은 스텁** | — | score 엔진 실구현 |
| **2번** Content & RAG | 파이프라인 동작, 폴백 탄탄 | ✅ 단독 OK | RAG 성능·faithfulness 상수 |
| **3번** Cognitive Care | WS·DB·Redis 동작 | ⚠️ **최종결과 경로 크래시** | REST/content[] 미지원, 결과 계약 불일치 |
| **4번** 프론트(웹앱) | UI 완성도 높음 | ⚠️ **실연동이 mock 폴백** | startSession 스키마 불일치 |
| **5번** QA | **코드 없음(문서만)** | ❌ | 검증대상 분산·비용0 충돌 |

**결론**: 개별 부품은 대체로 동작하나, **"조립(통합)"이 안 되는 상태**. 원인은 대부분 *계약 불일치*와
*스텁이 실값으로 안 바뀜*이다. 아래 크리티컬 패스 3개만 잡으면 폐루프가 살아난다.

---

## 1. 🔴 크리티컬 패스 — 데모까지 반드시 해결 (우선순위 순)

### CP-1. 3번 백엔드 크래시: `/finish`·`/result`가 blur/scroll에서 500
- **누구**: 3번
- **무엇**: `graph.py`가 `duration_ms` 없을 때 `None` 주입 → `cognitive_care.calculate_focus_score`에서 `None/1000` **TypeError**. blur 한 번만 있어도 최종 점수 조회가 죽음.
- **고치기**(한 줄): `duration = event.get("duration_ms"); if duration is None: duration = 1000`
- **왜 1순위**: 데모 마지막 화면(결과/대시보드)이 죽는 문제.

### CP-2. 3번↔4번 계약 불일치 (camelCase) → 실연동이 통째로 mock
- **누구**: 3번 + 4번 **공동**
- **무엇**:
  - 4번 `api.startSession`이 `{user_id, document_id}`(snake) 전송 → 3번은 `{userId, articleId}`(camel) 기대 → **422 → mock 폴백**.
  - 응답도 4번은 `data.session_id`로 읽고 3번은 `sessionId` 반환 → **undefined**.
  - 4번 `getSessionResult` 결과 계약: 3번 `to_session_result`는 `score_breakdown`에서 읽는데 `graph.py`는 flat 키만 채움 → **comprehension/engagement가 0**.
- **고치기**: **필드명을 camelCase로 통일**(요청 `userId/articleId`, 응답 `sessionId`), 3번 `graph.py`가 `score_breakdown` 채우기.
- **왜 2순위**: "실제 백엔드 연동"이 실제로는 동작 안 함. 이거 없이는 폐루프가 mock.

### CP-3. 확장 인입 계약 (ADR-001 REST + content[]) 미반영
- **누구**: 3번(백엔드) + 4번(확장 UI)
- **무엇**: 3번 백엔드는 **WS만** 있고 `POST /events`(REST 이벤트 구동)·`content[]` 세션 시작이 없음. 확장은 REST 배치 flush로 붙어야 함(ADR-001).
- **고치기**: 3번에 `POST /api/session/{id}/events`(→개입 반환) + `/start`가 `content[]` 수용 추가. (1번 로컬 `extension_session.py`가 참고 구현.)
- **왜 3순위**: 확장(주력 데모 표면)이 백엔드와 아예 통신 불가.

---

## 2. 🟡 교차 이슈 — 두 역할이 함께 맞춰야 하는 것

| # | 이슈 | 역할 | 조치 |
|---|---|---|---|
| X1 | **CORS `allow_credentials=True` + `origins=["*"]`** (2번·3번 backend 둘 다) | 2·3번 | 쿠키 안 쓰므로 **`allow_credentials=False`**로 통일 |
| X2 | **넛지 임계값 불일치** — 프론트 80/60/40 vs 백엔드 75/50/30 | 3·4번 | 한 값으로 확정(권장 75/50/30) |
| X3 | **퀴즈 채점·용어설명 엔드포인트 부재** — 4번이 `/quiz/submit`·`/explain` 호출하나 백엔드에 없음 | 2·3·4번 | 2번 lookup(무료)·채점 계약에 연결 or 3번 라우트 추가 |
| X4 | **점수가 실값이 아님** — 1번 score 스텁 / 3번 literacy=85 하드코딩 / 2번 faithfulness=1.0 상수 | 1·2·3번 | 실계산으로 교체(스텁↔real 토글 유지) |
| X5 | **검증 대상 코드베이스 분산** — 4개 backend가 폴더별로 흩어짐 | 1·5번 | **통합 기준 backend 1개 확정**(5번 QA 성립 전제) |

---

## 3. 역할별 핵심 요약 (상세는 개별 피드백 문서)

**2번 — Content & RAG** (`FEEDBACK_TO_ROLE2...`)
- 🔴 RAG 임베딩이 요청·청크마다 전체 용어집(1000+) 재인코딩 → 수십 초 지연 → **1회 캐시**
- 🔴 faithfulness 항상 1.0(죽은 코드) · 🟡 재구성 라우팅 `term_count` 분기 죽음(순서 버그) · `_meta` 계약 누출
- 🟢 확장용 **단어 단건 lookup(무료)** 함수 필요(3번 hover 엔드포인트 전제)

**3번 — Cognitive Care** (`FEEDBACK_TO_ROLE3...`)
- 🔴 CP-1 크래시 · CP-3 REST/content[] · H4 결과 계약(comprehension/engagement 0, literacy 85 하드코딩)
- 🟡 이벤트 스키마 3형태 공존 · `/result`가 `/finish` 선행에 강결합 · CORS
- 🟢 DB `echo=True`, redis 누수, `resolve.py`(머지충돌 스크립트) 커밋됨

**4번 — 프론트(웹앱)** (`FEEDBACK_TO_ROLE4...`)
- 🔴 CP-2 startSession 스키마 불일치 → mock 폴백 · 퀴즈/용어 엔드포인트 mock
- 🟡 넛지 임계값 불일치 · `useScoreEngine`가 API 점수 덮어씀 · **스크롤 WS 스로틀 없음(백엔드 폭주)** · `session_end` 미발화
- 🟢 `Math.random()` 기준선(재현성), 하드코딩 articleId
- ※ 확장 UI(팝업 온보딩·오버레이 퀴즈 모달·단어 툴팁)는 `extension/` 별도 산출물 — 여기 미포함

**5번 — QA** (`FEEDBACK_TO_ROLE5...`)
- 🔴 **코드 전무(문서만)** · 비용0 vs Ragas/LangSmith 충돌 · 검증대상 분산 · 검증할 로직이 대부분 스텁/상수
- 🟡 확장 QA 표면(웹/PDF content[]·REST·pdf.js 추출) 문서에 없음 · 골든셋 스키마 미정의
- 🟢 README 빈 파일 · Daily Plan이 과거를 완료처럼 서술 · 루트 스트레이 파일(`hi`, `test/index.html`)

---

## 4. 통합 체크리스트 (블로커 → 순서대로)

```
[ ] CP-1  3번: blur/scroll None 가드 (한 줄)              ← 즉시
[ ] CP-2  3·4번: camelCase 계약 통일 + score_breakdown 채우기
[ ] CP-3  3번: POST /events + /start content[] 수용
[ ] X1    2·3번: CORS allow_credentials=False
[ ] X2    3·4번: 넛지 임계값 75/50/30 통일
[ ] X4    1·2·3번: score/literacy/faithfulness 실값 교체
[ ] X5    1·5번: 검증 기준 backend 1개 확정
[ ] 2번   RAG 임베딩 캐시 (성능)
[ ] 4번   스크롤 WS 스로틀
[ ] X3    2·3·4번: 퀴즈 채점·용어 lookup 실연결
[ ] 5번   최소 QA(스캐폴딩·골든셋·회귀·스모크·리포트) 착수
```

---

## 5. 남은 일정 배치 (7/6 → 7/15)

| 구간 | 기간 | 내용 |
|---|---|---|
| **개발 완주** | 7/6 → **7/10** | 위 CP-1~3, X1~X5, 각 역할 잔여 구현 완료. **7/10 기능 프리즈** |
| **버그 수정·검토** | 7/11 → 7/14 | 신규 기능 금지. 웹·확장·PDF 3경로 회귀·통합 버그·리허설만 |
| **제출** | 7/15 | 최종 제출 |

**권장 순서(7/6~7/7)**: CP-1(3번, 즉시) → CP-2(3·4번, 반나절) → X1 CORS → 그다음 CP-3(확장 REST).
이 4개만 7/7까지 잡으면 **폐루프 실연동이 처음으로 end-to-end 동작**한다.

---

## 6. "정직" 원칙 (심사 방어)

- 미완/스텁 경로는 **숨기지 않고** 리포트·데모 설명에 명시(기획안 §4.3 "❌ 하지 말아야 할 말" 정신).
- 특히 **literacy_score·faithfulness가 현재 상수**라는 점 — 실값 교체 전까지는 "데모 스텁"임을 팀이 공유.
- 5번 Quality Report는 `verified` / `unverified`를 분리 기재.

> 개별 상세·수정 코드안은 `FEEDBACK_TO_ROLE{2,3,4,5}_FROM_ROLE1.md` 참고. 계약 변경은 1번에 공지.
