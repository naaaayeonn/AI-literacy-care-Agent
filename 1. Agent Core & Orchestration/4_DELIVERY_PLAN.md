# ④ 프론트엔드 & 시각화 — DELIVERY_PLAN.md

> **문서 목적**: 2026 AI·SW 경진대회에서 ④번 역할(프론트엔드 & 시각화)을
> 완수하기 위한 일자별 개발 실행 계획.
>
> ARCHITECTURE.md가 **"무엇을 어떤 구조로 만드는가"** 라면,
> 이 문서는 **"언제, 어떤 순서로, 어디까지 구현하는가"** 를 정의한다.

---

## 1. ④번 역할의 핵심 목표

**데모에서 사용자가 눈으로 보는 것은 모두 ④번의 책임이다.**

특히 아래 두 가지는 프로젝트 심사의 핵심 화면이므로 최우선으로 완성해야 한다:

1. **Literacy Score 전후 비교 그래프** (6/26) — "ChatGPT와 다르다"를 눈으로 증명
2. **실시간 집중도 + 넛지 개입 화면** (6/24~25) — 폐루프 동작을 체감하게 함

> **범위 확장 (2026-07)**: 계획 외 추가 기능 **크롬 확장(웹페이지 + pdf.js 뷰어)**의 UI가
> ④번 새 주력 산출물이 되었다. 웹앱은 **무설치 데모 폴백**으로 위치가 바뀌고, 확장 UI가
> 실제 읽는 페이지/PDF 위에 넛지·퀴즈·단어뜻을 오버레이한다. 확장 UI 남은 작업(팝업 온보딩·
> 퀴즈 모달·단어 툴팁·대시보드 기록)을 **7/10까지** 완성한다. 상세는 §8·§9 참조.
> 정본: [`docs/EXTENSION_DESIGN.md`](./docs/EXTENSION_DESIGN.md) §10·§13,
> [`docs/EXTENSION_INTEGRATION_FIXES.md`](./docs/EXTENSION_INTEGRATION_FIXES.md) 4번 절.

---

## 2. Milestone Overview

| Milestone | 날짜 | 목표 | 완료 기준 | 상태 |
|---|---|---|---|---|
| **M0** | 6/22 (월) | 더미 데이터로 전체 화면 표시 | 점수·본문·집중도가 화면에 보임 | ✅ 완료 |
| **M1** | 6/29 (월) | 폐루프 데모 완성 | 읽기→집중도→넛지→점수 흐름이 화면에서 동작 | ✅ 완료 |
| **M2** | 7/6 (월) | 웹앱 전 기능 통합 | 백엔드 API 실제 연동, 대시보드 완성 | ✅ 완료 |
| **M2.5** | 7/6 (월) | 확장 UI 골격 | popup 토글·PDF 뷰어·shared overlay(toast/badge)·session_client 연동 | ✅ 완료 |
| **M3** | **7/10 (금)** | **전 기능 완성 + 기능 동결** | **확장 UI 마감**(온보딩·퀴즈 모달·단어 툴팁·대시보드 기록) + 시연 3회 연속 | 🔄 진행 중 |
| **버그 검토** | 7/11~14 | 버그 수정·검토만 | 신규 기능 금지, 회귀 테스트·데모 리허설 | ⬜ 예정 |
| **제출** | 7/15 (수) | 최종 제출 | 제출 완료 | ⬜ 예정 |

---

## 3. Scope Definition

### ④번이 책임지는 것

| 영역 | 책임 내용 |
|---|---|
| **Reading Page** | 원문 본문 렌더링, 하이라이트, 어휘 툴팁, 단락 구조 |
| **Floating Control Panel** | 실시간 집중도·진행률·XP·레벨 표시 |
| **Nudge UI (3단계)** | Soft/Medium/Hard 넛지 배너 및 애니메이션 |
| **Quiz Card** | 인터럽트 팝업 퀴즈 UI, 정답 선택 인터랙션 |
| **Literacy Score 그래프** | Recharts 전후 비교 라인 차트 (데모 핵심) |
| **Growth Dashboard** | 주간/월간 성장 통계 시각화 |
| **Gamification UI** | 배지·레벨바·XP 카운터 |
| **라우팅** | /reading, /dashboard 페이지 분리 |
| **API 계약 타입** | 백엔드 JSON 응답 TypeScript 인터페이스 |
| **상태 구독** | Zustand store → 컴포넌트 실시간 반영 |
| **확장 팝업 온보딩** ★ | 동의 화면·ON/OFF 토글·문서 열기(로컬 pdf.js)·익명 UUID 생성 |
| **확장 오버레이** ★ | Shadow DOM 넛지 toast·집중도 badge·**퀴즈 모달**·**단어 뜻 툴팁** |
| **PDF 뷰어 UI** ★ | pdf.js 페이지 렌더·툴바·textLayer 위 툴팁/퀴즈 |
| **확장→대시보드 기록** ★ | 세션 결과(`/result`)를 GrowthDashboard로 전달 |

