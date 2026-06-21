import React from 'react';

/**
 * LevelBar Component Stub (TODO: 6/2x)
 * 현재 레벨과 다음 레벨까지의 진행 상황을 채우는 바입니다.
 */
export const LevelBar: React.FC<{ level?: number; percentage?: number }> = ({ level = 1, percentage = 45 }) => {
  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-1 text-xs">
        <span className="font-weight-semibold text-level">성장 레벨</span>
        <span className="text-text-secondary">Lv.{level} ({percentage}%)</span>
      </div>
      <div className="w-full bg-surface-alt rounded-full h-2.5 overflow-hidden border border-border">
        <div 
          className="bg-level h-full rounded-full transition-all duration-500" 
          style={{ width: `${percentage}%` }} 
        />
      </div>
    </div>
  );
};

export default LevelBar;
