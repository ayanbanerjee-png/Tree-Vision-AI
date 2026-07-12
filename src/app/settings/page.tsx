'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Sun, 
  Moon, 
  Cpu, 
  Server, 
  Info, 
  CheckCircle, 
  RefreshCw, 
  Sliders, 
  HelpCircle, 
  Save,
  XCircle
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useTheme } from '@/components/theme-provider';

export default function SettingsPage() {
  const { theme, toggleTheme } = useTheme();
  
  // State for API configuration
  const [apiEndpoint, setApiEndpoint] = useState('http://localhost:8000');
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'success' | 'failed'>('idle');

  // State for model options
  const [selectedModel, setSelectedModel] = useState('treevision-v1.4.0');
  const [confidenceThreshold, setConfidenceThreshold] = useState(75);
  const [savingSettings, setSavingSettings] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Load preferences from localStorage on client-side mount
  useEffect(() => {
    const savedEndpoint = localStorage.getItem('treevision-api-endpoint');
    if (savedEndpoint) {
      setApiEndpoint(savedEndpoint);
    }
    const savedModel = localStorage.getItem('treevision-selected-model');
    if (savedModel) {
      setSelectedModel(savedModel);
    }
    const savedThreshold = localStorage.getItem('treevision-confidence-threshold');
    if (savedThreshold) {
      setConfidenceThreshold(Number(savedThreshold));
    }
  }, []);

  const testConnection = async () => {
    setTestingConnection(true);
    setConnectionStatus('idle');

    try {
      const response = await fetch(`${apiEndpoint.replace(/\/$/, '')}/health`);
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'healthy') {
          setConnectionStatus('success');
          return;
        }
      }
      setConnectionStatus('failed');
    } catch (error) {
      console.error("Connection check failed:", error);
      setConnectionStatus('failed');
    } finally {
      setTestingConnection(false);
    }
  };

  const saveSettings = () => {
    setSavingSettings(true);
    setSaveSuccess(false);

    try {
      localStorage.setItem('treevision-api-endpoint', apiEndpoint.replace(/\/$/, ''));
      localStorage.setItem('treevision-selected-model', selectedModel);
      localStorage.setItem('treevision-confidence-threshold', String(confidenceThreshold));
      
      // Dispatch a custom event to notify other pages if they are listening
      window.dispatchEvent(new Event('treevision-settings-updated'));
    } catch (error) {
      console.error("Failed to save settings:", error);
    }

    setTimeout(() => {
      setSavingSettings(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    }, 1000);
  };

  return (
    <div className="flex-1 space-y-8 p-6 md:p-8 pt-6 max-w-[1600px] w-full mx-auto font-sans">
      
      {/* Title */}
      <div>
        <h1 className="font-outfit text-3xl font-bold tracking-tight text-slate-800 dark:text-zinc-100">
          Preferences & Settings
        </h1>
        <p className="text-sm text-slate-500 dark:text-zinc-400">
          Configure API connection endpoints, active neural models, and visual user interfaces.
        </p>
      </div>

      <div className="grid gap-6 grid-cols-1 lg:grid-cols-3">
        
        {/* Column 1 & 2: Main Configuration Cards (2 col span) */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Card 1: Active Theme selector */}
          <Card>
            <CardHeader>
              <CardTitle className="font-outfit text-base">Visual Theme</CardTitle>
              <CardDescription>Select your active interface appearance color palette</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                
                {/* Light Mode Selector Card */}
                <div 
                  onClick={() => theme === 'dark' && toggleTheme()}
                  className={`flex flex-col justify-between rounded-xl border p-4 cursor-pointer transition-all aspect-video select-none ${
                    theme === 'light' 
                      ? 'border-emerald-500 bg-emerald-500/5 dark:bg-emerald-500/10 shadow-sm' 
                      : 'border-slate-200/80 hover:bg-slate-50 dark:border-zinc-800/80 dark:hover:bg-zinc-900/30'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 dark:bg-zinc-800 text-slate-700 dark:text-zinc-300 border border-slate-200/50 dark:border-zinc-800/50">
                      <Sun size={16} />
                    </div>
                    {theme === 'light' && <CheckCircle size={16} className="text-emerald-500" />}
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-800 dark:text-zinc-200">Light Mode</p>
                    <span className="text-[10px] text-slate-400 dark:text-zinc-500 block mt-0.5">Clean Slate backgrounds</span>
                  </div>
                </div>

                {/* Dark Mode Selector Card */}
                <div 
                  onClick={() => theme === 'light' && toggleTheme()}
                  className={`flex flex-col justify-between rounded-xl border p-4 cursor-pointer transition-all aspect-video select-none ${
                    theme === 'dark' 
                      ? 'border-emerald-500 bg-emerald-500/5 dark:bg-emerald-500/10 shadow-sm' 
                      : 'border-slate-200/80 hover:bg-slate-50 dark:border-zinc-800/80 dark:hover:bg-zinc-900/30'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 dark:bg-zinc-800 text-slate-700 dark:text-zinc-300 border border-slate-200/50 dark:border-zinc-800/50">
                      <Moon size={16} />
                    </div>
                    {theme === 'dark' && <CheckCircle size={16} className="text-emerald-500" />}
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-800 dark:text-zinc-200">Dark Mode</p>
                    <span className="text-[10px] text-slate-400 dark:text-zinc-500 block mt-0.5">Zinc-950 midnight themes</span>
                  </div>
                </div>

              </div>
            </CardContent>
          </Card>

          {/* Card 2: Neural Net Model configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="font-outfit text-base">Classifier Engine Config</CardTitle>
              <CardDescription>Configure neural classification parameters and thresholds</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              
              {/* Model version */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-600 dark:text-zinc-400">Classifier Architecture Model</label>
                <select 
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full py-2.5 px-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white dark:bg-zinc-900 dark:border-zinc-800 dark:text-zinc-100"
                >
                  <option value="treevision-v1.4.0">TreeVision Classifier v1.4.0 (Recommended)</option>
                  <option value="treevision-v1.3.2">TreeVision Classifier v1.3.2 (Legacy)</option>
                  <option value="canopy-seg-v0.9">Canopy Segmentation Engine v0.9 (Experimental)</option>
                </select>
              </div>

              {/* Confidence thresholds slider */}
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <label className="font-bold text-slate-600 dark:text-zinc-400">Auditor Confidence Limit</label>
                  <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">{confidenceThreshold}%</span>
                </div>
                <input
                  type="range"
                  min="50"
                  max="95"
                  step="5"
                  value={confidenceThreshold}
                  onChange={(e) => setConfidenceThreshold(Number(e.target.value))}
                  className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-emerald-500 dark:bg-zinc-800"
                />
                <span className="text-[10px] text-slate-400 dark:text-zinc-500 block font-medium">
                  Assessments with predictions scoring below this threshold will automatically flag "Needs Review" status.
                </span>
              </div>

            </CardContent>
          </Card>

          {/* Card 3: Backend API Endpoints */}
          <Card>
            <CardHeader>
              <CardTitle className="font-outfit text-base">Backend Connection</CardTitle>
              <CardDescription>Configure remote gateway URL settings for real-time evaluations</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-600 dark:text-zinc-400">Gateway Assessment Endpoint</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={apiEndpoint}
                    onChange={(e) => setApiEndpoint(e.target.value)}
                    className="flex-1 px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white dark:bg-zinc-900 dark:border-zinc-800 dark:text-zinc-100"
                  />
                  <Button 
                    variant="outline" 
                    onClick={testConnection} 
                    disabled={testingConnection}
                    className="rounded-xl text-xs flex items-center space-x-1 border-slate-200"
                  >
                    {testingConnection ? (
                      <RefreshCw size={14} className="animate-spin" />
                    ) : (
                      <span>Test Connection</span>
                    )}
                  </Button>
                </div>
              </div>

              {/* Status Message */}
              {connectionStatus === 'success' && (
                <div className="flex items-center space-x-2 text-xs text-emerald-600 dark:text-emerald-400 font-semibold bg-emerald-500/10 p-3 rounded-xl border border-emerald-500/10">
                  <CheckCircle size={14} />
                  <span>Verified: Node handshake resolved. Pipeline online.</span>
                </div>
              )}
              {connectionStatus === 'failed' && (
                <div className="flex items-center space-x-2 text-xs text-red-600 dark:text-red-400 font-semibold bg-red-500/10 p-3 rounded-xl border border-red-500/10">
                  <XCircle size={14} />
                  <span>Error: Connection failed. Verify backend status and host port.</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Save Action Footer */}
          <div className="flex items-center justify-end space-x-4">
            {saveSuccess && (
              <span className="text-xs text-emerald-600 dark:text-emerald-400 font-bold">Preferences updated!</span>
            )}
            <Button 
              variant="primary" 
              onClick={saveSettings} 
              disabled={savingSettings}
              className="rounded-xl flex items-center space-x-1.5 shadow-md px-6"
            >
              {savingSettings ? (
                <RefreshCw size={16} className="animate-spin" />
              ) : (
                <>
                  <Save size={16} />
                  <span>Save Configuration</span>
                </>
              )}
            </Button>
          </div>

        </div>

        {/* Column 3: About Application Cards (1 col span) */}
        <div className="flex flex-col space-y-6">
          
          {/* Card 4: About Information */}
          <Card className="h-full flex flex-col justify-between">
            <div>
              <CardHeader>
                <CardTitle className="font-outfit text-base">About Application</CardTitle>
                <CardDescription>System specifications and environmental metrics</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                
                <div className="text-xs space-y-3">
                  <p className="text-slate-500 dark:text-zinc-400 font-light leading-relaxed">
                    TreeVision AI is developed for research teams to perform quick evaluations of biomass crowns. The platform employs high-resolution semantic segmentation nodes combined with taxonomy classification matrices.
                  </p>
                  
                  <div className="border-t border-slate-100 dark:border-zinc-800/80 pt-3.5 space-y-2">
                    <div className="flex justify-between">
                      <span className="text-slate-400 dark:text-zinc-500">License:</span>
                      <span className="font-semibold text-slate-700 dark:text-zinc-300">Commercial / Enterprise</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400 dark:text-zinc-500">Framework:</span>
                      <span className="font-semibold text-slate-700 dark:text-zinc-300">Next.js 15 (App Router)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400 dark:text-zinc-500">React Core:</span>
                      <span className="font-semibold text-slate-700 dark:text-zinc-300">React 19.0.0</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400 dark:text-zinc-500">Engine Build:</span>
                      <span className="font-mono text-slate-700 dark:text-zinc-300">1.4.0-production-release</span>
                    </div>
                  </div>
                </div>

              </CardContent>
            </div>
            
            <div className="p-6 border-t border-slate-200/30 dark:border-zinc-800/30 bg-slate-50/40 dark:bg-zinc-900/20 rounded-b-2xl flex items-center space-x-2.5">
              <Info size={16} className="text-slate-400" />
              <span className="text-[10px] text-slate-400 dark:text-zinc-500">Need support? Contact IT forestry core.</span>
            </div>
          </Card>
        </div>

      </div>
    </div>
  );
}
