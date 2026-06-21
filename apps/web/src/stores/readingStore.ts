import { create } from 'zustand';

interface ReadingState {
  currentArticleId: string | null;
  progress: number;
  setArticleId: (id: string | null) => void;
  setProgress: (progress: number) => void;
  reset: () => void;
}

export const useReadingStore = create<ReadingState>((set) => ({
  currentArticleId: null,
  progress: 0,
  setArticleId: (id) => set({ currentArticleId: id }),
  setProgress: (progress) => set({ progress }),
  reset: () => set({ currentArticleId: null, progress: 0 }),
}));
