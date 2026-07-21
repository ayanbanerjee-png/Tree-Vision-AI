'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  ChevronDown,
  ChevronUp,
  Clock,
  AlertCircle,
  Database,
  UserCheck,
} from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { INITIAL_MOCK_TREES } from '@/data/mockTrees';
import { TreeAnalysis, HealthStatus } from '@/types';

// ── Extended type carrying human-review fields alongside TreeAnalysis ─────────
interface LiveTreeRecord extends TreeAnalysis {
  reviewStatus:    string;        // 'pending' | 'approved' | 'rejected'
  reviewedSpecies: string | null;
  reviewedHealth:  string | null;
  reviewedAge:     string | null;
  reviewedFoliage: string | null;
  reviewedAt:      string | null;
  // Original ML values retained for secondary display
  mlSpecies:  string;
  mlHealth:   string;
  mlAge:      string;
  mlFoliage:  string;
}

export default function HistoryPage() {
  const [trees, setTrees] = useState<LiveTreeRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [healthFilter, setHealthFilter] = useState<string>('All');
  const [reviewFilter, setReviewFilter] = useState<string>('All');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    const fetchHistory = async () => {
      const gatewayUrl = localStorage.getItem('treevision-api-endpoint') || 'http://localhost:8000';
      try {
        setLoading(true);
        const res = await fetch(`${gatewayUrl.replace(/\/$/, '')}/predictions`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        const healthMap: Record<string, string> = {
          Healthy: 'Healthy',
          Stressed: 'Mild Decline',
          Damaged: 'Severe Disease',
          Dead: 'Severe Disease',
        };

        const liveTrees: LiveTreeRecord[] = data.map((item: any) => {
          // Determine effective (display) values — prefer reviewed override when set
          const effectiveSpecies  = item.reviewed_species ?? item.species;
          const effectiveHealth   = item.reviewed_health  ?? item.health;
          const effectiveAge      = item.reviewed_age     ?? item.age;
          const effectiveFoliage  = item.reviewed_foliage ?? item.foliage;

          return {
            // Base TreeAnalysis fields — use reviewed values as primary where available
            id:           item.request_id || `TR-${item.id}`,
            species:      effectiveSpecies,
            rawSpecies:   item.raw_species,
            confidence:   item.confidence,
            speciesGroup: item.species_group,
            health:       (healthMap[effectiveHealth] || effectiveHealth) as any,
            age:          effectiveAge as any,
            foliage:      effectiveFoliage as any,
            imageQuality: (item.image_quality.charAt(0).toUpperCase() + item.image_quality.slice(1)) as any,
            occlusion:    (item.occlusion === 'None' ? 'No' : item.occlusion) as any,
            needsReview:  item.needs_review,
            timestamp:    item.timestamp,
            top5: item.top_predictions
              ? item.top_predictions.map((p: any) => ({ species: p.species, confidence: p.confidence }))
              : [],
            // Human-review fields
            reviewStatus:    item.review_status    ?? 'pending',
            reviewedSpecies: item.reviewed_species ?? null,
            reviewedHealth:  item.reviewed_health  ?? null,
            reviewedAge:     item.reviewed_age     ?? null,
            reviewedFoliage: item.reviewed_foliage ?? null,
            reviewedAt:      item.reviewed_at      ?? null,
            // Original ML values for secondary display
            mlSpecies:  item.species,
            mlHealth:   item.health,
            mlAge:      item.age,
            mlFoliage:  item.foliage,
          };
        });

        const mockFiltered = INITIAL_MOCK_TREES.filter(
          mt => !liveTrees.some(lt => lt.id === mt.id)
        );
        // Cast mock trees to LiveTreeRecord with defaults
        const mockAsLive: LiveTreeRecord[] = mockFiltered.map(mt => ({
          ...mt,
          reviewStatus: 'pending',
          reviewedSpecies: null, reviewedHealth: null, reviewedAge: null,
          reviewedFoliage: null, reviewedAt: null,
          mlSpecies: mt.species, mlHealth: mt.health as string,
          mlAge: mt.age as string, mlFoliage: mt.foliage as string,
        }));
        setTrees([...liveTrees, ...mockAsLive]);
      } catch (err: any) {
        console.warn('Failed to fetch live predictions history, using static mock:', err);
        const mockAsLive: LiveTreeRecord[] = INITIAL_MOCK_TREES.map(mt => ({
          ...mt,
          reviewStatus: 'pending',
          reviewedSpecies: null, reviewedHealth: null, reviewedAge: null,
          reviewedFoliage: null, reviewedAt: null,
          mlSpecies: mt.species, mlHealth: mt.health as string,
          mlAge: mt.age as string, mlFoliage: mt.foliage as string,
        }));
        setTrees(mockAsLive);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const filteredTrees = trees.filter((tree) => {
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

  const getHealthBadge = (health: HealthStatus | string) => {
    switch (health) {
      case 'Healthy':       return <Badge variant="emerald">{health}</Badge>;
      case 'Mild Decline':  return <Badge variant="amber">{health}</Badge>;
      case 'Severe Disease':return <Badge variant="red">{health}</Badge>;
      default:              return <Badge variant="gray">{health}</Badge>;
    }
  };

  // ── Helper: render a field with reviewed-vs-ML split when overridden ────────
  const ReviewedField = ({
    label,
    reviewedValue,
    mlValue,
    isReviewed,
  }: {
    label: string;
    reviewedValue: string | null;
    mlValue: string;
    isReviewed: boolean;
  }) => {
    const display = isReviewed && reviewedValue ? reviewedValue : mlValue;
    return (
      <div>
        <span className="text-[10px] text-slate-400 dark:text-zinc-500">{label}</span>
        <p className="text-xs font-semibold text-slate-700 dark:text-zinc-300 mt-0.5">{display}</p>
        {isReviewed && reviewedValue && reviewedValue !== mlValue && (
          <p className="text-[10px] text-slate-400 dark:text-zinc-500 mt-0.5 italic">
            model: {mlValue}
          </p>
        )}
      </div>
    );
  };

  return (
    <div className="flex-1 space-y-8 p-6 md:p-8 pt-6 max-w-[1600px] w-full mx-auto font-sans">

      {/* Title */}
      <div>
        <h1 className="font-outfit text-3xl font-bold tracking-tight text-slate-800 dark:text-zinc-100">
          History Timeline
        </h1>
        <p className="text-sm text-slate-500 dark:text-zinc-400">
          Search and review previously identified species, health anomalies, and auditor corrections.
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
              const isHumanReviewed = tree.reviewStatus === 'approved' || tree.reviewStatus === 'rejected';
              const formattedDate = new Date(tree.timestamp).toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              });

              // Determine which individual fields were actually overridden
              const speciesOverridden = isHumanReviewed && tree.reviewedSpecies !== null;
              const healthOverridden  = isHumanReviewed && tree.reviewedHealth  !== null;
              const ageOverridden     = isHumanReviewed && tree.reviewedAge     !== null;
              const foliageOverridden = isHumanReviewed && tree.reviewedFoliage !== null;

              // Display species: reviewed > original ML display label
              const displaySpecies = speciesOverridden ? tree.reviewedSpecies! : tree.species;

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
                      isExpanded
                        ? 'border-emerald-500/40 dark:border-emerald-500/25 ring-1 ring-emerald-500/10'
                        : isHumanReviewed
                        ? 'border-violet-200/70 dark:border-violet-500/20'
                        : 'border-slate-200/60 dark:border-zinc-800/80'
                    }`}
                    onClick={() => toggleExpand(tree.id)}
                  >
                    <div className="p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 select-none">

                      {/* Timeline Info & Title */}
                      <div className="flex items-start space-x-4">
                        <div className={`flex h-10 w-10 items-center justify-center rounded-xl border ${
                          isHumanReviewed
                            ? 'bg-violet-50 dark:bg-violet-500/10 border-violet-100 dark:border-violet-500/20 text-violet-500'
                            : 'bg-slate-50 dark:bg-zinc-950 border-slate-100 dark:border-zinc-900 text-slate-500 dark:text-zinc-400'
                        }`}>
                          {isHumanReviewed ? <UserCheck size={16} /> : <Clock size={16} />}
                        </div>
                        <div>
                          <div className="flex items-center space-x-2 text-[10px] text-slate-400 dark:text-zinc-500 font-mono">
                            <span className="font-bold">{tree.id}</span>
                            <span>•</span>
                            <span>{formattedDate}</span>
                          </div>
                          <h4 className="font-outfit text-base font-extrabold text-slate-800 dark:text-zinc-100 mt-1 flex items-center gap-2 flex-wrap">
                            <span>{displaySpecies}</span>
                            {/* Human-reviewed badge */}
                            {isHumanReviewed && (
                              <span className="inline-flex items-center gap-1 rounded-full bg-violet-100 dark:bg-violet-500/15 text-violet-700 dark:text-violet-300 text-[9px] font-bold px-2 py-0.5 border border-violet-200/60 dark:border-violet-500/25">
                                <UserCheck size={9} />
                                Human-reviewed
                              </span>
                            )}
                            {tree.needsReview && !isHumanReviewed && (
                              <Badge variant="amber" className="text-[9px] px-1.5 py-0">Review Req</Badge>
                            )}
                          </h4>
                          {/* Show original ML species when it was overridden */}
                          {speciesOverridden && tree.reviewedSpecies !== tree.mlSpecies && (
                            <p className="text-[10px] text-slate-400 dark:text-zinc-500 mt-0.5">
                              model predicted: <span className="font-mono">{tree.mlSpecies}</span>
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Right Hand Stats */}
                      <div className="flex items-center space-x-6 w-full md:w-auto justify-between md:justify-end border-t md:border-t-0 border-slate-100 dark:border-zinc-900 pt-3 md:pt-0">
                        <div className="flex flex-col items-start gap-1">
                          {/* Health — primary (reviewed if set, else ML) */}
                          {getHealthBadge(tree.health)}
                          {/* Show ML health in muted text when overridden */}
                          {healthOverridden && tree.reviewedHealth !== tree.mlHealth && (
                            <span className="text-[9px] text-slate-400 dark:text-zinc-500">
                              model: {tree.mlHealth}
                            </span>
                          )}
                        </div>

                        <div className="flex flex-col items-start gap-1">
                          <Badge variant="gray">{tree.age}</Badge>
                          {ageOverridden && tree.reviewedAge !== tree.mlAge && (
                            <span className="text-[9px] text-slate-400 dark:text-zinc-500">
                              model: {tree.mlAge}
                            </span>
                          )}
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
                          onClick={(e) => e.stopPropagation()}
                        >
                          <div className="px-5 pb-5 border-t border-slate-100 dark:border-zinc-800/80 pt-4 bg-slate-50/20 dark:bg-zinc-900/10">

                            {/* Human review detail block */}
                            {isHumanReviewed && (
                              <div className="mb-4 rounded-xl border border-violet-200/60 dark:border-violet-500/20 bg-violet-50/50 dark:bg-violet-500/5 p-3.5">
                                <p className="text-[10px] uppercase font-bold tracking-wider text-violet-500 dark:text-violet-400 mb-2 flex items-center gap-1.5">
                                  <UserCheck size={11} /> Human Review — {tree.reviewStatus}
                                  {tree.reviewedAt && (
                                    <span className="font-normal normal-case text-violet-400 dark:text-violet-500 ml-1">
                                      · {new Date(tree.reviewedAt).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                                    </span>
                                  )}
                                </p>
                                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                                  <div>
                                    <span className="text-[10px] text-violet-400 dark:text-violet-500">Reviewed Species</span>
                                    <p className="font-semibold text-slate-700 dark:text-zinc-200 mt-0.5">
                                      {tree.reviewedSpecies ?? <span className="text-slate-400 italic">unchanged</span>}
                                    </p>
                                  </div>
                                  <div>
                                    <span className="text-[10px] text-violet-400 dark:text-violet-500">Reviewed Health</span>
                                    <p className="font-semibold text-slate-700 dark:text-zinc-200 mt-0.5">
                                      {tree.reviewedHealth ?? <span className="text-slate-400 italic">unchanged</span>}
                                    </p>
                                  </div>
                                  <div>
                                    <span className="text-[10px] text-violet-400 dark:text-violet-500">Reviewed Age</span>
                                    <p className="font-semibold text-slate-700 dark:text-zinc-200 mt-0.5">
                                      {tree.reviewedAge ?? <span className="text-slate-400 italic">unchanged</span>}
                                    </p>
                                  </div>
                                  <div>
                                    <span className="text-[10px] text-violet-400 dark:text-violet-500">Reviewed Foliage</span>
                                    <p className="font-semibold text-slate-700 dark:text-zinc-200 mt-0.5">
                                      {tree.reviewedFoliage ?? <span className="text-slate-400 italic">unchanged</span>}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            )}

                            <h5 className="text-[10px] uppercase font-bold text-slate-400 dark:text-zinc-500 mb-3 tracking-wider">Additional Pipeline Diagnostics</h5>
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                              <div>
                                <span className="text-[10px] text-slate-400 dark:text-zinc-500">Species Group</span>
                                <p className="text-xs font-semibold text-slate-700 dark:text-zinc-300 mt-0.5">{tree.speciesGroup}</p>
                              </div>
                              <div>
                                <span className="text-[10px] text-slate-400 dark:text-zinc-500">Foliage Density</span>
                                <p className="text-xs font-semibold text-slate-700 dark:text-zinc-300 mt-0.5">
                                  {tree.foliage}
                                  {foliageOverridden && tree.reviewedFoliage !== tree.mlFoliage && (
                                    <span className="text-slate-400 font-normal italic ml-1">(model: {tree.mlFoliage})</span>
                                  )}
                                </p>
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
                            {tree.top5 && tree.top5.length > 0 && (
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
                            )}
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
