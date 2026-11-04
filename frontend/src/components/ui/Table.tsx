import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export const Table: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className,
}) => (
  <div className="w-full overflow-x-auto border border-parchment-300 rounded-sm bg-white shadow-subtle">
    <table className={twMerge('w-full text-left border-collapse', className)}>{children}</table>
  </div>
);

export const TableHead: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className,
}) => (
  <thead className={twMerge('bg-[#F8F5EE] border-b border-parchment-300', className)}>
    {children}
  </thead>
);

export const TableBody: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className,
}) => (
  <tbody className={twMerge('divide-y divide-parchment-200', className)}>{children}</tbody>
);

export const TableRow: React.FC<{
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  isLossAlert?: boolean;
}> = ({ children, className, onClick, isLossAlert }) => (
  <tr
    onClick={onClick}
    className={twMerge(
      clsx(
        'transition-colors duration-100',
        isLossAlert ? 'bg-red-50/40 hover:bg-red-50/70' : 'hover:bg-parchment-50/80',
        onClick && 'cursor-pointer',
        className
      )
    )}
  >
    {children}
  </tr>
);

export const TableHeaderCell: React.FC<{
  children: React.ReactNode;
  className?: string;
  align?: 'left' | 'center' | 'right';
}> = ({ children, className, align = 'left' }) => (
  <th
    className={twMerge(
      clsx(
        'px-3.5 py-2.5 text-xs font-semibold text-charcoal-700 uppercase tracking-wider',
        align === 'right' && 'text-right',
        align === 'center' && 'text-center',
        align === 'left' && 'text-left',
        className
      )
    )}
  >
    {children}
  </th>
);

export const TableCell: React.FC<{
  children: React.ReactNode;
  className?: string;
  align?: 'left' | 'center' | 'right';
  isNumeric?: boolean;
}> = ({ children, className, align = 'left', isNumeric = false }) => (
  <td
    className={twMerge(
      clsx(
        'px-3.5 py-2.5 text-sm text-charcoal-800',
        isNumeric && 'font-mono tabular-nums text-charcoal-900',
        align === 'right' && 'text-right',
        align === 'center' && 'text-center',
        align === 'left' && 'text-left',
        className
      )
    )}
  >
    {children}
  </td>
);

