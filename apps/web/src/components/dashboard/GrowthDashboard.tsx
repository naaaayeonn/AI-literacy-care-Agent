/**
 * GrowthDashboard — 6/22 scoreStore 연결 실구현
 * LiteracyScoreChart + 요약 지표를 scoreStore에서 실제 값으로 표시.
 */
import React from 'react';
import { TrendingUp } from 'lucide-react';
import LiteracyScoreChart from './LiteracyScoreChart';
import { useScoreStore } from '../../stores/scoreStore';

export const GrowthDashboard: React.FC = () => {
  const { literacyScore, comprehensionScore, engagementScore, scoreSeries } = useScoreStore();

  // 케어 전후 최대 델타 계산
  const maxDelta =
    scoreSeries.length >= 2
      ? Math.max(...scoreSeries.map((d) => (d.after || 0) - (d.before || 0)))
      : 0;

  return (
    <div
      style={{
        backgroundColor: 'var(--color-surface)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--color-border)',
        boxShadow: 'var(--shadow-sm)',
        padding: 'var(--space-6)',
      }}
    >
      {/* 헤더 */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 'var(--space-5)' }}>
        <div>
          <h2
            style={{
              fontSize: 'var(--text-lg)',
              fontWeight: 'var(--weight-bold)' as unknown as number,
              color: 'var(--color-text)',
              fontFamily: 'var(--font-sans)',
              letterSpacing: 'var(--tracking-kr)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <span style={{ color: 'var(--color-primary)' }}><TrendingUp size={20} /></span>
            Literacy Score 주간 비교
          </h2>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', fontFamily: 'var(--font-sans)', marginTop: '4px' }}>
            AI 케어 에이전트 개입 전 / 후 점수 추이
          </p>
        </div>
        {/* 범례 */}
        <div style={{ display: 'flex', gap: 'var(--space-4)', flexShrink: 0 }}>
          <LegendDot color="var(--color-text-muted)" dashed label="케어 미적용" />
          <LegendDot color="var(--color-comprehension)" label="케어 적용" />
        </div>
      </div>

      {/* 차트 */}
      <LiteracyScoreChart />

      {/* 하단 요약 지표 */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 'var(--space-3)',
          marginTop: 'var(--space-5)',
        }}
      >
        <MetricChip
          label="리터러시 점수"
          value={`${literacyScore}점`}
          color="var(--color-primary)"
          delta={`+${maxDelta}점 향상`}
        />
        <MetricChip
          label="이해도"
          value={`${comprehensionScore}점`}
          color="var(--color-comprehension)"
        />
        <MetricChip
          label="집중도"
          value={`${engagementScore}점`}
          color="var(--color-engagement)"
        />
      </div>
    </div>
  );
};

function LegendDot({ color, dashed, label }: { color: string; dashed?: boolean; label: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
      <div
        style={{
          width: '20px',
          height: '2px',
          backgroundColor: color,
          borderRadius: '1px',
          ...(dashed
            ? { backgroundImage: `repeating-linear-gradient(to right, ${color} 0, ${color} 4px, transparent 4px, transparent 8px)`, backgroundColor: 'transparent' }
            : {}),
        }}
      />
      <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', fontFamily: 'var(--font-sans)' }}>
        {label}
      </span>
    </div>
  );
}

function MetricChip({ label, value, color, delta }: { label: string; value: string; color: string; delta?: string }) {
  return (
    <div
      style={{
        padding: 'var(--space-3)',
        backgroundColor: 'var(--color-surface-alt)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--color-border)',
        textAlign: 'center',
      }}
    >
      <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', fontFamily: 'var(--font-sans)', marginBottom: '4px' }}>
        {label}
      </p>
      <p style={{ fontSize: 'var(--text-xl)', fontWeight: 'var(--weight-bold)' as unknown as number, color, fontFamily: 'var(--font-sans)', fontVariantNumeric: 'tabular-nums' }}>
        {value}
      </p>
      {delta && (
        <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-growth)', fontFamily: 'var(--font-sans)', marginTop: '2px' }}>
          {delta}
        </p>
      )}
    </div>
  );
}

export default GrowthDashboard;
