# ④ 프론트엔드 & 시각화 — ARCHITECTURE.md

> **문서 목적**: 2026 AI·SW 경진대회 프로젝트 "AI 리터러시 케어 에이전트"에서
> ④번 역할(프론트엔드 & 시각화)이 무엇을 어떤 구조로 만드는지 정의한다.

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
