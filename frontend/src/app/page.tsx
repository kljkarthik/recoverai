'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { MetricCard } from '@/components/MetricCard';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import { ErrorBanner } from '@/components/ErrorBanner';
import { api } from '@/lib/api';
import { RecoveryMetrics, RecoveryWorkflow } from '@/lib/types';
import { TrendingUp, AlertTriangle, RefreshCw, CheckCircle2, PlayCircle, Sparkles, ArrowRight } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export default function OverviewPage() {
  const [metrics, setMetrics] = useState<RecoveryMetrics | null>(null);
  const [workflows, setWorkflows] = useState<RecoveryWorkflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [seeding, setSeeding] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [mRes, wRes] = await Promise.all([api.getMetrics(), api.getWorkflows({ limit: 10 })]);
      setMetrics(mRes);
      setWorkflows(wRes);
    } catch (err: any) {
      setError(err?.message || 'Failed to connect to backend API.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSeedData = async () => {
    setSeeding(true);
    try {
      await api.seedDemoData();
      await fetchData();
    } catch (err: any) {
      alert('Failed to seed demo data: ' + err?.message);
    } finally {
      setSeeding(false);
    }
  };

  if (loading) return <LoadingSkeleton />;

  const chartData = [
    { name: 'Revenue at Risk', value: metrics ? Number(metrics.revenue_at_risk) : 0, color: '#f43f5e' },
    { name: 'Revenue Recovered', value: metrics ? Number(metrics.revenue_recovered) : 0, color: '#10b981' },
  ];

  return (
    <div className="space-y-8">
      {error && <ErrorBanner message={error} onRetry={fetchData} />}

      {/* Header section */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-extrabold tracking-tight text-white">Executive Control Dashboard</h1>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
              Live Monitoring
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time autonomous revenue recovery metrics & deterministic safety oversight
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleSeedData}
            disabled={seeding}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-bold transition-all disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4 text-purple-400" />
            <span>{seeding ? 'Seeding Telemetry...' : 'Seed Demo Dataset'}</span>
          </button>

          <Link
            href="/demo"
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-bold shadow-lg shadow-blue-500/20 transition-all"
          >
            <PlayCircle className="w-4 h-4" />
            <span>Open Demo Studio</span>
          </Link>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          title="Revenue at Risk"
          value={`₹${metrics ? Number(metrics.revenue_at_risk).toLocaleString('en-IN') : '0'}`}
          subtitle={`${metrics ? metrics.total_failed_transactions : 0} failed / abandoned checkouts`}
          icon={AlertTriangle}
          color="rose"
        />

        <MetricCard
          title="Revenue Recovered"
          value={`₹${metrics ? Number(metrics.revenue_recovered).toLocaleString('en-IN') : '0'}`}
          subtitle={`${metrics ? metrics.successful_recoveries : 0} successful interventions`}
          icon={TrendingUp}
          color="emerald"
          trend="+100% Net ARR"
        />

        <MetricCard
          title="Recovery Rate"
          value={`${metrics ? metrics.recovery_rate : 0}%`}
          subtitle="Intervention conversion rate"
          icon={CheckCircle2}
          color="blue"
        />

        <MetricCard
          title="Active Interventions"
          value={workflows.filter((w) => w.status === 'IN_PROGRESS' || w.status === 'INITIATED').length}
          subtitle={`${workflows.length} total workflows recorded`}
          icon={RefreshCw}
          color="purple"
        />
      </div>

      {/* Visual Analytics & Recent Workflows Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Revenue Performance Chart */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 lg:col-span-1 flex flex-col justify-between">
          <div>
            <h3 className="font-bold text-slate-200 text-sm tracking-wide mb-1">Recovery Performance Ratio</h3>
            <p className="text-xs text-slate-400 mb-6">Revenue At Risk vs Net Revenue Recovered</p>

            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 20, right: 20, left: -20, bottom: 0 }}>
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }}
                    formatter={(val: any) => [`₹${Number(val).toLocaleString('en-IN')}`, 'Amount']}
                  />
                  <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 text-xs space-y-2 mt-4">
            <div className="flex justify-between text-slate-400">
              <span>Total Recovery Attempts:</span>
              <strong className="text-slate-200 font-mono">{metrics?.recovery_attempts || 0}</strong>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Safety Guardrail Enforcements:</span>
              <strong className="text-emerald-400 font-mono">100% Policy Engine Checked</strong>
            </div>
          </div>
        </div>

        {/* Recent Workflows Table */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 lg:col-span-2 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-bold text-slate-200 text-sm tracking-wide">Active Recovery Workflows</h3>
                <p className="text-xs text-slate-400">Live agent workflows and safety policy states</p>
              </div>

              <Link href="/workflows" className="text-xs text-blue-400 hover:text-blue-300 font-semibold flex items-center space-x-1">
                <span>View All Workflows</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
                    <th className="py-3 px-3">Workflow ID</th>
                    <th className="py-3 px-3">Category</th>
                    <th className="py-3 px-3">Status</th>
                    <th className="py-3 px-3">Step</th>
                    <th className="py-3 px-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {workflows.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-slate-500 font-sans">
                        No active workflows. Click "Seed Demo Dataset" or "Open Demo Studio" to launch workflows.
                      </td>
                    </tr>
                  ) : (
                    workflows.slice(0, 5).map((wf) => (
                      <tr key={wf.id} className="hover:bg-slate-800/40">
                        <td className="py-3 px-3 text-blue-400 font-semibold">{wf.id.substring(0, 8)}...</td>
                        <td className="py-3 px-3 text-slate-300">{wf.failure_category}</td>
                        <td className="py-3 px-3">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
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
                        <td className="py-3 px-3 text-slate-400">Step {wf.current_step}/{wf.max_retries}</td>
                        <td className="py-3 px-3 text-right font-sans">
                          <Link
                            href={`/workflows/${wf.id}`}
                            className="text-xs px-2.5 py-1 rounded bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 font-semibold"
                          >
                            Inspect
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
      </div>
    </div>
  );
}
