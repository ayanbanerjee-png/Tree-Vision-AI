'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ClipboardCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ChevronDown,
  RefreshCw,
  Database,
  Info,
  Loader2,
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

// ── Dropdown option definitions ────────────────────────────────────────────────
// Options marked unseenInTraining will display a visual "rare/unseen" tag so
// reviewers understand these are valid real-world states the model cannot output.

interface DropdownOption {
  value: string;
  unseenInTraining?: boolean;  // true = not a class the current model can output
}

const HEALTH_OPTIONS: DropdownOption[] = [
  { value: 'Healthy' },
  { value: 'Stressed' },
  { value: 'Damaged',  unseenInTraining: true },  // 1 training example, model blind in practice
  { value: 'Dead',     unseenInTraining: true },  // never in training data
];

const FOLIAGE_OPTIONS: DropdownOption[] = [
  { value: 'Full Canopy' },
  { value: 'Evergreen' },
  { value: 'Partial Foliage' },
  { value: 'Leafless', unseenInTraining: true },  // never in training data
];

const AGE_OPTIONS: DropdownOption[] = [
  { value: 'Seedling (0-2yr)' },
  { value: 'Young (2-10yr)' },
  { value: 'Maturing (10-30yr)' },
  { value: 'Mature (30+yr)' },
];

const SPECIES_OPTIONS: string[] = [
  'Aegle_marmelos',
  'Azadirachta_indica',
  'Borassus_flabellifer',
  'Cassia_fistula',
  'Cassia_siamea',
  'Cedrus_deodara',
  'Dalbergia_sissoo',
  'Delonix_regia',
  'Eucalyptus_globulus',
  'Ficus_benghalensis',
  'Ficus_religiosa',
  'Jacaranda_mimosifolia',
  'Kigelia_africana',
  'Lagerstroemia_speciosa',
  'Lantana_camara',
  'Liriodendron_chinense',
  'Moringa_oleifera',
  'Pinus_roxburghii',
  'Plumeria_rubra',
  'Pongamia_pinnata',
  'Sapindus_saponaria',
  'Saraca_asoca',
  'Tectona_grandis',
  'Terminalia_arjuna',
  'Vitex_negundo',
];

// ── Types ─────────────────────────────────────────────────────────────────────

interface QueueItem {
  id: number;
  request_id: string;
  timestamp: string;
  filename: string | null;
  species: string;
  raw_species: string;
  confidence: number;
  health: string;
  age: string;
  foliage: string;
  image_quality: string;
  occlusion: string;
  needs_review: boolean;
  ood_similarity: number | null;
  ood_nearest_species: string | null;
  tree_detector_status: string;
  review_status: string;
}

interface ReviewDraft {
  species: string;
  health: string;
  age: string;
  foliage: string;
}

// ── Sub-components ─────────────────────────────────────────────────────────────

/** A styled <select> that matches the existing project input style */
function StyledSelect({
  value,
  onChange,
  options,
  label,
}: {
  value: string;
  onChange: (v: string) => void;
  options: DropdownOption[];
  label: string;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[10px] uppercase font-bold tracking-wider text-slate-400 dark:text-zinc-500">
        {label}
      </label>
      <div className="relative">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full appearance-none pl-3 pr-8 py-2 border border-slate-200 rounded-xl text-sm text-slate-800 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-zinc-900 dark:border-zinc-700 dark:text-zinc-100"
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.value}{opt.unseenInTraining ? ' ⚠ rare/unseen in training' : ''}
            </option>
          ))}
        </select>
        <ChevronDown
          size={14}
          className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
        />
      </div>
      {/* Show inline callout when a reviewer has actively selected an unseen class */}
      {options.find((o) => o.value === value)?.unseenInTraining && (
        <p className="flex items-center gap-1 text-[10px] text-amber-600 dark:text-amber-400 mt-0.5">
          <AlertTriangle size={10} />
          This class is rare/unseen in training data — reviewer judgment call, not model output.
        </p>
      )}
    </div>
  );
}

