'use client';

import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { 
  Image as ImageIcon, 
  Percent, 
  AlertTriangle, 
  ShieldCheck, 
  ArrowRight, 
  PlusCircle, 
  Layers, 
  BarChart3, 
  TrendingUp, 
  Clock 
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@/components/ui/table';
import { INITIAL_MOCK_TREES, getStats } from '@/data/mockTrees';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const CHART_DATA = [
  { day: 'Mon', count: 12 },
  { day: 'Tue', count: 19 },
  { day: 'Wed', count: 15 },
  { day: 'Thu', count: 22 },
  { day: 'Fri', count: 30 },
  { day: 'Sat', count: 10 },
  { day: 'Sun', count: 8 },
];

export default function Dashboard() {
  const trees = INITIAL_MOCK_TREES;
  const stats = getStats(trees);

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08
      }
    }
  } as const;

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show: { 
      opacity: 1, 
      y: 0, 
      transition: { type: 'spring' as const, stiffness: 100, damping: 15 } 
    }
  } as const;

  const getHealthBadge = (health: string) => {
    switch (health) {
      case 'Healthy':
        return <Badge variant="emerald">{health}</Badge>;
      case 'Mild Decline':
        return <Badge variant="amber">{health}</Badge>;
      case 'Severe Disease':
        return <Badge variant="red">{health}</Badge>;
      default:
        return <Badge variant="gray">{health}</Badge>;
    }
  };

  return (
    <div className="flex-1 space-y-8 p-6 md:p-8 pt-6 max-w-[1600px] w-full mx-auto">
      
      {/* Welcome Header */}
      <div className="flex flex-col space-y-2 md:flex-row md:items-center md:justify-between md:space-y-0">
        <div>
          <h1 className="font-outfit text-3xl font-bold tracking-tight text-slate-800 dark:text-zinc-100">
            Overview Dashboard
          </h1>
          <p className="text-sm text-slate-500 dark:text-zinc-400">
            System diagnostics and recent forestry predictions.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Link href="/analyze" passHref>
            <Button variant="primary" className="rounded-xl flex items-center space-x-1.5 shadow-md">
              <PlusCircle size={16} />
              <span>Analyze Tree</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* Grid of Stats Cards */}
      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="grid gap-5 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4"
      >
        <motion.div variants={itemVariants}>
          <Card className="relative overflow-hidden">
            <div className="absolute right-[-10px] top-[-10px] text-slate-100/40 dark:text-zinc-800/10 pointer-events-none">
              <ImageIcon size={100} />
            </div>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardDescription className="font-medium text-xs">Total Processed</CardDescription>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                <ImageIcon size={16} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-extrabold font-outfit text-slate-800 dark:text-zinc-100">
                {stats.imagesProcessed}
              </div>
              <p className="text-[10px] text-slate-400 dark:text-zinc-500 mt-1 flex items-center space-x-1 font-medium">
                <TrendingUp size={12} className="text-emerald-500" />
                <span className="text-emerald-600 dark:text-emerald-400">+12%</span>
                <span>from last week</span>
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={itemVariants}>
          <Card className="relative overflow-hidden">
            <div className="absolute right-[-10px] top-[-10px] text-slate-100/40 dark:text-zinc-800/10 pointer-events-none">
              <Percent size={100} />
            </div>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardDescription className="font-medium text-xs">Avg Confidence</CardDescription>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-lime-500/10 text-lime-600 dark:text-lime-400">
                <Percent size={16} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-extrabold font-outfit text-slate-800 dark:text-zinc-100">
                {stats.avgConfidence}%
              </div>
              <p className="text-[10px] text-slate-400 dark:text-zinc-500 mt-1 font-medium">
                Stable within threshold limits
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={itemVariants}>
          <Card className="relative overflow-hidden">
            <div className="absolute right-[-10px] top-[-10px] text-slate-100/40 dark:text-zinc-800/10 pointer-events-none">
              <AlertTriangle size={100} />
            </div>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardDescription className="font-medium text-xs">Needs Review</CardDescription>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400">
                <AlertTriangle size={16} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-extrabold font-outfit text-slate-800 dark:text-zinc-100">
                {stats.needsReviewCount}
              </div>
              <p className="text-[10px] text-slate-400 dark:text-zinc-500 mt-1 font-medium">
                Low confidence detections
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={itemVariants}>
          <Card className="relative overflow-hidden">
            <div className="absolute right-[-10px] top-[-10px] text-slate-100/40 dark:text-zinc-800/10 pointer-events-none">
              <ShieldCheck size={100} />
            </div>
            <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
              <CardDescription className="font-medium text-xs">Healthy Trees</CardDescription>
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                <ShieldCheck size={16} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-extrabold font-outfit text-slate-800 dark:text-zinc-100">
                {stats.healthyTreesCount}
              </div>
              <p className="text-[10px] text-emerald-600 dark:text-emerald-400 mt-1 font-medium">
                {Math.round((stats.healthyTreesCount / stats.imagesProcessed) * 100)}% of total canopy
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>

      {/* Main Content Layout */}
      <div className="grid gap-6 grid-cols-1 lg:grid-cols-3">
        
        {/* Left Column: Recent Activity Chart */}
        <div className="lg:col-span-2 flex flex-col space-y-6">
          <Card className="flex-1 flex flex-col min-h-[350px]">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="font-outfit text-lg">Analysis Activity</CardTitle>
                <CardDescription>Daily images assessed over the current week</CardDescription>
              </div>
              <div className="flex items-center space-x-1.5 text-xs text-emerald-600 dark:text-emerald-400 font-semibold bg-emerald-500/10 px-2.5 py-1 rounded-lg">
                <TrendingUp size={14} />
                <span>+2.4k total</span>
              </div>
            </CardHeader>
            <CardContent className="flex-1 mt-4">
              <div className="h-[250px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={CHART_DATA} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0.0}/>
                      </linearGradient>
                    </defs>
                    <XAxis 
                      dataKey="day" 
                      stroke="#888888" 
                      fontSize={11} 
                      tickLine={false} 
                      axisLine={false} 
                    />
                    <YAxis 
                      stroke="#888888" 
                      fontSize={11} 
                      tickLine={false} 
                      axisLine={false} 
                      allowDecimals={false}
                    />
                    <Tooltip 
                      contentStyle={{
                        background: 'rgba(255, 255, 255, 0.95)',
                        border: '1px solid #e2e8f0',
                        borderRadius: '0.75rem',
                        fontSize: '12px',
                        color: '#0f172a'
                      }}
                      itemStyle={{ color: '#059669', fontWeight: 'bold' }}
                      labelStyle={{ fontWeight: 'bold', color: '#64748b' }}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="count" 
                      stroke="#059669" 
                      strokeWidth={2}
                      fillOpacity={1} 
                      fill="url(#colorCount)" 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Quick Actions */}
        <div className="flex flex-col space-y-6">
          <Card className="h-full flex flex-col justify-between">
            <div>
              <CardHeader>
                <CardTitle className="font-outfit text-lg">Quick Access</CardTitle>
                <CardDescription>Shortcut workflows for tree assessment</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Link href="/analyze" className="group flex items-center justify-between rounded-xl border border-slate-200/60 p-4 transition-all hover:bg-slate-50 hover:shadow-sm dark:border-zinc-800/80 dark:hover:bg-zinc-900/40">
                  <div className="flex items-center space-x-3.5">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600 dark:bg-emerald-400/10 dark:text-emerald-400">
                      <PlusCircle size={18} />
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-slate-800 dark:text-zinc-200">Analyze Tree</h4>
                      <p className="text-[10px] text-slate-400 dark:text-zinc-500">Run a single image scan</p>
                    </div>
                  </div>
                  <ArrowRight size={14} className="text-slate-400 transition-transform group-hover:translate-x-1" />
                </Link>

                <Link href="/batch" className="group flex items-center justify-between rounded-xl border border-slate-200/60 p-4 transition-all hover:bg-slate-50 hover:shadow-sm dark:border-zinc-800/80 dark:hover:bg-zinc-900/40">
                  <div className="flex items-center space-x-3.5">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-lime-500/10 text-lime-600 dark:bg-lime-400/10 dark:text-lime-400">
                      <Layers size={18} />
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-slate-800 dark:text-zinc-200">Batch Processing</h4>
                      <p className="text-[10px] text-slate-400 dark:text-zinc-500">Analyze multiple images</p>
                    </div>
                  </div>
                  <ArrowRight size={14} className="text-slate-400 transition-transform group-hover:translate-x-1" />
                </Link>

                <Link href="/analytics" className="group flex items-center justify-between rounded-xl border border-slate-200/60 p-4 transition-all hover:bg-slate-50 hover:shadow-sm dark:border-zinc-800/80 dark:hover:bg-zinc-900/40">
                  <div className="flex items-center space-x-3.5">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-500/10 text-blue-500 dark:bg-blue-400/10 dark:text-blue-400">
                      <BarChart3 size={18} />
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-slate-800 dark:text-zinc-200">Full Analytics</h4>
                      <p className="text-[10px] text-slate-400 dark:text-zinc-500">Species & stress breakdowns</p>
                    </div>
                  </div>
                  <ArrowRight size={14} className="text-slate-400 transition-transform group-hover:translate-x-1" />
                </Link>
              </CardContent>
            </div>
            <div className="p-6 border-t border-slate-200/30 dark:border-zinc-800/30 bg-slate-50/40 dark:bg-zinc-900/20 rounded-b-2xl">
              <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 dark:text-zinc-500 flex items-center space-x-1">
                <Clock size={12} />
                <span>Next Scheduled Cron Sync</span>
              </span>
              <p className="text-xs font-semibold text-slate-700 dark:text-zinc-300 mt-1">Every hour (Async Queue processing enabled)</p>
            </div>
          </Card>
        </div>
      </div>

      {/* Recent Predictions Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="font-outfit text-lg">Recent Predictions</CardTitle>
            <CardDescription>Latest models predictions results from neural network pipeline</CardDescription>
          </div>
          <Link href="/history" passHref>
            <Button variant="outline" size="sm" className="rounded-xl text-xs flex items-center space-x-1">
              <span>View History</span>
              <ArrowRight size={12} />
            </Button>
          </Link>
        </CardHeader>
        <CardContent className="mt-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Record ID</TableHead>
                <TableHead>Species</TableHead>
                <TableHead>Confidence</TableHead>
                <TableHead>Health Condition</TableHead>
                <TableHead>Age Class</TableHead>
                <TableHead>Needs Review</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {trees.slice(0, 4).map((tree) => (
                <TableRow key={tree.id}>
                  <TableCell className="font-mono text-xs font-bold text-slate-700 dark:text-zinc-300">{tree.id}</TableCell>
                  <TableCell className="font-semibold text-slate-800 dark:text-zinc-100">{tree.species}</TableCell>
                  <TableCell>
                    <span className={`font-semibold ${tree.confidence >= 85 ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-500'}`}>
                      {tree.confidence}%
                    </span>
                  </TableCell>
                  <TableCell>{getHealthBadge(tree.health)}</TableCell>
                  <TableCell>{tree.age}</TableCell>
                  <TableCell>
                    {tree.needsReview ? (
                      <Badge variant="amber">Yes</Badge>
                    ) : (
                      <Badge variant="gray">No</Badge>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
