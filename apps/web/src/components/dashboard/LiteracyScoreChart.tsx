/**
 * LiteracyScoreChart — 6/26 업그레이드 (데모 핵심 ★★)
 *
 * [변경 사항]
 * - 세션 진행 중 실시간으로 포인트가 추가되는 "라이브 그래프"로 전환
 * - 마지막 포인트(현재 세션)를 특수 Dot으로 강조 (맥박 애니메이션)
 * - scoreStore.literacyScore가 변화할 때 차트 헤더 수치도 실시간 갱신
 * - 이전 히스토리(일별) + 현재 세션 포인트(진행 구간) 모두 표시
 * - 케어 전/후 격차(Gap) ReferenceLine 하이라이트
 */
import React, { useMemo } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  Dot,
} from 'recharts';
import { useScoreStore } from '../../stores/scoreStore';
import type { ScoreDataPoint } from '../../types/shared';

// ── 커스텀 툴팁 ──────────────────────────────────────────────────────
interface TooltipPayload {
  color: string;
  name: string;
  value: number;
}
interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
  label?: string;
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  const gap = payload.length === 2 ? payload[1].value - payload[0].value : 0;
  return (
    <div style={{
      backgroundColor: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius-md)',
      padding: '10px 14px',
      boxShadow: 'var(--shadow-md)',
      fontFamily: 'var(--font-sans)',
      fontSize: 'var(--text-sm)',
      minWidth: '140px',
    }}>
      <p style={{ fontWeight: 600, color: 'var(--color-text)', marginBottom: '6px' }}>{label}</p>
      {payload.map((item) => (
        <p key={item.name} style={{ color: item.color, margin: '2px 0' }}>
          {item.name}: <strong>{item.value}점</strong>
        </p>
      ))}
      {gap > 0 && (
        <div style={{
          marginTop: '8px',
          paddingTop: '6px',
          borderTop: '1px solid var(--color-border)',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
        }}>
          <span style={{ fontSize: '14px' }}>📈</span>
          <span style={{ color: 'var(--color-growth)', fontSize: 'var(--text-xs)', fontWeight: 600 }}>
            +{gap}점 향상
          </span>
        </div>
      )}
    </div>
  );
};

// ── 라이브 포인트 강조 Dot ────────────────────────────────────────────
interface LiveDotProps {
  cx?: number;
  cy?: number;
  index?: number;
  dataLength: number;
}

const LiveDot: React.FC<LiveDotProps> = ({ cx = 0, cy = 0, index = 0, dataLength }) => {
  const isLast = index === dataLength - 1;
  if (!isLast) {
    return <Dot cx={cx} cy={cy} r={5} fill="var(--color-comprehension)" stroke="var(--color-surface)" strokeWidth={2} />;
  }
  // 마지막 포인트: 이중 원 강조 (라이브 표시)
  return (
    <g>
      <circle cx={cx} cy={cy} r={10} fill="var(--color-comprehension)" fillOpacity={0.2} />
      <circle cx={cx} cy={cy} r={6} fill="var(--color-comprehension)" stroke="var(--color-surface)" strokeWidth={2} />
    </g>
  );
};

// ── 메인 차트 ────────────────────────────────────────────────────────
interface LiteracyScoreChartProps {
  /** 높이 (기본 260px) */
  height?: number;
  /** 범례 숨김 여부 */
  hideLegend?: boolean;
}

export const LiteracyScoreChart: React.FC<LiteracyScoreChartProps> = ({
  height = 260,
  hideLegend = false,
}) => {
  const { scoreSeries, literacyScore } = useScoreStore();

  // 최대 향상폭 계산 (배지/헤더 표시용)
  const maxGap = useMemo(() => {
    if (scoreSeries.length < 2) return 0;
    return Math.max(...scoreSeries.map((d: ScoreDataPoint) => d.after - d.before));
  }, [scoreSeries]);

  const currentScore = scoreSeries.length > 0
    ? scoreSeries[scoreSeries.length - 1].after
    : literacyScore;

  return (
    <div>
      {/* 실시간 점수 헤더 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '12px',
      }}>
        <p style={{
          fontSize: 'var(--text-xs)',
          color: 'var(--color-text-muted)',
          fontFamily: 'var(--font-sans)',
        }}>
          AI 케어 에이전트 개입 전/후 Literacy Score
        </p>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* 현재 점수 라이브 뱃지 */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: '2px 8px',
            backgroundColor: 'var(--color-primary-tint)',
            borderRadius: 'var(--radius-full)',
          }}>
            <span style={{
              width: '6px', height: '6px', borderRadius: '50%',
              backgroundColor: 'var(--color-comprehension)',
              display: 'inline-block',
            }} />
            <span style={{
              fontSize: 'var(--text-xs)',
              fontWeight: 700,
              color: 'var(--color-comprehension)',
              fontFamily: 'var(--font-sans)',
              fontVariantNumeric: 'tabular-nums',
            }}>
              {currentScore}점
            </span>
          </div>

          {/* 향상폭 */}
          {maxGap > 0 && (
            <span style={{
              fontSize: 'var(--text-xs)',
              color: 'var(--color-growth)',
              fontFamily: 'var(--font-sans)',
              fontWeight: 600,
            }}>
              ↑ +{maxGap}점
            </span>
          )}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={scoreSeries} margin={{ top: 8, right: 20, left: -8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />

          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fontFamily: 'var(--font-sans)', fill: 'var(--color-text-secondary)' }}
            axisLine={{ stroke: 'var(--color-border)' }}
            tickLine={false}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fontSize: 11, fontFamily: 'var(--font-sans)', fill: 'var(--color-text-secondary)' }}
            axisLine={false}
            tickLine={false}
          />

          <Tooltip content={<CustomTooltip />} />
          {!hideLegend && (
            <Legend wrapperStyle={{ fontFamily: 'var(--font-sans)', fontSize: '12px', paddingTop: '12px' }} />
          )}

          {/* 평균선 */}
          <ReferenceLine
            y={50}
            stroke="var(--color-nudge-soft)"
            strokeDasharray="4 4"
            label={{ value: '평균', fill: 'var(--color-text-muted)', fontSize: 10, fontFamily: 'var(--font-sans)' }}
          />

          {/* 케어 미적용 (점선) */}
          <Line
            type="monotone"
            dataKey="before"
            name="케어 미적용"
            stroke="var(--color-text-muted)"
            strokeWidth={2}
            strokeDasharray="6 3"
            dot={{ fill: 'var(--color-text-muted)', r: 4, stroke: 'var(--color-surface)', strokeWidth: 2 }}
            activeDot={{ r: 6 }}
            isAnimationActive={true}
            animationDuration={600}
          />

          {/* 케어 적용 (실선 — 라이브 Dot 포함) */}
          <Line
            type="monotone"
            dataKey="after"
            name="케어 적용"
            stroke="var(--color-comprehension)"
            strokeWidth={3}
            dot={(props) => (
              <LiveDot
                cx={props.cx}
                cy={props.cy}
                index={props.index}
                dataLength={scoreSeries.length}
              />
            )}
            activeDot={{ r: 8, stroke: 'var(--color-comprehension)', strokeWidth: 2, fill: 'var(--color-surface)' }}
            isAnimationActive={true}
            animationDuration={800}
            animationEasing="ease-out"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default LiteracyScoreChart;
