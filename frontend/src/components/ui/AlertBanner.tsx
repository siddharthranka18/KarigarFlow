import React from 'react';
import { AlertTriangle, Info, CheckCircle2, XCircle } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface AlertBannerProps {
  type?: 'warning' | 'danger' | 'info' | 'success';
  title?: string;
  message: string;
  actionText?: string;
  onAction?: () => void;
  className?: string;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({
  type = 'warning',
  title,
  message,
  actionText,
  onAction,
  className,
}) => {
  const styles = {
    warning: {
      container: 'bg-status-warning-bg border-status-warning-border text-status-warning',
      icon: <AlertTriangle className="w-4 h-4 flex-shrink-0 text-status-warning" />,
    },
    danger: {
      container: 'bg-status-danger-bg border-status-danger-border text-status-danger',
      icon: <XCircle className="w-4 h-4 flex-shrink-0 text-status-danger" />,
    },
    info: {
      container: 'bg-status-info-bg border-status-info-border text-status-info',
      icon: <Info className="w-4 h-4 flex-shrink-0 text-status-info" />,
    },
    success: {
      container: 'bg-status-success-bg border-status-success-border text-status-success',
      icon: <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-status-success" />,
    },
  };

  const current = styles[type];

  return (
    <div
      className={twMerge(
        clsx(
          'border rounded-lg p-3.5 flex items-start gap-3 shadow-subtle',
          current.container,
          className
        )
      )}
    >
      {current.icon}
      <div className="flex-1 text-xs">
        {title && <span className="font-semibold block mb-0.5">{title}</span>}
        <span className="leading-relaxed opacity-95">{message}</span>
      </div>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="text-xs font-semibold underline hover:opacity-80 transition-opacity ml-2 flex-shrink-0"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};

