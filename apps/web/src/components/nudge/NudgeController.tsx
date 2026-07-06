/**
 * NudgeController — 6/24 신규 생성 (폐루프 핵심)
 *
 * focusScore를 구독해 nudgeLevel을 자동으로 결정하고,
 * 적절한 Nudge 컴포넌트 + QuizCard를 조건부 렌더링한다.
 *
 * [집중도 → 개입 단계 매핑]
 *   focusScore >= 80  → none   (개입 없음)
 *   focusScore 60~79  → soft   (SoftNudge: 가벼운 환기)
 *   focusScore 40~59  → medium (MediumNudge: 요약 힌트 + 퀴즈 권유)
 *   focusScore < 40   → hard   (HardNudge + QuizCard: 락다운)
 *
 * 데모 시연 시: 우측 패널 하단 [집중도 시뮬] 버튼으로 focusScore를 직접 낮출 수 있음.
 * (NudgeController는 ReadingPage 안에 배치)
 *
 * TODO 7/6: ③번 WebSocket InterventionCommand에서 nudgeLevel 수신 시 직접 setNudgeLevel 호출
 */
import React, { useEffect, useRef } from 'react';
import { useFocusStore } from '../../stores/focusStore';
import SoftNudge from '../nudge/SoftNudge';
import MediumNudge from '../nudge/MediumNudge';
import HardNudge from '../nudge/HardNudge';
import QuizCard from '../quiz/QuizCard';
import { getActiveWsClient } from '../../lib/ws';

/** focusScore → nudgeLevel 변환 */
function scoreToNudgeLevel(score: number): 'none' | 'soft' | 'medium' | 'hard' {
  if (score >= 80) return 'none';
  if (score >= 60) return 'soft';
  if (score >= 40) return 'medium';
  return 'hard';
}

export const NudgeController: React.FC = () => {
  const { focusScore, showNudge, dismissNudge, isNudgeVisible } = useFocusStore();
  const prevLevel = useRef<string>('none');

  useEffect(() => {
    // 7/6 추가: WebSocket이 활성화 및 연결된 상태라면 서버의 개입 명령이 상태를 제어하므로
    // 로컬에서의 자동 집중도 기반 넛지 판단은 바이패스(우회)합니다.
    const wsClient = getActiveWsClient();
    if (wsClient && wsClient.isConnected()) {
      return;
    }

    const newLevel = scoreToNudgeLevel(focusScore);

    // 레벨이 상승할 때만 Nudge 표시 (회복 중에는 재트리거 안 함)
    if (newLevel !== 'none' && newLevel !== prevLevel.current) {
      showNudge(newLevel as 'soft' | 'medium' | 'hard');
    }

    // 집중도가 80 이상 회복되면 Nudge 자동 해제
    if (newLevel === 'none' && isNudgeVisible) {
      dismissNudge();
    }

    prevLevel.current = newLevel;
  }, [focusScore, showNudge, dismissNudge, isNudgeVisible]);

  // nudgeLevel은 focusStore에서 관리되므로 여기서는 렌더만 담당
  return (
    <>
      {/* 3단계 Nudge — focusStore.nudgeLevel 기반 AnimatePresence 내부에서 처리 */}
      <SoftNudge />
      <MediumNudge />
      <HardNudge />

      {/* QuizCard — focusStore.isQuizVisible 구독 (portal-like 고정 팝업) */}
      <QuizCard />
    </>
  );
};

export default NudgeController;
