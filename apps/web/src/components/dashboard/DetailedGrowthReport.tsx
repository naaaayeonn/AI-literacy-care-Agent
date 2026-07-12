import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { Card } from '../common/Card';
import { api, type GrowthReportResponse } from '../../lib/api';
import { useSessionConfig } from '../../stores/sessionConfigStore';

// ── 데이터 타입 정의 ──────────────────────────────────────────────────
// (Zustand/API 타입 연동 완료로 비활성화)

// ── 커스텀 툴팁 ──────────────────────────────────────────────────────
const CustomRadarTooltip = ({ active, payload }: any) => {
  if (!active || !payload || !payload.length) return null;
  return (
    <div
      style={{
        backgroundColor: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)',
        padding: '10px 14px',
        boxShadow: 'var(--shadow-md)',
        fontFamily: 'var(--font-sans)',
        fontSize: 'var(--text-sm)',
      }}
    >
      <p style={{ fontWeight: 600, color: 'var(--color-text)', marginBottom: '6px' }}>
        {payload[0].payload.subject}
      </p>
      {payload.map((item: any) => (
        <p key={item.name} style={{ color: item.color, margin: '2px 0' }}>
          {item.name}: <strong>{item.value}점</strong>
        </p>
      ))}
    </div>
  );
};

const CustomActivityTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) return null;
  return (
    <div
      style={{
        backgroundColor: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)',
        padding: '10px 14px',
        boxShadow: 'var(--shadow-md)',
        fontFamily: 'var(--font-sans)',
        fontSize: 'var(--text-sm)',
      }}
    >
      <p style={{ fontWeight: 600, color: 'var(--color-text)', marginBottom: '6px' }}>
        {label}
      </p>
      {payload.map((item: any) => (
        <p key={item.name} style={{ color: item.color, margin: '2px 0' }}>
          {item.name}: <strong>{item.value}{item.name === '독해 시간' ? '분' : ' XP'}</strong>
        </p>
      ))}
    </div>
  );
};

