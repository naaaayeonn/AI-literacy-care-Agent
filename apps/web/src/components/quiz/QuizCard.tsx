/**
 * QuizCard — 6/25 완전 구현
 *
 * [구현된 기능]
 * - Framer Motion 스케일업 팝업 + 오버레이 블러 배경
 * - 선택지 클릭 → 정답/오답 즉시 피드백 (초록/빨강 하이라이트)
 * - 정답 시: XP 지급 + 집중도 회복 (+15점) + 넛지 해제
 * - 오답 시: 해설 표시, 재시도 없음 (점수는 0XP)
 * - 타이머 바 (30초 제한)
 * - focusStore.isQuizVisible 구독 → 조건부 렌더
 *
 * TODO 7/6: api.submitQuizAnswer() 실제 서버 검증 연동
 */
import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useFocusStore } from '../../stores/focusStore';
import { useScoreStore } from '../../stores/scoreStore';

// ── 퀴즈 데이터 (TODO 7/6: ①번 quizActive + currentQuiz store에서 수신) ──
interface QuizQuestion {
  id: string;
  question: string;
  options: string[];
  correctIndex: number;
  explanation: string;
  xpReward: number;
}

const MOCK_QUIZZES: QuizQuestion[] = [
  {
    id: 'q-001',
    question: '본문에서 설명한 "디지털 리터러시"에 해당하지 않는 것은?',
    options: [
      '온라인 정보의 출처를 비판적으로 평가하는 능력',
      '스마트폰 앱을 빠르게 설치하는 기술 숙련도',
      'AI가 생성한 콘텐츠의 신뢰성을 판별하는 역량',
      '디지털 환경에서 정보를 윤리적으로 활용하는 태도',
    ],
    correctIndex: 1,
    explanation: '디지털 리터러시는 단순한 기술 사용 능력이 아니라 정보를 비판적으로 읽고, 평가하고, 윤리적으로 활용하는 복합적 역량입니다.',
    xpReward: 30,
  },
  {
    id: 'q-002',
    question: 'LLM의 "환각 현상(Hallucination)"이 문해력 교육에서 위험한 이유로 가장 적절한 것은?',
    options: [
      'AI가 응답 속도가 느려져 사용자를 불편하게 만들기 때문이다',
      '그럴듯하지만 틀린 정보를 사실처럼 제공해 독자의 판단을 왜곡하기 때문이다',
      'AI가 어려운 어휘를 사용하여 독자의 이해를 방해하기 때문이다',
      'AI 응답이 너무 길어 핵심 내용을 파악하기 어렵기 때문이다',
    ],
    correctIndex: 1,
    explanation: '환각 현상은 AI가 실제로 없는 정보를 있는 것처럼 자신 있게 제시하여, 독자가 잘못된 정보를 사실로 받아들이게 만드는 것이 핵심 위험입니다.',
    xpReward: 30,
  },
];

// ── 상태 타입 ──────────────────────────────────────────────────────
type QuizPhase = 'answering' | 'correct' | 'incorrect';