/** Build a human-readable reason for review from a QueueItem */
function reviewReason(item: QueueItem): string {
  const reasons: string[] = [];
  if (item.ood_similarity !== null && item.ood_similarity < 0.50)
    reasons.push(`OOD: similarity ${(item.ood_similarity * 100).toFixed(0)}%`);
  if (item.confidence < 70) reasons.push(`Low confidence: ${item.confidence.toFixed(1)}%`);
  if (item.image_quality !== 'clear') reasons.push(`Image quality: ${item.image_quality}`);
  if (item.occlusion !== 'None' && item.occlusion !== 'No')
    reasons.push(`Occlusion: ${item.occlusion}`);
  return reasons.length > 0 ? reasons.join(' · ') : 'Flagged for review';
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function ReviewPage() {
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Record<number, ReviewDraft>>({});
  const [submitting, setSubmitting] = useState<Record<number, boolean>>({});
  const [submitted, setSubmitted] = useState<Record<number, 'approved' | 'rejected'>>({});

  const apiBase = useCallback(() => {
    if (typeof window === 'undefined') return 'http://localhost:8000';
    return (localStorage.getItem('treevision-api-endpoint') || 'http://localhost:8000').replace(/\/$/, '');
  }, []);

  const fetchQueue = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase()}/review-queue`);
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      const data: QueueItem[] = await res.json();
      setQueue(data);
      // Initialise drafts with current ML values so edits are opt-in, not mandatory
      const initial: Record<number, ReviewDraft> = {};
      data.forEach((item) => {
        initial[item.id] = {
          species: item.raw_species ?? item.species,
          health:  item.health,
          age:     item.age,
          foliage: item.foliage,
        };
      });
      setDrafts(initial);
    } catch (err: any) {
      setError(err.message ?? 'Failed to load review queue');
    } finally {
      setLoading(false);
    }
  }, [apiBase]);

  useEffect(() => { fetchQueue(); }, [fetchQueue]);

  const updateDraft = (id: number, field: keyof ReviewDraft, value: string) => {
    setDrafts((prev) => ({ ...prev, [id]: { ...prev[id], [field]: value } }));
  };

  const handleSubmit = async (item: QueueItem, decision: 'approved' | 'rejected') => {
    setSubmitting((prev) => ({ ...prev, [item.id]: true }));
    const draft = drafts[item.id];
    const body = {
      review_status: decision,
      species: draft.species !== (item.raw_species ?? item.species) ? draft.species : undefined,
      health:  draft.health  !== item.health  ? draft.health  : undefined,
      age:     draft.age     !== item.age     ? draft.age     : undefined,
      foliage: draft.foliage !== item.foliage ? draft.foliage : undefined,
    };
    try {
      const res = await fetch(`${apiBase()}/predictions/${item.id}/review`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errData.detail ?? `HTTP ${res.status}`);
      }
      setSubmitted((prev) => ({ ...prev, [item.id]: decision }));
      // Remove from visible queue after brief animation
      setTimeout(() => {
        setQueue((prev) => prev.filter((q) => q.id !== item.id));
      }, 1200);
    } catch (err: any) {
      alert(`Review submission failed: ${err.message}`);
    } finally {
      setSubmitting((prev) => ({ ...prev, [item.id]: false }));
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="flex-1 space-y-8 p-6 md:p-8 pt-6 max-w-[1400px] w-full mx-auto font-sans">

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-outfit text-3xl font-bold tracking-tight text-slate-800 dark:text-zinc-100 flex items-center gap-2.5">
            <ClipboardCheck size={28} className="text-emerald-500" />
            Auditor Review Queue
          </h1>
          <p className="text-sm text-slate-500 dark:text-zinc-400 mt-1">
            Review predictions flagged as needing human judgment. Edits write to separate columns —
            original ML outputs are preserved.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={fetchQueue}
          className="flex items-center gap-2 rounded-xl self-start sm:self-auto"
          disabled={loading}
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh
        </Button>
      </div>

      {/* Legend */}
      <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50/60 p-3.5 dark:border-amber-500/20 dark:bg-amber-500/5">
        <Info size={15} className="text-amber-500 mt-0.5 shrink-0" />
        <p className="text-xs text-amber-700 dark:text-amber-300 leading-relaxed">
          Options marked <strong>⚠ rare/unseen in training</strong> in the dropdowns are valid
          real-world states the current model has never been trained on (e.g. Dead, Leafless).
          Selecting them captures ground truth for future retraining — these are reviewer judgment
          calls, not model outputs.
        </p>
      </div>

      {/* Loading / Error states */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 size={32} className="animate-spin text-emerald-500" />
        </div>
      )}

      {!loading && error && (
        <div className="flex flex-col items-center justify-center py-20 text-center border border-dashed border-red-200 rounded-2xl bg-red-50/40 dark:border-red-500/20 dark:bg-red-500/5">
          <AlertTriangle size={36} className="text-red-400 mb-3" />
          <h3 className="font-semibold text-slate-700 dark:text-zinc-300">Could not load review queue</h3>
          <p className="text-xs text-slate-400 dark:text-zinc-500 max-w-xs mt-1">{error}</p>
          <Button variant="outline" onClick={fetchQueue} className="mt-4 rounded-xl text-xs">
            Retry
          </Button>
        </div>
      )}

      {!loading && !error && queue.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-center border border-dashed border-slate-200/60 rounded-2xl bg-slate-50/40 dark:border-zinc-800/50 dark:bg-zinc-900/10">
          <Database size={36} className="text-slate-300 dark:text-zinc-700 mb-3" />
          <h3 className="font-semibold text-slate-700 dark:text-zinc-300">No pending reviews</h3>
          <p className="text-xs text-slate-400 dark:text-zinc-500 max-w-[260px] mt-1">
            All predictions have been reviewed, or no predictions have been made yet.
          </p>
        </div>
      )}

      {/* Queue cards */}
      <AnimatePresence>
        {queue.map((item) => {
          const draft = drafts[item.id] ?? { species: item.species, health: item.health, age: item.age, foliage: item.foliage };
          const isSubmitting = submitting[item.id] ?? false;
          const decision = submitted[item.id];
          const requestLabel = item.request_id ? `TR-${item.request_id.toUpperCase().slice(0, 5)}` : `ID-${item.id}`;
          const formattedDate = new Date(item.timestamp).toLocaleString('en-US', {
            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
          });

          return (
            <motion.div
              key={item.id}
              layout="position"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: decision ? 0.4 : 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.97, y: -8 }}
              transition={{ duration: 0.22 }}
            >
              <Card className="border border-slate-200/70 dark:border-zinc-800/80 overflow-hidden">
                {/* Card top bar */}
                <div className="flex items-center justify-between px-5 py-3 border-b border-slate-100 dark:border-zinc-800 bg-slate-50/60 dark:bg-zinc-900/40">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs font-bold text-slate-500 dark:text-zinc-400">{requestLabel}</span>
                    <Badge variant="amber" className="text-[10px]">Pending Review</Badge>
                    {item.needs_review && (
                      <span className="text-[10px] text-rose-500 dark:text-rose-400 font-medium flex items-center gap-1">
                        <AlertTriangle size={10} />
                        {reviewReason(item)}
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] text-slate-400 dark:text-zinc-500">{formattedDate}</span>
                </div>

                <CardContent className="p-5 space-y-5">
                  {/* ML prediction summary row */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-50/80 dark:bg-zinc-900/30 border border-slate-100 dark:border-zinc-800">
                    <div>
                      <p className="text-[10px] uppercase font-bold tracking-wider text-slate-400 dark:text-zinc-500 mb-0.5">ML Species</p>
                      <p className="text-xs font-semibold text-slate-700 dark:text-zinc-200 break-words leading-snug">{item.raw_species ?? item.species}</p>
                      <p className="text-[10px] text-slate-400 dark:text-zinc-500 mt-0.5">
                        {item.confidence.toFixed(1)}% conf
                        {item.ood_similarity !== null && ` · ${(item.ood_similarity * 100).toFixed(0)}% OOD sim`}
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase font-bold tracking-wider text-slate-400 dark:text-zinc-500 mb-0.5">ML Health</p>
                      <p className="text-xs font-semibold text-slate-700 dark:text-zinc-200">{item.health}</p>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase font-bold tracking-wider text-slate-400 dark:text-zinc-500 mb-0.5">ML Age</p>
                      <p className="text-xs font-semibold text-slate-700 dark:text-zinc-200">{item.age}</p>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase font-bold tracking-wider text-slate-400 dark:text-zinc-500 mb-0.5">ML Foliage</p>
                      <p className="text-xs font-semibold text-slate-700 dark:text-zinc-200">{item.foliage}</p>
                    </div>
                  </div>

                  {/* Editable reviewer dropdowns */}
                  <div>
                    <p className="text-[10px] uppercase font-bold tracking-wider text-emerald-600 dark:text-emerald-400 mb-3">
                      Reviewer Corrections (edit only what is wrong)
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                      {/* Species */}
                      <div className="flex flex-col gap-1">
                        <label className="text-[10px] uppercase font-bold tracking-wider text-slate-400 dark:text-zinc-500">
                          Species
                        </label>
                        <div className="relative">
                          <select
                            value={draft.species}
                            onChange={(e) => updateDraft(item.id, 'species', e.target.value)}
                            disabled={isSubmitting}
                            className="w-full appearance-none pl-3 pr-8 py-2 border border-slate-200 rounded-xl text-sm text-slate-800 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:bg-zinc-900 dark:border-zinc-700 dark:text-zinc-100 disabled:opacity-50"
                          >
                            {SPECIES_OPTIONS.map((s) => (
                              <option key={s} value={s}>{s}</option>
                            ))}
                          </select>
                          <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                        </div>
                      </div>

                      {/* Health */}
                      <StyledSelect
                        label="Health"
                        value={draft.health}
                        onChange={(v) => updateDraft(item.id, 'health', v)}
                        options={HEALTH_OPTIONS}
                      />

                      {/* Age */}
                      <StyledSelect
                        label="Age"
                        value={draft.age}
                        onChange={(v) => updateDraft(item.id, 'age', v)}
                        options={AGE_OPTIONS}
                      />

                      {/* Foliage */}
                      <StyledSelect
                        label="Foliage"
                        value={draft.foliage}
                        onChange={(v) => updateDraft(item.id, 'foliage', v)}
                        options={FOLIAGE_OPTIONS}
                      />
                    </div>
                  </div>

                  {/* Action buttons */}
                  <div className="flex items-center gap-3 pt-1">
                    {decision ? (
                      <div className={`flex items-center gap-2 text-sm font-semibold ${decision === 'approved' ? 'text-emerald-600' : 'text-rose-500'}`}>
                        {decision === 'approved'
                          ? <><CheckCircle2 size={16} /> Approved</>
                          : <><XCircle size={16} /> Rejected</>
                        }
                      </div>
                    ) : (
                      <>
                        <Button
                          variant="primary"
                          onClick={() => handleSubmit(item, 'approved')}
                          disabled={isSubmitting}
                          className="flex items-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white shadow-md shadow-emerald-500/20"
                        >
                          {isSubmitting ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle2 size={14} />}
                          Approve
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => handleSubmit(item, 'rejected')}
                          disabled={isSubmitting}
                          className="flex items-center gap-2 rounded-xl border-rose-200 text-rose-600 hover:bg-rose-50 dark:border-rose-500/30 dark:text-rose-400 dark:hover:bg-rose-500/10"
                        >
                          {isSubmitting ? <Loader2 size={14} className="animate-spin" /> : <XCircle size={14} />}
                          Reject
                        </Button>
                        {item.filename && (
                          <span className="text-xs text-slate-400 dark:text-zinc-500 ml-auto truncate max-w-[200px]">
                            {item.filename}
                          </span>
                        )}
                      </>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
