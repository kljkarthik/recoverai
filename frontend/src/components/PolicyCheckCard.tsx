import React from 'react';
import { ShieldCheck, ShieldX, AlertOctagon, Lock } from 'lucide-react';
import { Decision } from '@/lib/types';

interface PolicyCheckCardProps {
  decision: Decision;
}

export const PolicyCheckCard: React.FC<PolicyCheckCardProps> = ({ decision }) => {
  const getPolicyBadge = (status: string) => {
    switch (status) {
      case 'ALLOWED':
        return {
          bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
          icon: ShieldCheck,
          text: 'Policy Approved (ALLOWED)',
        };
      case 'BLOCKED':
        return {
          bg: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
          icon: ShieldX,
          text: 'Policy Override (BLOCKED)',
        };
      case 'ESCALATED':
        return {
          bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
          icon: AlertOctagon,
          text: 'Forced Escalation (ESCALATED)',
        };
      default:
        return {
          bg: 'bg-slate-500/10 text-slate-400 border-slate-500/30',
          icon: Lock,
          text: status,
        };
    }
  };

  const policyTheme = getPolicyBadge(decision.policy_result);
  const StatusIcon = policyTheme.icon;

  return (
    <div className="glass-panel p-6 rounded-2xl border border-emerald-500/30 relative overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-200 text-sm tracking-wide">Deterministic PolicyEngine</h3>
            <p className="text-xs text-slate-400">Final Non-Bypassable Safety Authority Guardrail</p>
          </div>
        </div>

        <span className={`flex items-center space-x-1.5 text-xs font-semibold px-3 py-1 rounded-full border ${policyTheme.bg}`}>
          <StatusIcon className="w-4 h-4" />
          <span>{policyTheme.text}</span>
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Policy Decision Status
          </span>
          <span className="text-lg font-bold text-slate-100">{decision.policy_result}</span>
        </div>

        <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Final Permitted Strategy
          </span>
          <span className="text-lg font-bold text-emerald-400 font-mono">{decision.final_strategy}</span>
        </div>
      </div>

      <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 text-xs">
        <span className="font-semibold text-slate-400 block mb-1 uppercase tracking-wider text-[11px]">
          Guardrail Rule Evaluation Detail
        </span>
        <p className="text-slate-300 leading-relaxed font-mono">{decision.reason}</p>
      </div>
    </div>
  );
};
