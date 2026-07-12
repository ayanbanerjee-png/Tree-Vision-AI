'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import { Sidebar } from './sidebar';

export function LayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isLandingPage = pathname === '/';

  return (
    <div className="flex min-h-screen w-full bg-slate-50 text-slate-900 transition-colors duration-200 dark:bg-zinc-950 dark:text-zinc-50 font-sans">
      <Sidebar />
      <div className={`flex-1 flex flex-col min-w-0 ${isLandingPage ? '' : 'md:pl-64'}`}>
        <div className="flex-1 flex flex-col w-full">
          {children}
        </div>
      </div>
    </div>
  );
}
