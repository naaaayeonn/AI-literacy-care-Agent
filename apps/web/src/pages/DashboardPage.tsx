import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import GrowthDashboard from '../components/dashboard/GrowthDashboard';
import LevelBar from '../components/gamification/LevelBar';
import BadgeShelf from '../components/gamification/BadgeShelf';
import XpCounter from '../components/gamification/XpCounter';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';

/**
 * DashboardPage — /dashboard
 * 6/21: 성장 대시보드 전체 레이아웃 와이어프레임
 * - 상단: 요약 지표 카드 4개
 * - 중단: LiteracyScoreChart + 게이미피케이션
 * - 하단: 주간 성장 리포트 (TODO 6/30)
 *
 * TODO 6/30: 실제 세션 누적 데이터 연결
 * TODO 7/1: 게이미피케이션 실 데이터 연결
 */
export default function DashboardPage() {
  useEffect(() => {
    document.title = 'AI 리터러시 케어 — 성장 대시보드';
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">

      {/* ── 상단: 페이지 제목 + 읽기 화면으로 돌아가기 ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1
            className="text-2xl font-bold"
            style={{ color: 'var(--color-text)', fontFamily: 'var(--font-sans)', letterSpacing: 'var(--tracking-kr)' }}
          >
            📊 나의 리터러시 성장 기록
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-sans)' }}>
            읽기 행동 분석 및 Literacy Score 기반 성장 추이
          </p>
        </div>
        <Link to="/reading">
          <Button variant="outline" size="sm">← 읽기 화면으로</Button>
        </Link>
      </div>

      {/* ── 요약 지표 카드 ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard emoji="🎯" label="리터러시 점수" value="87" unit="점" color="var(--color-primary)" />
        <SummaryCard emoji="⚡" label="평균 집중도" value="85" unit="%" color="var(--color-engagement)" />
        <SummaryCard emoji="✅" label="평균 완독률" value="76" unit="%" color="var(--color-growth)" />
        <SummaryCard emoji="✨" label="누적 경험치" value="265" unit="XP" color="var(--color-xp)" />
      </div>

      {/* ── 중단: 차트 + 게이미피케이션 ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* Literacy Score 전후 비교 그래프 (데모 핵심) */}
        <div className="lg:col-span-8">
          <GrowthDashboard />
        </div>

        {/* 게이미피케이션 사이드 */}
        <div className="lg:col-span-4 space-y-4">
          {/* 레벨 & XP */}
          <Card variant="default" className="p-5 space-y-4">
            <h3
              className="text-sm font-semibold"
              style={{ color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}
            >
              🏆 성장 레벨
            </h3>
            <LevelBar level={2} percentage={65} />
            <div className="flex justify-between items-center">
              <span className="text-xs" style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-sans)' }}>
                누적 경험치
              </span>
              <XpCounter xp={265} />
            </div>
          </Card>

          {/* 배지 보관함 */}
          <Card variant="default" className="p-5">
            <h3
              className="text-sm font-semibold mb-4"
              style={{ color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}
            >
              🎖️ 배지 보관함
            </h3>
            <BadgeShelf />
          </Card>

          {/* 세션 통계 요약 */}
          <Card variant="flat" className="p-4 space-y-3">
            <h3
              className="text-xs font-semibold"
              style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-sans)' }}
            >
              📅 이번 주 요약
            </h3>
            <div className="space-y-2">
              {[
                { label: '완독한 글', value: '3편' },
                { label: '총 읽기 시간', value: '47분' },
                { label: '획득 XP', value: '115 XP' },
                { label: '퀴즈 정답률', value: '82%' },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between text-xs">
                  <span style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-sans)' }}>{label}</span>
                  <span className="font-semibold" style={{ color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}>{value}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* ── 하단: 주간/월간 성장 리포트 (TODO 6/30) ── */}
      <Card variant="flat" className="p-6">
        <div className="text-center py-8">
          <p className="text-2xl mb-2">📈</p>
          <p className="text-sm font-semibold" style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-sans)' }}>
            주간 / 월간 상세 성장 리포트
          </p>
          <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-sans)' }}>
            TODO 6/30 — 성장 대시보드 핵심 구현 단계에서 연결됩니다
          </p>
        </div>
      </Card>

    </div>
  );
}

/** 요약 지표 카드 */
function SummaryCard({
  emoji, label, value, unit, color,
}: {
  emoji: string;
  label: string;
  value: string;
  unit: string;
  color: string;
}) {
  return (
    <Card variant="default" className="p-4">
      <div className="flex items-start justify-between mb-2">
        <span className="text-xl">{emoji}</span>
      </div>
      <p className="text-xs mb-1" style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-sans)' }}>
        {label}
      </p>
      <div className="flex items-baseline gap-1">
        <span
          className="text-2xl font-bold tabular-nums"
          style={{ color, fontFamily: 'var(--font-sans)' }}
        >
          {value}
        </span>
        <span className="text-xs" style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-sans)' }}>
          {unit}
        </span>
      </div>
    </Card>
  );
}
