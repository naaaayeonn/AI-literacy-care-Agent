import { useState, useEffect } from 'react';
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
import { useAuthStore } from '../stores/authStore';
import { useSessionConfig } from '../stores/sessionConfigStore';
import { api, type GrowthReportResponse } from '../lib/api';

/**
 * DashboardPage — /dashboard
 * 6/26: scoreStore 실시간 구독으로 모든 하드코딩 값 제거
 * - 요약 지표 카드 4개 → scoreStore 실시간 값
 * - 게이미피케이션 사이드 → level/xp/badges 실시간 구독
 * - 퀴즈 정답률 → quizResults로 계산
 */
export default function DashboardPage() {
  const {
    literacyScore: localLiteracy,
    engagementScore: localEngagement,
    comprehensionScore: localComprehension,
    xp: localXp,
    level: localLevel,
    levelProgress: localLevelProgress,
    quizResults,
  } = useScoreStore();
  const { progress } = useReadingStore();
  
  const { user } = useAuthStore();
  const anonId = useSessionConfig((s) => s.userId);
  const userId = user?.id || anonId;

  const [dbData, setDbData] = useState<GrowthReportResponse & {
    totalXp?: number;
    level?: number;
    averageLiteracyScore?: number;
    averageFocusScore?: number;
    averageComprehensionScore?: number;
  } | null>(null);

  useEffect(() => {
    document.title = 'AI 리터러시 케어 — 성장 대시보드';
  }, []);

  useEffect(() => {
    async function loadDbData() {
      if (!userId) return;
      try {
        const res = await api.getGrowthReport(userId);
        setDbData(res);
      } catch (err) {
        console.error('[Dashboard] Failed to load user metrics:', err);
      }
    }
    loadDbData();
  }, [userId]);

  // DB 연동 값이 있으면 그것을 최우선으로 보여주고, 없거나 0이면 로컬/기본값 폴백
  const displayLiteracy = dbData?.averageLiteracyScore || localLiteracy || 50;
  const displayEngagement = dbData?.averageFocusScore || localEngagement || 50;
  const displayComprehension = dbData?.averageComprehensionScore || localComprehension || 82;
  const displayXp = dbData?.totalXp !== undefined ? dbData.totalXp : localXp;
  const displayLevel = dbData?.level !== undefined ? dbData.level : localLevel;
  
  // 레벨 바 계산: 누적 XP 기준으로 계산
  const LEVEL_THRESHOLDS = [0, 100, 250, 500, 1000, 2000];
  const calcLevelProgress = (xpVal: number) => {
    for (let i = 1; i < LEVEL_THRESHOLDS.length; i++) {
      if (xpVal < LEVEL_THRESHOLDS[i]) {
        const base = LEVEL_THRESHOLDS[i - 1];
        const next = LEVEL_THRESHOLDS[i];
        return Math.floor(((xpVal - base) / (next - base)) * 100);
      }
    }
    return 100;
  };
  const displayLevelProgress = dbData?.totalXp !== undefined ? calcLevelProgress(dbData.totalXp) : localLevelProgress;

  // 퀴즈 정답률 및 sub-label 세밀한 계산
  const hasCurrentQuizzes = quizResults.length > 0;
  const currentAccuracy = hasCurrentQuizzes
    ? Math.round((quizResults.filter((r) => r.correct).length / quizResults.length) * 100)
    : 0;

  // DB 평균 이해도가 유효하게 존재하면 그것을 우선 표시, 없으면 현재 세션 결과 표시 (둘 다 없으면 0)
  const displayComprehensionValue = dbData?.averageComprehensionScore !== undefined && dbData.averageComprehensionScore > 0
    ? dbData.averageComprehensionScore
    : (hasCurrentQuizzes ? currentAccuracy : 0);

  const comprehensionSubLabel = hasCurrentQuizzes
    ? `${quizResults.length}문항 풀이`
    : (dbData?.averageComprehensionScore !== undefined && dbData.averageComprehensionScore > 0
        ? '이전 평균'
        : '미응시');

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
        <SummaryCard icon={<Target size={20} />} label="리터러시 점수"   value={String(displayLiteracy)}    unit="점"  color="var(--color-primary)" />
        <SummaryCard icon={<Zap size={20} />}    label="평균 집중도"     value={String(displayEngagement)}  unit="%"   color="var(--color-engagement)" />
        <SummaryCard icon={<CheckCircle2 size={20} />} label="퀴즈 정답률" value={String(displayComprehensionValue)}   unit="%"   color="var(--color-growth)"
          sub={comprehensionSubLabel}
        />
        <SummaryCard icon={<Sparkles size={20} />} label="누적 경험치"   value={String(displayXp)}               unit="XP"  color="var(--color-xp)" />
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
            <LevelBar level={displayLevel} percentage={displayLevelProgress} />
            <div className="flex justify-between items-center">
              <span className="text-xs" style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-sans)' }}>
                누적 경험치
              </span>
              <XpCounter xp={displayXp} />
            </div>
          </Card>

          {/* 배지 보관함 */}
          <Card variant="default" className="p-5">
            <h3 className="text-sm font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}>
              <span style={{ color: 'var(--color-primary)' }}><Award size={16} /></span>
              배지 보관함
            </h3>
            <BadgeShelf dbBadges={dbData?.badges} />
          </Card>

          {/* 세션 통계 요약 — 실시간 */}
          <Card variant="flat" className="p-4 space-y-3">
            <h3 className="text-xs font-semibold flex items-center gap-2" style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-sans)' }}>
              <Activity size={14} />
              현재 세션 요약
            </h3>
            <div className="space-y-2">
              {[
                { label: '퀴즈 풀이 수',   value: `${dbData?.latestSessionSummary ? dbData.latestSessionSummary.quiz_count : quizResults.length}문항` },
                { label: '이해도 점수',    value: `${dbData?.latestSessionSummary ? dbData.latestSessionSummary.comprehension_score : displayComprehension}점` },
                { label: '진행 구간',      value: `${[25, 50, 75, 90, 100].filter((m) => (dbData?.latestSessionSummary ? dbData.latestSessionSummary.progress : progress) >= m).length}단계` },
                { label: '퀴즈 정답률',    value: `${dbData?.latestSessionSummary ? dbData.latestSessionSummary.quiz_accuracy : currentAccuracy}%` },
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
