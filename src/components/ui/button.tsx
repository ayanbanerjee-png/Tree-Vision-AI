'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'lime';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = '', variant = 'primary', size = 'md', fullWidth = false, children, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center font-medium rounded-xl transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 disabled:pointer-events-none disabled:opacity-50 select-none';
    
    const variants = {
      primary: 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm border border-emerald-700/10 dark:bg-emerald-600 dark:hover:bg-emerald-500',
      lime: 'bg-lime-500 hover:bg-lime-600 text-slate-900 font-semibold shadow-sm border border-lime-600/10 dark:bg-lime-400 dark:hover:bg-lime-500',
      secondary: 'bg-slate-100 hover:bg-slate-200 text-slate-900 dark:bg-zinc-800 dark:hover:bg-zinc-700 dark:text-zinc-100',
      outline: 'bg-transparent border border-slate-200 text-slate-700 hover:bg-slate-50 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-900',
      ghost: 'bg-transparent hover:bg-slate-100 text-slate-700 dark:text-zinc-300 dark:hover:bg-zinc-900',
    };

    const sizes = {
      sm: 'h-9 px-4 text-xs',
      md: 'h-10 px-5 text-sm',
      lg: 'h-12 px-6 text-base',
    };

    const widthStyle = fullWidth ? 'w-full' : '';

    return (
      <motion.button
        ref={ref}
        whileTap={{ scale: 0.98 }}
        className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${widthStyle} ${className}`}
        {...(props as any)}
      >
        {children}
      </motion.button>
    );
  }
);

Button.displayName = 'Button';
