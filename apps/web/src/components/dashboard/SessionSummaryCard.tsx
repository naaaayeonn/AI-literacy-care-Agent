/**
 * SessionSummaryCard — 6/26 신규 생성
 * progress >= 100 달성(완독) 시 ReadingPage 하단에 등장하는 최종 결과 카드.
 * Literacy Score 전후 비교 미니 차트 + 획득 XP + 배지 + 대시보드 이동 버튼.
 *
 * Framer Motion으로 아래에서 슬라이드업 등장.
 */
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useScoreStore } from '../../stores/scoreStore';
import { useReadingStore } from '../../stores/readingStore';
import { useFocusStore } from '../../stores/focusStore';
import LiteracyScoreChart from '../dashboard/LiteracyScoreChart';

interface SessionSummaryCardProps {
  isVisible: boolean;
}

export const SessionSummaryCard: React.FC<SessionSummaryCardProps> = ({ isVisible }) => {
  const { literacyScore, comprehensionScore, engagementScore, xp, quizResults, badges } = useScoreStore();

  const correctCount = quizResults.filter((r) => r.correct).length;
  const quizAccuracy = quizResults.length > 0
    ? Math.round((correctCount / quizResults.length) * 100)
    : null;

  const sessionXpEarned = quizResults.reduce((sum, r) => sum + r.xpAwarded, 0);

  // 이번 세션에서 획득한 배지 (최근 2개 이내)
  const sessionBadges = badges.slice(-2);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          key="session-summary"
          initial={{ opacity: 0, y: 32 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 16 }}
          transition={{ duration: 0.5, ease: [0.34, 1.1, 0.64, 1] }}
          style={{
            backgroundColor: 'var(--color-surface)',
            borderRadius: 'var(--radius-xl)',
            border: '2px solid var(--color-primary)',
            boxShadow: 'var(--shadow-lg)',
            overflow: 'hidden',
            fontFamily: 'var(--font-sans)',
          }}
        >
          {/* 상단 배너 */}
          <div style={{
            background: `linear-gradient(135deg, var(--color-primary) 0%, var(--color-comprehension) 100%)`,
            padding: 'var(--space-5) var(--space-6)',
            color: '#fff',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-2)' }}>
              <span style={{ fontSize: '28px' }}>🎉</span>
              <div>
                <p style={{ fontSize: 'var(--text-xs)', opacity: 0.85, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
                  읽기 완료 — 세션 결과
                </p>
                <p style={{ fontSize: 'var(--text-xl)', fontWeight: 700, letterSpacing: 'var(--tracking-kr)' }}>
                  Literacy Score
                  <span style={{ fontSize: '2rem', marginLeft: '10px', fontVariantNumeric: 'tabular-nums' }}>
                    {literacyScore}
                  </span>
                  <span style={{ fontSize: 'var(--text-sm)', opacity: 0.8, marginLeft: '4px' }}>/ 100</span>
                </p>
              </div>
            </div>
          </div>

          <div style={{ padding: 'var(--space-6)' }}>
            {/* 요약 지표 행 */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-3)', marginBottom: 'var(--space-6)' }}>
              <MiniMetric label="이해도" value={`${comprehensionScore}점`} color="var(--color-comprehension)"
                sub={quizAccuracy !== null ? `퀴즈 정답률 ${quizAccuracy}%` : '퀴즈 없음'} />
              <MiniMetric label="집중도" value={`${engagementScore}점`} color="var(--color-engagement)"
                sub="평균 집중도" />
              <MiniMetric label="획득 XP" value={`✨ +${sessionXpEarned}`} color="var(--color-xp)"
                sub={`누적: ${xp} XP`} />
            </div>

            {/* 라이브 차트 (소형) */}
            <div style={{ marginBottom: 'var(--space-5)' }}>
              <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginBottom: '8px' }}>
                📈 이번 세션 Literacy Score 변화
              </p>
              <LiteracyScoreChart height={180} hideLegend />
            </div>

            {/* 배지 획득 */}
            {sessionBadges.length > 0 && (
              <div style={{
                backgroundColor: 'var(--color-surface-alt)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-4)',
                marginBottom: 'var(--space-5)',
                border: '1px solid var(--color-border)',
              }}>
                <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginBottom: '8px' }}>
                  🎖️ 이번 세션 획득 배지
                </p>
                <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
                  {sessionBadges.map((b) => (
                    <div key={b.id} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '24px' }}>{b.emoji}</span>
                      <div>
                        <p style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--color-text)' }}>{b.name}</p>
                        <p style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>{b.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 액션 버튼 */}
            <div style={{ display: 'flex', gap: 'var(--space-3)', width: '100%' }}>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => {
                  useReadingStore.getState().setProgress(0);
                  useFocusStore.getState().reset();
                  useScoreStore.getState().restartDemoSession();
                }}
                style={{
                  flex: 1,
                  display: 'block',
                  textAlign: 'center',
                  padding: 'var(--space-3)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--color-primary)',
                  backgroundColor: 'transparent',
                  color: 'var(--color-primary)',
                  fontSize: 'var(--text-sm)',
                  fontWeight: 700,
                  fontFamily: 'var(--font-sans)',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s',
                }}
                onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.backgroundColor = 'var(--color-primary-tint)')}
                onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.backgroundColor = 'transparent')}
              >
                🔄 처음부터 다시 읽기
              </motion.button>
              
              <motion.div
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                style={{ flex: 1 }}
              >
                <Link
                  to="/dashboard"
                  style={{
                    display: 'block',
                    textAlign: 'center',
                    padding: 'var(--space-3)',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--color-primary)',
                    color: '#fff',
                    fontSize: 'var(--text-sm)',
                    fontWeight: 700,
                    fontFamily: 'var(--font-sans)',
                    textDecoration: 'none',
                    transition: 'opacity 0.2s',
                  }}
                  onMouseEnter={(e) => ((e.currentTarget as HTMLAnchorElement).style.opacity = '0.85')}
                  onMouseLeave={(e) => ((e.currentTarget as HTMLAnchorElement).style.opacity = '1')}
                >
                  📊 성장 대시보드 보기
                </Link>
              </motion.div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

/** 소형 지표 카드 */
function MiniMetric({ label, value, color, sub }: { label: string; value: string; color: string; sub?: string }) {
  return (
    <div style={{
      padding: 'var(--space-3)',
      backgroundColor: 'var(--color-surface-alt)',
      borderRadius: 'var(--radius-md)',
      border: '1px solid var(--color-border)',
      textAlign: 'center',
    }}>
      <p style={{ fontSize: '10px', color: 'var(--color-text-muted)', marginBottom: '4px', fontFamily: 'var(--font-sans)' }}>
        {label}
      </p>
      <p style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color, fontFamily: 'var(--font-sans)', fontVariantNumeric: 'tabular-nums' }}>
        {value}
      </p>
      {sub && (
        <p style={{ fontSize: '10px', color: 'var(--color-text-muted)', marginTop: '2px', fontFamily: 'var(--font-sans)' }}>
          {sub}
        </p>
      )}
    </div>
  );
}

export default SessionSummaryCard;
