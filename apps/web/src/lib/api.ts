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
  baselineScrollSpeed?: { easy: number; hard: number; dEasy?: number; dHard?: number };
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
  // 정답은 서버 채점(제출 응답의 correct)으로 판정한다. canonical 계약상 payload로
  // 내려오지 않으므로 optional. (구버전 호환 위해 타입만 남겨둠)
  correctOption?: string | number;
  explanation?: string;
  statement?: string;          // 확장 overlay 호환(question과 동일 값)
}

export interface InterventionCommand {
  type: InterventionType;
  payload: {
    // nudge
    nudgeLevel?: 'soft' | 'medium' | 'hard';
    nudgeMessage?: string;
    // quiz
    quizzes?: QuizData[];
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

// 문해 5대 지표(레이더). 각 0~100. score.py compute_literacy_domains 산출.
export interface LiteracyDomains {
  comprehension: number;  // 이해도 (퀴즈 정답률)
  focus: number;          // 집중 유지 (focus)
  closeReading: number;   // 정독 충실도 (본문 완독률)
  challenge: number;      // 난이도 도전력 (이해도 × 난이도)
  stability: number;      // 읽기 안정성 (감점, 이독성 보정)
}

// 글 프로필(사용자 역량 아님) — 이독성/난이도 + 라벨.
export interface TextProfile {
  readability: number;        // 0~100, 높을수록 읽기 쉬움
  difficulty: number;         // 0~100, 높을수록 어려움(전문성)
  readabilityLabel: string;   // 복잡 / 보통 / 매끄러움
  difficultyLabel: string;    // 쉬움 / 보통 / 어려움 / 전문
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
  literacyDomains?: LiteracyDomains;  // 문해 5대 지표(레이더)
  textProfile?: TextProfile;          // 글 프로필(이독성/난이도)
}

export interface GrowthReportResponse {
  weekly: {
    radarData: { subject: string; before: number; after: number }[];
    activityData: { label: string; time: number; xp: number }[];
    words: { word: string; meaning: string; level: '상' | '중' | '하'; status: 'completed' | 'review' }[];
    prescription: string[];
    weeklyScoreSeries?: { label: string; thisWeek: number | null; lastWeek: number | null }[];
  };
  monthly: {
    radarData: { subject: string; before: number; after: number }[];
    activityData: { label: string; time: number; xp: number }[];
    words: { word: string; meaning: string; level: '상' | '중' | '하'; status: 'completed' | 'review' }[];
    prescription: string[];
    weeklyScoreSeries?: { label: string; thisWeek: number | null; lastWeek: number | null }[];
  };
  latestSessionSummary?: {
    quiz_count: number;
    comprehension_score: number;
    progress: number;
    quiz_accuracy: number;
  };
  badges?: {
    id: string;
    name: string;
    emoji: string;
    description: string;
    acquiredAt?: string;
  }[];
  totalXp?: number;
  level?: number;
  averageLiteracyScore?: number;
  averageFocusScore?: number;
  averageComprehensionScore?: number;
}

// ──────────────────────────────────────────────
// API fetch stub (TODO 7/6 실구현)
// ──────────────────────────────────────────────

const getBaseUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  // Vercel 등 빌드 타임에 http://localhost:8000으로 구워져 있어도, 
  // 브라우저 접속 도메인이 localhost가 아닐 경우 배포용 백엔드로 강제 전환
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (hostname && hostname !== 'localhost' && hostname !== '127.0.0.1') {
      return 'https://ai-literacy-backend.onrender.com';
    }
  }
  return envUrl ?? 'http://127.0.0.1:8000';
};

const BASE_URL = getBaseUrl();
if (typeof window !== 'undefined' && window.localStorage) {
  try {
    window.localStorage.setItem('alc_backend_url', BASE_URL);
  } catch (e) {
    console.warn('[ALC] Failed to save alc_backend_url to localStorage:', e);
  }
}

// 7/15: 앱 로드 즉시 백엔드 warmup 핑. Render 무료 티어는 유휴 시 잠들어 첫 요청이 ~1분 걸리는데,
// 그동안 /events가 실패해 집중도가 100에 얼어붙는다. 온보딩(캘리브레이션) 동안 미리 깨워두면
// 읽기 시작 시점엔 warm 상태가 되어 집중도가 바로 반영된다. (fire-and-forget, 실패 무시)
if (typeof window !== 'undefined') {
  try {
    fetch(`${BASE_URL}/`, { method: 'GET', mode: 'no-cors', keepalive: true }).catch(() => {});
  } catch (e) {
    /* noop */
  }
}

