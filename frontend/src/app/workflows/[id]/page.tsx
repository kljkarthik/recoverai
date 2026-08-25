'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { RecoveryWorkflow, Transaction } from '@/lib/types';
import { WorkflowStepper } from '@/components/WorkflowStepper';
import { AIDecisionCard } from '@/components/AIDecisionCard';
import { PolicyCheckCard } from '@/components/PolicyCheckCard';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import { ErrorBanner } from '@/components/ErrorBanner';
import { BrainCircuit, ShieldCheck, Play, CheckCircle2, XCircle, ArrowLeft, RefreshCw } from 'lucide-react';
import Link from 'next/link';

export default function WorkflowDetailPage() {
  const params = useParams();
  const workflowId = params.id as string;

  const [workflow, setWorkflow] = useState<RecoveryWorkflow | null>(null);
  const [transaction, setTransaction] = useState<Transaction | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [deciding, setDeciding] = useState(false);
  const [attempting, setAttempting] = useState(false);

  const fetchWorkflowDetails = useCallback(async () => {
    if (!workflowId) return;
    setLoading(true);
    setError(null);
    try {
      const wf = await api.getWorkflow(workflowId);
      setWorkflow(wf);
      if (wf.transaction_id) {
        const tx = await api.getTransaction(wf.transaction_id);
        setTransaction(tx);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load workflow details.');
    } finally {
      setLoading(false);
    }
  }, [workflowId]);

  useEffect(() => {
    fetchWorkflowDetails();
  }, [fetchWorkflowDetails]);

  const handleTriggerDecision = async () => {
    if (!workflowId) return;
    setDeciding(true);
    try {
      await api.triggerDecision(workflowId);
      await fetchWorkflowDetails();
    } catch (err: any) {
      alert('Failed to trigger decision: ' + (err?.response?.data?.detail || err.message));
    } finally {
      setDeciding(false);
    }
  };

  const handleRecordAttempt = async (success: boolean) => {
    if (!workflowId || !transaction) return;
    setAttempting(true);
    try {
      await api.recordAttempt(workflowId, {
        success,
        amount_recovered: success ? Number(transaction.amount) : 0,
        response_metadata: { gateway: 'simulated_razorpay', timestamp: new Date().toISOString() },
      });
      await fetchWorkflowDetails();
    } catch (err: any) {
      alert('Failed to record attempt: ' + (err?.response?.data?.detail || err.message));
    } finally {
      setAttempting(false);
    }
  };

  if (loading) return <LoadingSkeleton />;
  if (error || !workflow) return <ErrorBanner message={error || 'Workflow not found.'} onRetry={fetchWorkflowDetails} />;

  const latestDecision = workflow.decisions && workflow.decisions.length > 0 ? workflow.decisions[workflow.decisions.length - 1] : null;
  const latestAction = workflow.actions && workflow.actions.length > 0 ? workflow.actions[workflow.actions.length - 1] : null;
  const hasDecision = Boolean(latestDecision);
  const hasAttempt = workflow.attempts && workflow.attempts.length > 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link href="/workflows" className="flex items-center space-x-1.5 text-xs text-slate-400 hover:text-slate-200">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Workflows</span>
        </Link>

        <span
          className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
            workflow.status === 'RECOVERED'
              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
              : workflow.status === 'IN_PROGRESS' || workflow.status === 'INITIATED'
              ? 'bg-blue-500/10 text-blue-400 border border-blue-500/30'
              : 'bg-slate-500/10 text-slate-400 border border-slate-500/30'
          }`}
        >
          Status: {workflow.status}
        </span>
      </div>

      {/* Header Info Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-mono text-blue-400 uppercase tracking-wider font-semibold">Workflow Inspector</span>
          <h1 className="text-xl font-bold text-slate-100 font-mono mt-0.5">{workflow.id}</h1>
          <p className="text-xs text-slate-400 mt-1">
            Category: <strong className="text-slate-200">{workflow.failure_category}</strong> | Created:{' '}
            {new Date(workflow.created_at).toLocaleString()}
          </p>
        </div>

        {transaction && (
          <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 text-xs space-y-1 font-mono text-right">
            <span className="text-slate-400 block text-[10px] uppercase">Associated Transaction</span>
            <div className="text-lg font-bold text-emerald-400">₹{Number(transaction.amount).toLocaleString('en-IN')}</div>
            <span className="text-slate-400">{transaction.payment_method.toUpperCase()} | Reason: {transaction.failure_reason}</span>
          </div>
        )}
      </div>

      {/* Stepper Visualizer */}
      <WorkflowStepper
        currentStep={workflow.current_step}
        status={workflow.status}
        hasDecision={hasDecision}
        hasAttempt={hasAttempt}
      />

      {/* Action Controls & Triggers */}
      {!hasDecision && (
        <div className="glass-panel p-6 rounded-2xl border border-indigo-500/30 text-center">
          <BrainCircuit className="w-8 h-8 text-indigo-400 mx-auto mb-2" />
          <h3 className="font-bold text-slate-200 text-base">Step 2: Trigger AI & Safety Engine Evaluation</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto mt-1 mb-4">
            Evaluate payment telemetry through LLMDecisionEngine and verify safety guardrails with PolicyEngine.
          </p>

          <button
            onClick={handleTriggerDecision}
            disabled={deciding}
            className="inline-flex items-center space-x-2 py-3 px-6 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold text-xs uppercase tracking-wider shadow-lg shadow-blue-500/20 transition-all disabled:opacity-50"
          >
            <Play className="w-4 h-4" />
            <span>{deciding ? 'Evaluating Decision & Policy...' : 'Evaluate Decision & Policy'}</span>
          </button>
        </div>
      )}

      {/* AI vs Policy Inspector Cards */}
      {latestDecision && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <AIDecisionCard decision={latestDecision} />
          <PolicyCheckCard decision={latestDecision} />
        </div>
      )}

      {/* Step 4: Simulate Attempt Trigger (If Decision Made & In Progress) */}
      {hasDecision && latestDecision?.final_strategy === 'RETRY' && (workflow.status === 'INITIATED' || workflow.status === 'IN_PROGRESS') && (
        <div className="glass-panel p-6 rounded-2xl border border-emerald-500/30">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Step 4: Execute Recovery Attempt</span>
              <h3 className="font-bold text-slate-200 text-base mt-0.5">Simulate Recovery Action Execution</h3>
              <p className="text-xs text-slate-400 mt-1">
                Execute a simulated gateway retry or outreach dispatch to capture payment.
              </p>
            </div>

            <div className="flex items-center space-x-3">
              <button
                onClick={() => handleRecordAttempt(true)}
                disabled={attempting}
                className="flex items-center space-x-2 py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-lg shadow-emerald-500/20 transition-all disabled:opacity-50"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Simulate Attempt Success</span>
              </button>

              <button
                onClick={() => handleRecordAttempt(false)}
                disabled={attempting}
                className="flex items-center space-x-2 py-2.5 px-4 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold transition-all disabled:opacity-50"
              >
                <XCircle className="w-4 h-4" />
                <span>Simulate Attempt Failure</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Workflow Attempts History */}
      {hasAttempt && (
        <div className="glass-panel p-6 rounded-2xl border border-slate-800">
          <h3 className="font-bold text-slate-200 text-sm tracking-wide mb-4">Simulated Attempt Execution Logs</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
                  <th className="py-2.5 px-3">Attempt #</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Outcome</th>
                  <th className="py-2.5 px-3">Amount Recovered</th>
                  <th className="py-2.5 px-3">Executed At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {workflow.attempts.map((att) => (
                  <tr key={att.id}>
                    <td className="py-3 px-3 text-blue-400 font-bold">Attempt #{att.attempt_number}</td>
                    <td className="py-3 px-3">{att.status}</td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${att.success ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`}>
                        {att.success ? 'SUCCESS' : 'FAILED'}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-200">₹{Number(att.amount_recovered).toLocaleString('en-IN')}</td>
                    <td className="py-3 px-3 text-slate-400">{new Date(att.executed_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
