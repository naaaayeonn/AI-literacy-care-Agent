import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import useFocusStore from '../../stores/focusStore';
import { useScoreStore } from '../../stores/scoreStore';
import { useReadingStore } from '../../stores/readingStore';
import { api } from '../../lib/api';
import type { QuizData } from '../../lib/api';

// ── 상태 타입 ──────────────────────────────────────────────────────
type QuizPhase = 'answering' | 'completed' | 'timeout';

interface AnswerState {
  selectedIndex: number;
  isCorrect: boolean;
  explanation: string | null;
  revealCorrectIndex: number;
}

// ── 메인 컴포넌트 ────────────────────────────────────────────────────
export const QuizCard: React.FC = () => {
  const { isQuizVisible, dismissQuiz, setFocusScore, focusScore, dismissNudge, activeQuizzes, setActiveQuizzes } = useFocusStore();
  const { addXp, recordQuizResult } = useScoreStore();
  const { sessionId } = useReadingStore();

  const currentQuizzes = useMemo<QuizData[] | null>(() => {
    return activeQuizzes && activeQuizzes.length > 0 ? activeQuizzes : null;
  }, [activeQuizzes]);

  const [phase, setPhase] = useState<QuizPhase>('answering');
  const [answers, setAnswers] = useState<Record<string, AnswerState>>({});
  const [timeLeft, setTimeLeft] = useState(30); // 30초 타이머

  // 모든 퀴즈를 풀었는지 확인
  const allAnswered = currentQuizzes && Object.keys(answers).length === currentQuizzes.length;

  useEffect(() => {
    if (allAnswered && phase === 'answering') {
      setPhase('completed');
    }
  }, [allAnswered, phase]);

  // 타이머
  useEffect(() => {
    if (!isQuizVisible || phase !== 'answering' || !currentQuizzes) return;
    if (timeLeft <= 0) {
      setPhase('timeout');
      return;
    }
    const timer = setTimeout(() => setTimeLeft((t) => t - 1), 1000);
    return () => clearTimeout(timer);
  }, [isQuizVisible, phase, timeLeft, currentQuizzes]);

  const handleSelect = useCallback(
    async (quiz: QuizData, index: number) => {
      if (phase !== 'answering' || answers[quiz.quizId]) return;

      // 옵티미스틱 업데이트 (로딩 상태)
      setAnswers(prev => ({
        ...prev,
        [quiz.quizId]: { selectedIndex: index, isCorrect: false, explanation: null, revealCorrectIndex: -1 }
      }));

      let isCorrect: boolean;
      let explanationFromServer: string | null = null;
      try {
        const res = await api.submitQuizAnswer(sessionId || '', quiz.quizId, quiz.options[index]);
        isCorrect = !!(res && res.correct);
        if (res && typeof res.explanation === 'string') explanationFromServer = res.explanation;
      } catch (err) {
        console.error('[API] Failed to submit quiz answer:', err);
        // Fallback: assume O/X correctness based on local (though answer is not in payload usually, just guess true for UX fallback)
        isCorrect = index === 0;
      }

      const resolvedCorrectIdx = quiz.options.length === 2 ? (isCorrect ? index : 1 - index) : 0;
      const xpReward = 10; // 짧은 문제당 10 XP

      setAnswers(prev => ({
        ...prev,
        [quiz.quizId]: {
          selectedIndex: index,
          isCorrect,
          explanation: explanationFromServer || quiz.explanation || (isCorrect ? '정답입니다!' : '오답입니다.'),
          revealCorrectIndex: resolvedCorrectIdx
        }
      }));

      if (isCorrect) {
        addXp(xpReward);
        setFocusScore(Math.min(100, focusScore + 5)); // 문제당 5점 회복
      }
      
      recordQuizResult({
        quizId: quiz.quizId,
        correct: isCorrect,
        xpAwarded: isCorrect ? xpReward : 0,
        timestamp: Date.now(),
      });
    },
    [phase, answers, addXp, setFocusScore, focusScore, recordQuizResult, sessionId]
  );

  const handleClose = useCallback(() => {
    dismissQuiz();
    dismissNudge();
    setActiveQuizzes(null);
    setPhase('answering');
    setAnswers({});
    setTimeLeft(30);
  }, [dismissQuiz, dismissNudge, setActiveQuizzes]);

  const timerPercent = (timeLeft / 30) * 100;
  const timerColor =
    timeLeft > 15 ? 'var(--color-engagement)' : timeLeft > 7 ? 'var(--color-xp)' : 'var(--color-nudge-hard)';

  const totalEarnedXp = currentQuizzes ? currentQuizzes.reduce((acc, q) => acc + (answers[q.quizId]?.isCorrect ? 10 : 0), 0) : 0;

  return (
    <AnimatePresence>
      {isQuizVisible && (
        <>
          <motion.div
            key="quiz-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            onClick={phase !== 'answering' ? handleClose : undefined}
            style={{
              position: 'fixed',
              inset: 0,
              backgroundColor: 'rgba(42,39,36,0.4)',
              backdropFilter: 'blur(4px)',
              zIndex: 'calc(var(--z-quiz) - 1)' as unknown as number,
            }}
          />

          <motion.div
            key="quiz-card"
            initial={{ opacity: 0, scale: 0.88, y: 24 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.92, y: 16 }}
            transition={{ duration: 0.32, ease: [0.34, 1.56, 0.64, 1] }}
            style={{
              position: 'fixed',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: '100%',
              maxWidth: '520px',
              zIndex: 'var(--z-quiz)' as unknown as number,
              padding: '0 16px',
            }}
          >
            <div
              style={{
                backgroundColor: 'var(--color-surface)',
                borderRadius: 'var(--radius-xl)',
                border: '1px solid var(--color-border)',
                boxShadow: 'var(--shadow-lg)',
                overflow: 'hidden',
                fontFamily: 'var(--font-sans)',
                display: 'flex',
                flexDirection: 'column',
                maxHeight: '85vh',
              }}
            >
              <div style={{ height: '4px', backgroundColor: 'var(--color-surface-alt)' }}>
                <motion.div
                  style={{
                    height: '100%',
                    backgroundColor: timerColor,
                    transition: 'background-color 0.3s',
                  }}
                  animate={{ width: `${timerPercent}%` }}
                  transition={{ duration: 0.5, ease: 'linear' }}
                />
              </div>

              <div style={{ padding: 'var(--space-6)', overflowY: 'auto', flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-5)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                    <span
                      style={{
                        display: 'inline-block',
                        padding: '4px 12px',
                        backgroundColor: 'var(--color-primary-tint)',
                        color: 'var(--color-primary)',
                        borderRadius: 'var(--radius-full)',
                        fontSize: 'var(--text-xs)',
                        fontWeight: 'var(--weight-semibold)' as unknown as number,
                      }}
                    >
                      집중 퀴즈 타임!
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: 'var(--text-sm)', color: timerColor, fontVariantNumeric: 'tabular-nums', fontWeight: 'var(--weight-semibold)' as unknown as number }}>
                    {timeLeft}초
                  </div>
                </div>

                {!currentQuizzes ? (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 'var(--space-8) 0', color: 'var(--color-text-muted)', fontSize: 'var(--text-sm)', gap: 'var(--space-3)' }}>
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      style={{
                        width: '28px',
                        height: '28px',
                        border: '3px solid var(--color-surface-alt)',
                        borderTop: '3px solid var(--color-primary)',
                        borderRadius: '50%',
                      }}
                    />
                    퀴즈를 실시간으로 생성 중입니다...
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                    {currentQuizzes.map((quiz, qIndex) => {
                      const ansState = answers[quiz.quizId];
                      const isAnswered = !!ansState && ansState.revealCorrectIndex !== -1;
                      
                      return (
                        <div key={quiz.quizId} style={{ 
                          padding: 'var(--space-4)', 
                          backgroundColor: 'var(--color-surface-alt)', 
                          borderRadius: 'var(--radius-lg)',
                          border: isAnswered ? (ansState.isCorrect ? '1px solid var(--color-growth)' : '1px solid var(--color-nudge-medium)') : '1px solid transparent',
                          transition: 'border 0.3s'
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 'var(--space-4)' }}>
                            <div style={{ flex: 1 }}>
                              <p style={{ 
                                fontSize: 'var(--text-sm)', 
                                color: 'var(--color-text)', 
                                lineHeight: '1.5',
                                fontWeight: 'var(--weight-medium)' as unknown as number,
                                margin: 0,
                                marginBottom: isAnswered ? 'var(--space-2)' : 0
                              }}>
                                <span style={{ color: 'var(--color-text-muted)', marginRight: '6px' }}>Q{qIndex + 1}.</span>
                                {quiz.question}
                              </p>
                              {isAnswered && (
                                <motion.p 
                                  initial={{ opacity: 0, height: 0 }}
                                  animate={{ opacity: 1, height: 'auto' }}
                                  style={{ 
                                    fontSize: 'var(--text-xs)', 
                                    color: ansState.isCorrect ? 'var(--color-growth)' : 'var(--color-nudge-medium)',
                                    margin: 0,
                                    marginTop: '8px'
                                  }}
                                >
                                  {ansState.isCorrect ? '정답입니다!' : '오답입니다.'} {ansState.explanation && <span style={{ color: 'var(--color-text-muted)' }}>- {ansState.explanation}</span>}
                                </motion.p>
                              )}
                            </div>
                            
                            <div style={{ display: 'flex', gap: '8px', flexShrink: 0 }}>
                              {quiz.options.map((option, idx) => {
                                const isO = option === 'O' || option === '맞다';
                                const emoji = isO ? '⭕' : '❌';
                                const isSelected = ansState?.selectedIndex === idx;
                                const isCorrectOption = ansState?.revealCorrectIndex === idx;
                                
                                let bg = '#fff';
                                let border = 'var(--color-border)';
                                let color = isO ? 'var(--color-primary)' : 'var(--color-nudge-medium)';
                                
                                if (isAnswered) {
                                  if (isCorrectOption) {
                                    bg = 'var(--color-growth-tint)'; border = 'var(--color-growth)'; color = 'var(--color-text)';
                                  } else if (isSelected) {
                                    bg = 'var(--color-nudge-medium-tint)'; border = 'var(--color-nudge-medium)'; color = 'var(--color-text)';
                                  } else {
                                    color = 'var(--color-text-muted)';
                                  }
                                } else if (isSelected) {
                                  bg = 'var(--color-surface-alt)'; // Loading state
                                }

                                return (
                                  <button
                                    key={idx}
                                    onClick={() => handleSelect(quiz, idx)}
                                    disabled={isAnswered || phase !== 'answering'}
                                    style={{
                                      width: '44px',
                                      height: '44px',
                                      display: 'flex',
                                      alignItems: 'center',
                                      justifyContent: 'center',
                                      fontSize: '1.2rem',
                                      borderRadius: 'var(--radius-md)',
                                      border: `1.5px solid ${border}`,
                                      backgroundColor: bg,
                                      color: color,
                                      cursor: (!isAnswered && phase === 'answering') ? 'pointer' : 'default',
                                      transition: 'all 0.2s, transform 0.1s',
                                      transform: isSelected ? 'scale(0.95)' : 'scale(1)',
                                    }}
                                    onMouseEnter={(e) => {
                                      if (!isAnswered && phase === 'answering') e.currentTarget.style.transform = 'scale(1.05)';
                                    }}
                                    onMouseLeave={(e) => {
                                      if (!isAnswered && phase === 'answering') e.currentTarget.style.transform = isSelected ? 'scale(0.95)' : 'scale(1)';
                                    }}
                                    onMouseDown={(e) => {
                                      if (!isAnswered && phase === 'answering') e.currentTarget.style.transform = 'scale(0.95)';
                                    }}
                                    onMouseUp={(e) => {
                                      if (!isAnswered && phase === 'answering') e.currentTarget.style.transform = 'scale(1.05)';
                                    }}
                                  >
                                    {emoji}
                                  </button>
                                );
                              })}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                <AnimatePresence>
                  {phase !== 'answering' && (
                    <motion.div
                      key="feedback"
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.3 }}
                      style={{ marginTop: 'var(--space-5)' }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
                        <span style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-semibold)' as unknown as number, color: 'var(--color-text)' }}>
                          {phase === 'timeout' ? '시간 초과!' : '퀴즈 완료'}
                        </span>
                        <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-growth)', fontWeight: 'var(--weight-bold)' as unknown as number }}>
                          총 +{totalEarnedXp} XP 획득
                        </span>
                      </div>

                      <button
                        onClick={handleClose}
                        style={{
                          width: '100%',
                          padding: 'var(--space-3)',
                          fontSize: 'var(--text-sm)',
                          fontFamily: 'var(--font-sans)',
                          fontWeight: 'var(--weight-semibold)' as unknown as number,
                          borderRadius: 'var(--radius-md)',
                          border: 'none',
                          backgroundColor: 'var(--color-engagement)',
                          color: '#fff',
                          cursor: 'pointer',
                        }}
                      >
                        계속 읽기
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default QuizCard;
