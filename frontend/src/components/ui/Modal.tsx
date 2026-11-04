import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl';
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  maxWidth = 'lg',
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.body.style.overflow = 'unset';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const maxWidths = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-charcoal-950/60 backdrop-blur-xs transition-opacity"
        onClick={onClose}
      />

      {/* Modal Dialog */}
      <div
        className={twMerge(
          clsx(
            'relative bg-white border border-parchment-300 rounded-sm shadow-xl w-full z-10 overflow-hidden max-h-[90vh] flex flex-col',
            maxWidths[maxWidth]
          )
        )}
      >
        {/* Header with antique brass accent */}
        <div className="relative border-b border-parchment-300 px-5 py-4 bg-[#FAF7F0] flex items-center justify-between">
          <div className="absolute top-0 left-0 right-0 h-1 bg-brass-600" />
          <div>
            <h3 className="text-base font-semibold text-charcoal-900 tracking-tight">{title}</h3>
            {subtitle && <p className="text-xs text-charcoal-600 mt-0.5">{subtitle}</p>}
          </div>
          <button
            onClick={onClose}
            className="text-charcoal-400 hover:text-charcoal-700 transition-colors p-1 rounded-sm focus:outline-none"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content body */}
        <div className="p-5 overflow-y-auto space-y-4">{children}</div>
      </div>
    </div>
  );
};