export const api = {
  /** 세션 시작 — 기사 로드 및 REST 엔드포인트 수신 */
  startSession: async (req: StartSessionRequest): Promise<StartSessionResponse> => {
    console.log('[API] startSession Request:', req);
    const useMock = import.meta.env.VITE_USE_MOCK === 'true' || import.meta.env.VITE_USE_MOCK === true;
    
    if (!useMock) {
      try {
        const res = await fetch(`${BASE_URL}/api/session/start`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(req),
        });
        if (res.ok) {
          const data = await res.json();
          // F2: 백엔드 실제 chunks/terms/difficultyScore 응답을 프론트 DTO로 안전 매핑
          return {
            sessionId: data.sessionId,
            article: {
              id: (data.article && data.article.id) || req.articleId || 'doc',
              title: (data.article && data.article.title) || 'AI 리터러시 데모 아티클',
              category: (data.article && data.article.category) || 'Technology',
              author: (data.article && data.article.author) || 'AI Care System',
              publishedAt: new Date().toISOString(),
              content: (data.article && data.article.content) || [],
              difficulty: data.article && data.article.difficulty
                ? parseFloat(data.article.difficulty) / 100
                : 0.5,
              chunks: (data.article && data.article.chunks) || [],
            } as any,
            wsEndpoint: data.wsEndpoint || '',
          };
        }
      } catch (err) {
        console.error('[API] Failed to startSession from server:', err);
        // mock fallback이 금지된 경우 에러 표출
        if (import.meta.env.DEV) {
          console.warn('[API] Real connection failed, throwing error to make it visible.');
          throw err;
        }
      }
    }

    // Fallback Mock 데이터 반환
    return {
      sessionId: `session-${Math.random().toString(36).substr(2, 9)}`,
      article: {
        id: req.articleId ?? 'doc',
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

  /** 실시간 읽기 행동 이벤트 REST 배치 전송 (F1) */
  sendEvents: async (sessionId: string, events: any[]): Promise<any> => {
    console.log('[API] sendEvents Request:', { sessionId, eventsCount: events.length });
    const useMock = import.meta.env.VITE_USE_MOCK === 'true' || import.meta.env.VITE_USE_MOCK === true;
    if (useMock) {
      throw new Error('Forced Mock Mode by VITE_USE_MOCK');
    }

    const res = await fetch(`${BASE_URL}/api/session/${sessionId}/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, events }),
      keepalive: true,
    });
    if (res.ok) {
      const data = await res.json();
      return data;
    }
    throw new Error(`Events server returned status ${res.status}`);
  },

  finishSession: async (sessionId: string, scores: { literacy_score: number; comprehension_score: number; engagement_score: number }): Promise<any> => {
    console.log('[API] finishSession Request:', { sessionId, scores });
    const useMock = import.meta.env.VITE_USE_MOCK === 'true' || import.meta.env.VITE_USE_MOCK === true;
    if (!useMock) {
      try {
        const res = await fetch(`${BASE_URL}/api/session/${sessionId}/finish`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(scores),
          keepalive: true,
        });
        if (res.ok) {
          return await res.json();
        } else {
          throw new Error(`Server returned status ${res.status}`);
        }
      } catch (err) {
        console.error('[API] Failed to finishSession on server:', err);
        throw err;
      }
    }
    return { status: 'success' };
  },

  /** 세션 결과 조회 — Literacy Score + Recharts 데이터 */
  getSessionResult: async (sessionId: string): Promise<SessionResultResponse> => {
    console.log('[API] getSessionResult Request:', sessionId);
    const useMock = import.meta.env.VITE_USE_MOCK === 'true' || import.meta.env.VITE_USE_MOCK === true;

    if (!useMock) {
      try {
        const res = await fetch(`${BASE_URL}/api/session/${sessionId}/result`);
        if (res.ok) {
          const data = await res.json();
          return data;
        }
      } catch (err) {
        console.error('[API] Failed to getSessionResult from server:', err);
        if (import.meta.env.DEV) {
          throw err;
        }
      }
    }

    // Fallback Mock 데이터 반환 (실측 실패 시 무임승차 방지를 위해 0점 처리)
    return {
      sessionId,
      literacyScore: 0,
      comprehensionScore: 0,
      engagementScore: 0,
      difficultyBonus: 0,
      completionRate: 0,
      xpEarned: 0,
      totalXp: 0,
      level: 1,
      scoreSeries: [],
      badges: [],
      sessionDurationMs: 0,
    };
  },

  /** 퀴즈 정답 제출 */
  submitQuizAnswer: async (sessionId: string, quizId: string, selectedOption: string) => {
    console.log('[API] submitQuizAnswer Request:', { sessionId, quizId, selectedOption });
    const useMock = import.meta.env.VITE_USE_MOCK === 'true' || import.meta.env.VITE_USE_MOCK === true;

    if (!useMock) {
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
        console.error('[API] Failed to submitQuizAnswer to server:', err);
        if (import.meta.env.DEV) {
          throw err;
        }
      }
    }

    return { correct: true, explanation: '정답입니다! (mock 서버 오프라인)' };
  },

  /** 사용자 성장 보고서 조회 (weekly/monthly) */
  getGrowthReport: async (userId: string): Promise<GrowthReportResponse> => {
    console.log('[API] getGrowthReport Request:', userId);
    const useMock = import.meta.env.VITE_USE_MOCK === 'true' || import.meta.env.VITE_USE_MOCK === true;
    if (!useMock) {
      try {
        const res = await fetch(`${BASE_URL}/api/user/${userId}/growth`);
        if (res.ok) {
          const data = await res.json();
          return data;
        } else {
          throw new Error(`Server returned status ${res.status}`);
        }
      } catch (err) {
        console.error('[API] Failed to getGrowthReport from server:', err);
        throw err;
      }
    }
    return {
      weekly: {
        radarData: [
          { subject: '이해도', before: 62, after: 84 },
          { subject: '독해 속도', before: 55, after: 78 },
          { subject: '정독율', before: 70, after: 88 },
          { subject: '추론 능력', before: 65, after: 80 },
          { subject: '집중 유지', before: 60, after: 92 },
        ],
        activityData: [
          { label: '월', time: 15, xp: 120 },
          { label: '화', time: 22, xp: 180 },
          { label: '수', time: 12, xp: 90 },
          { label: '목', time: 28, xp: 240 },
          { label: '금', time: 18, xp: 150 },
          { label: '토', time: 35, xp: 320 },
          { label: '일', time: 42, xp: 380 },
        ],
        words: [
          { word: '인공지능 전환 (AX)', meaning: 'AI 기술을 도입해 기존의 비즈니스 구조를 근본적으로 바꾸는 과정.', level: '상', status: 'completed' },
          { word: '녹색 전환 (GX)', meaning: '친환경적이고 지속 가능한 비즈니스 모델로의 변화.', level: '중', status: 'completed' },
          { word: '카나리아 (Canary)', meaning: '탄광의 새처럼 위험을 미리 알려주는 조기 경보 체계나 지표.', level: '상', status: 'review' },
          { word: '리터러시 (Literacy)', meaning: '글이나 정보를 읽고 비판적으로 이해하는 능력.', level: '하', status: 'completed' },
        ],
        prescription: [
          "학습자의 이번 주 총 집중 독해 시간은 <strong class=\"text-[var(--color-primary)]\">164분</strong>으로, 지난주 대비 약 <strong>28% 증가</strong>했습니다.",
          "특히 'AI 기술과 일자리 변화' 같은 난도 높은 비문학 단락을 읽을 때 평균 체류(Dwell) 시간이 길어졌으나, 실시간으로 개입한 <strong class=\"text-[var(--color-nudge-soft)]\">Soft Nudge 용어 해설</strong>과 <strong class=\"text-[var(--color-nudge-medium)]\">간이 퀴즈</strong>를 거치며 독해 밸런스를 맞췄습니다. 결과적으로 <strong>어휘 능력 지표가 22점 상승</strong>하는 매우 긍정적인 성과를 냈습니다.",
          "<strong>💡 성장 챌린지:</strong> 다음 주에는 LLM, RAG 등 더 깊은 기술 원리를 다루는 지문에 도전해보세요. 단락 구조 파악(Structural scanning) 훈련을 병행하면 추론 속도가 더 빨라질 것입니다."
        ]
      },
      monthly: {
        radarData: [
          { subject: '이해도', before: 58, after: 89 },
          { subject: '독해 속도', before: 50, after: 82 },
          { subject: '정독율', before: 65, after: 91 },
          { subject: '추론 능력', before: 60, after: 85 },
          { subject: '집중 유지', before: 55, after: 94 },
        ],
        activityData: [
          { label: '1주차', time: 78, xp: 680 },
          { label: '2주차', time: 92, xp: 820 },
          { label: '3주차', time: 110, xp: 1020 },
          { label: '4주차', time: 145, xp: 1350 },
        ],
        words: [
          { word: '대규모 언어 모델 (LLM)', meaning: '방대한 텍스트 데이터를 학습하여 사람의 언어를 이해하고 생성하는 AI 모델.', level: '중', status: 'completed' },
          { word: '환각 현상 (Hallucination)', meaning: '인공지능이 사실이 아닌 거짓 정보를 진짜처럼 생성하는 현상.', level: '상', status: 'completed' },
          { word: '메타인지 (Metacognition)', meaning: '자신의 인지 과정을 스스로 파악하고 제어하는 상위 수준의 사고 능력.', level: '상', status: 'review' },
          { word: '가독성 (Readability)', meaning: '글이 읽히는 쉽고 명확한 정도.', level: '하', status: 'completed' },
        ],
        prescription: [
          "이번 달 총 집중 독해 시간은 <strong class=\"text-[var(--color-primary)]\">650분</strong>으로, 꾸준한 우상향 곡선을 그렸습니다.",
          "특히 월 중순부터 시작한 <strong>'기술 비문학 읽기 챌린지'</strong>를 통해 낯선 전문 용어(예: LLM, 환각 현상 등)를 문맥으로 추론하는 능력이 급성장했습니다. 이 과정에서 <strong class=\"text-[var(--color-nudge-soft)]\">개념 연결 넛지</strong>를 적극적으로 활용한 점이 주효했습니다.",
          "<strong>💡 다음 달 목표:</strong> 현재 91%인 정독율을 유지하면서, 글을 읽는 <strong>독해 속도(현재 82)를 끌어올리는 훈련</strong>을 추천합니다. 익숙한 주제의 글을 타이머를 켜두고 조금 빠르게 읽어보세요."
        ]
      }
    };
  },

  /** RAG 기반 어려운 용어/문장 AI 설명 조회 (1번 RAG 팀 고도화 연동) */
  getTermDefinition: async (sessionId: string, term: string, context?: string): Promise<{ explanation: string; source?: string }> => {
    console.log('[API] getTermDefinition Request:', { sessionId, term, context: context?.slice(0, 50) });
    try {
      // 1번 팀 RAG 고도화: POST /api/terms/lookup + context 필드 전송
      const res = await fetch(`${BASE_URL}/api/terms/lookup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          word: term,
          sessionId,
          context: context || null,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        // source가 not_found이면 조용히 null 반환 (프론트에서 무시)
        if (data.source === 'not_found' || !data.definition) {
          return { explanation: '', source: 'not_found' };
        }
        return {
          explanation: data.definition,
          source: data.source,
        };
      }
    } catch (err) {
      console.error('[API] Failed to getTermDefinition from server, falling back to mock:', err);
    }

    return { explanation: `[AI 주석] '${term}'은(는) 문맥상 중요한 개념으로, 독자의 문해력 향상을 위해 선별된 단어입니다.` };
  },

  /** 사용자 단어장의 단어 상태 업데이트 또는 삭제 */
  updateVocabStatus: async (userId: string, word: string, status: 'completed' | 'review' | 'deleted') => {
    console.log('[API] updateVocabStatus Request:', { userId, word, status });
    const useMock = import.meta.env.VITE_USE_MOCK === 'true' || import.meta.env.VITE_USE_MOCK === true;
    if (!useMock) {
      try {
        const res = await fetch(`${BASE_URL}/api/user/${userId}/vocab/update`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ word, status }),
        });
        if (res.ok) {
          return await res.json();
        }
      } catch (err) {
        console.error('[API] Failed to updateVocabStatus on server:', err);
      }
    }
    return { status: 'success' };
  },
};
