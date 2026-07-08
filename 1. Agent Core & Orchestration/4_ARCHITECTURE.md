# ④ 프론트엔드 & 시각화 — ARCHITECTURE.md

> **문서 목적**: 2026 AI·SW 경진대회 프로젝트 "AI 리터러시 케어 에이전트"에서
> ④번 역할(프론트엔드 & 시각화)이 무엇을 어떤 구조로 만드는지 정의한다.

> **범위 확장 (2026-07)**: 계획 외 추가 기능인 **크롬 확장(웹페이지 + pdf.js 뷰어)**이
> 붙으면서 ④번의 화면 책임은 **두 갈래**가 되었다.
> - **웹앱(`apps/web`)** — 기존 React 데모 화면. 이제는 확장 미설치 심사위원을 위한
>   **무설치 데모 폴백**으로 위치가 바뀐다(§1-A).
> - **크롬 확장 UI** — **주력**. 실제 읽는 페이지/PDF 위에 오버레이로 넛지·퀴즈·단어뜻을
>   렌더하고, 팝업 온보딩을 제공한다. 이 확장 UI가 ④번의 새 주력 산출물이다.
>
> 확장 UI 상세 설계·계약은 [`docs/EXTENSION_DESIGN.md`](./docs/EXTENSION_DESIGN.md)
> (§9 PDF 뷰어, §10 역할별 작업, §13 온보딩)와
> [`docs/EXTENSION_INTEGRATION_FIXES.md`](./docs/EXTENSION_INTEGRATION_FIXES.md) 4번 절을
> 정본으로 하며, ④번 관점의 구조는 본 문서 **§10~§13**에 상세히 기술한다.

---

## 1. 역할 정의 (Role Definition)

**④번 역할은 "에이전트들이 계산한 결과를 사용자가 눈으로 보고 느끼도록 만드는 유일한 레이어"다.**

| 다른 역할이 만드는 것 | ④번이 하는 것 |
|---|---|
| ①이 Literacy Score를 **계산**한다 | ④가 그래프로 **시각화**한다 |
| ③이 집중도 데이터를 **수집**한다 | ④가 Floating Panel에 **실시간 표시**한다 |
| ②가 쉬운 문장·용어풀이를 **생성**한다 | ④가 하이라이트·툴팁으로 **렌더링**한다 |
| ①③이 개입 필요 여부를 **판단**한다 | ④가 넛지·퀴즈 팝업을 **표현**한다 |

**핵심 책임**: 데모의 "와, 이게 ChatGPT랑 다르다"는 첫인상을 만드는 것.
특히 **Literacy Score 전후 비교 그래프**는 프로젝트 차별화를 눈으로 증명하는 데모의 심장이다.

---

## 2. 기술 스택 (Tech Stack)

| 레이어 | 기술 | 선정 이유 |
|---|---|---|
| **UI 프레임워크** | React 19 + TypeScript | 컴포넌트 재사용, 타입 안전성 |
| **번들러** | Vite | HMR 속도, CSS-first 설정 |
| **라우팅** | React Router v7 | SPA 다중 페이지(읽기/대시보드/온보딩) |
| **상태 관리** | Zustand | 실시간 집중도·진행률·점수 구독, 보일러플레이트 최소 |
| **스타일링** | Tailwind CSS v4 (CSS-first) + CSS Custom Property 토큰 | 디자인 토큰 시스템과 Tailwind 유틸리티 동시 활용 |
| **차트** | Recharts | Literacy Score 전후 비교 라인 그래프 (데모 핵심) |
| **애니메이션** | Framer Motion | 넛지 등장 애니메이션, 부드러운 퀴즈 팝업 |
| **폰트** | Pretendard Variable (CDN) | 한글 가독성 최적화, 시스템 폴백 |

---

## 3. 화면 구조 (Page Architecture)

```
/                     → (리다이렉트) → /reading
/reading              → ReadingPage   ★ 메인 데모 화면
/dashboard            → DashboardPage → 성장 대시보드
/onboarding           → OnboardingPage → 시작 화면 (M1 이후)
```

### 3.1 Reading Page — 핵심 데모 화면

