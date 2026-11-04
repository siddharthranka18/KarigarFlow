import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface StatCardProps {
  title: string;
  value: string;
  fineGoldValue?: string;
  badge?: {
    text: string;
    variant: 'success' | 'warning' | 'danger' | 'brass' | 'default';
  };
  subtitle?: string;
  icon?: React.ReactNode;
  className?: string;
  isLossAlert?: boolean;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  fineGoldValue,
  badge,
  subtitle,
  icon,
  className,
  isLossAlert = false,
}) => {
  return (
    <div
      className={twMerge(
        clsx(
          'bg-white border rounded-sm p-4 relative overflow-hidden transition-all duration-150',
          isLossAlert
            ? 'border-status-danger bg-red-50/20 shadow-sm'
            : 'border-parchment-300 hover:border-parchment-400 shadow-subtle',
          className
        )
      )}
    >
      {/* Antique brass subtle top accent indicator */}
      <div
        className={clsx(
          'absolute top-0 left-0 right-0 h-0.5',
          isLossAlert ? 'bg-status-danger' : 'bg-brass-500/70'
        )}
      />

      <div className="flex items-start justify-between mb-2">
        <span className="text-xs font-semibold text-charcoal-600 tracking-wider uppercase">
          {title}
        </span>
        {icon && <span className="text-charcoal-400">{icon}</span>}
      </div>

      <div className="flex items-baseline gap-2 mb-1">
        <span className="text-2xl font-mono font-semibold text-charcoal-900 tabular-nums">
          {value}
        </span>
        {badge && (
          <span
            className={clsx(
              'text-[10px] font-mono px-1.5 py-0.5 rounded-xs uppercase font-medium border',
              badge.variant === 'danger' && 'bg-status-danger-bg text-status-danger border-status-danger-border',
              badge.variant === 'warning' && 'bg-status-warning-bg text-status-warning border-status-warning-border',
              badge.variant === 'success' && 'bg-status-success-bg text-status-success border-status-success-border',
              badge.variant === 'brass' && 'bg-brass-50 text-brass-800 border-brass-200',
              badge.variant === 'default' && 'bg-parchment-100 text-charcoal-600 border-parchment-300'
            )}
          >
            {badge.text}
          </span>
        )}
      </div>

      {fineGoldValue && (
        <div className="text-xs font-mono text-brass-700 mb-1 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-brass-500" />
          <span>{fineGoldValue} Pure Fine</span>
        </div>
      )}

      {subtitle && (
        <p className="text-xs text-charcoal-500 mt-2 pt-2 border-t border-parchment-200">
          {subtitle}
        </p>
      )}
    </div>
  );
};