### ④번이 직접 책임지지 않는 것

| 영역 | 담당 | ④번의 관여 |
|---|---|---|
| WebSocket 행동 데이터 수집 서버 | ③번 백엔드 | 이벤트 스키마 타입 정의하여 공유 |
| Literacy Score 계산 로직 | ①번 코어 | 결과 JSON 수신 후 시각화 |
| 퀴즈 생성 로직 | ①②번 | QuizCard에 props로 주입받음 |
| 쉬운 문장 변환 | ②번 콘텐츠 | 변환된 텍스트를 ReadingPane에서 렌더링 |
| DB/Redis 처리 | ③번 백엔드 | 응답 데이터 구조 합의만 |

---

## 4. 일자별 작업 계획

### W0 — 셋업 (6/20~6/22)

| 날짜 | 작업 | 완료 기준 | 상태 |
|---|---|---|---|
| **6/20 (토)** | 프로젝트 셋업, 디자인 토큰, Tailwind 바인딩, 전체 폴더 구조 생성 | `npm run dev` 에서 따뜻한 종이톤 화면 표시 | ✅ |
| **6/21 (일)** | **ARCHITECTURE.md + DELIVERY_PLAN.md 작성** | 문서 존재 | ✅ |
| | **`react-router-dom` 설치 및 라우팅 구성** | `/reading`, `/dashboard` URL 작동 | ✅ |
| | **RootLayout + ReadingPage + DashboardPage 레이아웃** | 와이어프레임 수준 화면 완성 | ✅ |
| | **API 계약 타입 정의 (`lib/api.ts`)** | 타입 인터페이스 문서화 | ✅ |
| | **Shared State 타입 보강 (`types/shared.ts`)** | ①번 스키마 반영 | ✅ |
| **6/22 (월)** M0 | 더미 데이터 연결 — 점수·텍스트·집중도 화면 표시 | 정적 mock으로 모든 화면 채워짐 | ✅ |

### W1 — 핵심 폐루프 (6/23~6/29)

| 날짜 | 작업 | 완료 기준 | 상태 |
|---|---|---|---|
| **6/23 (화)** | **ReadingPane 실구현** — 원문 렌더링, 단락 구조, 스크롤 진행률 훅 | 실제 본문이 68ch 컬럼으로 렌더링됨 | ✅ |
| | **HighlightText** — `background-color: var(--color-highlight)` 마킹 | 특정 단락에 노란 하이라이트 적용됨 | ✅ |
| | **TermTooltip** — 마우스오버 시 용어 풀이 팝업 | 호버 시 팝업 표시됨 | ✅ |
| **6/24 (수)** | **SoftNudge / MediumNudge UI** — Framer Motion 등장 애니메이션 | nudgeLevel 변화 시 자동 등장/퇴장 | ✅ |
| | **FloatingControlPanel** — 집중도·진행률 Zustand 구독 연결 | 스토어 변경 시 숫자 실시간 갱신 | ✅ |
| **6/25 (목)** | **QuizCard** — Interruption Pop-up, 선택지 클릭 인터랙션 | 퀴즈 카드 등장 후 선택 가능 | ✅ |
| | **HardNudge** — QuizCard 트리거 연동 | Hard 단계 진입 시 퀴즈 팝업 | ✅ |
| **6/26 (금)** | **★ LiteracyScoreChart v1** — Recharts 전후 비교 라인 그래프 | `scoreSeries` mock으로 그래프 렌더링됨 | ✅ |
| **6/27~28 (토·일)** | 그래프 데이터 연동 준비, 대시보드 레이아웃 polish | 화면 완성도 80% | ✅ |
| **6/29 (월)** M1 | 데모 화면 폴리시 — 전체 흐름 리허설 | 읽기→넛지→퀴즈→점수 화면 흐름 연속 시연 가능 | ✅ |

