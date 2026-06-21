import React from 'react';

/**
 * TermTooltip Component Stub (TODO: 6/2x)
 * 어려운 어휘 마우스 오버 시 표시할 툴팁 뼈대입니다.
 */
export const TermTooltip: React.FC<{ term?: string; definition?: string }> = ({ term, definition }) => {
  return (
    <div className="inline-block relative group">
      <span className="underline decoration-dotted decoration-primary cursor-help">
        {term || "어휘"}
      </span>
      <div className="absolute hidden group-hover:block bottom-full left-1/2 -translate-x-1/2 mb-2 p-3 bg-surface border border-border rounded-md shadow-md text-sm z-tooltip w-64">
        <p className="font-weight-semibold text-text">{term || "어휘"}</p>
        <p className="text-text-secondary mt-1">{definition || "어휘의 의미에 대한 설명입니다. (TODO 6/2x)"}</p>
      </div>
    </div>
  );
};

export default TermTooltip;
