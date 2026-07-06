/**
 * focusStore — 집중도 & 넛지 상태
 * 7/6: ③서버 WebSocket 개입 명령으로부터 동적 퀴즈 데이터를 수신할 수 있도록 activeQuiz 필드 추가
 */
import { create } from 'zustand';
import type { QuizData } from '../lib/api';

export type NudgeLevel = 'none' | 'soft' | 'medium' | 'hard';

interface FocusState {
  focusScore: number;           // 0~100
  nudgeLevel: NudgeLevel;
  nudgeMessage: string | null;   // 7/6 추가: 서버가 보낸 커스텀 넛지 메시지
  isNudgeVisible: boolean;
  isQuizVisible: boolean;
  activeQuiz: QuizData | null;   // 7/6 추가: 서버가 전달한 실시간 퀴즈 데이터

  setFocusScore: (score: number) => void;
  setNudgeLevel: (level: NudgeLevel) => void;
  showNudge: (level: NudgeLevel, message?: string) => void;
  dismissNudge: () => void;
  showQuiz: () => void;
  dismissQuiz: () => void;
  setActiveQuiz: (quiz: QuizData | null) => void; // 7/6 추가: 퀴즈 주입
  reset: () => void;
}

export const useFocusStore = create<FocusState>((set) => ({
  focusScore: 85,
  nudgeLevel: 'none',
  nudgeMessage: null,
  isNudgeVisible: false,
  isQuizVisible: false,
  activeQuiz: null,

  setFocusScore: (focusScore) => set({ focusScore }),
  setNudgeLevel: (nudgeLevel) => set({ nudgeLevel }),
  showNudge: (level, message) => set({ nudgeLevel: level, isNudgeVisible: true, nudgeMessage: message || null }),
  dismissNudge: () => set({ isNudgeVisible: false, nudgeLevel: 'none', nudgeMessage: null }),
  showQuiz: () => set({ isQuizVisible: true }),
  dismissQuiz: () => set({ isQuizVisible: false }),
  setActiveQuiz: (activeQuiz) => set({ activeQuiz }),
  reset: () =>
    set({
      focusScore: 100,
      nudgeLevel: 'none',
      nudgeMessage: null,
      isNudgeVisible: false,
      isQuizVisible: false,
      activeQuiz: null,
    }),
}));
export default useFocusStore;
