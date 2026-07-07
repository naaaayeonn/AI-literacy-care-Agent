import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger';
  size?: 'sm' | 'md' | 'lg';
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  ...props
}) => {
  const baseStyle = 'font-sans font-weight-medium transition-colors cursor-pointer select-none rounded-md';
  
  const variantStyles = {
    primary: 'bg-primary hover:bg-primary-hover text-surface shadow-sm',
    secondary: 'bg-surface-alt hover:bg-border text-text',
    outline: 'bg-transparent hover:bg-primary-tint text-primary border border-primary',
    danger: 'bg-danger hover:opacity-90 text-surface shadow-sm',
  };

  const sizeStyles = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-5 py-2.5 text-base',
  };

  const combinedClassName = `${baseStyle} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`;

  return (
    <button className={combinedClassName} {...props}>
      {children}
    </button>
  );
};
export default Button;
