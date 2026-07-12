'use client';

import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, CartesianGrid } from 'recharts';
import { 
  TrendingUp, 
  Activity, 
  HelpCircle, 
  ShieldCheck, 
  Percent 
} from 'lucide-react';

const SPECIES_DISTRIBUTION = [
  { name: 'Neem', value: 35, color: '#059669' },     // Emerald 600
  { name: 'Banyan', value: 20, color: '#10b981' },   // Emerald 500
  { name: 'Eucalyptus', value: 15, color: '#84cc16' }, // Lime 500
  { name: 'Peepal', value: 12, color: '#a3e635' },     // Lime 400
  { name: 'Mango', value: 18, color: '#64748b' }      // Slate 500
];

const HEALTH_DISTRIBUTION = [
  { status: 'Healthy', count: 72, color: '#059669' },
  { status: 'Mild Decline', count: 18, color: '#f59e0b' }, // Amber 500
  { status: 'Severe Disease', count: 10, color: '#ef4444' } // Red 500
];

const CONFIDENCE_DISTRIBUTION = [
  { bucket: '90-100%', count: 48 },
  { bucket: '80-89%', count: 28 },
  { bucket: '70-79%', count: 14 },
  { bucket: '50-69%', count: 6 },
  { bucket: '<50%', count: 4 }
];

export default function AnalyticsPage() {
  const totalAnalyzed = 1420;
  const reviewRate = 7.4; // % of total trees needing review

  return (
    <div className="flex-1 space-y-8 p-6 md:p-8 pt-6 max-w-[1600px] w-full mx-auto font-sans">
      
      {/* Title */}
      <div>
        <h1 className="font-outfit text-3xl font-bold tracking-tight text-slate-800 dark:text-zinc-100">
          Analytics & Insights
        </h1>
        <p className="text-sm text-slate-500 dark:text-zinc-400">
          Aggregated taxonomic parameters and health distributions across all scanned locations.
        </p>
      </div>

      {/* Aggregate Cards */}
      <div className="grid gap-5 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold">Total Scanned Trees</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-black font-outfit text-slate-800 dark:text-zinc-100">
              {totalAnalyzed.toLocaleString()}
            </div>
            <div className="flex items-center space-x-1 mt-1 text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold">
              <TrendingUp size={12} />
              <span>+18% month-over-month</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold">Average Neural Score</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-black font-outfit text-slate-800 dark:text-zinc-100">
              87.2%
            </div>
            <div className="text-[10px] text-slate-400 dark:text-zinc-500 mt-1">
              Threshold confidence limit: 75%
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold">Audit Request Rate</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-black font-outfit text-slate-800 dark:text-zinc-100">
              {reviewRate}%
            </div>
            <div className="flex items-center space-x-1 mt-1 text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold">
              <span>-1.2% reduction in noise filters</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold">Biomass Health Ratio</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-black font-outfit text-slate-800 dark:text-zinc-100">
              92.6%
            </div>
            <div className="text-[10px] text-slate-400 dark:text-zinc-500 mt-1">
              Active foliage coverage optimal
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Charts Layout */}
      <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
        
        {/* Pie: Species Distribution */}
        <Card className="min-h-[380px] flex flex-col justify-between">
          <CardHeader>
            <CardTitle className="font-outfit text-base">Species Distribution</CardTitle>
            <CardDescription>Taxonomy breakdown percentage of scanned trees</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col sm:flex-row items-center justify-around mt-4">
            <div className="h-[220px] w-[220px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={SPECIES_DISTRIBUTION}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {SPECIES_DISTRIBUTION.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: any) => `${value}%`} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="space-y-2 mt-4 sm:mt-0 max-w-[200px] w-full">
              {SPECIES_DISTRIBUTION.map((species, index) => (
                <div key={index} className="flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2">
                    <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: species.color }} />
                    <span className="font-medium text-slate-700 dark:text-zinc-300">{species.name}</span>
                  </div>
                  <span className="font-bold text-slate-900 dark:text-zinc-100">{species.value}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Bar: Health Distribution */}
        <Card className="min-h-[380px] flex flex-col justify-between">
          <CardHeader>
            <CardTitle className="font-outfit text-base">Physiological Health Distribution</CardTitle>
            <CardDescription>Overall assessed stress signals across forest nodes</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 mt-6">
            <div className="h-[220px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={HEALTH_DISTRIBUTION} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis 
                    dataKey="status" 
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
                  />
                  <Tooltip 
                    formatter={(value: any) => [`${value}%`, 'Percentage']}
                    contentStyle={{
                      background: 'rgba(255, 255, 255, 0.95)',
                      border: '1px solid #e2e8f0',
                      borderRadius: '0.5rem',
                      fontSize: '12px'
                    }}
                  />
                  <Bar dataKey="count" radius={[8, 8, 0, 0]} barSize={40}>
                    {HEALTH_DISTRIBUTION.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Line/Area: Confidence Distribution */}
        <Card className="min-h-[380px] lg:col-span-2 flex flex-col justify-between">
          <CardHeader>
            <CardTitle className="font-outfit text-base">Classifier Confidence Distribution</CardTitle>
            <CardDescription>Distribution frequency of softmax scores across predictions</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 mt-6">
            <div className="h-[220px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={CONFIDENCE_DISTRIBUTION} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" className="dark:stroke-zinc-800/80" />
                  <XAxis 
                    dataKey="bucket" 
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
                  />
                  <Tooltip 
                    formatter={(value: any) => [`${value}%`, 'Share']}
                    contentStyle={{
                      background: 'rgba(255, 255, 255, 0.95)',
                      border: '1px solid #e2e8f0',
                      borderRadius: '0.5rem',
                      fontSize: '12px'
                    }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="count" 
                    stroke="#059669" 
                    strokeWidth={3} 
                    activeDot={{ r: 6 }} 
                    dot={{ strokeWidth: 2, r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
