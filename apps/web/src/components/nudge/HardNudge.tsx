/**
 * HardNudge — 6/25 실구현 (QuizCard 트리거 연동)
 * 3단계 개입: 읽기 화면 위에 오버레이 배너 + 즉시 QuizCard 표시
 * focusScore < 40 또는 gazeOutCount >= 3 일 때 NudgeController가 showNudge('hard') 호출
 *
 * 사용처: NudgeController → focusStore.nudgeLevel === 'hard' 일 때 렌더
 *          QuizCard는 isQuizVisible로 별도 렌더 (HardNudge와 동시에 표시됨)
 */
import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useFocusStore } from '../../stores/focusStore';

interface HardNudgeProps {
  message?: string;
}

export const HardNudge: React.FC<HardNudgeProps> = ({ message }) => {
  const { isNudgeVisible, nudgeLevel, dismissNudge, showQuiz, isQuizVisible, nudgeMessage } = useFocusStore();
  const isVisible = isNudgeVisible && nudgeLevel === 'hard';

  // HardNudge 등장 시 자동으로 QuizCard도 열기
  useEffect(() => {
    if (isVisible && !isQuizVisible) {
      // 약간의 딜레이 후 퀴즈 팝업 (HardNudge 애니메이션 완료 후)
      const timer = setTimeout(showQuiz, 500);
      return () => clearTimeout(timer);
    }
  }, [isVisible, isQuizVisible, showQuiz]);

  const displayMessage =
    message ??
    nudgeMessage ??
    '집중도가 심각하게 저하되었습니다. 퀴즈를 완료해야 읽기를 계속할 수 있습니다.';

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          key="hard-nudge"
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -12 }}
          transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
          style={{
            position: 'sticky',
            top: 0,
            zIndex: 'calc(var(--z-panel) + 1)' as unknown as number,
            backgroundColor: 'var(--color-nudge-hard-tint)',
            borderBottom: '3px solid var(--color-nudge-hard)',
            padding: 'var(--space-3) var(--space-5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 'var(--space-4)',
          }}
          role="alert"
          aria-live="assertive"
          aria-atomic="true"
        >
          {/* 왼쪽: 아이콘 + 메시지 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            {/* 경고 펄스 */}
            <motion.div
              animate={{ scale: [1, 1.2, 1], opacity: [1, 0.7, 1] }}
              transition={{ repeat: Infinity, duration: 1.5 }}
              style={{ fontSize: '22px', lineHeight: 1 }}
            >
              🚨
            </motion.div>
            <div>
              <p
                style={{
                  fontSize: 'var(--text-xs)',
                  fontWeight: 'var(--weight-bold)' as unknown as number,
                  color: 'var(--color-nudge-hard)',
                  fontFamily: 'var(--font-sans)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  marginBottom: '2px',
                }}
              >
                리딩 락다운 — 집중도 위험
              </p>
              <p
                style={{
                  fontSize: 'var(--text-sm)',
                  color: 'var(--color-text)',
                  fontFamily: 'var(--font-sans)',
                }}
              >
                {displayMessage}
              </p>
            </div>
          </div>

          {/* 오른쪽: 액션 버튼 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', flexShrink: 0 }}>
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={showQuiz}
              style={{
                padding: '6px 14px',
                fontSize: 'var(--text-xs)',
                fontFamily: 'var(--font-sans)',
                fontWeight: 'var(--weight-semibold)' as unknown as number,
                borderRadius: 'var(--radius-md)',
                border: 'none',
                backgroundColor: 'var(--color-nudge-hard)',
                color: '#fff',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              퀴즈로 해제 →
            </motion.button>
            <button
              onClick={dismissNudge}
              aria-label="닫기"
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--color-text-muted)',
                fontSize: '16px',
                padding: '4px',
                lineHeight: 1,
              }}
            >
              ✕
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default HardNudge;
