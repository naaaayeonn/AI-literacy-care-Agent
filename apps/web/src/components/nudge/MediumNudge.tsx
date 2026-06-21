import React from 'react';

/**
 * MediumNudge Component Stub (TODO: 6/2x)
 * 2단계 개입: 주의 유도 질문 또는 요약 팝업 (지속적인 시선 이탈 감지)
 */
export const MediumNudge: React.FC<{ message?: string }> = ({ message }) => {
  return (
    <div className="p-4 bg-nudge-medium-tint border-l-4 border-nudge-medium rounded-r-md text-sm text-text">
      <div className="font-weight-semibold text-nudge-medium mb-1">⚠️ 주의 리마인더 (Medium Nudge)</div>
      <p>{message || "스크롤 속도가 조금 빠릅니다. 지금까지 읽은 핵심 용어의 정의를 다시 짚어드릴까요?"}</p>
    </div>
  );
};

export default MediumNudge;
