/**
 * scoreStore — Literacy Score & 게이미피케이션
 * 6/26: 실시간 Score Engine 연동을 위한 액션 추가
 *   - appendLivePoint(): 세션 진행 중 실시간 점수 포인트 추가
 *   - updateLiveScore(): 현재 세션의 최신 점수만 갱신 (마지막 포인트 덮어쓰기)
 *   - quizResults 누적 → comprehensionScore 자동 재계산
 */
import { create } from 'zustand';
import type { ScoreDataPoint, AcquiredBadge } from '../types/shared';

// ── 타입 ──────────────────────────────────────────────────────────────
export interface QuizResult {
  quizId: string;
  correct: boolean;
  xpAwarded: number;
  timestamp: number;
}

interface ScoreState {
  literacyScore: number;
  comprehensionScore: number;
  engagementScore: number;
  xp: number;
  level: number;
  levelProgress: number;
  scoreSeries: ScoreDataPoint[];  // 현재 세션 포인트 (라이브 차트용)
  weeklyScoreSeries: ScoreDataPoint[]; // 주간 요일 데이터 (대시보드 차트용)
  badges: AcquiredBadge[];
  isFinalized: boolean; // 세션 최종 서버 점수 갱신 후 가드용 플래그

  // 6/26 추가: 현재 세션 퀴즈 결과 목록
  quizResults: QuizResult[];

  // 기존 액션
  setLiteracyScore: (score: number, comprehension: number, engagement: number) => void;
  setFinalized: (finalized: boolean) => void; // 완료 플래그 액션
  addXp: (amount: number) => void;
  setScoreSeries: (series: ScoreDataPoint[]) => void;
  addBadge: (badge: AcquiredBadge) => void;

  // 6/26 신규 액션
  /** 세션 진행 중 실시간 포인트 추가 (세션 라이브 차트에 새 점 찍기) */
  appendLivePoint: (point: ScoreDataPoint) => void;
  /** 마지막 포인트를 갱신 (진행 중 덮어쓰기) */
  updateLiveScore: (after: number) => void;
  /** 주간 요일 차트용 데이터 업데이트 */
  updateWeeklyScore: (dayLabel: string, thisWeekScore: number, lastWeekScore?: number) => void;
  /** 퀴즈 결과 기록 → comprehensionScore 재계산 */
  recordQuizResult: (result: QuizResult) => void;

  restartDemoSession: () => void;
  reset: () => void;
}

// ── 레벨 계산 ─────────────────────────────────────────────────────────
const LEVEL_THRESHOLDS = [0, 100, 250, 500, 1000, 2000];

function calcLevel(xp: number): { level: number; progress: number } {
  let level = 1;
  for (let i = 1; i < LEVEL_THRESHOLDS.length; i++) {
    if (xp >= LEVEL_THRESHOLDS[i]) level = i + 1;
    else {
      const base = LEVEL_THRESHOLDS[i - 1];
      const next = LEVEL_THRESHOLDS[i];
      return { level, progress: Math.floor(((xp - base) / (next - base)) * 100) };
    }
  }
  return { level, progress: 100 };
}

/** 퀴즈 결과 목록 → comprehensionScore (0~100) */
function calcComprehension(results: QuizResult[]): number {
  if (results.length === 0) return 82; // mock 기본값
  const correct = results.filter((r) => r.correct).length;
  return Math.round((correct / results.length) * 100);
}

// ── Zustand Store ─────────────────────────────────────────────────────
export const useScoreStore = create<ScoreState>((set, get) => ({
  literacyScore: 0,
  comprehensionScore: 0,
  engagementScore: 0,
  xp: 0,
  level: 1,
  levelProgress: 0,
  scoreSeries: [],
  weeklyScoreSeries: [],
  badges: [],
  quizResults: [],
  isFinalized: false,

  // ── 기존 액션 ──
  setLiteracyScore: (literacyScore, comprehensionScore, engagementScore) =>
    set({ literacyScore, comprehensionScore, engagementScore }),

  setFinalized: (isFinalized) => set({ isFinalized }),

  addXp: (amount) =>
    set((s) => {
      const nextXp = s.xp + amount;
      const { level, progress } = calcLevel(nextXp);
      return { xp: nextXp, level, levelProgress: progress };
    }),

  setScoreSeries: (scoreSeries) => set({ scoreSeries }),

  addBadge: (badge) => set((s) => ({ badges: [...s.badges, badge] })),

  // ── 6/26 신규 액션 ──

  appendLivePoint: (point) =>
    set((s) => ({ scoreSeries: [...s.scoreSeries, point] })), // 세션 로직 복원 (누적)

  updateLiveScore: (after) =>
    set((s) => {
      if (s.scoreSeries.length === 0) return {};
      const updated = [...s.scoreSeries];
      const last = updated[updated.length - 1];
      updated[updated.length - 1] = { ...last, after };
      return { scoreSeries: updated };
    }),

  updateWeeklyScore: (dayLabel, thisWeek, lastWeek) =>
    set((s) => {
      const existingIdx = s.weeklyScoreSeries.findIndex(p => p.label === dayLabel);
      if (existingIdx >= 0) {
        const updated = [...s.weeklyScoreSeries];
        updated[existingIdx] = { ...updated[existingIdx], thisWeek, ...(lastWeek !== undefined && { lastWeek }) };
        return { weeklyScoreSeries: updated };
      }
      return { weeklyScoreSeries: [...s.weeklyScoreSeries, { label: dayLabel, thisWeek, lastWeek: lastWeek ?? 0 }] };
    }),

  recordQuizResult: (result) =>
    set((s) => {
      const newResults = [...s.quizResults, result];
      const comprehensionScore = calcComprehension(newResults);
      // 새 이해도 기반으로 literacyScore도 재계산
      const { engagementScore } = get();
      const newLiteracy = Math.round(
        comprehensionScore * 0.4 + engagementScore * 0.4 + 20 // 난이도 보정 +20 (mock)
      );
      return {
        quizResults: newResults,
        comprehensionScore,
        literacyScore: Math.min(100, newLiteracy),
      };
    }),

  restartDemoSession: () =>
    set({
      literacyScore: 0,
      comprehensionScore: 0,
      engagementScore: 0,
      xp: 0,
      level: 1,
      levelProgress: 0,
      scoreSeries: [], // 빈 배열로 초기화 (하드코딩 제거)
      weeklyScoreSeries: [],
      badges: [],
      quizResults: [],
      isFinalized: false,
    }),

  reset: () =>
    set({
      literacyScore: 0, comprehensionScore: 0, engagementScore: 0,
      xp: 0, level: 1, levelProgress: 0,
      scoreSeries: [], badges: [], quizResults: [],
      isFinalized: false,
    }),
}));
