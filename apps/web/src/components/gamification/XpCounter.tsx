import React, { useEffect, useState } from 'react';
import { animate } from 'framer-motion';

interface XpCounterProps {
  xp: number;
}

/**
 * XpCounter Component
 * 경험치가 누적될 때 숫자가 끊기지 않고 롤링 업(Count-up) 애니메이션을 부드럽게 출력합니다.
 */
export const XpCounter: React.FC<XpCounterProps> = ({ xp }) => {
  const [displayXp, setDisplayXp] = useState(xp);

  useEffect(() => {
    // 이전 displayXp 값부터 새로운 xp 값까지 0.8초 동안 카운트업 진행
    const controls = animate(displayXp, xp, {
      duration: 0.8,
      ease: 'easeOut',
      onUpdate: (latest) => setDisplayXp(Math.round(latest)),
    });
    return () => controls.stop();
  }, [xp]);

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontFamily: 'var(--font-sans)' }}>
      <span style={{ fontSize: '14px', animation: 'pulse 2s infinite' }}>✨</span>
      <span
        style={{
          fontSize: 'var(--text-sm)',
          fontWeight: 700,
          color: 'var(--color-xp)',
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        {displayXp.toLocaleString()}
      </span>
      <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', fontWeight: 500 }}>
        XP
      </span>
    </div>
  );
};

export default XpCounter;
