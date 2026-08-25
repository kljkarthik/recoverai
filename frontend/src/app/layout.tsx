import React from 'react';
import '@/styles/globals.css';
import { Navbar } from '@/components/Navbar';

export const metadata = {
  title: 'RecoverAI — Autonomous Revenue Recovery Agent',
  description: 'AI-driven payment failure diagnosis, bounded strategy selection, and deterministic safety guardrails.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-[#090d16] text-slate-100 min-h-screen flex flex-col antialiased selection:bg-blue-500 selection:text-white">
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">{children}</main>
        <footer className="glass-panel border-t border-slate-800/80 py-6 px-8 text-center text-xs text-slate-500">
          <p>RecoverAI — Razorpay AI Buildathon Submission (Track 03: AI Revenue Recovery)</p>
          <p className="mt-1 text-[11px]">Autonomous Agent with Deterministic Safety Guardrail Authority</p>
        </footer>
      </body>
    </html>
  );
}