```
┌─────────────────────────────────────────────────────────────────────┐
│  Header  [🧠 AI 리터러시 케어 에이전트]        [집중도 85%] [진행 42%] │
├──────────────────────────────────┬──────────────────────────────────┤
│                                  │                                  │
│   ReadingPane (좌측 68%)         │   FloatingControlPanel (우측)   │
│   ┌──────────────────────────┐  │   ┌──────────────────────────┐  │
│   │ [카테고리 배지]           │  │   │ 실시간 케어 제어판        │  │
│   │ h1 제목                  │  │   │ ── 집중도: 85%           │  │
│   │ 저자·날짜                │  │   │ ── 진행률: 42%           │  │
│   │ ─────────────────        │  │   │ ── [LevelBar Lv.2 65%]  │  │
│   │ 본문 단락 (.reading)     │  │   │ ── XP: ✨ 265            │  │
│   │ [하이라이트 구간]         │  │   │ ── [BadgeShelf]          │  │
│   │ [TermTooltip 호버]       │  │   └──────────────────────────┘  │
│   │  ...                     │  │                                  │
│   └──────────────────────────┘  │   [Nudge 배너 — 조건부]         │
│                                  │                                  │
│   [SoftNudge / MediumNudge]     │   [QuizCard 팝업 — 조건부]      │
│   [HardNudge + QuizCard]         │                                  │
│                                  │                                  │
└──────────────────────────────────┴──────────────────────────────────┘
```

### 3.2 Dashboard Page — 성장 추적

```
┌─────────────────────────────────────────────────────────────────────┐
│  Header  [🧠 AI 리터러시 케어 에이전트]       [← 읽기 화면으로]       │
├─────────────────────────────────────────────────────────────────────┤
│  [요약 지표 카드 행]                                                  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                   │
│  │ 리터러시 │ │ 평균집중 │ │ 완독률  │ │ 현재XP  │                   │
│  │ 점수 92 │ │ 도 85%  │ │  76%   │ │  265   │                   │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘                   │
│                                                                     │
│  ┌──────────────────────────────┐ ┌──────────────────────────────┐  │
│  │  LiteracyScoreChart          │ │  레벨 & 게이미피케이션         │  │
│  │  (Recharts LineChart)        │ │  [LevelBar]                  │  │
│  │  케어 전 ─── / 케어 후 ───  │ │  [BadgeShelf]                │  │
│  └──────────────────────────────┘ └──────────────────────────────┘  │
│                                                                     │
│  성장 리포트 (주간/월간) — M1 이후 연결                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. 컴포넌트 트리 (Component Tree)

```
src/
├── app/
│   ├── router.tsx          ✅ 라우터 정의 (react-router-dom)
│   └── layouts/
│       └── RootLayout.tsx  ✅ 헤더 + 공통 레이아웃
│
├── pages/                  ✅ 6/21 완성
│   ├── ReadingPage.tsx     ✅ /reading (WebSocket·세션 연동 완료)
│   ├── DashboardPage.tsx   ✅ /dashboard (성장 대시보드 완료)
│   └── OnboardingPage.tsx  → / (추후)
│
├── components/
│   ├── reading/
│   │   ├── ReadingPane.tsx         ✅ 6/23 실구현 (스크롤·체류·blur 이벤트 연동)
│   │   ├── HighlightText.tsx       ✅ 6/23 구현 완료
│   │   └── TermTooltip.tsx         ✅ 6/23 구현 + 7/5 RAG API 연동 + 7/7 인라인 글로스
│   ├── nudge/
│   │   ├── SoftNudge.tsx           ✅ 6/24 구현 완료
│   │   ├── MediumNudge.tsx         ✅ 6/24 구현 완료
│   │   └── HardNudge.tsx           ✅ 6/25 구현 (퀴즈 연동 완료)
│   ├── quiz/
│   │   └── QuizCard.tsx            ✅ 6/25 구현 + 7/8 타이머 최적화 완료
│   ├── dashboard/
│   │   ├── GrowthDashboard.tsx     ✅ 6/30 구현 완료
│   │   ├── LiteracyScoreChart.tsx  ✅ 6/26 구현 완료 (데모 핵심)
│   │   └── DetailedGrowthReport.tsx ✅ 6/30 구현 완료
│   ├── gamification/
│   │   ├── LevelBar.tsx            ✅ 7/1 구현 완료
│   │   ├── BadgeShelf.tsx          ✅ 7/1 구현 완료
│   │   └── XpCounter.tsx           ✅ 7/1 구현 + 7/8 Hook 최적화
│   ├── panel/
│   │   └── FloatingControlPanel.tsx ✅ 7/1 구현 + 7/6 WS모니터링 + 7/8 렌더 최적화
│   └── common/
│       ├── Button.tsx              ✅ 구현 완료
│       └── Card.tsx                ✅ 구현 완료
│
├── stores/
│   ├── readingStore.ts     ✅ 집중도·진행률 → WebSocket 이벤트 연동 완료
│   ├── focusStore.ts       ✅ 집중도 점수 → 넛지 트리거 연동 완료
│   └── scoreStore.ts       ✅ Literacy Score·XP·레벨 완성
│
├── styles/
│   ├── tokens.css          ✅ 디자인 토큰 완성
│   └── globals.css         ✅ Tailwind 바인딩 완성
│
├── lib/
│   ├── api.ts              ✅ 백엔드 REST API 연동 완료 (스키마 매핑 포함)
│   └── ws.ts               ✅ WebSocket 클라이언트 실구현 완료
│
└── types/
    └── shared.ts           ✅ ①번 Shared State 스키마 반영 완료
