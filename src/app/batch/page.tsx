'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload, 
  Layers, 
  Play, 
  Download, 
  CheckCircle, 
  X, 
  RefreshCw, 
  AlertTriangle, 
  Trash2, 
  Sparkles,
  FileSpreadsheet
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import { BatchItem, TreeAnalysis } from '@/types';

export default function BatchPage() {
  const [queue, setQueue] = useState<BatchItem[]>([]);
  const [processing, setProcessing] = useState(false);
  const [isDragActive, setIsDragActive] = useState(false);
  const [totalProgress, setTotalProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true);
    } else if (e.type === 'dragleave') {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFilesToQueue(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFilesToQueue(Array.from(e.target.files));
    }
  };

  const addFilesToQueue = (files: File[]) => {
    const newItems: BatchItem[] = files.map((file) => ({
      id: `BATCH-${Math.floor(100000 + Math.random() * 900000)}`,
      name: file.name,
      size: file.size,
      progress: 0,
      status: 'pending',
      file: file
    }));

    setQueue((prev) => [...prev, ...newItems]);
    setTotalProgress(0);
  };

  const seedDemoFiles = () => {
    const demoFiles = [
      { name: 'neem_canopy_close.jpg', size: 1024 * 720 },
      { name: 'banyan_roots_wide.png', size: 1024 * 1040 },
      { name: 'diseased_leaves_rust.jpg', size: 1024 * 510 },
      { name: 'mango_orchard_gis.webp', size: 1024 * 980 },
      { name: 'teak_plantation_row.jpg', size: 1024 * 850 }
    ];

    const newItems: BatchItem[] = demoFiles.map((f) => {
      // Create empty dummy blobs for demo assets so they represent real File payloads
      const dummyBlob = new Blob([''], { type: 'image/jpeg' });
      const dummyFile = new File([dummyBlob], f.name, { type: 'image/jpeg' });
      return {
        id: `BATCH-${Math.floor(100000 + Math.random() * 900000)}`,
        name: f.name,
        size: f.size,
        progress: 0,
        status: 'pending',
        file: dummyFile
      };
    });

    setQueue((prev) => [...prev, ...newItems]);
    setTotalProgress(0);
  };

  const clearQueue = () => {
    setQueue([]);
    setTotalProgress(0);
    setProcessing(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeQueueItem = (id: string) => {
    setQueue((prev) => prev.filter((item) => item.id !== id));
  };

  // Run the batch pipeline concurrently/sequentially on FastAPI backend
  const startBatchProcessing = async () => {
    if (queue.length === 0 || processing) return;
    setProcessing(true);

    const updatedQueue = [...queue];
    const pendingItems = updatedQueue.filter(item => item.status !== 'completed');

    if (pendingItems.length === 0) {
      setProcessing(false);
      return;
    }

    // Mark items as processing
    pendingItems.forEach(item => {
      item.status = 'processing';
      item.progress = 10;
    });
    setQueue([...updatedQueue]);

    // Simulated progress bar ticker to animate upload stream transition
    const progressTicker = setInterval(() => {
      pendingItems.forEach(item => {
        if (item.progress < 90) {
          item.progress += Math.floor(Math.random() * 8) + 2;
        }
      });
      const cumulativeProgress = updatedQueue.reduce((acc, t) => acc + t.progress, 0);
      setTotalProgress(Math.round(cumulativeProgress / updatedQueue.length));
      setQueue([...updatedQueue]);
    }, 400);

    const formData = new FormData();
    pendingItems.forEach(item => {
      if (item.file) {
        // Appends to key "files" which is accepted as a list by FastAPI predict-batch
        formData.append('files', item.file);
      }
    });

    const gatewayUrl = localStorage.getItem('treevision-api-endpoint') || 'http://localhost:8000';

    try {
      const response = await fetch(`${gatewayUrl.replace(/\/$/, '')}/predict-batch`, {
        method: 'POST',
        body: formData
      });

      clearInterval(progressTicker);

      if (!response.ok) {
        throw new Error(`Batch pipeline server error: status ${response.status}`);
      }

      const rawResults = await response.json();

      const healthMap: Record<string, string> = {
        "Healthy": "Healthy",
        "Stressed": "Mild Decline",
        "Damaged": "Severe Disease",
        "Dead": "Severe Disease"
      };

      // Map raw models outputs back to queue elements
      pendingItems.forEach((item, index) => {
        const rawRes = rawResults[index];
        if (rawRes) {
          item.status = 'completed';
          item.progress = 100;
          item.result = {
            id: `TR-${Math.floor(1000 + Math.random() * 9000)}`,
            species: rawRes.species,
            confidence: rawRes.confidence,
            speciesGroup: rawRes.species_group,
            health: (healthMap[rawRes.health] || rawRes.health) as any,
            age: rawRes.age as any,
            foliage: rawRes.foliage as any,
            imageQuality: (rawRes.image_quality.charAt(0).toUpperCase() + rawRes.image_quality.slice(1)) as any,
            occlusion: (rawRes.occlusion === 'None' ? 'No' : rawRes.occlusion) as any,
            needsReview: rawRes.needs_review,
            timestamp: new Date().toISOString(),
            top5: rawRes.top_predictions.map((p: any) => ({
              species: p.species,
              confidence: p.confidence
            }))
          };
        } else {
          item.status = 'failed';
          item.progress = 100;
        }
      });

    } catch (error) {
      console.error("Batch inference failed:", error);
      clearInterval(progressTicker);
      pendingItems.forEach(item => {
        item.status = 'failed';
        item.progress = 100;
      });
    } finally {
      const cumulativeProgress = updatedQueue.reduce((acc, t) => acc + t.progress, 0);
      setTotalProgress(Math.round(cumulativeProgress / updatedQueue.length));
      setQueue([...updatedQueue]);
      setProcessing(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed': return <Badge variant="emerald">Completed</Badge>;
      case 'processing': return <Badge variant="blue" className="animate-pulse">Processing</Badge>;
      case 'pending': return <Badge variant="gray">Queued</Badge>;
      case 'failed': return <Badge variant="red">Failed</Badge>;
      default: return <Badge variant="gray">{status}</Badge>;
    }
  };

  const getHealthBadge = (health: string) => {
    switch (health) {
      case 'Healthy': return <Badge variant="emerald">{health}</Badge>;
      case 'Mild Decline': return <Badge variant="amber">{health}</Badge>;
      case 'Severe Disease': return <Badge variant="red">{health}</Badge>;
      default: return <Badge variant="gray">{health}</Badge>;
    }
  };

  const handleExport = () => {
    // Generate a downloadable CSV report of the diagnostic predictions
    const completedItems = queue.filter(item => item.status === 'completed' && item.result);
    if (completedItems.length === 0) return;

    const headers = ["ID", "File Name", "Species", "Confidence (%)", "Species Group", "Health Status", "Age Class", "Foliage Density", "Image Quality", "Occlusion", "Needs Review"];
    const rows = completedItems.map(item => {
      const res = item.result!;
      return [
        res.id,
        item.name,
        `"${res.species.replace(/"/g, '""')}"`,
        res.confidence,
        res.speciesGroup,
        res.health,
        res.age,
        res.foliage,
        res.imageQuality,
        res.occlusion,
        res.needsReview ? "Yes" : "No"
      ];
    });

    const csvContent = [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", url);
    downloadAnchor.setAttribute("download", `treevision_batch_report_${Date.now()}.csv`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const isExportEnabled = queue.some(item => item.status === 'completed');

  return (
    <div className="flex-1 space-y-8 p-6 md:p-8 pt-6 max-w-[1600px] w-full mx-auto">
      
      {/* Title */}
      <div className="flex flex-col space-y-2 md:flex-row md:items-center md:justify-between md:space-y-0">
        <div>
          <h1 className="font-outfit text-3xl font-bold tracking-tight text-slate-800 dark:text-zinc-100">
            Batch Analysis
          </h1>
          <p className="text-sm text-slate-500 dark:text-zinc-400">
            Upload multiple forest assessment images to run queue parsing diagnostics concurrently.
          </p>
        </div>
        <div className="flex items-center space-x-2.5">
          {queue.length === 0 && (
            <Button variant="outline" size="sm" onClick={seedDemoFiles} className="rounded-xl flex items-center space-x-1.5 text-xs">
              <Sparkles size={14} className="text-emerald-500" />
              <span>Load Demo Images</span>
            </Button>
          )}
          {queue.length > 0 && (
            <Button variant="ghost" size="sm" onClick={clearQueue} disabled={processing} className="rounded-xl text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 text-xs flex items-center space-x-1">
              <Trash2 size={14} />
              <span>Clear Queue</span>
            </Button>
          )}
        </div>
      </div>

      <div className="grid gap-6 grid-cols-1 xl:grid-cols-4 items-start">
        
        {/* Upload Dropzone Widget (1 col) */}
        <div className="xl:col-span-1 flex flex-col space-y-6">
          <Card className="h-full flex flex-col justify-between">
            <CardHeader>
              <CardTitle className="font-outfit text-base">Bulk File Source</CardTitle>
              <CardDescription>Select tree images to append to the background diagnostics thread</CardDescription>
            </CardHeader>
            <CardContent>
              <motion.div
                onDragEnter={handleDrag}
                onDragOver={handleDrag}
                onDragLeave={handleDrag}
                onDrop={handleDrop}
                onClick={() => !processing && fileInputRef.current?.click()}
                whileHover={!processing ? { scale: 0.99 } : {}}
                className={`flex flex-col items-center justify-center border border-dashed rounded-xl p-8 text-center transition-all duration-300 min-h-[220px] ${
                  processing ? 'opacity-40 cursor-not-allowed border-slate-200' : 'cursor-pointer border-slate-200 hover:border-emerald-500/80 dark:border-zinc-800 dark:hover:border-emerald-500/80'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept="image/*"
                  onChange={handleFileChange}
                  disabled={processing}
                  className="hidden"
                />
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600 dark:bg-emerald-400/10 dark:text-emerald-400 mb-3">
                  <Upload size={18} />
                </div>
                <p className="text-xs font-semibold text-slate-800 dark:text-zinc-200">Drop multiple files</p>
                <span className="text-[10px] text-slate-400 dark:text-zinc-500 mt-1 max-w-[150px] block">Click to browse your explorer</span>
              </motion.div>
            </CardContent>
            
            {queue.length > 0 && (
              <div className="p-6 border-t border-slate-200/35 dark:border-zinc-800/50 bg-slate-50/50 dark:bg-zinc-900/20 rounded-b-2xl flex flex-col space-y-4">
                {/* Overall Batch Progress */}
                <div>
                  <div className="flex items-center justify-between text-xs font-semibold text-slate-700 dark:text-zinc-300 mb-2">
                    <span>Batch progress</span>
                    <span>{totalProgress}%</span>
                  </div>
                  <Progress value={totalProgress} />
                </div>
                
                <Button 
                  variant="primary" 
                  onClick={startBatchProcessing} 
                  disabled={processing || queue.every(t => t.status === 'completed')}
                  className="rounded-xl flex items-center justify-center space-x-1.5 w-full py-2.5 shadow-md"
                >
                  {processing ? (
                    <>
                      <RefreshCw size={14} className="animate-spin" />
                      <span>Classifying...</span>
                    </>
                  ) : (
                    <>
                      <Play size={14} />
                      <span>Run Batch Assessment</span>
                    </>
                  )}
                </Button>
              </div>
            )}
          </Card>
        </div>

        {/* Results Queue Table View (3 col) */}
        <div className="xl:col-span-3 flex flex-col space-y-6">
          <Card className="h-full">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="font-outfit text-lg">Diagnostics Job Queue</CardTitle>
                <CardDescription>
                  {queue.length === 0 
                    ? 'No images loaded. Seed demo images or drag source files.' 
                    : `${queue.filter(i => i.status === 'completed').length} of ${queue.length} processed`}
                </CardDescription>
              </div>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleExport} 
                disabled={!isExportEnabled} 
                className="rounded-xl text-xs flex items-center space-x-1.5 border-slate-200"
              >
                <FileSpreadsheet size={14} className="text-emerald-500" />
                <span>Export Report (CSV)</span>
              </Button>
            </CardHeader>
            <CardContent className="mt-4">
              {queue.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-center bg-slate-50/50 border border-slate-200/50 border-dashed rounded-2xl dark:bg-zinc-900/10 dark:border-zinc-800/50">
                  <Layers size={36} className="text-slate-300 dark:text-zinc-700 mb-3" />
                  <h3 className="font-semibold text-slate-700 dark:text-zinc-300">File queue empty</h3>
                  <p className="text-xs text-slate-400 dark:text-zinc-500 max-w-[280px] mt-1">
                    Select demo items or upload your local imagery folders to begin batch classification.
                  </p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>File Name</TableHead>
                      <TableHead>File Size</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Predicted Species</TableHead>
                      <TableHead>Confidence</TableHead>
                      <TableHead>Health Assessment</TableHead>
                      <TableHead>Needs Review</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {queue.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell className="font-medium text-slate-800 dark:text-zinc-200 max-w-[160px] truncate">
                          {item.name}
                        </TableCell>
                        <TableCell className="text-xs text-slate-400 dark:text-zinc-500 font-mono">
                          {Math.round(item.size / 1024)} KB
                        </TableCell>
                        <TableCell>{getStatusBadge(item.status)}</TableCell>
                        <TableCell>
                          {item.result ? (
                            <span className="font-semibold text-slate-800 dark:text-zinc-200">
                              {item.result.species.split(' (')[0]}
                            </span>
                          ) : (
                            <span className="text-slate-400 font-light">—</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {item.result ? (
                            <span className={`font-semibold ${item.result.confidence >= 80 ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-500'}`}>
                              {item.result.confidence}%
                            </span>
                          ) : (
                            <span className="text-slate-400 font-light">—</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {item.result ? (
                            getHealthBadge(item.result.health)
                          ) : (
                            <span className="text-slate-400 font-light">—</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {item.result ? (
                            item.result.needsReview ? (
                              <Badge variant="amber">Yes</Badge>
                            ) : (
                              <Badge variant="gray">No</Badge>
                            )
                          ) : (
                            <span className="text-slate-400 font-light">—</span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>

      </div>
    </div>
  );
}
