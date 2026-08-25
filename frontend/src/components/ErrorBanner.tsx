import React from 'react';
import { AlertOctagon, RefreshCw } from 'lucide-react';

interface ErrorBannerProps {
  message?: string;
  onRetry?: () => void;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({
  message = 'Backend API is currently unavailable or unreachable at http://localhost:8000/api/v1.',
  onRetry,
}) => {
  return (
    <div className="glass-panel p-5 rounded-2xl border border-rose-500/40 bg-rose-500/10 mb-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div className="flex items-center space-x-3">
        <div className="p-2.5 rounded-xl bg-rose-500/20 text-rose-400">
          <AlertOctagon className="w-6 h-6" />
        </div>
        <div>
          <h4 className="font-bold text-rose-300 text-sm">Connection Warning</h4>
          <p className="text-xs text-rose-200/80 mt-0.5">{message}</p>
        </div>
      </div>

      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 text-xs font-bold transition-all shrink-0"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retry Connection</span>
        </button>
      )}
    </div>
  );
};
