'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { RecoveryWorkflow } from '@/lib/types';
import { RefreshCw, ArrowRight, ShieldCheck, Activity } from 'lucide-react';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<RecoveryWorkflow[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchWorkflows = async () => {
    setLoading(true);
    try {
      const data = await api.getWorkflows({ limit: 100 });
      setWorkflows(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkflows();
  }, []);

  if (loading) return <LoadingSkeleton />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-white">Recovery Workflows</h1>
        <p className="text-xs text-slate-400 mt-1">
          Active and historical autonomous recovery intervention pipelines
        </p>
      </div>

      <div className="glass-panel rounded-2xl border border-slate-800 p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
                <th className="py-3 px-4">Workflow ID</th>
                <th className="py-3 px-4">Transaction ID</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Current Step</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Inspect Detail</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {workflows.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-slate-500 font-sans">
                    No active workflows found.
                  </td>
                </tr>
              ) : (
                workflows.map((wf) => (
                  <tr key={wf.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4 text-blue-400 font-semibold">{wf.id}</td>
                    <td className="py-3.5 px-4 text-slate-300">{wf.transaction_id.substring(0, 12)}...</td>
                    <td className="py-3.5 px-4 text-slate-200">{wf.failure_category}</td>
                    <td className="py-3.5 px-4 text-slate-400">Step {wf.current_step}/{wf.max_retries}</td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`px-2.5 py-1 rounded-md text-[10px] font-bold uppercase ${
                          wf.status === 'RECOVERED'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                            : wf.status === 'IN_PROGRESS' || wf.status === 'INITIATED'
                            ? 'bg-blue-500/10 text-blue-400 border border-blue-500/30'
                            : 'bg-slate-500/10 text-slate-400 border border-slate-500/30'
                        }`}
                      >
                        {wf.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right font-sans">
                      <Link
                        href={`/workflows/${wf.id}`}
                        className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 text-xs font-semibold"
                      >
                        <span>Inspect Flow</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
