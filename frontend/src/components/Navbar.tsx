'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ShieldCheck, Activity, BrainCircuit, RefreshCw, PlayCircle, FileText, CreditCard } from 'lucide-react';
import { api } from '@/lib/api';

export const Navbar: React.FC = () => {
  const pathname = usePathname();
  const [healthy, setHealthy] = useState<boolean | null>(null);

  const checkStatus = async () => {
    try {
      const res = await api.checkHealth();
      setHealthy(res.status === 'healthy');
    } catch {
      setHealthy(false);
    }
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { label: 'Overview', href: '/', icon: Activity },
    { label: 'Transactions', href: '/transactions', icon: CreditCard },
    { label: 'Workflows', href: '/workflows', icon: RefreshCw },
    { label: 'Audit Trail', href: '/audit', icon: FileText },
    { label: 'Demo Studio', href: '/demo', icon: PlayCircle },
  ];

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 px-6 py-3.5 flex items-center justify-between">
      <div className="flex items-center space-x-8">
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="p-2 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-purple-500 text-white shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-transform">
            <BrainCircuit className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-1.5">
              <span className="font-bold text-xl tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-200 to-slate-400">
                Recover<span className="text-blue-400">AI</span>
              </span>
              <span className="text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                Autonomous
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">Revenue Recovery & Safety Guardrails</p>
          </div>
        </Link>

        <nav className="hidden md:flex items-center space-x-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                  active
                    ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                <Icon className={`w-4 h-4 ${active ? 'text-blue-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-900/80 border border-slate-800 text-xs font-mono">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span className="text-slate-300 hidden sm:inline">PolicyEngine:</span>
          <span className="text-emerald-400 font-bold">Active</span>
        </div>

        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-900/80 border border-slate-800 text-xs font-mono">
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              healthy === true ? 'bg-emerald-500 animate-pulse' : healthy === false ? 'bg-rose-500' : 'bg-amber-500'
            }`}
          />
          <span className="text-slate-400 uppercase tracking-wider text-[10px]">
            {healthy === true ? 'Backend Online' : healthy === false ? 'Disconnected' : 'Checking'}
          </span>
        </div>
      </div>
    </header>
  );
};
