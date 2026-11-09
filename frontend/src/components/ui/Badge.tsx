import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'brass' | 'stone';
  size?: 'sm' | 'md';
  className?: string;
  icon?: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  className,
  icon,
}) => {
  const baseStyles = 'inline-flex items-center font-mono font-medium rounded-md select-none';

  const variants = {
    default: 'bg-parchment-200 text-charcoal-700 border border-parchment-300',
    success: 'bg-status-success-bg text-status-success border border-status-success-border',
    warning: 'bg-status-warning-bg text-status-warning border border-status-warning-border',
    danger: 'bg-status-danger-bg text-status-danger border border-status-danger-border',
    brass: 'bg-brass-100 text-brass-800 border border-brass-300',
    stone: 'bg-stone-100 text-stone-700 border border-stone-300',
  };

  const sizes = {
    sm: 'text-[10px] px-1.5 py-0.5 gap-1',
    md: 'text-xs px-2 py-0.5 gap-1.5',
  };

  return (
    <span className={twMerge(clsx(baseStyles, variants[variant], sizes[size], className))}>
      {icon && <span className="flex-shrink-0">{icon}</span>}
      {children}
    </span>
  );
};

