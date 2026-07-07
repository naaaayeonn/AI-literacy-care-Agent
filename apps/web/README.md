# AI 리터러시 케어 에이전트 (AI Literacy Care Agent) - FE Setup

이 프로젝트는 사용자의 독해 행동 분석 및 학습 성장을 지원하는 리터러시 케어 서비스의 프론트엔드(`apps/web`) 셋업 및 디자인 시스템 구축 결과물입니다. 팀 모노레포에 원활하게 drop-in 될 수 있도록 의존성과 경로가 깔끔하게 독립된 Vite 프로젝트 형태로 설계되었습니다.

---

## 🚀 실행 방법

### 1. 패키지 설치
```bash
npm install
```

### 2. 로컬 개발 서버 실행
```bash
npm run dev
```

---

## 📂 폴더 구조

```text
src/
  ├── app/                  # App 셸, 레이아웃 및 라우팅 (6/21 ① 확정 전 스텁)
  ├── components/
  │   ├── reading/          # ReadingPane, HighlightText, TermTooltip (스텁)
  │   ├── nudge/            # SoftNudge, MediumNudge, HardNudge (스텁)
  │   ├── quiz/             # QuizCard (스텁)
  │   ├── dashboard/        # GrowthDashboard, LiteracyScoreChart (스텁)
  │   ├── gamification/     # LevelBar, BadgeShelf, XpCounter (스텁)
  │   ├── panel/            # FloatingControlPanel (스텁)
  │   └── common/           # Button, Card 등 공통 UI 컴포넌트 (토큰 적용 예시)
  ├── features/
  │   ├── reading/          # 읽기 행동 분석 기능 비즈니스 로직
  │   ├── focus/            # 집중력 추적 기능 비즈니스 로직
  │   └── score/            # 리터러시 점수 산출 비즈니스 로직
  ├── stores/               # Zustand 전역 상태 저장소 (readingStore, focusStore, scoreStore)
  ├── styles/
  │   ├── tokens.css        # 디자인 토큰 정의 (CSS 변수 기반 규격)
  │   └── globals.css       # Tailwind 임포트, Reset, 읽기 본문 유틸 등
  ├── lib/                  # 외부 모듈 연동 (api.ts, ws.ts, mockData.ts)
  ├── types/                # 공유 타입 정의 (shared.ts - 6/21 ① 확정 전 스텁)
  └── mock/                 # 데모 데이터 (한국어 더미 본문 1편, 시계열 점수 데이터)
```

---

## 🎨 디자인 토큰 사용 규칙 (styles/tokens.css)

모든 스타일링은 `styles/tokens.css`에 지정된 CSS 변수를 활용합니다. 
Tailwind CSS 테마 설정(`@theme` 디렉티브)에 변수들을 매핑해두었으므로, 다음과 같이 Tailwind 클래스명으로 바로 사용 가능합니다.

### 1. 색상 (Colors)
* **배경 & 카드 표면**: `bg-bg` (따뜻한 종이톤), `bg-surface`, `bg-surface-alt`, `border-border`
* **텍스트**: `text-text` (warm near-black), `text-text-secondary`, `text-text-muted`
* **브랜드 & 피드백**: `bg-primary`, `hover:bg-primary-hover`, `bg-primary-tint`
* **지표 시각화**: `text-comprehension` (결과/이해도), `text-engagement` (과정/집중도)
* **성장/긍정 피드백**: `text-growth`, `bg-growth-tint`
* **3단계 넛지(Nudge) 대응**:
  * Soft: `bg-nudge-soft-tint`, `text-nudge-soft`
  * Medium: `bg-nudge-medium-tint`, `text-nudge-medium`
  * Hard: `bg-nudge-hard-tint`, `text-nudge-hard`
* **게이미피케이션**: `text-xp`, `bg-level`
* **스마트 하이라이팅**: `bg-highlight`

### 2. 레이아웃 & 간격 (Spacing & Radius)
* **둥글기**: `rounded-sm` (8px), `rounded-md` (12px), `rounded-lg` (16px), `rounded-xl` (24px)
* **간격**: Tailwind 간격 단위 `1`~`16`이 각각 디자인 토큰의 `space-1`~`space-16`으로 매핑되어 있습니다. (예: `p-4` = 16px)

### 3. 타이포그래피 (Typography)
* **읽기 영역 특화 클래스**: 읽기 본문 영역에 `.reading` 클래스를 부여하면, 68ch 수준의 가독 가로폭(`--reading-measure`), 1.8배 줄간격(`--leading-reading`), 1.125rem 크기(`--text-reading`)가 적용됩니다.
* **Pretendard 웹폰트**: CDN을 통해 기본 로드되며, 환경에 맞추어 `system-ui`로 부드럽게 Fallback 처리됩니다.

---

## ⚠️ 주의 사항

1. **독립 Vite 앱 ↔ 모노레포 호환**: 경로 별칭 `@/`를 설정하여, 모노레포 이식 시 경로 깨짐을 최소화하도록 구성하였습니다.
2. **6/20 작업 범위 엄격 준수**: 실시간 하이라이트 알고리즘, 실시간 넛지 분기 로직, 퀴즈 정오답 처리 및 실시간 차트 업데이트는 구현되어 있지 않은 정적 뷰(스텁) 상태입니다.
