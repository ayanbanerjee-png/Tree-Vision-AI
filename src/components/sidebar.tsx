'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  LayoutDashboard, 
  TreePine, 
  Layers, 
  BarChart3, 
  History, 
  Settings, 
  Menu, 
  X, 
  Cpu, 
  Trees,
  ClipboardCheck
} from 'lucide-react';
import { useTheme } from './theme-provider';

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/analyze', label: 'Analyze Tree', icon: TreePine },
  { href: '/batch', label: 'Batch Analysis', icon: Layers },
  { href: '/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/history', label: 'History', icon: History },
  { href: '/review', label: 'Auditor Review', icon: ClipboardCheck },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export const Sidebar = () => {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const { theme } = useTheme();

  // If we are on the landing page, we might want to hide the sidebar, but wait, 
  // the sidebar is the primary navigation. To keep it clean, we can display it on 
  // all pages except the landing page, or include a way to access the landing page.
  // Let's render the layout with sidebar everywhere, but on the landing page we can 
  // hide the sidebar or offer a clean experience. Let's make the sidebar hide on the landing page ('/')
  // to give it a spacious, beautiful landing feel.
  const isLandingPage = pathname === '/';

  if (isLandingPage) return null;

  return (
    <>
      {/* Mobile Top Bar */}
      <div className="flex h-16 items-center justify-between border-b border-slate-200/80 bg-white px-6 dark:border-zinc-800/80 dark:bg-zinc-950 md:hidden sticky top-0 z-40">
        <Link href="/" className="flex items-center space-x-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-500 to-lime-400 shadow-md shadow-emerald-500/20 text-white font-bold text-lg">
            <Trees size={18} className="text-white" />
          </div>
          <span className="font-outfit text-lg font-bold tracking-tight text-slate-800 dark:text-zinc-100">
            TreeVision
          </span>
        </Link>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="rounded-xl border border-slate-200 p-2 text-slate-600 hover:bg-slate-50 dark:border-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-900"
        >
          {isOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.4 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 z-40 bg-black md:hidden"
            />
            <motion.div
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="fixed bottom-0 top-0 left-0 z-50 flex w-[280px] flex-col border-r border-slate-200/80 bg-white/95 backdrop-blur-md p-6 dark:border-zinc-800/80 dark:bg-zinc-950/95"
            >
              <div className="flex items-center justify-between pb-6 border-b border-slate-200/50 dark:border-zinc-800/50">
                <Link href="/" className="flex items-center space-x-2.5" onClick={() => setIsOpen(false)}>
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-500 to-lime-400 shadow-md text-white font-bold">
                    <Trees size={18} />
                  </div>
                  <span className="font-outfit text-lg font-bold tracking-tight text-slate-800 dark:text-zinc-100">
                    TreeVision AI
                  </span>
                </Link>
                <button
                  onClick={() => setIsOpen(false)}
                  className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 dark:text-zinc-400 dark:hover:bg-zinc-900"
                >
                  <X size={18} />
                </button>
              </div>

              <nav className="flex-1 space-y-1.5 py-6">
                {NAV_ITEMS.map((item) => {
                  const isActive = pathname === item.href;
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setIsOpen(false)}
                      className={`flex items-center space-x-3.5 rounded-xl px-4 py-3 text-sm font-medium transition-all ${
                        isActive
                          ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400 shadow-sm border border-emerald-500/10'
                          : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800 dark:text-zinc-400 dark:hover:bg-zinc-900 dark:hover:text-zinc-200'
                      }`}
                    >
                      <Icon size={18} className={isActive ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400 dark:text-zinc-500'} />
                      <span>{item.label}</span>
                    </Link>
                  );
                })}
              </nav>

              <div className="border-t border-slate-200/50 pt-4 dark:border-zinc-800/50 flex flex-col space-y-2">
                <div className="flex items-center space-x-3 rounded-xl bg-slate-50 p-3.5 dark:bg-zinc-900/60 border border-slate-200/45 dark:border-zinc-800/40">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 dark:bg-emerald-400/10 text-emerald-600 dark:text-emerald-400">
                    <Cpu size={16} />
                  </div>
                  <div>
                    <p className="text-[10px] uppercase font-bold tracking-wider text-slate-400 dark:text-zinc-500">Model Version</p>
                    <p className="text-xs font-semibold text-slate-700 dark:text-zinc-300">v1.4.0-prod</p>
                  </div>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Desktop Sidebar */}
      <div className="hidden md:flex fixed top-0 bottom-0 left-0 z-30 w-64 flex-col border-r border-slate-200/80 bg-white p-6 dark:border-zinc-800/80 dark:bg-zinc-950">
        <div className="flex items-center space-x-2.5 pb-6 border-b border-slate-200/50 dark:border-zinc-800/50">
          <Link href="/" className="flex items-center space-x-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-500 to-lime-400 shadow-md shadow-emerald-500/20 text-white font-bold text-xl">
              <Trees size={20} className="text-white" />
            </div>
            <div>
              <span className="font-outfit text-base font-bold tracking-tight text-slate-800 dark:text-zinc-100 block leading-tight">
                TreeVision AI
              </span>
              <span className="text-[10px] text-slate-400 dark:text-zinc-500 block">Species & Health</span>
            </div>
          </Link>
        </div>

        <nav className="flex-1 space-y-1.5 py-6">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center space-x-3.5 rounded-xl px-4 py-3 text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400 shadow-sm border border-emerald-500/10'
                    : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800 dark:text-zinc-400 dark:hover:bg-zinc-900 dark:hover:text-zinc-200'
                }`}
              >
                <Icon size={18} className={isActive ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400 dark:text-zinc-500'} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-slate-200/50 pt-4 dark:border-zinc-800/50 flex flex-col space-y-2">
          <div className="flex items-center space-x-3 rounded-xl bg-slate-50 p-3.5 dark:bg-zinc-900/60 border border-slate-200/45 dark:border-zinc-800/40">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 dark:bg-emerald-400/10 text-emerald-600 dark:text-emerald-400">
              <Cpu size={16} />
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold tracking-wider text-slate-400 dark:text-zinc-500">Model Version</p>
              <p className="text-xs font-semibold text-slate-700 dark:text-zinc-300">v1.4.0-prod</p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};
