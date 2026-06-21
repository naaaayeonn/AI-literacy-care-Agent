import React from 'react';
import LevelBar from '../gamification/LevelBar';
import BadgeShelf from '../gamification/BadgeShelf';
import XpCounter from '../gamification/XpCounter';

/**
 * FloatingControlPanel Component Stub (TODO: 6/2x)
 * 우측 상단 플로팅되어 실시간 진행 상황 및 에이전트 모니터링 정보를 제공하는 컴포넌트 뼈대입니다.
 */
export const FloatingControlPanel: React.FC = () => {
  return (
    <div className="bg-surface border border-border rounded-xl p-5 shadow-panel w-full space-y-4 font-sans">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-weight-bold text-text">실시간 케어 제어판</h3>
        <span className="inline-flex items-center gap-1.5 text-[11px] font-weight-semibold text-growth bg-growth-tint px-2 py-0.5 rounded-full">
          <span className="w-1.5 h-1.5 rounded-full bg-growth animate-pulse" />
          모니터링 활성
        </span>
      </div>

      {/* 실시간 집중도 & 읽기 진행률 (데모 핵심 지표 스텁) */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 bg-surface-alt rounded-lg border border-border">
          <div className="text-[11px] text-text-secondary">실시간 집중도</div>
          <div className="text-lg font-weight-bold text-primary mt-0.5">85%</div>
        </div>
        <div className="p-3 bg-surface-alt rounded-lg border border-border">
          <div className="text-[11px] text-text-secondary">읽기 진행률</div>
          <div className="text-lg font-weight-bold text-text mt-0.5">42%</div>
        </div>
      </div>

      <div className="space-y-3 pt-2">
        <LevelBar level={2} percentage={65} />
        
        <div className="flex justify-between items-center">
          <span className="text-xs text-text-secondary font-weight-medium">누적 경험치</span>
          <XpCounter xp={265} />
        </div>
        
        <hr className="border-border" />
        
        <BadgeShelf />
      </div>

      <div className="text-[10px] text-text-muted text-center pt-1 border-t border-border/50">
        시선 트래킹 감도: 상 (92%)
      </div>
    </div>
  );
};

export default FloatingControlPanel;
