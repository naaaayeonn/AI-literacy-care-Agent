import React from 'react';
import { motion } from 'framer-motion';

interface LevelBarProps {
  level?: number;
  percentage?: number;
}

/**
 * LevelBar Component
 * 현재 성장 레벨과 다음 레벨까지의 진행 상황을 시각화합니다.
 * framer-motion을 통해 게이지 바 충전 애니메이션을 부드럽게 표현합니다.
 */
export const LevelBar: React.FC<LevelBarProps> = ({ level = 1, percentage = 45 }) => {
  return (
    <div className="w-full" style={{ fontFamily: 'var(--font-sans)' }}>
      {/* 라벨 영역 */}
      <div className="flex justify-between items-center mb-1.5 text-xs">
        <div className="flex items-center gap-1">
          <span
            className="flex items-center justify-center w-5 h-5 rounded-md text-[10px] font-bold text-white shadow-sm"
            style={{
              backgroundColor: 'var(--color-level)',
              boxShadow: '0 0 8px rgba(130, 87, 230, 0.4)',
            }}
          >
            L
          </span>
          <span className="font-semibold" style={{ color: 'var(--color-text)' }}>
            성장 레벨
          </span>
        </div>
        <span style={{ color: 'var(--color-text-secondary)', fontWeight: 600 }}>
          Lv.{level} <span style={{ color: 'var(--color-text-muted)', fontWeight: 400 }}>({percentage}%)</span>
        </span>
      </div>

      {/* 게이지 바 영역 */}
      <div
        className="w-full rounded-full h-3.5 overflow-hidden border border-[var(--color-border)] relative cursor-help"
        title={`Lv.${level + 1}까지 ${100 - percentage}% 남음`}
        style={{
          backgroundColor: 'var(--color-surface-alt)',
        }}
      >
        <motion.div
          className="h-full rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          style={{
            backgroundColor: 'var(--color-level)',
            backgroundImage: 'linear-gradient(90deg, var(--color-level), #9A7CFA)',
            boxShadow: 'inset 0 1px 1px rgba(255,255,255,0.2)',
          }}
        />
        {/* 잔여 가이드선 */}
        <div
          className="absolute inset-0 flex items-center justify-center text-[9px] pointer-events-none font-bold"
          style={{
            color: percentage > 55 ? '#fff' : 'var(--color-text-secondary)',
            textShadow: percentage > 55 ? '0 1px 2px rgba(0,0,0,0.2)' : 'none',
          }}
        >
          다음 레벨까지 {100 - percentage}%
        </div>
      </div>
    </div>
  );
};

export default LevelBar;
