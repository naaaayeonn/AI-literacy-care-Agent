import { create } from 'zustand';

interface ScoreState {
  literacyScore: number;
  xp: number;
  level: number;
  addXp: (amount: number) => void;
  setLiteracyScore: (score: number) => void;
  reset: () => void;
}

export const useScoreStore = create<ScoreState>((set) => ({
  literacyScore: 0,
  xp: 0,
  level: 1,
  addXp: (amount) => set((state) => {
    const nextXp = state.xp + amount;
    const nextLevel = Math.floor(nextXp / 100) + 1;
    return { xp: nextXp, level: nextLevel };
  }),
  setLiteracyScore: (score) => set({ literacyScore: score }),
  reset: () => set({ literacyScore: 0, xp: 0, level: 1 }),
}));
