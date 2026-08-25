import React from 'react';
import { BrainCircuit, AlertTriangle, CheckCircle2, ShieldAlert } from 'lucide-react';
import { Decision } from '@/lib/types';

interface AIDecisionCardProps {
  decision: Decision;
}

export const AIDecisionCard: React.FC<AIDecisionCardProps> = ({ decision }) => {
  const details = decision.explanation_details || {};
  const isFallback = details.fallback_used || details.engine_type === 'llm_fallback';
  const confidencePct = Math.round(decision.confidence_score * 100);

  const getStrategyBadge = (strategy: string) => {
    switch (strategy) {
      case 'RETRY':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
      case 'NOTIFY_CUSTOMER':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/30';
      case 'ESCALATE':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'NO_ACTION':
        return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
    }
  };

  return (
    <div className="glass-panel p-6 rounded-2xl border border-indigo-500/30 relative overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <BrainCircuit className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-200 text-sm tracking-wide">AI Recommendation Layer</h3>
            <p className="text-xs text-slate-400">LLM Advisory Recommendation & Risk Analysis</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {isFallback ? (
            <span className="flex items-center space-x-1 text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Safe Fallback Triggered</span>
            </span>
          ) : (
            <span className="flex items-center space-x-1 text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Direct AI Output</span>
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Recommended Strategy
          </span>
          <span
            className={`inline-block text-sm font-bold px-3 py-1 rounded-lg border ${getStrategyBadge(
              decision.recommended_strategy
            )}`}
          >
            {decision.recommended_strategy}
          </span>
        </div>

        <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">AI Confidence Score</span>
            <span className="text-xs font-bold text-indigo-400">{confidencePct}%</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 mt-2">
            <div
              className={`h-2 rounded-full transition-all duration-500 ${
                confidencePct >= 80
                  ? 'bg-gradient-to-r from-blue-500 to-indigo-400'
                  : confidencePct >= 60
                  ? 'bg-amber-500'
                  : 'bg-rose-500'
              }`}
              style={{ width: `${confidencePct}%` }}
            />
          </div>
        </div>
      </div>

      <div className="space-y-3 text-xs">
        <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <span className="font-semibold text-slate-400 block mb-1 uppercase tracking-wider text-[11px]">
            AI Explanation Rationale
          </span>
          <p className="text-slate-300 leading-relaxed font-mono">{decision.reason}</p>
        </div>

        {details.primary_risk_factor && (
          <div className="flex items-center space-x-2 text-slate-400 bg-slate-900/40 p-3 rounded-lg border border-slate-800/60">
            <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              Primary Risk Factor: <strong className="text-slate-200">{details.primary_risk_factor}</strong>
            </span>
          </div>
        )}

        {isFallback && details.fallback_reason && (
          <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs">
            <strong>Fallback Reason:</strong> {details.fallback_reason}
          </div>
        )}
      </div>
    </div>
  );
};
