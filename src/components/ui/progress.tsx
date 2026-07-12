'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface ProgressProps {
  value: number; // 0 to 100
  className?: string;
  color?: 'emerald' | 'lime' | 'default';
}

export const Progress = ({ value, className = '', color = 'emerald' }: ProgressProps) => {
  const clampedValue = Math.min(100, Math.max(0, value));

  const colors = {
    emerald: 'bg-emerald-500',
    lime: 'bg-lime-500',
    default: 'bg-slate-900 dark:bg-zinc-100',
  };

  return (
    <div className={`relative h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-zinc-800 ${className}`}>
      <motion.div
        className={`h-full rounded-full ${colors[color]}`}
        initial={{ width: 0 }}
        animate={{ width: `${clampedValue}%` }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
      />
    </div>
  );
};
