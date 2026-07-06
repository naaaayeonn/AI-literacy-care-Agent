import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'flat' | 'nudge-soft' | 'nudge-medium' | 'nudge-hard';
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  className = '',
  ...props
}) => {
  const baseStyle = 'rounded-lg border transition-all';
  
  const variantStyles = {
    default: 'bg-surface border-border shadow-sm',
    flat: 'bg-surface-alt border-border',
    'nudge-soft': 'bg-nudge-soft-tint border-nudge-soft/30 text-text',
    'nudge-medium': 'bg-nudge-medium-tint border-nudge-medium/30 text-text',
    'nudge-hard': 'bg-nudge-hard-tint border-nudge-hard/30 text-text',
  };

  const combinedClassName = `${baseStyle} ${variantStyles[variant]} ${className}`;

  return (
    <div className={combinedClassName} {...props}>
      {children}
    </div>
  );
};

export default Card;
