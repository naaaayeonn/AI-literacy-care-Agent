/**
 * 공유 상태 타입 (6/21 보강 — ①번 스키마 반영)
 * ①번 오케스트레이터가 확정한 ReadingSessionState 구조를 기반으로
 * ④번 프론트에서 구독할 필드를 정의합니다.
 *
 * TODO: 6/21 ①번(이소희)이 공유 상태 스키마를 확정하면 이 파일을 업데이트할 것.
 */

// ──────────────────────────────────────────────
// ①번이 정의하는 Shared State (읽는 상태)
// ──────────────────────────────────────────────

/** 전체 폐루프 세션 상태 (①번 Main Orchestrator 관리) */
export interface ReadingSessionState {
  sessionId: string;
  userId: string;
  articleId: string;

  // 읽기 행동 지표 (③번 WebSocket → ①번 Cognitive Care 처리)
  progress: number;             // 0~100 진행률
  scrollVelocity: number;       // px/s
  dwellTimeMs: number;          // 현재 단락 체류 시간
  gazeOutCount: number;         // 탭 블러 횟수

  // 집중도 (①③번 공동 관리)
  focusScore: number;           // 0~100
  nudgeLevel: NudgeLevel;       // 현재 개입 단계

  // 이해도 (①②번 공동 관리)
  quizActive: boolean;          // 퀴즈 팝업 활성화 여부
  currentQuiz: QuizSnapshot | null;
  quizHistory: QuizResult[];

  // Literacy Score (①번 Score Engine 산출)
  literacyScore: number;
  comprehensionScore: number;
  engagementScore: number;

  // 세션 메타
  startedAt: number;            // Unix ms
  status: SessionStatus;
}

export type NudgeLevel = 'none' | 'soft' | 'medium' | 'hard';
export type SessionStatus = 'active' | 'paused' | 'completed' | 'error';

export interface QuizSnapshot {
  quizId: string;
  question: string;
  options: string[];
}

export interface QuizResult {
  quizId: string;
  selectedOption: string;
  correct: boolean;
  timestamp: number;
}

// ──────────────────────────────────────────────
// ④번이 구독하는 파생 타입 (UI 렌더용)
// ──────────────────────────────────────────────

/** FloatingControlPanel에 표시할 실시간 지표 */
export interface LiveMetrics {
  focusScore: number;           // 0~100
  progress: number;             // 0~100
  nudgeLevel: NudgeLevel;
  literacyScore: number;
}

/** Recharts LiteracyScoreChart에 전달할 데이터 포인트 */
export interface ScoreDataPoint {
  label: string;
  before: number;               // 케어 미적용 기준값
  after: number;                // 케어 적용 실제값
}

/** 게이미피케이션 상태 */
export interface GamificationState {
  xp: number;
  level: number;
  levelProgress: number;        // 0~100 (현재 레벨 내 진행률)
  badges: AcquiredBadge[];
}

export interface AcquiredBadge {
  id: string;
  name: string;
  emoji: string;
  description: string;
  acquiredAt: string;
}