```

---

## 5. 상태 관리 설계 (State Management)

### 5.1 Zustand Store 구조

```typescript
// readingStore — 읽기 세션 상태
{
  currentArticleId: string | null
  progress: number           // 0~100 (스크롤 기반)
  scrollVelocity: number     // px/s (③번이 WebSocket으로 전송)
  dwellTime: number          // 현재 섹션 체류 시간(ms)
  gazeOutCount: number       // 탭 블러 횟수
}

// focusStore — 집중도 상태
{
  focusScore: number         // 0~100 (③번 집중도 Scoring Logic 결과)
  nudgeLevel: 'none' | 'soft' | 'medium' | 'hard'
  isNudgeVisible: boolean
  isQuizVisible: boolean
}

// scoreStore — Literacy Score & 게이미피케이션
{
  literacyScore: number      // ①번 Score Engine 결과
  comprehensionScore: number // 이해도(퀴즈 기반)
  engagementScore: number    // 집중도(행동 기반)
  xp: number
  level: number
}
```

### 5.2 데이터 흐름

```
③ WebSocket 이벤트 (행동 데이터)
    └→ ws.ts onMessage
        └→ readingStore.setProgress()
        └→ focusStore.setFocusScore()
              └→ FloatingControlPanel (실시간 구독)
              └→ nudgeLevel 변화 → Nudge 컴포넌트 조건부 렌더

① REST API 응답 (세션 결과)
    └→ api.ts getSessionResult()
        └→ scoreStore.setLiteracyScore()
              └→ LiteracyScoreChart (데모 핵심 그래프)
```

---

## 6. API 계약 (Backend Integration Contract)

③번 백엔드와의 JSON 계약. ④번이 타입을 정의하고 ③번이 이 형식에 맞춰 응답한다.

### 6.1 세션 시작 요청

```typescript
// POST /api/session/start
interface StartSessionRequest {
  articleId: string;
  userId: string;
}

// Response
interface StartSessionResponse {
  sessionId: string;
  article: {
    id: string;
    title: string;
    content: string[];        // 단락 배열
    difficulty: number;       // 0~1 (가독성 지수 기반)
    category: string;
  };
  wsEndpoint: string;         // WebSocket 연결 URL
}
```

### 6.2 WebSocket 실시간 이벤트

```typescript
// ④→③ 클라이언트가 보내는 읽기 행동 이벤트
interface ReadingBehaviorEvent {
  type: 'scroll' | 'dwell' | 'blur' | 'focus' | 'progress';
  sessionId: string;
  timestamp: number;
  payload: {
    scrollVelocity?: number;   // px/s
    dwellSection?: string;     // 단락 ID
    dwellMs?: number;          // 체류 시간
    progress?: number;         // 0~100
  };
}

