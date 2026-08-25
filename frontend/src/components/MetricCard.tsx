import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: 'blue' | 'emerald' | 'purple' | 'amber' | 'rose';
  trend?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  color = 'blue',
  trend,
}) => {
  const colorMap = {
    blue: {
      border: 'border-blue-500/30',
      bg: 'bg-blue-500/10',
      text: 'text-blue-400',
      glow: 'glow-blue',
    },
    emerald: {
      border: 'border-emerald-500/30',
      bg: 'bg-emerald-500/10',
      text: 'text-emerald-400',
      glow: 'glow-emerald',
    },
    purple: {
      border: 'border-purple-500/30',
      bg: 'bg-purple-500/10',
      text: 'text-purple-400',
      glow: 'glow-purple',
    },
    amber: {
      border: 'border-amber-500/30',
      bg: 'bg-amber-500/10',
      text: 'text-amber-400',
      glow: 'glow-amber',
    },
    rose: {
      border: 'border-rose-500/30',
      bg: 'bg-rose-500/10',
      text: 'text-rose-400',
      glow: '',
    },
  };

  const currentTheme = colorMap[color];

  return (
    <div className={`glass-panel p-5 rounded-2xl border ${currentTheme.border} transition-all duration-200 hover:border-slate-700`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</span>
        <div className={`p-2.5 rounded-xl ${currentTheme.bg} ${currentTheme.text}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>

      <div className="mt-4 flex items-baseline justify-between">
        <span className="text-2xl lg:text-3xl font-bold tracking-tight text-white">{value}</span>
        {trend && (
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            {trend}
          </span>
        )}
      </div>

      {subtitle && <p className="mt-1 text-xs text-slate-400 font-medium">{subtitle}</p>}
    </div>
  );
};
