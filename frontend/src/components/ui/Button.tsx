import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  icon,
  className,
  disabled,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-colors duration-150 rounded-sm focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed select-none';

  const variants = {
    // Antique brass button with high contrast text
    primary: 'bg-brass-600 text-white hover:bg-brass-700 active:bg-brass-800 focus:ring-brass-500 shadow-subtle',
    // Craft parchment/stone button
    secondary: 'bg-white text-charcoal-800 border border-parchment-300 hover:bg-parchment-100 hover:border-parchment-400 focus:ring-brass-400 shadow-subtle',
    outline: 'bg-transparent text-brass-700 border border-brass-400 hover:bg-brass-50 focus:ring-brass-500',
    danger: 'bg-status-danger text-white hover:bg-red-800 focus:ring-red-500',
    ghost: 'bg-transparent text-charcoal-700 hover:bg-parchment-200 focus:ring-charcoal-400',
  };

  const sizes = {
    sm: 'text-xs px-2.5 py-1.5 gap-1.5',
    md: 'text-sm px-3.5 py-2 gap-2',
    lg: 'text-base px-5 py-2.5 gap-2.5',
  };

  return (
    <button
      className={twMerge(clsx(baseStyles, variants[variant], sizes[size], className))}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
      ) : icon ? (
        <span className="flex-shrink-0">{icon}</span>
      ) : null}
      {children}
    </button>
  );
};

