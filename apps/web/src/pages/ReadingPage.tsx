import { useEffect } from 'react';
import ReadingPane from '../components/reading/ReadingPane';
import FloatingControlPanel from '../components/panel/FloatingControlPanel';
import SoftNudge from '../components/nudge/SoftNudge';
import { Card } from '../components/common/Card';

/**
 * ReadingPage — /reading
 * 6/21: 와이어프레임 수준의 레이아웃 완성
 * - 좌: ReadingPane (본문 + 진행률 바)
 * - 우: FloatingControlPanel (실시간 집중도·XP·레벨)
 * - 조건부 Nudge 배너 (현재는 데모용 Soft 고정)
 *
 * TODO 6/23: 실제 스크롤 이벤트 감지 → readingStore 연결
 * TODO 6/24: focusStore 구독 → nudgeLevel 기반 조건부 렌더
 */
export default function ReadingPage() {
  useEffect(() => {
    document.title = 'AI 리터러시 케어 — 읽기';
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
      <div className="flex flex-col lg:flex-row gap-6 items-start">

        {/* ── 좌측: 본문 읽기 영역 (68% 너비) ── */}
        <div className="flex-1 min-w-0 space-y-4">

          {/* 읽기 진행률 바 */}
          <ReadingProgressBar progress={42} />

          {/* 본문 패널 */}
          <ReadingPane />

          {/* Soft Nudge 데모 배너 (TODO 6/24: focusStore 구독으로 조건부 렌더) */}
          <SoftNudge message="이 단락에는 핵심 개념이 집중되어 있어요. 조금 더 천천히 읽어볼까요?" />

          {/* 6/21 범위 안내 카드 */}
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
                [6/21 와이어프레임]
              </span>{' '}
              라우팅·레이아웃·API 계약 확정 단계입니다. 실제 스크롤 감지(6/23), 넛지 동작(6/24),
              퀴즈 팝업(6/25), Literacy Score 그래프(6/26)는 이후 일정에서 구현됩니다.
            </p>
          </Card>
        </div>

        {/* ── 우측: 플로팅 제어판 (고정 사이드바) ── */}
        <aside className="w-full lg:w-80 lg:shrink-0 lg:sticky lg:top-20 space-y-4">
          <FloatingControlPanel />
        </aside>

      </div>
    </div>
  );
}

/** 읽기 진행률 상단 바 */
function ReadingProgressBar({ progress }: { progress: number }) {
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
          className="h-full rounded-full transition-all duration-700"
          style={{
            width: `${progress}%`,
            background: `linear-gradient(90deg, var(--color-primary), var(--color-engagement))`,
          }}
        />
      </div>
      <span className="text-xs shrink-0" style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-sans)' }}>
        {/* TODO 6/23: 실제 예상 완독 시간 */}
        약 3분 남음
      </span>
    </div>
  );
}