### W2 — 기능 완성 (6/30~7/6)

| 날짜 | 작업 | 완료 기준 | 상태 |
|---|---|---|---|
| **6/30 (화)** | **성장 대시보드(GrowthDashboard)** — 주간/월간 통계 레이아웃 | 대시보드 페이지 UI 완성 | ✅ |
| **7/1 (수)** | **게이미피케이션 UI** — LevelBar·BadgeShelf·XpCounter 실구현 | FloatingPanel + Dashboard에 배지·레벨 표시 | ✅ |
| | **FloatingControlPanel 완성** — 전체 실시간 지표 연결 | 모든 지표 갱신됨 | ✅ |
| **7/2~4 (목~토)** | UI 에셋·아이콘·스타일 정리, 반응형 레이아웃 | 모바일/태블릿 레이아웃 이상 없음 | ✅ |
| **7/5 (일)** | 대시보드·게이미피케이션 마무리, 엣지 케이스 정리 + 인라인 글로스 | RAG 주석 속도 개선 및 인라인 토글 추가 | ✅ |
| **7/6 (월)** M2 | **실제 백엔드 API 연결** — api.ts fetch 구현, WebSocket 클라이언트 연결 | 백엔드 REST/WS 연동 완료, 스키마 매핑 | ✅ |

### W3 — 웹앱 통합·QA (7/7~7/9)

| 날짜 | 작업 | 완료 기준 | 상태 |
|---|---|---|---|
| **7/7 (화)** | 통합 연결·UX 다듬기 (sugaringdh 백엔드 브랜치 병합) | feature/backend 병합 완료 | ✅ |
| **7/8~9 (수·목)** | 웹앱 UI 버그 수정 (ESLint 경고 소탕, 렌더 최적화) | lint 0 warning, 빌드 성공 | ✅ |

### W3+ — 확장 UI 마감 (7/7~7/10) ★ 추가 작업

> 확장 UI 골격(M2.5)은 완료. 아래는 **남은 UI 조각 + 온보딩**을 7/10 기능 프리즈까지 채운다.
> 정본: EXTENSION_DESIGN §10(4번), §13(온보딩).

| 날짜 | 작업 | 완료 기준 | 상태 |
|---|---|---|---|
| **~7/6 (완료분)** | popup on/off 토글, PDF 뷰어 렌더(viewer.js), shared overlay(toast/badge), session_client 개입 render | 확장 로드 시 넛지 toast·집중도 badge 표시 | ✅ |
| **7/7 (월)** | **팝업 온보딩 UI** — 개인정보 동의 화면 + UUID 생성(`crypto.randomUUID`→storage) + `config.js` 고정 USER_ID 제거 | 최초 오픈 시 동의→userId 생성, 재오픈 시 토글만 | ⬜ |
| **7/8 (화)** | **문서 열기 버튼 + 로컬 PDF 파일 피커** → pdf.js 뷰어 연결 (ADR-002, 서버 업로드 없음) | 팝업에서 로컬 PDF 선택 시 뷰어로 렌더 | ⬜ |
| **7/8~9 (화·수)** | **퀴즈 모달 UI** — overlay `quiz` 커맨드 → Shadow DOM 모달(문항·선택지·정답). 웹앱 QuizCard UX 재현 | Hard 개입 시 모달 등장·선택·채점 전송 | ⬜ |
| **7/9 (수)** | **단어 뜻 툴팁 UI** — hover→`caretRangeFromPoint` 단어 추출→terms 캐시/lookup→툴팁. 웹·PDF(textLayer) 공통 | 단어 hover 시 뜻 툴팁 표시(무료 경로) | ⬜ |
| **7/9~10 (수·목)** | **확장→대시보드 기록** — `session_client.stop()`의 `/result` 응답을 GrowthDashboard로 전달 | 세션 종료 후 점수/배지가 대시보드에 반영 | ⬜ |
| **7/10 (금)** | **PDF 뷰어 사용성 폴리시** — 툴바(페이지 네비/확대·축소), 기본 뷰어 대비 이질감 최소화 | PDF 스크롤·확대 정상, 툴바 동작 | ⬜ |
| **7/10 (금)** M3 | **전 기능 완성 + 기능 동결** — 웹·PDF·확장 3경로 시연 3회 연속 동작 | 이후 신규 기능 없음 | 🔄 |

