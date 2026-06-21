import React from 'react';

/**
 * HardNudge Component Stub (TODO: 6/2x)
 * 3단계 개입: 읽기 진행 차단 및 인터랙션 유도 (심각한 집중력 이탈)
 */
export const HardNudge: React.FC<{ message?: string; onResolve?: () => void }> = ({ message, onResolve }) => {
  return (
    <div className="p-4 bg-nudge-hard-tint border-l-4 border-nudge-hard rounded-r-md text-sm text-text">
      <div className="font-weight-semibold text-nudge-hard mb-1">🚨 리딩 락다운 (Hard Nudge)</div>
      <p className="mb-3">{message || "집중도가 많이 저하되었습니다. 잠시 읽기를 멈추고 환기를 위한 질문에 답해보세요."}</p>
      {onResolve && (
        <button 
          onClick={onResolve}
          className="px-3 py-1.5 bg-nudge-hard hover:opacity-90 text-surface text-xs font-weight-medium rounded-md"
        >
          해제 질문 풀기
        </button>
      )}
    </div>
  );
};

export default HardNudge;
