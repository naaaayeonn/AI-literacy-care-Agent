/**
 * useScoreEngine — 6/26 실시간 Literacy Score 계산 엔진
 *
 * 읽기 진행 중 focusScore + progress + quizResults를 실시간으로 합산해
 * scoreStore의 literacyScore · engagementScore · scoreSeries를 업데이트한다.
 *
 * [Literacy Score 계산식 — 6/26 프론트 버전]
 *   engagement = focusScore × (progress / 100)           // 집중 유지율
 *   comprehension = calcComprehension(quizResults)        // 퀴즈 정답률
 *   difficultyBonus = 0.6 × 20 = 12                      // 기사 난이도 0.6 (mock)
 *   literacyScore = engagement×0.4 + comprehension×0.4 + difficultyBonus
 *
 * NOTE: 이 공식은 ①번 오케스트레이터 확정 전 프론트 자체 버전.
 *       ①번 Score Engine 결과가 API로 수신되면 setLiteracyScore()로 덮어쓴다.
 *
 * 사용 위치: ReadingPage에 마운트 (읽기 세션 동안 실행)
 *
 * TODO 7/6: ①번 REST API getSessionResult() 호출로 최종 점수 교체
 */
import { useEffect, useRef } from 'react';
import { useReadingStore } from '../stores/readingStore';
import { useFocusStore } from '../stores/focusStore';
import { useScoreStore } from '../stores/scoreStore';
import type { ScoreDataPoint } from '../types/shared';

const ARTICLE_DIFFICULTY = 0.6; // mock 난이도 계수

/** progress 구간 → 차트 label 변환 */
function progressToLabel(progress: number): string {
  if (progress < 25) return '읽기 시작';
  if (progress < 50) return '1/4 지점';
  if (progress < 75) return '절반';
  if (progress < 90) return '3/4 지점';
  return '완독';
}

/** 진행 구간 체크 (25/50/75/90/100 통과 시 새 포인트 찍기) */
const MILESTONES = [25, 50, 75, 90, 100];

export function useScoreEngine() {
  const { progress, scrollVelocity } = useReadingStore();
  const { focusScore } = useFocusStore();
  const {
    appendLivePoint,
    updateLiveScore,
    setLiteracyScore,
    quizResults,
    isFinalized,
  } = useScoreStore();

  const passedMilestones = useRef<Set<number>>(new Set());
  const sessionBaseline = useRef<number>(50); // "케어 미적용" 가상 기준선

  // ── 실시간 점수 계산 ──────────────────────────────────────────────
  const calcLiveScores = () => {
    // 집중도 기반 engagement: 스크롤 속도가 느릴수록 가중치 높음
    const velocityPenalty = Math.min(20, Math.floor(scrollVelocity / 30));
    const rawEngagement = Math.max(0, focusScore - velocityPenalty);

    // 이해도: 퀴즈 결과 기반 (퀴즈 없으면 focusScore × 0.9)
    const comprehension =
      quizResults.length > 0
        ? Math.round(
            (quizResults.filter((r) => r.correct).length / quizResults.length) * 100
          )
        : Math.round(focusScore * 0.9);

    const difficultyBonus = Math.round(ARTICLE_DIFFICULTY * 20);
    const literacy = Math.min(
      100,
      Math.round(rawEngagement * 0.4 + comprehension * 0.4 + difficultyBonus)
    );

    return { engagement: rawEngagement, comprehension, literacy };
  };

  // ── 마일스톤 도달 시 차트에 새 포인트 추가 ────────────────────────
  useEffect(() => {
    if (isFinalized) return;
    const milestone = MILESTONES.find(
      (m) => progress >= m && !passedMilestones.current.has(m)
    );
    if (!milestone) return;

    passedMilestones.current.add(milestone);

    const { literacy } = calcLiveScores();

    // "케어 미적용" 가상선: 기준선에서 소폭 변동 (실제로는 ①번이 제공)
    const baselineNoise = Math.floor(Math.random() * 6) - 3;
    const before = Math.max(30, sessionBaseline.current + baselineNoise);

    const newPoint: ScoreDataPoint = {
      label: progressToLabel(milestone),
      before,
      after: literacy,
    };

    appendLivePoint(newPoint);

    // 마지막 포인트에서 literacyScore 스토어도 업데이트 및 세션 완료 상태 확정
    if (milestone === 100) {
      setLiteracyScore(literacy, calcLiveScores().comprehension, calcLiveScores().engagement);
      useScoreStore.setState({ isFinalized: true });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [progress, isFinalized]);

  // ── 퀴즈 결과 변경 → 현재 세션 마지막 포인트 실시간 갱신 ──────────
  useEffect(() => {
    if (isFinalized) return;
    if (quizResults.length === 0) return;
    const { literacy } = calcLiveScores();
    updateLiveScore(literacy);
    // engagementScore도 최신값으로
    setLiteracyScore(literacy, calcLiveScores().comprehension, calcLiveScores().engagement);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [quizResults, isFinalized]);

  // ── 집중도 변화 → engagementScore 실시간 반영 ──────────────────────
  useEffect(() => {
    if (isFinalized) return;
    const { engagement, comprehension, literacy } = calcLiveScores();
    // engagementScore는 즉시 반영 (그래프는 마일스톤만)
    setLiteracyScore(literacy, comprehension, engagement);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusScore, isFinalized]);
}
