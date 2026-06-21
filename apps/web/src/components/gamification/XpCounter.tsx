import React from 'react';

/**
 * XpCounter Component Stub (TODO: 6/2x)
 * 획득한 경험치(XP)를 예쁘게 카운팅해서 보여주는 UI 스텁입니다.
 */
export const XpCounter: React.FC<{ xp?: number }> = ({ xp = 150 }) => {
  return (
    <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-surface-alt border border-border rounded-full text-xs font-weight-bold">
      <span className="text-xp">✨</span>
      <span className="text-text">{xp} <span className="text-text-muted font-weight-medium">XP</span></span>
    </div>
  );
};

export default XpCounter;
