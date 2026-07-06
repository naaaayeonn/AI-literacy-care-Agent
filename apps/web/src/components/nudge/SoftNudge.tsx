/**
 * SoftNudge — 6/24 실구현
 * 1단계 개입: 가벼운 시각적 환기 (집중도 60~79%)
 * Framer Motion으로 아래에서 슬라이드업 등장 + 자동 소멸(8초)
 *
 * 사용처: NudgeController가 focusStore.nudgeLevel === 'soft' 일 때 렌더
 */
import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useFocusStore } from '../../stores/focusStore';

interface SoftNudgeProps {
  /** 외부에서 직접 메시지를 주입할 때 사용 (데모·테스트용) */
  message?: string;
  /** 자동 닫힘 딜레이(ms). 기본 8000ms */
  autoDismissMs?: number;
}

export const SoftNudge: React.FC<SoftNudgeProps> = ({
  message,
  autoDismissMs = 8000,
}) => {
  const { isNudgeVisible, nudgeLevel, dismissNudge, nudgeMessage } = useFocusStore();
  const isVisible = isNudgeVisible && nudgeLevel === 'soft';

  // 자동 소멸
  useEffect(() => {
    if (!isVisible) return;
    const timer = setTimeout(dismissNudge, autoDismissMs);
    return () => clearTimeout(timer);
  }, [isVisible, autoDismissMs, dismissNudge]);

  const displayMessage =
    message ??
    nudgeMessage ??
    '스크롤 속도가 평균보다 빠릅니다. 이 단락의 핵심 내용을 놓치지 않도록 잠깐 되짚어볼까요?';

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          key="soft-nudge"
          initial={{ opacity: 0, y: 16, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 8, scale: 0.97 }}
          transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
          style={{
            backgroundColor: 'var(--color-nudge-soft-tint)',
            borderLeft: '4px solid var(--color-nudge-soft)',
            borderRadius: '0 var(--radius-md) var(--radius-md) 0',
            padding: 'var(--space-4)',
            display: 'flex',
            alignItems: 'flex-start',
            gap: 'var(--space-3)',
          }}
          role="status"
          aria-live="polite"
        >
          {/* 아이콘 */}
          <span style={{ fontSize: '20px', lineHeight: 1, flexShrink: 0, marginTop: '1px' }}>💡</span>

          {/* 본문 */}
          <div style={{ flex: 1 }}>
            <p
              style={{
                fontSize: 'var(--text-xs)',
                fontWeight: 'var(--weight-semibold)' as unknown as number,
                color: 'var(--color-nudge-soft)',
                fontFamily: 'var(--font-sans)',
                marginBottom: '4px',
              }}
            >
              리터러시 케어 — 가벼운 알림
            </p>
            <p
              style={{
                fontSize: 'var(--text-sm)',
                color: 'var(--color-text)',
                fontFamily: 'var(--font-sans)',
                lineHeight: 'var(--leading-normal)',
              }}
            >
              {displayMessage}
            </p>
          </div>

          {/* 닫기 버튼 */}
          <button
            onClick={dismissNudge}
            aria-label="알림 닫기"
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--color-text-muted)',
              fontSize: '16px',
              padding: '2px',
              lineHeight: 1,
              flexShrink: 0,
              transition: 'color 0.2s',
            }}
            onMouseEnter={(e) => ((e.target as HTMLElement).style.color = 'var(--color-text)')}
            onMouseLeave={(e) => ((e.target as HTMLElement).style.color = 'var(--color-text-muted)')}
          >
            ✕
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default SoftNudge;
