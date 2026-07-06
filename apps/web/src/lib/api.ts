/**
 * ③번 백엔드와의 API 계약 타입 및 fetch stub (6/21 확정)
 * ③번 담당자는 이 파일의 인터페이스를 참고해 FastAPI 응답 형식을 맞춰준다.
 */
import { sampleArticle } from '../mock/sampleArticle';

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
  articleId?: string;
  userId: string;
  content?: string[];          // 크롬 확장 프로그램용: 페이지 긁어온 텍스트
  source?: any;                // 크롬 확장 프로그램용: 메타데이터
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
    console.log('[API] startSession Request:', req);
    try {
      const res = await fetch(`${BASE_URL}/api/session/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req),
      });
      if (res.ok) {
        const data = await res.json();
        return data;
      }
    } catch (err) {
      console.error('[API] Failed to startSession from server, falling back to mock:', err);
    }

    // Fallback Mock 데이터 반환
    return {
      sessionId: `session-${Math.random().toString(36).substr(2, 9)}`,
      article: {
        id: req.articleId,
        title: sampleArticle.title,
        category: sampleArticle.category,
        author: sampleArticle.author,
        publishedAt: sampleArticle.publishedAt,
        content: sampleArticle.content,
        difficulty: 0.6,
      },
      wsEndpoint: `${BASE_URL.replace(/^http/, 'ws')}/ws/reading/mock-session-${Date.now()}`,
    };
  },

  /** 세션 결과 조회 — Literacy Score + Recharts 데이터 */
  getSessionResult: async (sessionId: string): Promise<SessionResultResponse> => {
    console.log('[API] getSessionResult Request:', sessionId);
    try {
      const res = await fetch(`${BASE_URL}/api/session/${sessionId}/result`);
      if (res.ok) {
        const data = await res.json();
        return data;
      }
    } catch (err) {
      console.error('[API] Failed to getSessionResult from server, falling back to mock:', err);
    }

    // Fallback Mock 데이터 반환
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
    console.log('[API] submitQuizAnswer Request:', { sessionId, quizId, selectedOption });
    try {
      const res = await fetch(`${BASE_URL}/api/session/${sessionId}/quiz/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quizId, selectedOption }),
      });
      if (res.ok) {
        const data = await res.json();
        return data;
      }
    } catch (err) {
      console.error('[API] Failed to submitQuizAnswer to server, falling back to mock:', err);
    }

    return { correct: true, explanation: '정답입니다! (mock 서버 오프라인)' };
  },

  /** RAG 기반 어려운 용어/문장 AI 설명 조회 (2번 Content Reducer 연동) */
  getTermDefinition: async (sessionId: string, term: string): Promise<{ explanation: string }> => {
    console.log('[API] getTermDefinition Request:', { sessionId, term });
    try {
      // 백엔드 API 명세에 맞춤: GET /api/terms/lookup?word={term}
      const res = await fetch(`${BASE_URL}/api/terms/lookup?word=${encodeURIComponent(term)}&sessionId=${encodeURIComponent(sessionId)}`, {
        method: 'GET',
      });
      if (res.ok) {
        const data = await res.json();
        // RAG 엔진이 응답으로 { term, definition, source, faithfulnessScore } 를 반환함. 프론트엔드는 explanation 필드 기대.
        return { explanation: data.definition || `[AI 주석] RAG 사전에서 '${term}'의 뜻을 찾지 못했습니다.` };
      }
    } catch (err) {
      console.error('[API] Failed to getTermDefinition from server, falling back to mock:', err);
    }

    return { explanation: `[AI 주석] '${term}'은(는) 문맥상 중요한 개념으로, 독자의 문해력 향상을 위해 선별된 단어입니다.` };
  },
};