### 버그 수정·검토 (7/11~7/14) — 기능 동결

> **신규 기능 추가 금지.** 웹앱·확장·PDF 3경로 버그 수정과 데모 안정화만.

| 날짜 | 작업 |
|---|---|
| **7/11 (금)** | 통합 버그 소탕 — 확장 오버레이 z-index/Shadow DOM 충돌, 퀴즈 모달·툴팁 엣지 케이스 |
| **7/12 (토)** | 확장 실환경 점검 — viewer가 shared 로드 성공 여부, CORS, PDF 리다이렉트 오작동(다운로드 링크) |
| **7/13 (일)** | 발표 화면 최적화 (폰트·여백·애니메이션 타이밍) + 시연 리허설(웹·확장·PDF) |
| **7/14 (월)** | 데모 빌드 점검, 확장 로드/배포 환경 확인, 회귀 테스트 반복 |

### 제출 (7/15)

| 날짜 | 작업 |
|---|---|
| **7/15 (수)** | **프로그램 최종 제출** |

---

## 5. Phase별 Must Have / Should Have / Not Today

### 6/21 Must Have
- [x] ARCHITECTURE.md 존재
- [x] DELIVERY_PLAN.md 존재
- [x] `/reading`, `/dashboard` URL 라우팅 동작
- [x] RootLayout 헤더 공통 레이아웃
- [x] ReadingPage 와이어프레임 수준 레이아웃
- [x] DashboardPage 레이아웃 뼈대
- [x] API 응답 JSON TypeScript 인터페이스 정의
- [x] Shared State 타입 보강

### 6/21 Should Have
- [x] 네비게이션 링크 (읽기 화면 ↔ 대시보드 이동)
- [x] 페이지 제목 (브라우저 탭 title) 설정

### 6/21 Not Today
- 실제 스크롤 이벤트 감지 → 6/23
- 하이라이트 동작 → 6/23
- 넛지 애니메이션 → 6/24
- 퀴즈 팝업 동작 → 6/25
- Recharts 실시간 갱신 → 6/26~28
- 백엔드 실제 연결 → 7/6

---

## 6. ①③번과의 협업 체크포인트

| 날짜 | 협업 내용 |
|---|---|
| **6/21** | ④가 API 계약 타입 (`ReadingBehaviorEvent`, `SessionResultResponse`) 공유 → ③이 참고 |
| **6/22** | M0 더미 E2E 확인 — ③의 WebSocket 더미와 ④의 화면이 통신 가능한지 확인 |
| **6/26** | ①의 Score Engine 결과 JSON 형식 확인 → LiteracyScoreChart 데이터 매핑 |
| **7/6** | M2 — ③번 API 엔드포인트 전체 연결 (`/api/session/*` alias) |
| **7/8~9** | ②번 단어 뜻(terms) 무료 lookup 계약 확인 → 확장 단어 툴팁 연결 |
| **7/9~10** | ③번 `/api/session/{id}/result` 응답 → 확장 대시보드 기록 매핑 확인 |

---

## 7. 리스크 & 대응

| 리스크 | 대응 |
|---|---|
| ③번 WebSocket 스펙 변경 | 확장은 REST(ADR-001)로 확정 — `session_client` 배치 flush. 웹앱만 `ws.ts` adapter 유지 |
| Recharts 그래프 타이밍 이슈 | mock 데이터로 선 완성 후 실 데이터 연결로 단계 분리 |
| 반응형 레이아웃 시간 부족 | 데스크탑 우선 → 7/2~4 최소작업일에 정리 |
| ①번 Score 계산 결과 늦어짐 | mock `scoreSeries.ts` 더미 데이터로 그래프 먼저 완성, 이후 교체 |
| 확장 오버레이 ↔ 페이지 CSS 충돌 | **Shadow DOM 격리**(overlay.js) — 이미 적용, 퀴즈 모달도 동일 격리 |
| 확장 심사/설치 장벽(데모) | **웹 읽기 화면을 무설치 폴백**으로 유지 (확장 미설치 심사위원 대비) |
| 단어 뜻 유료 API 유혹 | **무료 경로만** — 세션 시작 `terms[]` 캐시 우선, RAG/stub. 신규 과금 금지 |
| 확장 UI 마감 일정 압박(7/10) | 웹앱 완성분(QuizCard 등) UX를 overlay로 재현해 신규 설계 최소화 |
