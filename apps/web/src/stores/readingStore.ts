/**
 * readingStore — 읽기 세션 상태
 * 6/22: mock 초기값 연결, scrollVelocity·dwellTime 필드 추가
 * 6/23: 스크롤 감지 훅에서 setProgress / setScrollVelocity 호출
 */
import { create } from 'zustand';
import { sampleArticle } from '../mock/sampleArticle';

interface ReadingState {
  // 세션 정보
  currentArticleId: string | null;
  sessionId: string | null;

  // 읽기 행동 지표
  progress: number;             // 0~100 (스크롤 위치 기반)
  scrollVelocity: number;       // px/s
  dwellTimeMs: number;          // 현재 단락 체류 시간(ms)
  gazeOutCount: number;         // 탭 블러 횟수
  readingStartedAt: number | null; // 읽기 시작 Unix ms

  // 하이라이트 범위 (6/23: ③서버 또는 규칙 기반)
  highlightedParagraphs: number[]; // 하이라이트할 단락 인덱스 배열
  termDefinitions: Record<string, string>; // AI RAG 용어 사전 캐시 (7/5 추가)
  showGlossesInline: boolean; // RAG AI 주석 본문 상시 표시 모드 (7/5 추가)

  // actions
  startSession: (articleId: string, sessionId: string) => void;
  setProgress: (progress: number) => void;
  setScrollVelocity: (velocity: number) => void;
  setDwellTime: (ms: number) => void;
  incrementGazeOut: () => void;
  setHighlights: (paragraphIndices: number[]) => void;
  setTermDefinition: (term: string, definition: string) => void;
  setTermDefinitions: (definitions: Record<string, string>) => void;
  toggleGlossesInline: () => void;
  reset: () => void;
}

export const useReadingStore = create<ReadingState>((set) => ({
  // 6/22: mock 초기값으로 사전 세팅 (더미 데이터 E2E)
  currentArticleId: sampleArticle.id,
  sessionId: 'mock-session-001',
  progress: 0,
  scrollVelocity: 0,
  dwellTimeMs: 0,
  gazeOutCount: 0,
  readingStartedAt: null,
  highlightedParagraphs: [0, 2], // 0번·2번 단락 하이라이트 (mock)
  termDefinitions: {},
  showGlossesInline: false,

  startSession: (articleId, sessionId) =>
    set({ currentArticleId: articleId, sessionId, readingStartedAt: Date.now(), progress: 0 }),
  setProgress: (progress) => set({ progress }),
  setScrollVelocity: (scrollVelocity) => set({ scrollVelocity }),
  setDwellTime: (dwellTimeMs) => set({ dwellTimeMs }),
  incrementGazeOut: () => set((s) => ({ gazeOutCount: s.gazeOutCount + 1 })),
  setHighlights: (highlightedParagraphs) => set({ highlightedParagraphs }),
  setTermDefinition: (term, definition) =>
    set((s) => ({ termDefinitions: { ...s.termDefinitions, [term]: definition } })),
  setTermDefinitions: (termDefinitions) => set({ termDefinitions }),
  toggleGlossesInline: () => set((s) => ({ showGlossesInline: !s.showGlossesInline })),
  reset: () =>
    set({
      currentArticleId: null,
      sessionId: null,
      progress: 0,
      scrollVelocity: 0,
      dwellTimeMs: 0,
      gazeOutCount: 0,
      readingStartedAt: null,
      highlightedParagraphs: [],
      termDefinitions: {},
      showGlossesInline: false,
    }),
}));
