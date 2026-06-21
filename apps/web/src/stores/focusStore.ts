import { create } from 'zustand';

interface FocusState {
  focusScore: number;
  isNudgeActive: boolean;
  setFocusScore: (score: number) => void;
  setNudgeActive: (active: boolean) => void;
  reset: () => void;
}

export const useFocusStore = create<FocusState>((set) => ({
  focusScore: 100,
  isNudgeActive: false,
  setFocusScore: (score) => set({ focusScore: score }),
  setNudgeActive: (active) => set({ isNudgeActive: active }),
  reset: () => set({ focusScore: 100, isNudgeActive: false }),
}));
