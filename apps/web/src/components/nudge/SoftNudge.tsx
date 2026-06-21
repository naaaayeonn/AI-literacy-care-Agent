import React from 'react';

/**
 * SoftNudge Component Stub (TODO: 6/2x)
 * 1단계 개입: 가벼운 시각적 환기 (집중도 저하 초기 단계)
 */
export const SoftNudge: React.FC<{ message?: string }> = ({ message }) => {
  return (
    <div className="p-4 bg-nudge-soft-tint border-l-4 border-nudge-soft rounded-r-md text-sm text-text">
      <div className="font-weight-semibold text-nudge-soft mb-1">💡 리터러시 케어 알림 (Soft Nudge)</div>
      <p>{message || "이 단락에 유용한 핵심 내용이 포함되어 있어요. 조금만 더 집중해 읽어볼까요?"}</p>
    </div>
  );
};

export default SoftNudge;
