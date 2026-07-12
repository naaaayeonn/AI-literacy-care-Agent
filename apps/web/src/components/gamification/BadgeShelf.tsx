import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, Zap, Target, Flame } from 'lucide-react';
import { useScoreStore } from '../../stores/scoreStore';

// 전체 배지 카탈로그
const BADGE_CATALOG = [
  { id: 'first-read',    icon: BookOpen, name: '첫 완독',    desc: '첫 번째 글을 끝까지 읽었어요!' },
  { id: 'focus-master',  icon: Zap,      name: '초집중 리더', desc: '평균 집중도 90% 이상 달성!' },
  { id: 'vocab-master',  icon: Target,   name: '어휘 마스터', desc: '용어 툴팁을 10번 이상 확인했어요!' },
  { id: 'streak-3',      icon: Flame,    name: '3일 연속',   desc: '3일 연속 읽기 세션 완료!' },
];

interface BadgeShelfProps {
  /** true이면 이름 숨기고 아이콘만 표시 (FloatingPanel 축약형) */
  compact?: boolean;
}

export const BadgeShelf: React.FC<BadgeShelfProps> = ({ compact = false }) => {
  const { badges } = useScoreStore();
  const acquiredMap = new Map(badges.map((b) => [b.id, b]));

  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: compact ? '10px' : '14px',
        justifyContent: compact ? 'flex-start' : 'space-between',
      }}
    >
      {BADGE_CATALOG.map((badge) => {
        const acquiredBadge = acquiredMap.get(badge.id);
        const acquired = !!acquiredBadge;
        return (
          <BadgeItem
            key={badge.id}
            id={badge.id}
            icon={badge.icon}
            name={badge.name}
            desc={badge.desc}
            acquired={acquired}
            acquiredAt={acquiredBadge?.acquiredAt}
            compact={compact}
          />
        );
      })}
    </div>
  );
};

interface BadgeItemProps {
  id: string;
  icon: React.ElementType;
  name: string;
  desc: string;
  acquired: boolean;
  acquiredAt?: string;
  compact: boolean;
}

const BadgeItem: React.FC<BadgeItemProps> = ({
  icon: Icon,
  name,
  desc,
  acquired,
  acquiredAt,
  compact,
}) => {
  const [isHovered, setIsHovered] = useState(false);

  // 날짜 포맷팅
  const formattedDate = acquiredAt
    ? new Date(acquiredAt).toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
      })
    : '';

  return (
    <div
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        position: 'relative',
        display: 'flex',
        flexDirection: compact ? 'row' : 'column',
        alignItems: 'center',
        gap: '6px',
        cursor: 'pointer',
      }}
    >
      {/* 배지 아이콘 원형 */}
      <motion.div
        whileHover={{ scale: 1.1, y: -2 }}
        whileTap={{ scale: 0.95 }}
        style={{
          width: compact ? '36px' : '48px',
          height: compact ? '36px' : '48px',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: compact ? '18px' : '24px',
          backgroundColor: acquired ? 'var(--color-surface)' : 'var(--color-surface-alt)',
          border: `2px solid ${acquired ? 'var(--color-xp)' : 'var(--color-border)'}`,
          boxShadow: acquired
            ? '0 0 12px rgba(242, 183, 5, 0.4), var(--shadow-sm)'
            : 'none',
          opacity: acquired ? 1 : 0.35,
          filter: acquired ? 'none' : 'grayscale(1)',
          transition: 'border-color 0.3s, box-shadow 0.3s, opacity 0.3s',
        }}
      >
        <Icon size={compact ? 18 : 24} />
      </motion.div>

      {/* compact 모드가 아닐 때 배지 이름 표시 */}
      {!compact && (
        <span
          style={{
            fontSize: 'var(--text-xs)',
            fontWeight: acquired ? 600 : 400,
            color: acquired ? 'var(--color-text)' : 'var(--color-text-muted)',
            fontFamily: 'var(--font-sans)',
            textAlign: 'center',
            maxWidth: '64px',
            lineHeight: '1.2',
          }}
        >
          {name}
        </span>
      )}

      {/* ── 커스텀 툴팁 (Portal 없이 CSS absolute 활용) ── */}
      <AnimatePresence>
        {isHovered && (
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.95 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            style={{
              position: 'absolute',
              bottom: compact ? '42px' : '62px',
              left: compact ? '18px' : '50%',
              transform: compact ? 'none' : 'translateX(-50%)',
              zIndex: 100,
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              padding: '10px 12px',
              boxShadow: 'var(--shadow-panel)',
              width: '180px',
              pointerEvents: 'none',
              fontFamily: 'var(--font-sans)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
              <span style={{ color: acquired ? 'var(--color-primary)' : 'var(--color-text-muted)' }}><Icon size={16} /></span>
              <span style={{ fontWeight: 700, fontSize: 'var(--text-xs)', color: 'var(--color-text)' }}>
                {name}
              </span>
            </div>
            
            <p style={{ fontSize: '10px', color: 'var(--color-text-secondary)', lineHeight: '1.4', margin: '4px 0' }}>
              {desc}
            </p>

            <div
              style={{
                marginTop: '6px',
                paddingTop: '6px',
                borderTop: '1px solid var(--color-border)',
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '9px',
                fontWeight: 600,
              }}
            >
              <span style={{ color: acquired ? 'var(--color-growth)' : 'var(--color-text-muted)' }}>
                {acquired ? '획득 완료' : '미획득'}
              </span>
              {acquired && formattedDate && (
                <span style={{ color: 'var(--color-text-muted)' }}>{formattedDate}</span>
              )}
            </div>

            {/* 말꼬리 화살표 */}
            <div
              style={{
                position: 'absolute',
                bottom: '-6px',
                left: compact ? '8px' : '50%',
                transform: compact ? 'none' : 'translateX(-50%) rotate(45deg)',
                width: '10px',
                height: '10px',
                backgroundColor: 'var(--color-surface)',
                borderRight: '1px solid var(--color-border)',
                borderBottom: '1px solid var(--color-border)',
              }}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default BadgeShelf;
