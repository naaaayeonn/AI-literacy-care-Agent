/**
 * ③번 백엔드와의 API 계약 타입 및 fetch stub (6/21 확정)
 * ③번 담당자는 이 파일의 인터페이스를 참고해 FastAPI 응답 형식을 맞춰준다.
 */

// ──────────────────────────────────────────────
// 공통 타입
// ──────────────────────────────────────────────

export interface Article {
  id: string;
  title: string;
  category: string;
  author: string;
  publishedAt: string;
  content: string[];           // 단락 배열 (단락 ID는 인덱스로 관리)
  difficulty: number;          // 0~1: 가독성 지수 기반 난이도 (①번 Content Reducer 출력)
}

// ──────────────────────────────────────────────
// 세션 시작 / 종료
// ──────────────────────────────────────────────

export interface StartSessionRequest {
  articleId: string;
  userId: string;
}

export interface StartSessionResponse {
  sessionId: string;
  article: Article;
  wsEndpoint: string;          // WebSocket 연결 URL ex) "ws://localhost:8000/ws/session/{sessionId}"
}

// ──────────────────────────────────────────────
// WebSocket 이벤트 (④→③: 읽기 행동 데이터)
// ──────────────────────────────────────────────

export type ReadingEventType = 'scroll' | 'dwell' | 'blur' | 'focus' | 'progress' | 'quiz_answer';

export interface ReadingBehaviorEvent {
  type: ReadingEventType;
  sessionId: string;
  timestamp: number;           // Unix ms
  payload: {
    scrollVelocity?: number;   // px/s
    paragraphId?: string;      // 현재 읽고 있는 단락 ID
    dwellMs?: number;          // 단락 체류 시간 (ms)
    progress?: number;         // 0~100 진행률
    quizId?: string;           // 퀴즈 ID
    selectedOption?: string;   // 선택한 정답
  };
}

// ──────────────────────────────────────────────
// WebSocket 이벤트 (③→④: 서버 개입 커맨드)
// ──────────────────────────────────────────────

export type InterventionType = 'nudge' | 'quiz' | 'highlight' | 'score_update' | 'session_end';

export interface HighlightRange {
  paragraphIndex: number;      // 단락 인덱스
  start: number;               // 문자 시작 위치
  end: number;                 // 문자 종료 위치
}

export interface QuizData {
  quizId: string;
  question: string;
  options: string[];
  correctOption: string;       // 실제 UI에서는 숨기고, 제출 후 서버 검증
  explanation?: string;
}

export interface InterventionCommand {
  type: InterventionType;
  payload: {
    // nudge
    nudgeLevel?: 'soft' | 'medium' | 'hard';
    nudgeMessage?: string;
    // quiz
    quiz?: QuizData;
    // highlight
    highlights?: HighlightRange[];
    // score_update (실시간 갱신)
    focusScore?: number;       // 0~100
    progress?: number;         // 0~100
    // session_end
    sessionResultId?: string;
  };
}

// ──────────────────────────────────────────────
// 세션 최종 결과 (Literacy Score, 시각화용)
// ──────────────────────────────────────────────

export interface ScoreSeriesPoint {
  label: string;               // ex) "읽기 전", "읽기 후", "1주 후"
  before: number;              // 케어 미적용 예상 점수 (기준값)
  after: number;               // 케어 적용 실제 점수
}

export interface BadgeData {
  id: string;
  name: string;
  emoji: string;
  description: string;
  acquiredAt: string;          // ISO date string
}

export interface SessionResultResponse {
  sessionId: string;
  literacyScore: number;       // 0~100 최종 합산
  comprehensionScore: number;  // 이해도 (퀴즈 정답률 × 난이도 보정)
  engagementScore: number;     // 집중도 (행동 데이터 기반)
  difficultyBonus: number;     // 난이도 보정값 (±)
  completionRate: number;      // 완독률 (%)
  xpEarned: number;            // 이번 세션 획득 XP
  totalXp: number;             // 누적 XP
  level: number;               // 현재 레벨
  scoreSeries: ScoreSeriesPoint[];  // Recharts용 시계열 데이터
  badges: BadgeData[];         // 이번 세션에서 획득한 배지
  sessionDurationMs: number;   // 총 읽기 시간
}

// ──────────────────────────────────────────────
// API fetch stub (TODO 7/6 실구현)
// ──────────────────────────────────────────────

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const api = {
  /** 세션 시작 — 기사 로드 및 WebSocket 엔드포인트 수신 */
  startSession: async (req: StartSessionRequest): Promise<StartSessionResponse> => {
    // TODO 7/6: 실제 fetch 구현
    console.log('[API] startSession', req);
    return {
      sessionId: 'mock-session-001',
      article: {
        id: req.articleId,
        title: '(mock) 기사 제목',
        category: '테크/교육',
        author: '더미 저자',
        publishedAt: '2026-06-21',
        content: ['(mock) 본문 단락입니다.'],
        difficulty: 0.6,
      },
      wsEndpoint: `ws://localhost:8000/ws/session/mock-session-001`,
    };
  },

  /** 세션 결과 조회 — Literacy Score + Recharts 데이터 */
  getSessionResult: async (sessionId: string): Promise<SessionResultResponse> => {
    // TODO 7/6: 실제 fetch 구현
    console.log('[API] getSessionResult', sessionId);
    const res = await fetch(`${BASE_URL}/api/session/${sessionId}/result`).catch(() => null);
    if (res?.ok) return res.json();
    // fallback: mock 반환
    return {
      sessionId,
      literacyScore: 87,
      comprehensionScore: 82,
      engagementScore: 91,
      difficultyBonus: 5,
      completionRate: 95,
      xpEarned: 115,
      totalXp: 265,
      level: 2,
      scoreSeries: [
        { label: '케어 전', before: 52, after: 52 },
        { label: '1일차', before: 50, after: 65 },
        { label: '3일차', before: 48, after: 74 },
        { label: '5일차', before: 49, after: 82 },
        { label: '7일차', before: 51, after: 87 },
      ],
      badges: [
        { id: 'first-read', name: '첫 완독', emoji: '📚', description: '첫 번째 글을 끝까지 읽었어요!', acquiredAt: new Date().toISOString() },
      ],
      sessionDurationMs: 720000,
    };
  },

  /** 퀴즈 정답 제출 */
  submitQuizAnswer: async (sessionId: string, quizId: string, selectedOption: string) => {
    // TODO 7/6: 실제 fetch 구현
    console.log('[API] submitQuizAnswer', { sessionId, quizId, selectedOption });
    return { correct: true, explanation: '정답입니다! (mock)' };
  },
};
