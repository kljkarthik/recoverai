'use client';

import React, { useState } from 'react';
import { DemoScenarioCard } from '@/components/DemoScenarioCard';
import { PlayCircle, Sparkles, ShieldCheck, CheckCircle2, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export default function DemoPage() {
  const [activeResult, setActiveResult] = useState<any | null>(null);

  const scenarios = [
    {
      id: 'network_timeout',
      scenarioType: 'network_timeout',
      title: 'Scenario A: Temporary Network Degradation',
      subtitle: 'Soft Decline / Smart Retry',
      description: 'Simulates a transient gateway timeout during UPI processing. AI recommends RETRY, PolicyEngine approves action.',
      expectedResult: 'AI Rec: RETRY | Policy: ALLOWED | Final: RETRY | Revenue Recovered: ₹3,999.00',
      badgeColor: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
    },
    {
      id: 'insufficient_funds',
      scenarioType: 'insufficient_funds',
      title: 'Scenario B: Insufficient Funds Outreach',
      subtitle: 'Account Depletion / Customer Outreach',
      description: 'Simulates insufficient funds card decline. AI recommends NOTIFY_CUSTOMER to prompt account re-funding, PolicyEngine approves.',
      expectedResult: 'AI Rec: NOTIFY_CUSTOMER | Policy: ALLOWED | Final: NOTIFY_CUSTOMER',
      badgeColor: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
    },
    {
      id: 'hard_decline',
      scenarioType: 'hard_decline',
      title: 'Scenario C: Stolen Card Hard Decline',
      subtitle: 'Safety Guardrail Override',
      description: 'Simulates a hard decline for a stolen card. AI attempts or evaluates retry, but PolicyEngine OVERRIDES & BLOCKS retry to prevent fee penalties.',
      expectedResult: 'Policy Result: BLOCKED | Final Strategy: NO_ACTION (100% Policy Overridden)',
      badgeColor: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    },
    {
      id: 'high_value',
      scenarioType: 'high_value',
      title: 'Scenario D: High-Value Escalation Guardrail',
      subtitle: '₹65,000 Monetary Threshold Escalation',
      description: 'Simulates a high-value transaction exceeding ₹50,000 threshold. PolicyEngine forces manual escalation regardless of AI recommendation.',
      expectedResult: 'Policy Result: ESCALATED | Final Strategy: ESCALATE (Forced Human Review)',
      badgeColor: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    },
  ];

  return (
    <div className="space-y-8">
      <div className="glass-panel p-8 rounded-3xl border border-blue-500/30 bg-gradient-to-r from-blue-950/40 via-slate-900/80 to-purple-950/40 relative overflow-hidden">
        <div className="relative z-10 max-w-3xl">
          <div className="flex items-center space-x-2 mb-3">
            <span className="p-2 rounded-xl bg-blue-500/20 text-blue-400 border border-blue-500/30">
              <PlayCircle className="w-5 h-5" />
            </span>
            <span className="text-xs font-bold uppercase tracking-wider text-blue-400">Interactive Demonstration Studio</span>
          </div>

          <h1 className="text-3xl font-extrabold tracking-tight text-white mb-2">
            1-Click Autonomous Scenario Runner
          </h1>
          <p className="text-sm text-slate-300 leading-relaxed mb-6">
            Demonstrate RecoverAI's end-to-end 7-step pipeline in real-time. Each scenario creates synthetic transaction telemetry, invokes the LLM decision engine, passes through PolicyEngine safety guardrails, and updates recovery audit logs.
          </p>
        </div>
      </div>

      {/* Scenarios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {scenarios.map((sc) => (
          <DemoScenarioCard
            key={sc.id}
            {...sc}
            onScenarioExecuted={(res) => setActiveResult(res)}
          />
        ))}
      </div>

      {/* Live Pipeline Result Modal / Inspection Panel */}
      {activeResult && (
        <div className="glass-panel p-6 rounded-2xl border border-emerald-500/40 bg-emerald-950/20">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <h3 className="font-bold text-slate-200 text-sm">Last Scenario Execution Pipeline Output</h3>
            </div>
            <Link
              href={`/workflows/${activeResult.workflow_id}`}
              className="text-xs px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold flex items-center space-x-1"
            >
              <span>Inspect Full Workflow Detail</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-500 block text-[10px] uppercase">Scenario</span>
              <span className="font-bold text-slate-200">{activeResult.scenario_type}</span>
            </div>
            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-500 block text-[10px] uppercase">AI Rec Strategy</span>
              <span className="font-bold text-indigo-400">{activeResult.recommended_strategy}</span>
            </div>
            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-500 block text-[10px] uppercase">Policy Check</span>
              <span className="font-bold text-emerald-400">{activeResult.policy_result}</span>
            </div>
            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-500 block text-[10px] uppercase">Final Strategy</span>
              <span className="font-bold text-blue-400">{activeResult.final_strategy}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
