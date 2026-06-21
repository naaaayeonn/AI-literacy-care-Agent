import React from 'react';
import LiteracyScoreChart from './LiteracyScoreChart';

/**
 * GrowthDashboard Component Stub (TODO: 6/2x)
 * 학습 성장 상태와 통계 지표를 시각화하는 전체 대시보드 셸입니다.
 */
export const GrowthDashboard: React.FC = () => {
  return (
    <div className="p-6 bg-surface rounded-lg border border-border shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-weight-bold text-text">성장 대시보드</h2>
          <p className="text-xs text-text-secondary">리터러시 케어 서비스 이용에 따른 점수 추이</p>
        </div>
        <div className="flex gap-2">
          <span className="flex items-center gap-1.5 text-xs text-text-secondary">
            <span className="w-2.5 h-2.5 rounded-full bg-comprehension" />
            케어 전
          </span>
          <span className="flex items-center gap-1.5 text-xs text-text-secondary">
            <span className="w-2.5 h-2.5 rounded-full bg-growth" />
            케어 후
          </span>
        </div>
      </div>

      <div className="h-64 mb-6">
        <LiteracyScoreChart />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-surface-alt rounded-lg border border-border text-center">
          <div className="text-xs text-text-secondary">평균 이해도 향상율</div>
          <div className="text-xl font-weight-bold text-growth mt-1">+34.8%</div>
        </div>
        <div className="p-4 bg-surface-alt rounded-lg border border-border text-center">
          <div className="text-xs text-text-secondary">집중 유지 시간</div>
          <div className="text-xl font-weight-bold text-primary mt-1">+12.4분</div>
        </div>
      </div>
    </div>
  );
};

export default GrowthDashboard;
