import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  unit?: string; // e.g. 'g', '%', 'INR'
  rightElement?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, unit, rightElement, className, ...props }, ref) => {
    const generatedId = React.useId();
    const inputId = props.id || generatedId;
    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className="block text-xs font-medium text-charcoal-700 mb-1.5">
            {label}
            {props.required && <span className="text-status-danger ml-0.5">*</span>}
          </label>
        )}
        <div className="relative">
          <input
            ref={ref}
            className={twMerge(
              clsx(
                'w-full bg-white border text-sm text-charcoal-900 rounded-lg px-3 py-2 transition-colors duration-150',
                'placeholder:text-charcoal-400 focus:outline-none focus:ring-1',
                unit || rightElement ? 'pr-12' : '',
                error
                  ? 'border-status-danger focus:border-status-danger focus:ring-status-danger'
                  : 'border-parchment-300 focus:border-brass-600 focus:ring-brass-500',
                className
              )
            )}
            {...props}
            id={inputId}
          />
          {(unit || rightElement) && (
            <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none text-xs font-mono font-medium text-charcoal-500">
              {unit || rightElement}
            </div>
          )}
        </div>
        {error ? (
          <p className="text-xs text-status-danger mt-1 font-medium">{error}</p>
        ) : helperText ? (
          <p className="text-xs text-charcoal-500 mt-1">{helperText}</p>
        ) : null}
      </div>
    );
  }
);

Input.displayName = 'Input';

