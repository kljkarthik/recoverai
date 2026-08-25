'use client';

import React, { useState } from 'react';
import { AuditLog } from '@/lib/types';
import { ShieldCheck, FileJson, Search, Clock, UserCheck } from 'lucide-react';

interface AuditLogTableProps {
  logs: AuditLog[];
}

export const AuditLogTable: React.FC<AuditLogTableProps> = ({ logs }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedJson, setSelectedJson] = useState<Record<string, any> | null>(null);

  const filteredLogs = logs.filter(
    (log) =>
      log.event_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.actor.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.decision.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.reason.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getEventBadge = (eventType: string) => {
    switch (eventType) {
      case 'WORKFLOW_CREATED':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
      case 'DECISION_MADE':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/30';
      case 'POLICY_CHECKED':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'RECOVERY_ATTEMPTED':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'RECOVERY_COMPLETED':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
      case 'RECOVERY_FAILED':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
    }
  };

  return (
    <div className="glass-panel rounded-2xl border border-slate-800 p-6">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="font-bold text-slate-200 text-lg">Immutable Audit Trail Explorer</h3>
            <span className="text-[10px] font-mono uppercase bg-slate-800 text-slate-400 px-2 py-0.5 rounded border border-slate-700">
              Read-Only
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            100% decision traceability & compliance audit log of all system evaluations
          </p>
        </div>

        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search event, actor, decision..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl pl-9 pr-4 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
              <th className="py-3 px-4">Timestamp</th>
              <th className="py-3 px-4">Event Type</th>
              <th className="py-3 px-4">Actor</th>
              <th className="py-3 px-4">Decision / Action</th>
              <th className="py-3 px-4">Reason</th>
              <th className="py-3 px-4 text-right">Metadata</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {filteredLogs.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-8 text-slate-500 font-sans">
                  No audit log records found matching your filter criteria.
                </td>
              </tr>
            ) : (
              filteredLogs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4 text-slate-400 whitespace-nowrap">
                    <div className="flex items-center space-x-1.5">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      <span>{new Date(log.timestamp).toLocaleString()}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap">
                    <span className={`inline-block px-2.5 py-0.5 rounded-md border text-[11px] font-bold ${getEventBadge(log.event_type)}`}>
                      {log.event_type}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-300 whitespace-nowrap">
                    <div className="flex items-center space-x-1.5">
                      <UserCheck className="w-3.5 h-3.5 text-blue-400" />
                      <span>{log.actor}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-slate-200 font-bold whitespace-nowrap">{log.decision}</td>
                  <td className="py-3 px-4 text-slate-300 font-sans max-w-md truncate">{log.reason}</td>
                  <td className="py-3 px-4 text-right whitespace-nowrap">
                    {log.metadata_json ? (
                      <button
                        onClick={() => setSelectedJson(log.metadata_json || null)}
                        className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-blue-400 text-xs font-sans transition-colors border border-slate-700"
                      >
                        <FileJson className="w-3.5 h-3.5" />
                        <span>Inspect Payload</span>
                      </button>
                    ) : (
                      <span className="text-slate-600 font-sans">—</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* JSON Viewer Modal */}
      {selectedJson && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="glass-panel p-6 rounded-2xl border border-slate-700 max-w-xl w-full shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
              <h4 className="font-bold text-slate-200 text-sm flex items-center space-x-2">
                <FileJson className="w-4 h-4 text-blue-400" />
                <span>Audit Telemetry Metadata Payload</span>
              </h4>
              <button
                onClick={() => setSelectedJson(null)}
                className="text-slate-400 hover:text-white text-sm px-2 py-1 rounded bg-slate-800"
              >
                ✕ Close
              </button>
            </div>
            <pre className="bg-slate-950 p-4 rounded-xl text-emerald-400 font-mono text-xs overflow-x-auto max-h-96 border border-slate-800">
              {JSON.stringify(selectedJson, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};