// ③→④ 서버가 보내는 개입 커맨드
interface InterventionCommand {
  type: 'nudge' | 'quiz' | 'highlight' | 'score_update';
  payload: {
    nudgeLevel?: 'soft' | 'medium' | 'hard';
    nudgeMessage?: string;
    quizQuestion?: string;
    quizOptions?: string[];
    highlightRanges?: Array<{ start: number; end: number; paragraphId: string }>;
    focusScore?: number;
    progress?: number;
  };
}
```

### 6.3 세션 결과 응답 (최종 Literacy Score)

```typescript
// GET /api/session/:sessionId/result
interface SessionResultResponse {
  sessionId: string;
  literacyScore: number;        // 0~100 합산 점수
  comprehensionScore: number;   // 이해도 (퀴즈 기반)
  engagementScore: number;      // 집중도 (행동 기반)
  difficultyBonus: number;      // 난이도 보정값
  xpEarned: number;
  completionRate: number;       // 완독률 (%)
  scoreSeries: Array<{          // Recharts용 시계열 데이터
    label: string;
    before: number;
    after: number;
  }>;
  badges: Array<{
    id: string;
    name: string;
    emoji: string;
    acquiredAt: string;
  }>;
}
```

---

## 7. 디자인 토큰 활용 규칙 (Token Usage)

| 토큰 | Tailwind 클래스 | 사용 위치 |
|---|---|---|
| `--color-comprehension: #4356D6` | `text-comprehension` `stroke-comprehension` | Recharts 이해도 라인 |
| `--color-engagement: #15A2A2` | `text-engagement` | Recharts 집중도 라인 |
| `--color-nudge-soft-tint` | `bg-nudge-soft-tint` | SoftNudge 배경 |
| `--color-nudge-medium-tint` | `bg-nudge-medium-tint` | MediumNudge 배경 |
| `--color-nudge-hard-tint` | `bg-nudge-hard-tint` | HardNudge 배경 |
| `--color-growth` | `text-growth` | 케어 후 점수 상승값 |
| `--color-xp` | `text-xp` | XP 카운터 |
| `--color-level` | `bg-level` | LevelBar 채움 색 |
| `--color-highlight` | `bg-highlight` | 스마트 하이라이트 |
| `--reading-measure: 68ch` | `.reading` | 읽기 본문 영역 |

---

## 8. ①번과의 연동 계약

①번 오케스트레이터가 확정한 공유 상태 중 ④번이 구독하는 필드:

```typescript
// ①번이 정의, ④번이 읽는 필드
{
  progress: number;           // FloatingPanel 진행률
  focusScore: number;         // FloatingPanel 집중도
  nudgeLevel: string;         // 어떤 Nudge를 보여줄지
  literacyScore: number;      // 최종 점수 → 그래프
  xp: number;                 // 게이미피케이션
  level: number;              // 게이미피케이션
  quizActive: boolean;        // QuizCard 팝업 트리거
  currentQuiz: object | null; // 퀴즈 내용
}
```

---

## 9. ③번(백엔드)이 ④번에 의존하는 것

③번은 ④번이 정의한 **ReadingBehaviorEvent** 스키마에 맞춰 WebSocket 수신 로직을 구현한다.
④번은 이 스키마를 `src/lib/ws.ts`에 TypeScript 인터페이스로 먼저 정의해 팀에 공유한다.

> **전송방식 주의(ADR-001)**: 위 §6.2의 WebSocket 계약은 **웹앱(데모 폴백)** 한정으로 유지된다.
> **확장은 REST 이벤트 구동**으로 확정되었다(§10-6). 즉 확장 UI는 `ws.ts`가 아니라
> `shared/session_client.js`의 배치 flush POST를 사용한다.

---

## 10. 크롬 확장 UI (추가 기능) — 상세

> **원칙**: 코어(이벤트→개입→점수)와 계약은 그대로. 확장 UI는 "실제 읽는 페이지/PDF 위에
> 오버레이로 개입을 렌더 + 팝업 온보딩"만 담당한다. 웹앱과 UX를 **중복 구현하지 않는다**
> (확장=주력, 웹읽기=데모 폴백, 대시보드=공용). EXTENSION_DESIGN §2·§10·§13.

### 10-A. 역할 재정의 (웹앱 ↔ 확장)

| 컴포넌트 | 위치 | 역할 |
|---|---|---|
| **크롬 확장** | `extension/` | **주력** — 실제 읽기 측정 + 라이브 넛지/퀴즈/단어뜻 오버레이 |
| **웹 대시보드** | `apps/web` `/dashboard` | **공용** — 점수/성장/배지 확인 (기존 GrowthDashboard 재사용) |
| **웹 읽기 화면** | `apps/web` `/reading` | **무설치 데모 폴백** — 확장 미설치 심사위원 시연용 |

