import React from 'react';

/**
 * HighlightText Component Stub (TODO: 6/2x)
 * 학습 촉진을 위한 스마트 하이라이팅을 렌더링하는 stub입니다.
 */
export const HighlightText: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  return (
    <span className="bg-highlight text-text font-weight-medium rounded-sm px-0.5">
      {children || "HighlightText Stub"}
    </span>
  );
};

export default HighlightText;
