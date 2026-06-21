import React from 'react';

/**
 * BadgeShelf Component Stub (TODO: 6/2x)
 * 획득한 배지들을 모아 보여주는 컴포넌트 뼈대입니다.
 */
export const BadgeShelf: React.FC = () => {
  // 예시 배지 데이터 stub
  const badges = [
    { emoji: "📚", name: "첫 완독", acquired: true },
    { emoji: "⚡", name: "초집중 리더", acquired: true },
    { emoji: "🎯", name: "어휘 마스터", acquired: false },
    { emoji: "🔥", name: "3일 연속", acquired: false }
  ];

  return (
    <div>
      <div className="text-xs font-weight-semibold text-text-secondary mb-2">업적 배지 보관함</div>
      <div className="flex gap-3">
        {badges.map((badge, idx) => (
          <div 
            key={idx} 
            className={`w-10 h-10 rounded-full border flex items-center justify-center text-lg relative group cursor-help transition-all ${
              badge.acquired 
                ? 'bg-surface border-border shadow-sm' 
                : 'bg-surface-alt border-border/50 filter grayscale opacity-40'
            }`}
          >
            <span>{badge.emoji}</span>
            <div className="absolute hidden group-hover:block bottom-full mb-1.5 px-2 py-1 bg-text text-surface text-[10px] rounded whitespace-nowrap z-tooltip">
              {badge.name} ({badge.acquired ? "획득" : "미획득"})
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default BadgeShelf;
