import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { BarChart2, Target, Zap, CheckCircle2, Sparkles, Trophy, Award, Activity } from 'lucide-react';
import GrowthDashboard from '../components/dashboard/GrowthDashboard';
import DetailedGrowthReport from '../components/dashboard/DetailedGrowthReport';
import LevelBar from '../components/gamification/LevelBar';
import BadgeShelf from '../components/gamification/BadgeShelf';
import XpCounter from '../components/gamification/XpCounter';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { useScoreStore } from '../stores/scoreStore';
import { useReadingStore } from '../stores/readingStore';

/**
 * DashboardPage — /dashboard
 * 6/26: scoreStore 실시간 구독으로 모든 하드코딩 값 제거
 * - 요약 지표 카드 4개 → scoreStore 실시간 값
 * - 게이미피케이션 사이드 → level/xp/badges 실시간 구독
 * - 퀴즈 정답률 → quizResults로 계산
 */
export default function DashboardPage() {
  const {
    literacyScore,
    engagementScore,
    comprehensionScore,
    xp,
    level,
    levelProgress,
    quizResults,
  } = useScoreStore();
  const { progress } = useReadingStore();

  useEffect(() => {
    document.title = 'AI 리터러시 케어 — 성장 대시보드';
  }, []);

  // 퀴즈 정답률
  const quizAccuracy = quizResults.length > 0
    ? Math.round((quizResults.filter((r) => r.correct).length / quizResults.length) * 100)
    : comprehensionScore; // 퀴즈 미진행 시 comprehension 값 표시



  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">

      {/* ── 상단: 페이지 제목 ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1
            className="text-2xl font-bold flex items-center gap-2"
            style={{ color: 'var(--color-text)', fontFamily: 'var(--font-sans)', letterSpacing: 'var(--tracking-kr)' }}
          >
            <span style={{ color: 'var(--color-primary)' }}><BarChart2 size={24} /></span>
            나의 리터러시 성장 기록
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-sans)' }}>
            읽기 행동 분석 및 Literacy Score 기반 성장 추이
          </p>
        </div>
        <Link to="/reading">
          <Button variant="outline" size="sm">← 읽기 화면으로</Button>
        </Link>
      </div>

      {/* ── 요약 지표 카드 — scoreStore 실시간 연결 ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <SummaryCard icon={<Target size={20} />} label="리터러시 점수"   value={String(literacyScore)}    unit="점"  color="var(--color-primary)" />
        <SummaryCard icon={<Zap size={20} />}    label="평균 집중도"     value={String(engagementScore)}  unit="%"   color="var(--color-engagement)" />
        <SummaryCard icon={<CheckCircle2 size={20} />} label="퀴즈 정답률" value={String(quizAccuracy)}   unit="%"   color="var(--color-growth)"
          sub={quizResults.length > 0 ? `${quizResults.length}문항 풀이` : '미응시'}
        />
        <SummaryCard icon={<Sparkles size={20} />} label="누적 경험치"   value={String(xp)}               unit="XP"  color="var(--color-xp)" />
      </div>

      {/* ── 중단: 차트 + 게이미피케이션 ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* Literacy Score 전후 비교 그래프 (데모 핵심 ★) */}
        <div className="lg:col-span-8">
          <GrowthDashboard />
        </div>

        {/* 게이미피케이션 사이드 — scoreStore 실시간 */}
        <div className="lg:col-span-4 space-y-4">

          {/* 레벨 & XP */}
          <Card variant="default" className="p-5 space-y-4">
            <h3 className="text-sm font-semibold flex items-center gap-2" style={{ color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}>
              <span style={{ color: 'var(--color-primary)' }}><Trophy size={16} /></span>
              성장 레벨
            </h3>
            <LevelBar level={level} percentage={levelProgress} />
            <div className="flex justify-between items-center">
              <span className="text-xs" style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-sans)' }}>
                누적 경험치
              </span>
              <XpCounter xp={xp} />
            </div>
          </Card>

          {/* 배지 보관함 */}
          <Card variant="default" className="p-5">
            <h3 className="text-sm font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}>
              <span style={{ color: 'var(--color-primary)' }}><Award size={16} /></span>
              배지 보관함
            </h3>
            <BadgeShelf />
          </Card>

          {/* 세션 통계 요약 — 실시간 */}
          <Card variant="flat" className="p-4 space-y-3">
            <h3 className="text-xs font-semibold flex items-center gap-2" style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-sans)' }}>
              <Activity size={14} />
              현재 세션 요약
            </h3>
            <div className="space-y-2">
              {[
                { label: '퀴즈 풀이 수',   value: `${quizResults.length}문항` },
                { label: '이해도 점수',    value: `${comprehensionScore}점` },
                { label: '진행 구간',      value: `${[25, 50, 75, 90, 100].filter((m) => progress >= m).length}단계` },
                { label: '퀴즈 정답률',    value: `${quizAccuracy}%` },
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

      {/* ── 하단: 주간/월간 성장 리포트 (6/30 구현 완료) ── */}
      <DetailedGrowthReport />

    </div>
  );
}

/** 요약 지표 카드 */
function SummaryCard({
  icon, label, value, unit, color, sub,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  unit: string;
  color: string;
  sub?: string;
}) {
  return (
    <motion.div
      whileHover={{ y: -6, scale: 1.02 }}
      transition={{ type: 'spring', stiffness: 300, damping: 15 }}
      style={{ display: 'flex', flexDirection: 'column', height: '100%' }}
    >
      <Card variant="default" className="p-4 h-full flex flex-col justify-between">
        <div>
          <div className="flex items-start justify-between mb-2">
            <span style={{ color }}>{icon}</span>
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
        </div>
        {sub && (
          <p className="text-xs mt-2 pt-2 border-t border-[var(--color-border)]" style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-sans)' }}>
            {sub}
          </p>
        )}
      </Card>
    </motion.div>
  );
}
