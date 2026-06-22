import React from 'react';
import { motion } from 'framer-motion';

interface HighlightTextProps {
  children: React.ReactNode;
  /** 하이라이트 강도: normal(기본), strong(진하게) */
  intensity?: 'normal' | 'strong';
  /** 하이라이트 색 오버라이드 (없으면 --color-highlight 사용) */
  color?: string;
}

/**
 * HighlightText Component
 * 지정된 텍스트 범위에 형광펜 배경을 씌웁니다.
 * framer-motion을 통해 왼쪽에서 오른쪽으로 칠해지는 드로잉 애니메이션 효과를 부여합니다.
 */
export const HighlightText: React.FC<HighlightTextProps> = ({
  children,
  intensity = 'normal',
  color,
}) => {
  const bgColor = color ?? 'var(--color-highlight)';
  const opacity = intensity === 'strong' ? 1 : 0.75;

  return (
    <motion.mark
      initial={{ backgroundSize: '0% 100%' }}
      animate={{ backgroundSize: '100% 100%' }}
      transition={{ duration: 0.6, ease: [0.25, 1, 0.5, 1], delay: 0.1 }}
      style={{
        background: `linear-gradient(to right, ${bgColor}, ${bgColor}) no-repeat left bottom`,
        color: 'inherit',
        padding: '1px 3px',
        borderRadius: '3px',
        opacity,
        boxDecorationBreak: 'clone',
        WebkitBoxDecorationBreak: 'clone',
        display: 'inline',
        transition: 'opacity 0.3s ease',
      }}
    >
      {children}
    </motion.mark>
  );
};

export default HighlightText;