// ── 메인 컴포넌트 ────────────────────────────────────────────────────
export const QuizCard: React.FC = () => {
  const { isQuizVisible, dismissQuiz, setFocusScore, focusScore, dismissNudge } = useFocusStore();
  const { addXp, recordQuizResult } = useScoreStore();

  const [currentQuiz] = useState<QuizQuestion>(
    () => MOCK_QUIZZES[Math.floor(Math.random() * MOCK_QUIZZES.length)]
  );
  const [phase, setPhase] = useState<QuizPhase>('answering');
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [timeLeft, setTimeLeft] = useState(30); // 30초 타이머

  // 타이머
  useEffect(() => {
    if (!isQuizVisible || phase !== 'answering') return;
    if (timeLeft <= 0) {
      setPhase('incorrect');
      setSelectedIndex(-1); // 시간 초과
      return;
    }
    const timer = setTimeout(() => setTimeLeft((t) => t - 1), 1000);
    return () => clearTimeout(timer);
  }, [isQuizVisible, phase, timeLeft]);

  const handleSelect = useCallback(
    (index: number) => {
      if (phase !== 'answering') return;
      setSelectedIndex(index);
      const isCorrect = index === currentQuiz.correctIndex;
      setPhase(isCorrect ? 'correct' : 'incorrect');

      if (isCorrect) {
        // 정답: XP 지급 + 집중도 회복
        addXp(currentQuiz.xpReward);
        setFocusScore(Math.min(100, focusScore + 15));
      }
      // 6/26: scoreStore에 퀴즈 결과 기록 → comprehensionScore 재계산 + 그래프 갱신
      recordQuizResult({
        quizId: currentQuiz.id,
        correct: isCorrect,
        xpAwarded: isCorrect ? currentQuiz.xpReward : 0,
        timestamp: Date.now(),
      });
    },
    [phase, currentQuiz, addXp, setFocusScore, focusScore, recordQuizResult]
  );

  const handleClose = useCallback(() => {
    dismissQuiz();
    dismissNudge();
    setPhase('answering');
    setSelectedIndex(null);
    setTimeLeft(30);
  }, [dismissQuiz, dismissNudge]);

  const timerPercent = (timeLeft / 30) * 100;
  const timerColor =
    timeLeft > 15 ? 'var(--color-engagement)' : timeLeft > 7 ? 'var(--color-xp)' : 'var(--color-nudge-hard)';

  return (
    <AnimatePresence>
      {isQuizVisible && (
        <>
          {/* 오버레이 */}
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
              backgroundColor: 'rgba(33,31,27,0.55)',
              backdropFilter: 'blur(4px)',
              zIndex: 'calc(var(--z-quiz) - 1)' as unknown as number,
            }}
          />

          {/* 퀴즈 카드 */}
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
              maxWidth: '480px',
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
              }}
            >
              {/* 타이머 바 */}
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

              <div style={{ padding: 'var(--space-6)' }}>
                {/* 헤더 */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                    <span
                      style={{
                        display: 'inline-block',
                        padding: '2px 10px',
                        backgroundColor: 'var(--color-primary-tint)',
                        color: 'var(--color-primary)',
                        borderRadius: 'var(--radius-full)',
                        fontSize: 'var(--text-xs)',
                        fontWeight: 'var(--weight-semibold)' as unknown as number,
                      }}
                    >
                      이해도 평가
                    </span>
                    <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                      ✨ 정답 시 +{currentQuiz.xpReward} XP
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: 'var(--text-sm)', color: timerColor, fontVariantNumeric: 'tabular-nums', fontWeight: 'var(--weight-semibold)' as unknown as number }}>
                    ⏱ {timeLeft}초
                  </div>
                </div>

                {/* 질문 */}
                <h3
                  style={{
                    fontSize: 'var(--text-base)',
                    fontWeight: 'var(--weight-semibold)' as unknown as number,
                    color: 'var(--color-text)',
                    lineHeight: 'var(--leading-normal)',
                    letterSpacing: 'var(--tracking-kr)',
                    marginBottom: 'var(--space-5)',
                  }}
                >
                  {currentQuiz.question}
                </h3>

                {/* 선택지 */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', marginBottom: 'var(--space-5)' }}>
                  {currentQuiz.options.map((option, index) => {
                    const isSelected = selectedIndex === index;
                    const isCorrectOption = index === currentQuiz.correctIndex;
                    const revealed = phase !== 'answering';

                    let bg = 'var(--color-surface)';
                    let border = 'var(--color-border)';
                    let textColor = 'var(--color-text)';

                    if (revealed) {
                      if (isCorrectOption) {
                        bg = '#d1fae5'; border = '#10b981'; textColor = '#065f46';
                      } else if (isSelected && !isCorrectOption) {
                        bg = '#fee2e2'; border = '#ef4444'; textColor = '#991b1b';
                      }
                    } else if (isSelected) {
                      bg = 'var(--color-primary-tint)';
                      border = 'var(--color-primary)';
                    }

                    // ── 7/3 마이크로 애니메이션 설정 ──
                    let animProps = {};
                    let transProps = {};
                    if (revealed) {
                      if (isCorrectOption) {
                        // 정답 시 맥박(Pulse) 효과
                        animProps = { scale: [1, 1.03, 1], boxShadow: '0 0 12px rgba(16, 185, 129, 0.4)' };
                        transProps = { duration: 0.5, ease: 'easeInOut' };
                      } else if (isSelected) {
                        // 오답 선택 시 흔들림(Shake) 효과
                        animProps = { x: [0, -6, 6, -6, 6, 0] };
                        transProps = { duration: 0.4 };
                      }
                    }

                    return (
                      <motion.button
                        key={index}
                        whileHover={phase === 'answering' ? { scale: 1.01 } : {}}
                        whileTap={phase === 'answering' ? { scale: 0.99 } : {}}
                        animate={animProps}
                        transition={revealed ? transProps : undefined}
                        onClick={() => handleSelect(index)}
                        disabled={phase !== 'answering'}
                        style={{
                          width: '100%',
                          textAlign: 'left',
                          padding: 'var(--space-3) var(--space-4)',
                          fontSize: 'var(--text-sm)',
                          fontFamily: 'var(--font-sans)',
                          lineHeight: 'var(--leading-normal)',
                          letterSpacing: 'var(--tracking-kr)',
                          borderRadius: 'var(--radius-md)',
                          border: `1.5px solid ${border}`,
                          backgroundColor: bg,
                          color: textColor,
                          cursor: phase === 'answering' ? 'pointer' : 'default',
                          transition: 'background-color 0.25s, border-color 0.25s, color 0.25s',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 'var(--space-3)',
                        }}
                      >
                        <span
                          style={{
                            flexShrink: 0,
                            width: '22px',
                            height: '22px',
                            borderRadius: '50%',
                            backgroundColor: revealed && isCorrectOption ? '#10b981' : revealed && isSelected ? '#ef4444' : 'var(--color-surface-alt)',
                            border: '1px solid var(--color-border)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '11px',
                            fontWeight: 'var(--weight-bold)' as unknown as number,
                            color: revealed && (isCorrectOption || isSelected) ? '#fff' : 'var(--color-text-secondary)',
                          }}
                        >
                          {revealed && isCorrectOption ? '✓' : revealed && isSelected ? '✗' : ['①','②','③','④'][index]}
                        </span>
                        {option}
                      </motion.button>
                    );
                  })}
                </div>

                {/* 결과 피드백 */}
                <AnimatePresence>
                  {phase !== 'answering' && (
                    <motion.div
                      key="feedback"
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      <div
                        style={{
                          padding: 'var(--space-4)',
                          borderRadius: 'var(--radius-md)',
                          backgroundColor: phase === 'correct' ? '#f0fdf4' : '#fef2f2',
                          border: `1px solid ${phase === 'correct' ? '#bbf7d0' : '#fecaca'}`,
                          marginBottom: 'var(--space-4)',
                        }}
                      >
                        <p
                          style={{
                            fontSize: 'var(--text-sm)',
                            fontWeight: 'var(--weight-semibold)' as unknown as number,
                            color: phase === 'correct' ? '#065f46' : '#991b1b',
                            fontFamily: 'var(--font-sans)',
                            marginBottom: '6px',
                          }}
                        >
                          {phase === 'correct'
                            ? `🎉 정답! +${currentQuiz.xpReward} XP 획득!`
                            : selectedIndex === -1
                            ? '⏰ 시간 초과!'
                            : '❌ 오답입니다'}
                        </p>
                        <p
                          style={{
                            fontSize: 'var(--text-xs)',
                            color: phase === 'correct' ? '#065f46' : '#991b1b',
                            fontFamily: 'var(--font-sans)',
                            lineHeight: 'var(--leading-relaxed)',
                          }}
                        >
                          {currentQuiz.explanation}
                        </p>
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
                          backgroundColor: phase === 'correct' ? 'var(--color-engagement)' : 'var(--color-primary)',
                          color: '#fff',
                          cursor: 'pointer',
                        }}
                      >
                        {phase === 'correct' ? '✨ 계속 읽기' : '다음으로 →'}
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* 하단 안내 */}
                {phase === 'answering' && (
                  <p style={{ textAlign: 'center', fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', fontFamily: 'var(--font-sans)' }}>
                    정답은 Literacy Score에 실시간으로 반영됩니다
                  </p>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default QuizCard;