### 10-B. 확장 UI 파일 구조 (④번 소유분 ★)

```
extension/
├─ manifest.json              MV3 · content_scripts · declarativeNetRequest · web_accessible_resources
├─ config.js                  API_BASE, 임계값, REST 설정 (전 컴포넌트 공유)
├─ popup/                     ★ 팝업 온보딩 UI
│  ├─ popup.html              토글 + (추가) 동의 화면 + 문서 열기 버튼
│  ├─ popup.js                on/off 저장 + (추가) consent·UUID·파일피커
│  └─ popup.css
├─ content/
│  ├─ content_script.js       웹 어댑터(extract()/getProgress()) → shared 주입 (얇은 글루)
│  └─ overlay.css
├─ shared/                    웹 · PDF 공용
│  ├─ tracker.js              읽기행동 이벤트 캡처 → 정규화 스키마 방출
│  ├─ overlay.js              ★ Shadow DOM 오버레이 (toast/badge → 퀴즈 모달·단어툴팁 확장)
│  └─ session_client.js       세션 수명 + REST 배치 flush + 개입 render()
├─ pdf/                       ★ PDF 뷰어 UI
│  ├─ viewer.html/js/css      pdf.js 렌더(canvas + textLayer) + shared 주입 (PDF 어댑터)
└─ background/service_worker.js  세션 storage · PDF 리다이렉트 동적 규칙
```

### 10-C. 팝업 온보딩 UI (EXTENSION_DESIGN §13, ADR-002)

첫 실행 시 팝업에서 **비용 0·PII 없음** 원칙으로 온보딩한다.

```
설치 → 팝업 최초 오픈
  1) 개인정보 동의 화면  [동의]        (미동의 → 아무 것도 수집 안 함)
       └ consent 저장 + userId(UUID) 생성
  2) ON/OFF 토글 (기본 OFF)
       ON → enabled=true → 크롬에서 "보던 대로" 자동 측정(웹 + PDF 링크→pdf.js 뷰어)
  3) [문서 열기] 버튼 → 로컬 PDF 파일 피커 → pdf.js 뷰어로 렌더(서버 업로드 없음)
  (재오픈 시: 1) 건너뛰고 현재 세션 상태 + 토글만 표시)
```

- **사용자 식별**: 설치 시 `crypto.randomUUID()` → `chrome.storage.local.userId`. 없으면 생성,
  있으면 재사용. `config.js`의 고정 `USER_ID`를 이 로직으로 교체. **로그인/회원가입 없음.**
- **동의 저장**: `chrome.storage.local.consent = { version, acceptedAt }`. 동의 버전 갱신 시 재동의.
- **정직 고지**("안 하는 것"): 화면 상시 감시 아님 · EEG/카메라 없음 · 크롬 밖 앱 안 봄.

### 10-D. 공용 오버레이 — 퀴즈 모달 · 단어 뜻 툴팁 (§9-7)

`shared/overlay.js`(Shadow DOM 격리)는 현재 **toast/badge**까지 구현됨. 추가로 확장:

- **넛지 toast**(구현): 개입 메시지 배너(soft/medium). 집중도 **badge**로 상시 표시.
- **퀴즈 모달**(추가): Hard 개입 시 `<quiz>` 커맨드 → 모달 형태 퀴즈(문항·선택지·정답 인터랙션).
  웹앱 `QuizCard`와 동일 UX를 Shadow DOM 안에서 재현.
- **단어 뜻 툴팁**(추가): 본문/`textLayer` `<span>` hover → `caretRangeFromPoint`로 커서 밑 단어
  추출 → 용어풀이 요청(무료 경로) → 툴팁 표시. 세션 시작 `terms[]` 캐시 우선, 없으면 lookup.

### 10-E. PDF 뷰어 UI (EXTENSION_DESIGN §9, 구현됨)

- pdf.js가 PDF를 페이지별 `<canvas>` + 좌표 맞춘 `<span>` **textLayer**로 렌더 → PDF가
  "일반 웹페이지"가 되어 웹과 **동일한** tracker/overlay를 그대로 재사용.
- 진입 2경로: ① PDF 링크를 service worker의 declarativeNetRequest가 가로채 `viewer.html?file=<URL>`로
  리다이렉트, ② 팝업 파일 피커로 로컬 PDF 열기(서버 업로드 없음).
