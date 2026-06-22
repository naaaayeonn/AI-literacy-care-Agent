import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import ReadingPane from '../components/reading/ReadingPane';
import FloatingControlPanel from '../components/panel/FloatingControlPanel';
import NudgeController from '../components/nudge/NudgeController';
import SessionSummaryCard from '../components/dashboard/SessionSummaryCard';
import { Card } from '../components/common/Card';
import { useReadingStore } from '../stores/readingStore';
import { useScoreEngine } from '../lib/useScoreEngine';

/**
 * ReadingPage — /reading
 * 6/24: NudgeController 연결 — 폐루프 실시간 개입 시스템
 * 6/26: useScoreEngine 연결 — 실시간 Literacy Score 계산 + 차트 자동 갱신
 *       SessionSummaryCard — 완독(progress >= 100) 시 결과 카드 표시
 */
export default function ReadingPage() {
  const progress = useReadingStore((s) => s.progress);

  // 6/26: Score Engine 마운트 (ReadingPage 수명 동안 실행)
  useScoreEngine();

  useEffect(() => {
    document.title = 'AI 리터러시 케어 — 읽기';
  }, []);

  const isFinished = progress >= 100;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
      {/* ── 폐루프 개입 시스템 ── */}
      <NudgeController />

      <div className="flex flex-col lg:flex-row gap-6 items-start">

        {/* ── 좌측: 본문 읽기 영역 ── */}
        <div className="flex-1 min-w-0 space-y-4">

          {/* 읽기 진행률 바 */}
          <ReadingProgressBar progress={progress} />

          {/* 본문 패널 */}
          <ReadingPane />

          {/* 완독 시: SessionSummaryCard 슬라이드업 등장 */}
          <SessionSummaryCard isVisible={isFinished} />

          {/* 완독 전: 안내 카드 */}
          {!isFinished && (
            <Card variant="flat" className="p-4">
              <p
                className="text-xs"
                style={{
                  color: 'var(--color-text-muted)',
                  fontFamily: 'var(--font-sans)',
                  lineHeight: 'var(--leading-normal)',
                }}
              >
                <span className="font-semibold" style={{ color: 'var(--color-text-secondary)' }}>
                  [6/26 Score Engine 작동 중]
                </span>{' '}
                스크롤할수록 Literacy Score가 실시간 계산됩니다. 25%/50%/75%/90%/완독 구간마다 대시보드 차트에 새 포인트가 추가됩니다.
                우측 패널 [집중도 시뮬]로 넛지→퀴즈 흐름을 시연하면, 퀴즈 결과도 즉시 점수에 반영됩니다.
              </p>
            </Card>
          )}
        </div>

        {/* ── 우측: 플로팅 제어판 ── */}
        <aside className="w-full lg:w-80 lg:shrink-0 lg:sticky lg:top-20 space-y-4">
          <FloatingControlPanel />
        </aside>

      </div>
    </div>
  );
}

/** 읽기 진행률 상단 바 */
function ReadingProgressBar({ progress }: { progress: number }) {
  const remainingMin = Math.max(0, Math.round((5 * (100 - progress)) / 100));

  return (
    <div
      className="rounded-lg border p-3 flex items-center gap-4"
      style={{
        backgroundColor: 'var(--color-surface)',
        borderColor: 'var(--color-border)',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-sm" style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-sans)' }}>
          읽기 진행률
        </span>
        <span
          className="text-sm font-semibold tabular-nums"
          style={{ color: 'var(--color-primary)', fontFamily: 'var(--font-sans)' }}
        >
          {progress}%
        </span>
      </div>
      <div
        className="flex-1 rounded-full h-2 overflow-hidden"
        style={{ backgroundColor: 'var(--color-surface-alt)', border: '1px solid var(--color-border)' }}
      >
        <div
          className="h-full rounded-full"
          style={{
            width: `${progress}%`,
            background: progress >= 100
              ? `linear-gradient(90deg, var(--color-engagement), var(--color-growth))`
              : `linear-gradient(90deg, var(--color-primary), var(--color-engagement))`,
            transition: 'width 0.5s ease',
          }}
        />
      </div>
      <span className="text-xs shrink-0" style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-sans)' }}>
        {progress >= 100 ? '🎉 완독!' : `약 ${remainingMin}분 남음`}
      </span>
      {progress > 0 && (
        <Link
          to="/dashboard"
          className="shrink-0 text-xs px-2 py-1 rounded"
          style={{
            backgroundColor: 'var(--color-primary-tint)',
            color: 'var(--color-primary)',
            fontFamily: 'var(--font-sans)',
          }}
        >
          📊 점수 보기
        </Link>
      )}
    </div>
  );
}