export default function DetailedGrowthReport() {
  const [tab, setTab] = useState<'weekly' | 'monthly'>('weekly');
  const [data, setData] = useState<GrowthReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const userId = useSessionConfig((s) => s.userId);

  useEffect(() => {
    async function fetchData() {
      if (!userId) return;
      setLoading(true);
      const res = await api.getGrowthReport(userId);
      setData(res);
      setLoading(false);
    }
    fetchData();
  }, [userId]);

  if (loading || !data) {
    return (
      <Card variant="default" className="p-6 space-y-6 flex justify-center items-center h-64">
        <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>리포트 데이터를 불러오는 중...</p>
      </Card>
    );
  }

  const currentRadarData = tab === 'weekly' ? data.weekly.radarData : data.monthly.radarData;
  const currentActivityData = tab === 'weekly' ? data.weekly.activityData : data.monthly.activityData;
  const currentWords = tab === 'weekly' ? data.weekly.words : data.monthly.words;

  // 핵심 성장 성과: 레이더에서 before→after 증가폭이 가장 큰 지표를 실데이터로 도출(하드코딩 폐기).
  const topGrowth = currentRadarData.reduce(
    (best, d) => (d.after - d.before > best.delta ? { subject: d.subject, delta: d.after - d.before } : best),
    { subject: '', delta: -Infinity }
  );
  const topGrowthLabel =
    topGrowth.subject && topGrowth.delta > 0
      ? `${topGrowth.subject} +${topGrowth.delta.toFixed(1)}점 성장`
      : '데이터 축적 중';

  return (
    <Card variant="default" className="p-6 space-y-6">
      {/* ── 헤더 & 탭 전환 ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--color-border)] pb-4">
        <div>
          <h2
            className="text-lg font-bold flex items-center gap-2"
            style={{ color: 'var(--color-text)', fontFamily: 'var(--font-sans)', letterSpacing: 'var(--tracking-kr)' }}
          >
            📈 주간 / 월간 상세 성장 분석 리포트
          </h2>
          <p className="text-xs mt-1" style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-sans)' }}>
            학습자의 상세 문해력 성장 지표 및 오케스트레이션 분석 데이터
          </p>
        </div>

        {/* 탭 버튼 */}
        <div className="flex bg-[var(--color-surface-alt)] p-1 rounded-lg self-start sm:self-center">
          <button
            onClick={() => setTab('weekly')}
            className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-all duration-200 ${
              tab === 'weekly'
                ? 'bg-white shadow-sm text-[var(--color-primary)]'
                : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
            }`}
            style={{ fontFamily: 'var(--font-sans)' }}
          >
            주간 분석
          </button>
          <button
            onClick={() => setTab('monthly')}
            className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-all duration-200 ${
              tab === 'monthly'
                ? 'bg-white shadow-sm text-[var(--color-primary)]'
                : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
            }`}
            style={{ fontFamily: 'var(--font-sans)' }}
          >
            월간 분석
          </button>
        </div>
      </div>

      {/* ── 탭 콘텐츠 (Framer Motion 애니메이션) ── */}
      <AnimatePresence mode="wait">
        <motion.div
          key={tab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.25, ease: 'easeOut' }}
          className="space-y-6"
        >
          {/* ── 상단: 차트 영역 (2열 레이아웃) ── */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            {/* 1. 레이더 차트 (문해력 5대 핵심 지표) */}
            <div className="lg:col-span-6 flex flex-col justify-between p-4 bg-[var(--color-bg)] rounded-[var(--radius-md)] border border-[var(--color-border)]">
              <div>
                <h3 className="text-sm font-semibold flex items-center gap-1.5 mb-1" style={{ color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}>
                  다면 역량 성장 분석 (문해 5대 지표)
                </h3>
                <p className="text-xs mb-4" style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-sans)' }}>
                  케어 미적용 상태와 적용 후의 세부 역량 성장 비교
                </p>
              </div>

              <div className="h-64 w-full flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart cx="50%" cy="50%" outerRadius="80%" data={currentRadarData}>
                    <PolarGrid stroke="var(--color-border)" />
                    <PolarAngleAxis
                      dataKey="subject"
                      tick={{ fill: 'var(--color-text-secondary)', fontSize: 11, fontFamily: 'var(--font-sans)' }}
                    />
                    <PolarRadiusAxis
                      angle={30}
                      domain={[0, 100]}
                      tick={{ fill: 'var(--color-text-muted)', fontSize: 9 }}
                      axisLine={false}
                    />
                    <Radar
                      name="케어 미적용"
                      dataKey="before"
                      stroke="var(--color-text-muted)"
                      fill="var(--color-text-muted)"
                      fillOpacity={0.1}
                      strokeWidth={1.5}
                      strokeDasharray="4 4"
                    />
                    <Radar
                      name="케어 적용"
                      dataKey="after"
                      stroke="var(--color-primary)"
                      fill="var(--color-primary)"
                      fillOpacity={0.25}
                      strokeWidth={2}
                    />
                    <Tooltip content={<CustomRadarTooltip />} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>

              {/* 레이더 범례 */}
              <div className="flex justify-center gap-4 mt-2 text-xs">
                <div className="flex items-center gap-1">
                  <span className="w-3 h-0.5 bg-[var(--color-text-muted)] border-dashed border-t inline-block" />
                  <span style={{ color: 'var(--color-text-secondary)' }}>케어 미적용</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="w-3 h-2 bg-[var(--color-primary-tint)] border border-[var(--color-primary)] rounded-sm inline-block" />
                  <span style={{ color: 'var(--color-text-secondary)' }}>케어 적용 (현재)</span>
                </div>
              </div>
            </div>

            {/* 2. 복합 차트 (독해 시간 & XP 트렌드) */}
            <div className="lg:col-span-6 flex flex-col justify-between p-4 bg-[var(--color-bg)] rounded-[var(--radius-md)] border border-[var(--color-border)]">
              <div>
                <h3 className="text-sm font-semibold flex items-center gap-1.5 mb-1" style={{ color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}>
                  독해 학습 시간 & 획득 XP 추이
                </h3>
                <p className="text-xs mb-4" style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-sans)' }}>
                  일별/주차별 집중 독해 시간(분) 및 미션 달성으로 획득한 경험치
                </p>
              </div>

              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={currentActivityData} margin={{ top: 10, right: -5, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis
                      dataKey="label"
                      tick={{ fill: 'var(--color-text-secondary)', fontSize: 11, fontFamily: 'var(--font-sans)' }}
                      axisLine={{ stroke: 'var(--color-border)' }}
                      tickLine={false}
                    />
                    {/* YAxis 좌측: 독해 시간 */}
                    <YAxis
                      yAxisId="left"
                      orientation="left"
                      tick={{ fill: 'var(--color-text-secondary)', fontSize: 10, fontFamily: 'var(--font-sans)' }}
                      axisLine={false}
                      tickLine={false}
                      label={{ value: '시간 (분)', angle: -90, position: 'insideLeft', offset: 10, fill: 'var(--color-text-muted)', fontSize: 10 }}
                    />
                    {/* YAxis 우측: XP */}
                    <YAxis
                      yAxisId="right"
                      orientation="right"
                      tick={{ fill: 'var(--color-text-secondary)', fontSize: 10, fontFamily: 'var(--font-sans)' }}
                      axisLine={false}
                      tickLine={false}
                      label={{ value: '경험치 (XP)', angle: 90, position: 'insideRight', offset: 10, fill: 'var(--color-text-muted)', fontSize: 10 }}
                    />
                    <Tooltip content={<CustomActivityTooltip />} />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px', fontFamily: 'var(--font-sans)' }} />
                    <Bar
                      yAxisId="left"
                      dataKey="time"
                      name="독해 시간"
                      fill="var(--color-primary)"
                      radius={[4, 4, 0, 0]}
                      maxBarSize={30}
                    />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="xp"
                      name="획득 XP"
                      stroke="var(--color-growth)"
                      strokeWidth={2.5}
                      dot={{ fill: 'var(--color-growth)', r: 4, stroke: 'var(--color-surface)', strokeWidth: 1.5 }}
                      activeDot={{ r: 6 }}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* ── 하단: AI 피드백 & 어휘 마스터 보드 ── */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            
            {/* AI 리터러시 코치 제언 */}
            <div className="md:col-span-7 p-5 bg-[var(--color-surface-alt)] rounded-[var(--radius-md)] border border-[var(--color-border)] flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-xl"></span>
                  <h4 className="text-sm font-bold" style={{ color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}>
                    AI 리터러시 코치의 주간 성장 처방전
                  </h4>
                </div>
                
                {tab === 'weekly' ? (
                  <div className="space-y-3 text-xs leading-relaxed" style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-sans)' }}>
                    {data.weekly.prescription?.map((p: string, i: number) => (
                      <p key={i} dangerouslySetInnerHTML={{ __html: p }} />
                    ))}
                  </div>
                ) : (
                  <div className="space-y-3 text-xs leading-relaxed" style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-sans)' }}>
                    {data.monthly.prescription?.map((p: string, i: number) => (
                      <p key={i} dangerouslySetInnerHTML={{ __html: p }} />
                    ))}
                  </div>
                )}
              </div>

              {/* 핵심 성과 요약 */}
              <div className="mt-4 pt-4 border-t border-[var(--color-border)] flex items-center justify-between text-xs font-semibold">
                <span style={{ color: 'var(--color-text-secondary)' }}>핵심 성장 성과</span>
                <span className="text-[var(--color-growth)]">
                  {topGrowthLabel}
                </span>
              </div>
            </div>

            {/* 어휘 마스터 보드 */}
            <div className="md:col-span-5 p-5 bg-[var(--color-surface)] rounded-[var(--radius-md)] border border-[var(--color-border)] flex flex-col justify-between">
              <div>
                <h4 className="text-sm font-bold mb-3 flex items-center gap-1.5" style={{ color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}>
                  {tab === 'weekly' ? '이번 주' : '이번 달'} 습득 핵심 어휘 보드
                </h4>
                <div className="space-y-3">
                  {currentWords.map((item: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-lg border border-[var(--color-border)] hover:bg-[var(--color-surface-alt)] transition-colors duration-200"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-bold" style={{ color: 'var(--color-text)' }}>
                          {item.word}
                        </span>
                        <div className="flex items-center gap-1">
                          <span
                            className="px-1.5 py-0.5 text-[10px] font-medium rounded"
                            style={{
                              backgroundColor:
                                item.level === '상'
                                  ? 'var(--color-nudge-hard-tint)'
                                  : item.level === '중'
                                  ? 'var(--color-nudge-medium-tint)'
                                  : 'var(--color-primary-tint)',
                              color:
                                item.level === '상'
                                  ? 'var(--color-nudge-hard)'
                                  : item.level === '중'
                                  ? 'var(--color-nudge-medium)'
                                  : 'var(--color-primary)',
                            }}
                          >
                            난이도:{item.level}
                          </span>
                          <span
                            className="px-1.5 py-0.5 text-[10px] font-bold rounded"
                            style={{
                              backgroundColor:
                                item.status === 'completed'
                                  ? 'var(--color-growth-tint)'
                                  : 'var(--color-nudge-medium-tint)',
                              color:
                                item.status === 'completed'
                                  ? 'var(--color-growth)'
                                  : 'var(--color-nudge-medium)',
                            }}
                          >
                            {item.status === 'completed' ? '완료' : '복습 필요'}
                          </span>
                        </div>
                      </div>
                      <p className="text-[11px] leading-tight" style={{ color: 'var(--color-text-secondary)', fontFamily: 'var(--font-sans)' }}>
                        {item.meaning}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* 단어장 바로가기 버튼 */}
              <button
                className="mt-4 w-full py-2 bg-[var(--color-surface-alt)] border border-[var(--color-border)] hover:bg-[var(--color-border)] text-xs font-semibold rounded-lg transition-colors duration-200"
                style={{ color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}
              >
                전체 단어장 보러가기
              </button>
            </div>

          </div>

        </motion.div>
      </AnimatePresence>

    </Card>
  );
}
