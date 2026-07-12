'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, 
  Filter, 
  Calendar, 
  ChevronDown, 
  ChevronUp, 
  Heart, 
  Clock, 
  AlertCircle, 
  Trees,
  CheckCircle,
  Database
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { INITIAL_MOCK_TREES } from '@/data/mockTrees';
import { TreeAnalysis, HealthStatus } from '@/types';

export default function HistoryPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [healthFilter, setHealthFilter] = useState<string>('All');
  const [reviewFilter, setReviewFilter] = useState<string>('All');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const filteredTrees = INITIAL_MOCK_TREES.filter((tree) => {
    const matchesSearch = 
      tree.species.toLowerCase().includes(searchQuery.toLowerCase()) || 
      tree.id.toLowerCase().includes(searchQuery.toLowerCase());
      
    const matchesHealth = healthFilter === 'All' || tree.health === healthFilter;
    
    const matchesReview = 
      reviewFilter === 'All' || 
      (reviewFilter === 'Needs Review' && tree.needsReview) || 
      (reviewFilter === 'Normal' && !tree.needsReview);

    return matchesSearch && matchesHealth && matchesReview;
  });

  const getHealthBadge = (health: HealthStatus) => {
    switch (health) {
      case 'Healthy': return <Badge variant="emerald">{health}</Badge>;
      case 'Mild Decline': return <Badge variant="amber">{health}</Badge>;
      case 'Severe Disease': return <Badge variant="red">{health}</Badge>;
      default: return <Badge variant="gray">{health}</Badge>;
    }
  };

  return (
    <div className="flex-1 space-y-8 p-6 md:p-8 pt-6 max-w-[1600px] w-full mx-auto font-sans">
      
      {/* Title */}
      <div>
        <h1 className="font-outfit text-3xl font-bold tracking-tight text-slate-800 dark:text-zinc-100">
          History Timeline
        </h1>
        <p className="text-sm text-slate-500 dark:text-zinc-400">
          Search and review previously identified species, health anomalies, and auditor audits.
        </p>
      </div>

      {/* Filter Toolbar */}
      <Card className="p-4 bg-white/60 dark:bg-zinc-900/40 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          {/* Search box */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <input
              type="text"
              placeholder="Search by Species name or ID (e.g. TR-1082)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white dark:bg-zinc-900 dark:border-zinc-800 dark:text-zinc-100"
            />
          </div>

          {/* Selector Toggles */}
          <div className="flex flex-wrap items-center gap-3">
            
            {/* Health Selector */}
            <div className="flex items-center space-x-2 text-xs">
              <span className="font-medium text-slate-400 dark:text-zinc-500">Health:</span>
              <div className="inline-flex rounded-lg border border-slate-200 p-0.5 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-950">
                {['All', 'Healthy', 'Mild Decline', 'Severe Disease'].map((h) => (
                  <button
                    key={h}
                    onClick={() => setHealthFilter(h)}
                    className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all ${
                      healthFilter === h
                        ? 'bg-white text-slate-900 shadow-sm dark:bg-zinc-900 dark:text-zinc-100'
                        : 'text-slate-500 hover:text-slate-800 dark:text-zinc-400 dark:hover:text-zinc-200'
                    }`}
                  >
                    {h}
                  </button>
                ))}
              </div>
            </div>

            {/* Audit Status Selector */}
            <div className="flex items-center space-x-2 text-xs">
              <span className="font-medium text-slate-400 dark:text-zinc-500">Audit:</span>
              <div className="inline-flex rounded-lg border border-slate-200 p-0.5 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-950">
                {['All', 'Needs Review', 'Normal'].map((r) => (
                  <button
                    key={r}
                    onClick={() => setReviewFilter(r)}
                    className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all ${
                      reviewFilter === r
                        ? 'bg-white text-slate-900 shadow-sm dark:bg-zinc-900 dark:text-zinc-100'
                        : 'text-slate-500 hover:text-slate-800 dark:text-zinc-400 dark:hover:text-zinc-200'
                    }`}
                  >
                    {r}
                  </button>
                ))}
              </div>
            </div>

          </div>
        </div>
      </Card>

      {/* History Timeline Stream */}
      <div className="space-y-4">
        {filteredTrees.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center bg-slate-50/50 border border-slate-200/50 border-dashed rounded-2xl dark:bg-zinc-900/10 dark:border-zinc-800/50">
            <Database size={36} className="text-slate-300 dark:text-zinc-700 mb-3" />
            <h3 className="font-semibold text-slate-700 dark:text-zinc-300">No predictions found</h3>
            <p className="text-xs text-slate-400 dark:text-zinc-500 max-w-[280px] mt-1">
              No history items match the active search query or filter parameters.
            </p>
          </div>
        ) : (
          <AnimatePresence>
            {filteredTrees.map((tree) => {
              const isExpanded = expandedId === tree.id;
              const formattedDate = new Date(tree.timestamp).toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              });

              return (
                <motion.div
                  key={tree.id}
                  layout="position"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                >
                  <Card 
                    className={`transition-shadow hover:shadow-md cursor-pointer border ${
                      isExpanded ? 'border-emerald-500/40 dark:border-emerald-500/25 ring-1 ring-emerald-500/10' : 'border-slate-200/60 dark:border-zinc-800/80'
                    }`}
                    onClick={() => toggleExpand(tree.id)}
                  >
                    <div className="p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 select-none">
                      
                      {/* Timeline Info & Title */}
                      <div className="flex items-start space-x-4">
                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-50 dark:bg-zinc-950 text-slate-500 dark:text-zinc-400 border border-slate-100 dark:border-zinc-900">
                          <Clock size={16} />
                        </div>
                        <div>
                          <div className="flex items-center space-x-2 text-[10px] text-slate-400 dark:text-zinc-500 font-mono">
                            <span className="font-bold">{tree.id}</span>
                            <span>•</span>
                            <span>{formattedDate}</span>
                          </div>
                          <h4 className="font-outfit text-base font-extrabold text-slate-800 dark:text-zinc-100 mt-1 flex items-center space-x-2">
                            <span>{tree.species}</span>
                            {tree.needsReview && (
                              <Badge variant="amber" className="text-[9px] px-1.5 py-0">Review Req</Badge>
                            )}
                          </h4>
                        </div>
                      </div>

                      {/* Right Hand Stats */}
                      <div className="flex items-center space-x-6 w-full md:w-auto justify-between md:justify-end border-t md:border-t-0 border-slate-100 dark:border-zinc-900 pt-3 md:pt-0">
                        <div className="flex items-center space-x-2.5">
                          {getHealthBadge(tree.health)}
                          <Badge variant="gray">{tree.age}</Badge>
                        </div>
                        
                        <div className="flex items-center space-x-4">
                          <div className="text-right">
                            <span className="text-[10px] text-slate-400 dark:text-zinc-500 block">Confidence</span>
                            <span className={`text-base font-bold ${tree.confidence >= 85 ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-500'}`}>
                              {tree.confidence}%
                            </span>
                          </div>
                          
                          <Button variant="ghost" size="sm" className="rounded-lg p-1.5">
                            {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                          </Button>
                        </div>
                      </div>

                    </div>

                    {/* Collapsible details section */}
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.25 }}
                          className="overflow-hidden"
                          onClick={(e) => e.stopPropagation()} // Prevent collapse toggling on clicking details
                        >
                          <div className="px-5 pb-5 border-t border-slate-100 dark:border-zinc-800/80 pt-4 bg-slate-50/20 dark:bg-zinc-900/10">
                            <h5 className="text-[10px] uppercase font-bold text-slate-400 dark:text-zinc-500 mb-3 tracking-wider">Additional Pipeline Diagnostics</h5>
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                              <div>
                                <span className="text-[10px] text-slate-400 dark:text-zinc-500">Species Group</span>
                                <p className="text-xs font-semibold text-slate-700 dark:text-zinc-300 mt-0.5">{tree.speciesGroup}</p>
                              </div>
                              <div>
                                <span className="text-[10px] text-slate-400 dark:text-zinc-500">Foliage Density</span>
                                <p className="text-xs font-semibold text-slate-700 dark:text-zinc-300 mt-0.5">{tree.foliage}</p>
                              </div>
                              <div>
                                <span className="text-[10px] text-slate-400 dark:text-zinc-500">Image Quality</span>
                                <p className="text-xs font-semibold text-slate-700 dark:text-zinc-300 mt-0.5">{tree.imageQuality}</p>
                              </div>
                              <div>
                                <span className="text-[10px] text-slate-400 dark:text-zinc-500">Occlusion Ratio</span>
                                <p className="text-xs font-semibold text-slate-700 dark:text-zinc-300 mt-0.5">{tree.occlusion}</p>
                              </div>
                            </div>

                            {/* Top predictions softmax list */}
                            <div className="mt-5 rounded-xl border border-slate-200/50 p-4 dark:border-zinc-800/60 bg-white/60 dark:bg-zinc-900/40">
                              <span className="text-[10px] uppercase font-bold text-slate-400 dark:text-zinc-500 tracking-wider">Candidate Classifier Breakdown</span>
                              <div className="mt-3 space-y-2">
                                {tree.top5.map((candidate, idx) => (
                                  <div key={idx} className="flex items-center justify-between text-xs">
                                    <span className="font-medium text-slate-700 dark:text-zinc-300">{candidate.species}</span>
                                    <span className="font-mono font-bold text-slate-800 dark:text-zinc-100">{candidate.confidence}%</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </Card>
                </motion.div>
              );
            })}
          </AnimatePresence>
        )}
      </div>

    </div>
  );
}
