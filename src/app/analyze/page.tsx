'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload, 
  Image as ImageIcon, 
  Trash2, 
  Cpu, 
  TrendingUp,
  Activity,
  Heart,
  Calendar,
  Layers,
  Sparkles,
  RefreshCw,
  Camera,
  AlertCircle,
  XCircle
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { TreeAnalysis } from '@/types';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const LOADING_STEPS = [
  'Uploading image payload...',
  'Assessing image quality (blur & brightness)...',
  'Executing species classification backbone...',
  'Extracting DINOv2 embedding features...',
  'Predicting physiological health stress...',
  'Estimating specimen age class...',
  'Evaluating canopy foliage density...',
  'Detecting object occlusions...',
  'Synthesizing final assessment report...'
];

export default function AnalyzePage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [analysisResult, setAnalysisResult] = useState<TreeAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Rotate loading steps during real processing
  useEffect(() => {
    let interval: any;
    if (analyzing) {
      interval = setInterval(() => {
        setLoadingStep((prev) => {
          if (prev < LOADING_STEPS.length - 1) {
            return prev + 1;
          }
          return prev;
        });
      }, 400); // 400ms interval for 9 steps takes ~3.6 seconds to complete loading indicators
    } else {
      setLoadingStep(0);
    }
    return () => clearInterval(interval);
  }, [analyzing]);

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

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setFile(file);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const setFile = (file: File) => {
    setSelectedFile(file);
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result as string);
    };
    reader.readAsDataURL(file);
    setAnalysisResult(null); // Clear previous results
    setError(null);
  };

  const removeFile = () => {
    setSelectedFile(null);
    setImagePreview(null);
    setAnalysisResult(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const startAnalysis = async () => {
    if (!selectedFile) return;
    setAnalyzing(true);
    setAnalysisResult(null);
    setError(null);

    const formData = new FormData();
    formData.append('image', selectedFile);

    const gatewayUrl = localStorage.getItem('treevision-api-endpoint') || 'http://localhost:8000';

    try {
      const response = await fetch(`${gatewayUrl.replace(/\/$/, '')}/predict`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server returns status error (${response.status})`);
      }

      const rawResult = await response.json();

      // Translate backend classes to match UI styles expected by frontend components
      const healthMap: Record<string, string> = {
        "Healthy": "Healthy",
        "Stressed": "Mild Decline",
        "Damaged": "Severe Disease",
        "Dead": "Severe Disease"
      };

      const mappedResult: TreeAnalysis = {
        id: `TR-${Math.floor(1000 + Math.random() * 9000)}`,
        species: rawResult.species,
        rawSpecies: rawResult.raw_species,
        confidence: rawResult.confidence,
        speciesGroup: rawResult.species_group,
        health: (healthMap[rawResult.health] || rawResult.health) as any,
        age: rawResult.age as any,
        foliage: rawResult.foliage as any,
        imageQuality: (rawResult.image_quality.charAt(0).toUpperCase() + rawResult.image_quality.slice(1)) as any,
        occlusion: (rawResult.occlusion === 'None' ? 'No' : rawResult.occlusion) as any,
        needsReview: rawResult.needs_review,
        timestamp: new Date().toISOString(),
        top5: rawResult.top_predictions.map((p: any) => ({
          species: p.species,
          confidence: p.confidence
        }))
      };

      setAnalysisResult(mappedResult);
    } catch (e: any) {
      console.error(e);
      setError(e.message || "Could not resolve API request. Verify the backend uvicorn service is online.");
    } finally {
      setAnalyzing(false);
    }
  };

  const getHealthBadgeVariant = (health: string) => {
    switch (health) {
      case 'Healthy': return 'emerald';
      case 'Mild Decline': return 'amber';
      case 'Severe Disease': return 'red';
      default: return 'gray';
    }
  };

  const getAccuracyColor = (conf: number) => {
    if (conf >= 90) return 'text-emerald-600 dark:text-emerald-400';
    if (conf >= 75) return 'text-lime-600 dark:text-lime-400';
    return 'text-amber-500';
  };

  // Convert Top-5 predictions to simple percentages for Recharts
  const chartData = analysisResult
    ? analysisResult.top5.map(t => ({
        name: t.species.split(' (')[0], // Short name
        confidence: Math.round(t.confidence)
      }))
    : [];

  return (
    <div className="flex-1 space-y-8 p-6 md:p-8 pt-6 max-w-[1600px] w-full mx-auto">
      
      {/* Title */}
      <div>
        <h1 className="font-outfit text-3xl font-bold tracking-tight text-slate-800 dark:text-zinc-100">
          Analyze Tree
        </h1>
        <p className="text-sm text-slate-500 dark:text-zinc-400">
          Upload individual foliage or trunk photos to identify tree classifications and stress parameters.
        </p>
      </div>

      <div className="grid gap-6 grid-cols-1 lg:grid-cols-5 items-start">
        
        {/* Left Columns (3 span): Uploader & Preview Panel */}
        <div className="lg:col-span-3 flex flex-col space-y-6">
          <Card className="h-full flex flex-col justify-between">
            <CardHeader>
              <CardTitle className="font-outfit text-lg">Input Photo Upload</CardTitle>
              <CardDescription>Drag and drop a clear photo of the leaves or full tree posture</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col justify-center">
              
              {!imagePreview ? (
                // Dropzone
                <motion.div
                  onDragEnter={handleDrag}
                  onDragOver={handleDrag}
                  onDragLeave={handleDrag}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  whileHover={{ scale: 0.995 }}
                  className={`flex flex-col items-center justify-center border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-300 min-h-[300px] ${
                    isDragActive 
                      ? 'border-emerald-500 bg-emerald-500/5 dark:bg-emerald-500/10' 
                      : 'border-slate-200 hover:border-emerald-500/80 dark:border-zinc-800 dark:hover:border-emerald-500/80'
                  }`}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10 dark:bg-emerald-400/10 text-emerald-600 dark:text-emerald-400 mb-4">
                    <Upload size={24} />
                  </div>
                  <h3 className="font-semibold text-slate-800 dark:text-zinc-200">Drag & drop your file</h3>
                  <p className="text-xs text-slate-500 dark:text-zinc-400 mt-1 max-w-[240px]">
                    Supports JPG, PNG, WebP up to 10MB. For best results, use sharp close-up images.
                  </p>
                </motion.div>
              ) : (
                // Preview Panel
                <div className="space-y-4">
                  <div className="relative rounded-2xl border border-slate-200 overflow-hidden bg-slate-100 dark:border-zinc-800 dark:bg-zinc-950 aspect-[4/3] flex items-center justify-center max-h-[400px]">
                    <img 
                      src={imagePreview} 
                      alt="Tree Preview" 
                      className="w-full h-full object-cover"
                    />
                    
                    {/* Pulsing Scan bar overlay when analyzing */}
                    {analyzing && (
                      <motion.div 
                        initial={{ top: '0%' }}
                        animate={{ top: '100%' }}
                        transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
                        className="absolute left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 to-lime-400 shadow-md shadow-emerald-500/50 z-20 pointer-events-none"
                      />
                    )}
                  </div>
                  
                  {/* Actions */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <ImageIcon size={14} className="text-slate-400" />
                      <span className="text-xs text-slate-500 dark:text-zinc-400 font-mono truncate max-w-[200px]">
                        {selectedFile?.name}
                      </span>
                    </div>
                    {!analyzing && (
                      <Button variant="ghost" size="sm" onClick={removeFile} className="text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-xl">
                        <Trash2 size={14} className="mr-1.5" />
                        <span>Remove</span>
                      </Button>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
            
            {imagePreview && (
              <div className="p-6 border-t border-slate-200/35 dark:border-zinc-800/50 bg-slate-50/50 dark:bg-zinc-900/20 rounded-b-2xl flex justify-end">
                <Button 
                  variant="primary" 
                  onClick={startAnalysis} 
                  disabled={analyzing} 
                  className="rounded-xl flex items-center space-x-2 px-6"
                >
                  {analyzing ? (
                    <>
                      <RefreshCw size={16} className="animate-spin" />
                      <span>Processing Neural Nets...</span>
                    </>
                  ) : (
                    <>
                      <Cpu size={16} />
                      <span>Identify & Assess</span>
                    </>
                  )}
                </Button>
              </div>
            )}
          </Card>
        </div>

        {/* Right Columns (2 span): Loading/Results */}
        <div className="lg:col-span-2 flex flex-col space-y-6">
          <AnimatePresence mode="wait">
            
            {/* 1. Initial State - Waiting for upload */}
            {!imagePreview && !analyzing && !analysisResult && !error && (
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="h-full"
              >
                <Card className="h-full flex flex-col items-center justify-center p-8 text-center min-h-[380px] bg-slate-50/50 border-dashed dark:bg-zinc-900/10">
                  <div className="h-12 w-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-400 dark:bg-zinc-900 dark:text-zinc-600 mb-4">
                    <Camera size={22} />
                  </div>
                  <h3 className="font-semibold text-slate-700 dark:text-zinc-300">Analysis Preview</h3>
                  <p className="text-xs text-slate-400 dark:text-zinc-500 max-w-[200px] mt-1.5">
                    Your deep neural network findings will be visualised here after image processing runs.
                  </p>
                </Card>
              </motion.div>
            )}

            {/* 4. Error Feedback State */}
            {error && !analyzing && (
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="h-full"
              >
                <Card className="h-full flex flex-col items-center justify-center p-8 text-center min-h-[380px] bg-red-50/5 border-red-500/20 border border-dashed dark:bg-red-950/5">
                  <div className="h-12 w-12 rounded-full bg-red-100 flex items-center justify-center text-red-500 dark:bg-red-950/10 dark:text-red-400 mb-4">
                    <XCircle size={22} />
                  </div>
                  <h3 className="font-semibold text-slate-800 dark:text-zinc-200">Connection Failure</h3>
                  <p className="text-xs text-slate-500 dark:text-zinc-400 max-w-[260px] mt-2 leading-relaxed">
                    {error}
                  </p>
                  <Button variant="outline" size="sm" onClick={startAnalysis} className="mt-5 rounded-xl border-slate-200">
                    <RefreshCw size={12} className="mr-1.5 animate-pulse" />
                    <span>Try Again</span>
                  </Button>
                </Card>
              </motion.div>
            )}

            {/* 2. Loading Pipeline State */}
            {analyzing && (
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="h-full"
              >
                <Card className="h-full flex flex-col justify-between p-6 min-h-[380px]">
                  <CardHeader className="p-0">
                    <CardTitle className="font-outfit text-lg flex items-center space-x-2">
                      <Sparkles className="text-emerald-500 animate-pulse" size={18} />
                      <span>Pipeline Diagnostic</span>
                    </CardTitle>
                    <CardDescription>Analyzing pixel weights against classifier clusters...</CardDescription>
                  </CardHeader>
                  <CardContent className="flex-1 flex flex-col justify-center space-y-6 py-8">
                    {/* Animated pipeline steps */}
                    <div className="space-y-4">
                      {LOADING_STEPS.map((step, idx) => {
                        const isDone = idx < loadingStep;
                        const isCurrent = idx === loadingStep;
                        return (
                          <div 
                            key={idx} 
                            className={`flex items-center space-x-3 text-xs transition-opacity duration-300 ${
                              isDone ? 'text-emerald-600 dark:text-emerald-400 font-medium' : isCurrent ? 'text-slate-800 dark:text-zinc-100 font-bold' : 'text-slate-400 dark:text-zinc-600'
                            }`}
                          >
                            <div className="flex h-5 w-5 items-center justify-center rounded-full border border-slate-200 dark:border-zinc-800 font-mono text-[10px]">
                              {isDone ? '✓' : idx + 1}
                            </div>
                            <span className="truncate">{step}</span>
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                  <div className="w-full bg-slate-100 dark:bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${(loadingStep / (LOADING_STEPS.length - 1)) * 100}%` }}
                      transition={{ duration: 0.6 }}
                      className="bg-emerald-500 h-full"
                    />
                  </div>
                </Card>
              </motion.div>
            )}

            {/* 3. Finished Assessment results */}
            {analysisResult && !analyzing && (
              <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="space-y-6"
              >
                {/* Result Card Primary */}
                <Card className="relative overflow-hidden">
                  <div className="absolute right-0 top-0 bg-emerald-500/10 text-emerald-600 px-3.5 py-1 text-[10px] font-bold uppercase rounded-bl-xl dark:bg-emerald-500/20 dark:text-emerald-400">
                    Classification Finished
                  </div>
                  <CardHeader>
                    <CardDescription className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-zinc-500">Predicted Species</CardDescription>
                    <CardTitle className="font-outfit text-xl font-extrabold text-slate-800 dark:text-zinc-100 mt-1">
                      {analysisResult.species}
                    </CardTitle>
                    {analysisResult.rawSpecies && analysisResult.rawSpecies !== analysisResult.species && (
                      <div className="text-xs text-slate-400 dark:text-zinc-500 mt-1 italic font-normal">
                        Raw model guess: {analysisResult.rawSpecies}
                      </div>
                    )}
                  </CardHeader>
                  <CardContent className="space-y-5">
                    <div className="flex justify-between items-center pb-4 border-b border-slate-100 dark:border-zinc-800/80">
                      <div>
                        <span className="text-xs text-slate-400 dark:text-zinc-500">Confidence Score</span>
                        <p className={`text-2xl font-black font-outfit mt-0.5 ${getAccuracyColor(analysisResult.confidence)}`}>
                          {analysisResult.confidence}%
                        </p>
                      </div>
                      <div>
                        <span className="text-xs text-slate-400 dark:text-zinc-500 block text-right">Needs Audit</span>
                        <div className="mt-1 text-right">
                          {analysisResult.needsReview ? (
                            <Badge variant="amber" className="flex items-center space-x-1"><AlertCircle size={10} className="mr-1"/> Yes</Badge>
                          ) : (
                            <Badge variant="gray">No</Badge>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Metadata Parameter Details Grid */}
                    <div className="grid grid-cols-2 gap-3.5">
                      <div className="rounded-xl border border-slate-100 bg-slate-50/50 p-3 dark:border-zinc-800/50 dark:bg-zinc-900/40">
                        <span className="text-[10px] text-slate-400 dark:text-zinc-500 uppercase font-bold flex items-center space-x-1">
                          <Heart size={10} className="text-slate-400" />
                          <span>Health Stress</span>
                        </span>
                        <p className="text-xs font-semibold text-slate-700 dark:text-zinc-300 mt-1 flex items-center space-x-1.5">
                          {getHealthBadgeVariant(analysisResult.health) === 'emerald' && <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />}
                          {getHealthBadgeVariant(analysisResult.health) === 'amber' && <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />}
                          {getHealthBadgeVariant(analysisResult.health) === 'red' && <span className="h-1.5 w-1.5 rounded-full bg-red-500" />}
                          <span>{analysisResult.health}</span>
                        </p>
                      </div>

                      <div className="rounded-xl border border-slate-100 bg-slate-50/50 p-3 dark:border-zinc-800/50 dark:bg-zinc-900/40">
                        <span className="text-[10px] text-slate-400 dark:text-zinc-500 uppercase font-bold flex items-center space-x-1">
                          <Calendar size={10} className="text-slate-400" />
                          <span>Age Class</span>
                        </span>
                        <p className="text-xs font-semibold text-slate-700 dark:text-zinc-300 mt-1">{analysisResult.age}</p>
                      </div>

                      <div className="rounded-xl border border-slate-100 bg-slate-50/50 p-3 dark:border-zinc-800/50 dark:bg-zinc-900/40">
                        <span className="text-[10px] text-slate-400 dark:text-zinc-500 uppercase font-bold flex items-center space-x-1">
                          <Activity size={10} className="text-slate-400" />
                          <span>Foliage Density</span>
                        </span>
                        <p className="text-xs font-semibold text-slate-700 dark:text-zinc-300 mt-1">{analysisResult.foliage}</p>
                      </div>

                      <div className="rounded-xl border border-slate-100 bg-slate-50/50 p-3 dark:border-zinc-800/50 dark:bg-zinc-900/40">
                        <span className="text-[10px] text-slate-400 dark:text-zinc-500 uppercase font-bold flex items-center space-x-1">
                          <Layers size={10} className="text-slate-400" />
                          <span>Group</span>
                        </span>
                        <p className="text-xs font-semibold text-slate-700 dark:text-zinc-300 mt-1 truncate">{analysisResult.speciesGroup}</p>
                      </div>

                      <div className="rounded-xl border border-slate-100 bg-slate-50/50 p-3 dark:border-zinc-800/50 dark:bg-zinc-900/40">
                        <span className="text-[10px] text-slate-400 dark:text-zinc-500 uppercase font-bold">Image Quality</span>
                        <p className="text-xs font-semibold text-slate-700 dark:text-zinc-300 mt-1">{analysisResult.imageQuality}</p>
                      </div>

                      <div className="rounded-xl border border-slate-100 bg-slate-50/50 p-3 dark:border-zinc-800/50 dark:bg-zinc-900/40">
                        <span className="text-[10px] text-slate-400 dark:text-zinc-500 uppercase font-bold">Occlusion Ratio</span>
                        <p className="text-xs font-semibold text-slate-700 dark:text-zinc-300 mt-1">{analysisResult.occlusion}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Top-5 Predictions Chart */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="font-outfit text-sm font-bold flex items-center space-x-1">
                      <TrendingUp size={14} className="text-emerald-500" />
                      <span>Neural Net Classification Breakdown</span>
                    </CardTitle>
                    <CardDescription>Top-5 candidate softmax output distribution</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[200px] w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={chartData}
                          layout="vertical"
                          margin={{ top: 5, right: 10, left: 10, bottom: 5 }}
                        >
                          <XAxis type="number" domain={[0, 100]} hide />
                          <YAxis 
                            dataKey="name" 
                            type="category" 
                            fontSize={10} 
                            axisLine={false} 
                            tickLine={false} 
                            width={75}
                            stroke="#888888"
                          />
                          <Tooltip
                            formatter={(value: any) => [`${value}%`, 'Confidence']}
                            contentStyle={{
                              background: 'rgba(255, 255, 255, 0.95)',
                              border: '1px solid #e2e8f0',
                              borderRadius: '0.5rem',
                              fontSize: '11px'
                            }}
                          />
                          <Bar dataKey="confidence" radius={[0, 4, 4, 0]} barSize={12}>
                            {chartData.map((entry, index) => (
                              <Cell 
                                key={`cell-${index}`} 
                                fill={index === 0 ? '#059669' : '#94a3b8'} 
                              />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
