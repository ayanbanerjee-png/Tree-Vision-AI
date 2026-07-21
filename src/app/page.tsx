'use client';

import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { 
  Trees, 
  ArrowRight, 
  BrainCircuit, 
  Activity, 
  ShieldCheck, 
  Zap, 
  Sparkles, 
  ChevronRight,
  Database,
  CloudLightning
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15
    }
  }
} as const;

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: { 
    opacity: 1, 
    y: 0, 
    transition: { type: 'spring' as const, stiffness: 100, damping: 15 } 
  }
} as const;

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-x-hidden bg-slate-50 dark:bg-zinc-950 font-sans">
      
      {/* Background Gradients */}
      <div className="absolute top-[-20%] left-[-10%] h-[600px] w-[600px] rounded-full bg-emerald-500/10 dark:bg-emerald-500/5 blur-[120px] pointer-events-none pulse-glow" />
      <div className="absolute top-[10%] right-[-10%] h-[500px] w-[500px] rounded-full bg-lime-400/10 dark:bg-lime-400/5 blur-[120px] pointer-events-none pulse-glow" style={{ animationDelay: '3s' }} />

      {/* Top Navbar */}
      <header className="sticky top-0 z-50 w-full border-b border-slate-200/50 bg-white/70 backdrop-blur-md dark:border-zinc-900/50 dark:bg-zinc-950/70">
        <div className="mx-auto flex max-w-7xl h-16 items-center justify-between px-6 sm:px-8">
          <Link href="/" className="flex items-center space-x-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-500 to-lime-400 shadow-md shadow-emerald-500/20 text-white font-bold text-lg">
              <Trees size={18} className="text-white" />
            </div>
            <span className="font-outfit text-lg font-bold tracking-tight text-slate-800 dark:text-zinc-100">
              TreeVision AI
            </span>
          </Link>
          <div className="flex items-center space-x-4">
            <Link href="/dashboard" passHref>
              <Button variant="outline" size="sm" className="hidden sm:inline-flex rounded-xl">
                Documentation
              </Button>
            </Link>
            <Link href="/dashboard" passHref>
              <Button variant="primary" size="sm" className="rounded-xl flex items-center space-x-1.5">
                <span>Go to App</span>
                <ArrowRight size={14} />
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="mx-auto max-w-7xl px-6 pt-16 pb-24 sm:px-8 md:pt-24 lg:pt-32 text-center">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="flex flex-col items-center space-y-6"
        >
          {/* Tagline Badge */}
          <motion.div 
            variants={itemVariants} 
            className="inline-flex items-center space-x-1.5 rounded-full bg-emerald-500/10 dark:bg-emerald-400/10 px-3.5 py-1 text-xs font-semibold text-emerald-700 dark:text-emerald-400 border border-emerald-500/20"
          >
            <Sparkles size={12} className="animate-pulse" />
            <span>Introducing TreeVision AI v1.4.0</span>
          </motion.div>

          {/* Heading */}
          <motion.h1 
            variants={itemVariants}
            className="font-outfit text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl md:text-6xl dark:text-zinc-100 max-w-4xl leading-[1.1]"
          >
            AI-powered <span className="bg-gradient-to-r from-emerald-600 to-lime-500 bg-clip-text text-transparent dark:from-emerald-400 dark:to-lime-400">Tree Species</span> Identification & Assessment
          </motion.h1>

          {/* Subtitle */}
          <motion.p 
            variants={itemVariants}
            className="text-base text-slate-500 sm:text-lg dark:text-zinc-400 max-w-2xl font-light"
          >
            Identify tree species, check physiological health, analyze canopy density, and generate assessment compliance reports in seconds using our deep learning engine.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div 
            variants={itemVariants}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4"
          >
            <Link href="/analyze" passHref>
              <Button variant="primary" size="lg" className="rounded-2xl px-8 shadow-lg shadow-emerald-600/15">
                Analyze a Tree
              </Button>
            </Link>
            <Link href="/dashboard" passHref>
              <Button variant="outline" size="lg" className="rounded-2xl px-8">
                Explore Dashboard
              </Button>
            </Link>
          </motion.div>

          {/* Large Interactive Dashboard Showcase Mockup */}
          <motion.div
            variants={itemVariants}
            className="w-full pt-16 max-w-5xl"
          >
            <div className="relative rounded-3xl border border-slate-200/80 bg-white p-2.5 shadow-2xl dark:border-zinc-800/80 dark:bg-zinc-900/60 shadow-emerald-950/5">
              <div className="overflow-hidden rounded-2xl border border-slate-200/50 bg-slate-50 dark:border-zinc-800/50 dark:bg-zinc-950 aspect-[16/9] flex flex-col items-center justify-center p-6 relative">
                
                {/* Simulated scanning animation overlay */}
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(16,185,129,0.03),transparent)] pointer-events-none" />
                
                <div className="z-10 flex flex-col items-center text-center space-y-4 max-w-md">
                  <div className="relative flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-tr from-emerald-500 to-lime-400 text-white shadow-xl shadow-emerald-500/25">
                    <BrainCircuit size={40} />
                    <motion.div 
                      className="absolute inset-0 rounded-2xl border-2 border-lime-400"
                      animate={{ scale: [1, 1.15, 1], opacity: [1, 0, 1] }}
                      transition={{ repeat: Infinity, duration: 2.5 }}
                    />
                  </div>
                  <div>
                    <h3 className="font-outfit text-xl font-bold text-slate-800 dark:text-zinc-100">Live AI Analytics Platform</h3>
                    <p className="text-xs text-slate-500 dark:text-zinc-400 mt-1">
                      Interactive sandbox loaded with neural network confidence charts, health parameters, batch queues, and historical GIS timeline logs.
                    </p>
                  </div>
                  <Link href="/dashboard" passHref>
                    <Button variant="secondary" size="sm" className="rounded-xl flex items-center space-x-1">
                      <span>Launch Sandbox Application</span>
                      <ChevronRight size={14} />
                    </Button>
                  </Link>
                </div>

                {/* Floating mockup UI widgets */}
                <Card className="absolute top-6 left-6 w-52 shadow-lg border border-slate-100/50 dark:border-zinc-800/50 bg-white/90 dark:bg-zinc-900/90 hidden lg:block text-left p-4">
                  <div className="flex items-center space-x-2.5">
                    <div className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
                    <span className="text-[10px] uppercase font-bold text-slate-400 dark:text-zinc-500">Live Prediction</span>
                  </div>
                  <p className="text-sm font-bold text-slate-800 dark:text-zinc-200 mt-1">Neem Tree (94%)</p>
                  <div className="mt-2.5 h-1.5 w-full bg-slate-100 rounded-full dark:bg-zinc-800">
                    <div className="h-full bg-emerald-500 rounded-full w-[94%]" />
                  </div>
                </Card>

                <Card className="absolute bottom-6 right-6 w-56 shadow-lg border border-slate-100/50 dark:border-zinc-800/50 bg-white/90 dark:bg-zinc-900/90 hidden lg:block text-left p-4">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] uppercase font-bold text-slate-400 dark:text-zinc-500">Health Index</span>
                    <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400">98.2%</span>
                  </div>
                  <div className="mt-2.5 flex items-center space-x-2">
                    <Activity size={14} className="text-emerald-500" />
                    <span className="text-xs font-medium text-slate-700 dark:text-zinc-300">Optimal Foliage Density</span>
                  </div>
                </Card>

              </div>
            </div>
          </motion.div>
        </motion.div>
      </section>

      {/* Features Grid */}
      <section className="bg-white dark:bg-zinc-900/40 py-24 border-t border-b border-slate-200/40 dark:border-zinc-900/50">
        <div className="mx-auto max-w-7xl px-6 sm:px-8">
          <div className="text-center space-y-3 pb-16">
            <h2 className="font-outfit text-3xl font-bold tracking-tight text-slate-900 dark:text-zinc-100">
              Advanced Tree Analytics Ecosystem
            </h2>
            <p className="text-sm text-slate-500 dark:text-zinc-400 max-w-lg mx-auto">
              Equipped with deep metrics detailing tree taxonomy, stress signals, age estimation, and digital record keeping.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <Card hoverLift className="flex flex-col space-y-4">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600 dark:bg-emerald-400/10 dark:text-emerald-400">
                <BrainCircuit size={22} />
              </div>
              <div>
                <h4 className="font-outfit font-bold text-slate-800 dark:text-zinc-100">Species Taxonomy</h4>
                <p className="text-xs text-slate-500 dark:text-zinc-400 mt-1">
                  Recognizes broadleaf, conifer, fruit tree, palm, and shrub species automatically with percentage-based scoring.
                </p>
              </div>
            </Card>

            <Card hoverLift className="flex flex-col space-y-4">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-lime-500/10 text-lime-600 dark:bg-lime-400/10 dark:text-lime-400">
                <Activity size={22} />
              </div>
              <div>
                <h4 className="font-outfit font-bold text-slate-800 dark:text-zinc-100">Health Stress Assessment</h4>
                <p className="text-xs text-slate-500 dark:text-zinc-400 mt-1">
                  Detects signs of stress, damage, and decline using an independently-trained health classifier.
                </p>
              </div>
            </Card>

            <Card hoverLift className="flex flex-col space-y-4">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-500/10 text-blue-500 dark:bg-blue-400/10 dark:text-blue-400">
                <Zap size={22} />
              </div>
              <div>
                <h4 className="font-outfit font-bold text-slate-800 dark:text-zinc-100">Batch Processing</h4>
                <p className="text-xs text-slate-500 dark:text-zinc-400 mt-1">
                  Upload multiple tree photos at once and get concurrent analysis results in a single request.
                </p>
              </div>
            </Card>

            <Card hoverLift className="flex flex-col space-y-4">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-500 dark:bg-indigo-400/10 dark:text-indigo-400">
                <Database size={22} />
              </div>
              <div>
                <h4 className="font-outfit font-bold text-slate-800 dark:text-zinc-100">History Timeline</h4>
                <p className="text-xs text-slate-500 dark:text-zinc-400 mt-1">
                  Search and review every past analysis, including auditor corrections, in one chronological log.
                </p>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* Call to Action */}
      <section className="mx-auto max-w-7xl px-6 py-24 sm:px-8 text-center">
        <div className="relative rounded-3xl bg-gradient-to-tr from-emerald-900 to-zinc-950 p-8 sm:p-12 md:p-16 overflow-hidden shadow-2xl dark:from-emerald-950/70 dark:to-zinc-900/60">
          
          <div className="absolute top-0 right-0 h-[250px] w-[250px] rounded-full bg-lime-400/10 blur-[80px] pointer-events-none" />
          
          <div className="relative z-10 flex flex-col items-center space-y-5 max-w-xl mx-auto">
            <h2 className="font-outfit text-3xl font-bold tracking-tight text-white">
              Ready to catalog your green canopy?
            </h2>
            <p className="text-sm text-emerald-100/70">
              Join forestry researchers, arborists, and smart cities engineering teams using TreeVision to track biomass cover and urban forest indices.
            </p>
            <div className="pt-2">
              <Link href="/dashboard" passHref>
                <Button variant="lime" size="lg" className="rounded-2xl flex items-center space-x-2">
                  <span>Enter Application Dashboard</span>
                  <ArrowRight size={16} />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200/50 dark:border-zinc-900/50 py-10 bg-slate-50 dark:bg-zinc-950 text-center text-xs text-slate-400 dark:text-zinc-500">
        <p>© 2026 TreeVision AI. All rights reserved. Built with Next.js 15, React 19, Tailwind CSS, and Framer Motion.</p>
      </footer>

    </div>
  );
}
