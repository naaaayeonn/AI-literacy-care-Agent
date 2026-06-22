import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface TermTooltipProps {
  term: string;
  definition: string;
  /** 팝업이 열릴 방향 */
  placement?: 'top' | 'bottom';
  children?: React.ReactNode;
}

/**
 * TermTooltip Component
 * 특정 용어에 마우스를 올리면 RAG 기반 풀이가 팝업으로 표시됩니다.
 * AnimatePresence와 framer-motion을 통해 부드러운 스케일 및 페이드 효과로 나타납니다.
 */
export const TermTooltip: React.FC<TermTooltipProps> = ({
  term,
  definition,
  placement = 'top',
  children,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);

  // 외부 클릭 시 닫기
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [isOpen]);

  const tooltipBase: React.CSSProperties = {
    position: 'absolute',
    left: '50%',
    width: '240px',
    backgroundColor: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    boxShadow: 'var(--shadow-panel)',
    padding: '10px 12px',
    zIndex: 'var(--z-tooltip)' as unknown as number,
    pointerEvents: 'none',
    fontFamily: 'var(--font-sans)',
    fontSize: 'var(--text-sm)',
    lineHeight: 'var(--leading-normal)',
  };

  const tooltipStyle: React.CSSProperties =
    placement === 'top'
      ? { ...tooltipBase, bottom: 'calc(100% + 8px)' }
      : { ...tooltipBase, top: 'calc(100% + 8px)' };

  return (
    <span
      ref={ref}
      style={{ position: 'relative', display: 'inline' }}
      onMouseEnter={() => setIsOpen(true)}
      onMouseLeave={() => setIsOpen(false)}
      onFocus={() => setIsOpen(true)}
      onBlur={() => setIsOpen(false)}
    >
      {/* 용어 텍스트 — 점선 밑줄로 툴팁 암시 */}
      <span
        style={{
          borderBottom: '1.5px dashed var(--color-primary)',
          color: 'var(--color-primary)',
          cursor: 'help',
          fontWeight: 600,
        }}
        tabIndex={0}
        aria-describedby={`tooltip-${term}`}
      >
        {children ?? term}
      </span>

      {/* 팝업 툴팁 */}
      <AnimatePresence>
        {isOpen && (
          <motion.span
            id={`tooltip-${term}`}
            role="tooltip"
            initial={{ opacity: 0, y: placement === 'top' ? 8 : -8, scale: 0.95, x: '-50%' }}
            animate={{ opacity: 1, y: 0, scale: 1, x: '-50%' }}
            exit={{ opacity: 0, y: placement === 'top' ? 8 : -8, scale: 0.95, x: '-50%' }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            style={tooltipStyle}
          >
            <span
              style={{
                display: 'block',
                fontWeight: 700,
                color: 'var(--color-text)',
                marginBottom: '4px',
              }}
            >
              {term}
            </span>
            <span style={{ color: 'var(--color-text-secondary)', display: 'block', fontSize: '11px', lineHeight: '1.4' }}>
              {definition}
            </span>
            <span
              style={{
                display: 'block',
                marginTop: '8px',
                fontSize: '9px',
                fontWeight: 600,
                color: 'var(--color-text-muted)',
              }}
            >
              📖 AI 리터러시 케어 용어 사전
            </span>
            {/* 말꼬리 화살표 */}
            <div
              style={{
                position: 'absolute',
                left: '50%',
                transform: 'translateX(-50%) rotate(45deg)',
                width: '8px',
                height: '8px',
                backgroundColor: 'var(--color-surface)',
                borderRight: '1px solid var(--color-border)',
                borderBottom: placement === 'top' ? '1px solid var(--color-border)' : 'none',
                borderTop: placement === 'bottom' ? '1px solid var(--color-border)' : 'none',
                bottom: placement === 'top' ? '-5px' : 'auto',
                top: placement === 'bottom' ? '-5px' : 'auto',
              }}
            />
          </motion.span>
        )}
      </AnimatePresence>
    </span>
  );
};

export default TermTooltip;
