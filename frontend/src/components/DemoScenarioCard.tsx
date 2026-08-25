'use client';

import React, { useState } from 'react';
import { PlayCircle, ShieldCheck, ArrowRight, CheckCircle2, AlertTriangle, ShieldX } from 'lucide-react';
import { api } from '@/lib/api';

interface DemoScenarioCardProps {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  scenarioType: string;
  expectedResult: string;
  badgeColor: string;
  onScenarioExecuted?: (result: any) => void;
}

export const DemoScenarioCard: React.FC<DemoScenarioCardProps> = ({
  title,
  subtitle,
  description,
  scenarioType,
  expectedResult,
  badgeColor,
  onScenarioExecuted,
}) => {
  const [loading, setLoading] = useState(false);
  const [lastResult, setLastResult] = useState<any | null>(null);

  const runScenario = async () => {
    setLoading(true);
    try {
      const res = await api.simulateScenario(scenarioType);
      setLastResult(res);
      if (onScenarioExecuted) {
        onScenarioExecuted(res);
      }
    } catch (err: any) {
      alert(`Failed to execute scenario: ${err?.message || 'API error'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col justify-between hover:border-slate-700 transition-all">
      <div>
        <div className="flex items-center justify-between mb-3">
          <span className={`text-[11px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-md border ${badgeColor}`}>
            {subtitle}
          </span>
          <PlayCircle className="w-5 h-5 text-blue-400 opacity-80" />
        </div>

        <h3 className="text-lg font-bold text-slate-100 mb-2">{title}</h3>
        <p className="text-xs text-slate-400 leading-relaxed mb-4">{description}</p>

        <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800/80 mb-5">
          <span className="text-[10px] font-semibold uppercase text-slate-500 block mb-1">Expected Pipeline Outcome</span>
          <span className="text-xs font-mono text-slate-300 font-semibold">{expectedResult}</span>
        </div>
      </div>

      <div>
        {lastResult && (
          <div className="mb-4 p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs font-mono space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">AI Rec:</span>
              <span className="text-indigo-400 font-bold">{lastResult.recommended_strategy}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Policy Check:</span>
              <span className="text-emerald-400 font-bold">{lastResult.policy_result}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Final Strategy:</span>
              <span className="text-blue-400 font-bold">{lastResult.final_strategy}</span>
            </div>
          </div>
        )}

        <button
          onClick={runScenario}
          disabled={loading}
          className="w-full flex items-center justify-center space-x-2 py-3 px-4 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold text-xs uppercase tracking-wider shadow-lg shadow-blue-500/20 transition-all disabled:opacity-50"
        >
          {loading ? (
            <span>Executing Engine Pipeline...</span>
          ) : (
            <>
              <span>Run Scenario Simulation</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
    </div>
  );
};