- viewer.js는 PDF용 `extract()`/`getProgress()`만 주입하는 **PDF 어댑터**. 툴바(페이지 네비·확대/축소),
  단어 hover 툴팁·퀴즈 모달 UI가 ④번 남은 몫.

### 10-F. 전송방식 정합 (REST, ADR-001)

- 확장은 `shared/session_client.js`가 이벤트 큐를 `FLUSH_INTERVAL_MS`마다(또는 blur/pause 즉시)
  `POST /api/session/{id}/events`로 배치 flush → **응답에 실린 개입**을 `render()`가 렌더한다.
- `render()`는 `nudge`/`highlight`/`quiz`/`score_update` 커맨드를 overlay로 표현.
- idle 넛지: `IDLE_NUDGE_MS` 무동작 → 클라가 `pause` 이벤트 전송 → 서버 넛지 응답.
- 즉 확장 UI는 WebSocket(`ws.ts`)을 쓰지 않는다. 웹앱 데모 폴백만 WS 유지.

### 10-G. 세션 종료 → 대시보드 기록

- `session_client.stop()`이 세션 종료 시 `GET /api/session/{id}/result` 호출까지 구현됨.
- **남은 몫(④)**: 결과 응답을 **GrowthDashboard로 전달**해 성장 그래프/배지에 반영(공용 대시보드 재사용).

---

## 11. 확장 UI ↔ 백엔드 계약 (요약, 정본은 API_CONTRACT §9)

확장은 **camelCase + `content[]` + REST**로 백엔드와 통신한다. ④번이 호출하는 3개 경로:

```typescript
// 세션 시작 — 추출한 본문 배열을 넘긴다 (웹=Readability / PDF=pdf.js 공통)
POST /api/session/start
  → { userId, source:{url,title,type}, content:string[] }
  ← { sessionId, chunks, simplifiedText, terms, difficultyScore }

// 이벤트 배치 → 개입 명령 (이벤트 구동, 폴링 아님)
POST /api/session/{sessionId}/events
  → { events:[{ type, timestamp_ms, position, duration_ms }] }
  ← InterventionCommand  // nudge / quiz / highlight / score_update

// 세션 종료 → 최종 결과 (대시보드용)
GET /api/session/{sessionId}/result
  ← SessionResultResponse
```

> `wsEndpoint`는 REST 확정(ADR-001)으로 응답에서 제거됨. 이벤트 스키마는 tracker가
> `{ type, timestamp_ms, position(0~1), duration_ms }`로 정규화해 방출한다.

---

## 12. 상태·저장 (확장)

| 저장소 | 키 | 용도 |
|---|---|---|
| `chrome.storage.local` | `enabled` | on/off 토글 상태 (content script가 `onChanged` 구독) |
| `chrome.storage.local` | `userId` | 설치별 익명 UUID (ADR-002) |
| `chrome.storage.local` | `consent` | `{ version, acceptedAt }` — 동의 전 무수집 |
| service worker (메모리/session) | 세션 수명 | 탭·네비 이벤트로 깨어나 모니터링 (MV3 이벤트 기반) |

> **MV3 현실**: service worker는 상시 데몬이 아니라 이벤트로 자고 깬다. 상태는 storage에 두어
> 재기동에도 유지. 탭/네비게이션마다 깨어나 체감은 "항상 켜짐".

---

## 13. 확장 UI 리스크 & 대응

| 리스크 | 대응 |
|---|---|
| 페이지 CSS와 오버레이 충돌 | **Shadow DOM 격리**(overlay.js) — 이미 적용 |
| 확장 심사/설치 장벽(데모) | **웹 읽기 화면을 무설치 폴백**으로 유지 |
| 퀴즈 모달·단어 툴팁 미완 | 7/10 전 완성, overlay 확장으로 웹앱 UX 재현 |
| 스캔(이미지) PDF엔 글자 없음 | MVP는 "글자 레이어 있는 PDF"만. OCR(Tesseract.js)은 후속 |
| viewer가 shared 로드 실패 | web_accessible_resources·상대경로 로딩 실환경 점검(QA 항목) |
| 유료 사전 API 유혹 | 단어 뜻은 **무료 경로만**(terms 캐시/RAG/stub). 신규 과금 금지 |
