'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Transaction } from '@/lib/types';
import { CreditCard, Play, Filter, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';

export default function TransactionsPage() {
  const router = useRouter();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [initiatingId, setInitiatingId] = useState<string | null>(null);

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const data = await api.getTransactions({ limit: 100 });
      setTransactions(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, []);

  const handleInitiateWorkflow = async (txId: string) => {
    setInitiatingId(txId);
    try {
      const wf = await api.createWorkflow(txId);
      router.push(`/workflows/${wf.id}`);
    } catch (err: any) {
      alert('Failed to initiate workflow: ' + (err?.response?.data?.detail || err.message));
      setInitiatingId(null);
    }
  };

  const filtered = transactions.filter((t) => {
    if (filterStatus === 'all') return true;
    return t.status === filterStatus;
  });

  if (loading) return <LoadingSkeleton />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-white">Failed Transactions Explorer</h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time payment failures and abandoned checkouts eligible for revenue recovery
          </p>
        </div>

        <div className="flex items-center space-x-2 bg-slate-900/80 p-1.5 rounded-xl border border-slate-800">
          <Filter className="w-3.5 h-3.5 text-slate-400 ml-2" />
          {['all', 'failed', 'abandoned', 'success'].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all ${
                filterStatus === st
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      <div className="glass-panel rounded-2xl border border-slate-800 p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
                <th className="py-3 px-4">Transaction ID</th>
                <th className="py-3 px-4">Amount (INR)</th>
                <th className="py-3 px-4">Method</th>
                <th className="py-3 px-4">Failure Reason</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Autonomous Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-slate-500 font-sans">
                    No transactions found. Click "Seed Demo Dataset" on the Overview page to generate synthetic data.
                  </td>
                </tr>
              ) : (
                filtered.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4 text-blue-400 font-semibold">{tx.id}</td>
                    <td className="py-3.5 px-4 font-bold text-slate-100">₹{Number(tx.amount).toLocaleString('en-IN')}</td>
                    <td className="py-3.5 px-4 text-slate-300 uppercase">{tx.payment_method}</td>
                    <td className="py-3.5 px-4 text-rose-400">{tx.failure_reason || 'None'}</td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`px-2.5 py-1 rounded-md text-[10px] font-bold uppercase ${
                          tx.status === 'success'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                            : tx.status === 'failed' || tx.status === 'abandoned'
                            ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                            : 'bg-slate-500/10 text-slate-400 border border-slate-500/30'
                        }`}
                      >
                        {tx.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right font-sans">
                      {tx.status === 'failed' || tx.status === 'abandoned' ? (
                        <button
                          onClick={() => handleInitiateWorkflow(tx.id)}
                          disabled={initiatingId === tx.id}
                          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-bold transition-all disabled:opacity-50"
                        >
                          <Play className="w-3.5 h-3.5" />
                          <span>{initiatingId === tx.id ? 'Initiating...' : 'Initiate Workflow'}</span>
                        </button>
                      ) : (
                        <span className="text-xs text-slate-500 font-mono">Resolved</span>
                      )}
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
