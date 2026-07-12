import React from 'react';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'emerald' | 'lime' | 'amber' | 'red' | 'gray' | 'blue';
}

export const Badge = ({ className = '', variant = 'gray', children, ...props }: BadgeProps) => {
  const baseStyles = 'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold select-none border transition-colors';
  
  const variants = {
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200/50 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20',
    lime: 'bg-lime-50 text-lime-700 border-lime-200/50 dark:bg-lime-500/10 dark:text-lime-400 dark:border-lime-500/20',
    amber: 'bg-amber-50 text-amber-700 border-amber-200/50 dark:bg-amber-500/10 dark:text-amber-400 dark:border-amber-500/20',
    red: 'bg-red-50 text-red-700 border-red-200/50 dark:bg-red-500/10 dark:text-red-400 dark:border-red-500/20',
    gray: 'bg-slate-100 text-slate-700 border-slate-200/50 dark:bg-zinc-800 dark:text-zinc-300 dark:border-zinc-700/50',
    blue: 'bg-blue-50 text-blue-700 border-blue-200/50 dark:bg-blue-500/10 dark:text-blue-400 dark:border-blue-500/20',
  };

  return (
    <span className={`${baseStyles} ${variants[variant]} ${className}`} {...props}>
      {children}
    </span>
  );
};
