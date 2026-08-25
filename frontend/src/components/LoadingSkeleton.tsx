import React from 'react';

export const LoadingSkeleton: React.FC = () => {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-8 bg-slate-800/60 rounded-xl w-1/3"></div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-28 bg-slate-800/40 rounded-2xl border border-slate-800"></div>
        ))}
      </div>
      <div className="h-64 bg-slate-800/40 rounded-2xl border border-slate-800"></div>
    </div>
  );
};
