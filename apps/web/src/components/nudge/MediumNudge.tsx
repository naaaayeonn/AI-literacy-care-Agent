/**
 * MediumNudge — 6/24 실구현
 * 2단계 개입: 주의 유도 + 요약 힌트 제공 (집중도 40~59%)
 * Framer Motion 우측에서 슬라이드인 + 배경 펄스 효과
 * 자동 소멸 없음 — 사용자가 직접 닫거나 퀴즈로 전환
 *
 * 사용처: NudgeController가 focusStore.nudgeLevel === 'medium' 일 때 렌더
 */
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useFocusStore } from '../../stores/focusStore';
import { useReadingStore } from '../../stores/readingStore';

interface MediumNudgeProps {
  message?: string;
  /** "퀴즈로 전환" 버튼 클릭 시 콜백 (없으면 숨김) */
  onEscalate?: () => void;
}

export const MediumNudge: React.FC<MediumNudgeProps> = ({ message, onEscalate }) => {
  const { isNudgeVisible, nudgeLevel, dismissNudge, showQuiz, setNudgeLevel, nudgeMessage, nudgeSummary } = useFocusStore();
  const isVisible = isNudgeVisible && nudgeLevel === 'medium';

  const handleEscalate = () => {
    // Medium → Hard + QuizCard 표시
    useReadingStore.getState().enqueueEvent({
      type: 'request_quiz',
      timestamp_ms: Date.now(),
      metadata: { requested_by: 'user_escalation' }
    });
    setNudgeLevel('hard');
    showQuiz();
    onEscalate?.();
  };

  const displayMessage =
    message ??
    nudgeMessage ??
    '집중도가 저하되고 있습니다. 지금까지 읽은 내용의 핵심을 한 번 짚어볼까요?';

  const renderSummary = () => {
    if (nudgeSummary) {
      // 요약 텍스트를 문장 단위나 줄바꿈 단위로 분리하여 리스트로 보여줍니다.
      const lines = nudgeSummary.split(/(?<=[다요했됩습])[.]\s*|\n+/).filter(s => s.trim().length > 0);
      if (lines.length > 0) {
        return (
          <ul style={{ margin: 0, paddingLeft: '1.2em', fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', fontFamily: 'var(--font-sans)', lineHeight: 'var(--leading-relaxed)' }}>
            {lines.map((line, idx) => (
              <li key={idx}>{line.trim()}{line.trim().endsWith('다') ? '.' : ''}</li>
            ))}
          </ul>
        );
      }
    }
    // 폴백 기본 목록
    return (
      <ul style={{ margin: 0, paddingLeft: '1.2em', fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', fontFamily: 'var(--font-sans)', lineHeight: 'var(--leading-relaxed)' }}>
        <li>디지털 리터러시는 단순 기술 사용을 넘어 비판적 사고력을 포함한다</li>
        <li>LLM의 환각 현상은 정보 신뢰성을 저해하는 핵심 위협 요인이다</li>
      </ul>
    );
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          key="medium-nudge"
          initial={{ opacity: 0, x: 40 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 40 }}
          transition={{ duration: 0.35, ease: [0.4, 0, 0.2, 1] }}
          style={{
            backgroundColor: 'var(--color-nudge-medium-tint)',
            border: '1px solid var(--color-nudge-medium)',
            borderLeft: '5px solid var(--color-nudge-medium)',
            borderRadius: '0 var(--radius-lg) var(--radius-lg) 0',
            padding: 'var(--space-5)',
            boxShadow: 'var(--shadow-md)',
          }}
          role="alert"
          aria-live="assertive"
        >
          {/* 헤더 행 */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              {/* 펄스 인디케이터 */}
              
              <span
                style={{
                  fontSize: 'var(--text-xs)',
                  fontWeight: 'var(--weight-semibold)' as unknown as number,
                  color: 'var(--color-nudge-medium)',
                  fontFamily: 'var(--font-sans)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                집중도 저하 감지
              </span>
            </div>
            <button
              onClick={dismissNudge}
              aria-label="알림 닫기"
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--color-text-muted)',
                fontSize: '14px',
                lineHeight: 1,
                padding: '2px',
              }}
            >
              ✕
            </button>
          </div>

          {/* 메시지 */}
          <p
            style={{
              fontSize: 'var(--text-sm)',
              color: 'var(--color-text)',
              fontFamily: 'var(--font-sans)',
              lineHeight: 'var(--leading-relaxed)',
              marginBottom: 'var(--space-4)',
            }}
          >
            {displayMessage}
          </p>

          {/* 빠른 요약 힌트 */}
          <div
            style={{
              backgroundColor: 'var(--color-surface)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-3)',
              marginBottom: 'var(--space-4)',
              border: '1px solid var(--color-border)',
            }}
          >
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', fontFamily: 'var(--font-sans)', marginBottom: '6px', fontWeight: 'var(--weight-semibold)' as unknown as number }}>
              📌 지금까지의 핵심 요약
            </p>
            {renderSummary()}
          </div>

          {/* 액션 버튼 */}
          <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
            <button
              onClick={dismissNudge}
              style={{
                flex: 1,
                padding: '8px 12px',
                fontSize: 'var(--text-xs)',
                fontFamily: 'var(--font-sans)',
                fontWeight: 'var(--weight-medium)' as unknown as number,
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--color-surface)',
                color: 'var(--color-text-secondary)',
                cursor: 'pointer',
                transition: 'background-color 0.2s',
              }}
            >
              계속 읽기
            </button>
            <button
              onClick={handleEscalate}
              style={{
                flex: 1,
                padding: '8px 12px',
                fontSize: 'var(--text-xs)',
                fontFamily: 'var(--font-sans)',
                fontWeight: 'var(--weight-semibold)' as unknown as number,
                border: 'none',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--color-nudge-medium)',
                color: '#fff',
                cursor: 'pointer',
                transition: 'opacity 0.2s',
              }}
              onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.opacity = '0.85')}
              onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.opacity = '1')}
            >
              이해도 퀴즈 풀기 →
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default MediumNudge;
