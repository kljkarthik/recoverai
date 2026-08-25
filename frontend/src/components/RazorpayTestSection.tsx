'use client';

import React, { useState } from 'react';
import { api } from '@/lib/api';
import { RazorpayFailureResult, RazorpayVerifyResult } from '@/lib/types';
import { CreditCard, ShieldCheck, AlertTriangle, ArrowRight, CheckCircle2, RefreshCw, Zap } from 'lucide-react';
import Link from 'next/link';

export function RazorpayTestSection() {
  const [amount, setAmount] = useState<number>(1499.00);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [verifyResult, setVerifyResult] = useState<RazorpayVerifyResult | null>(null);
  const [failureResult, setFailureResult] = useState<RazorpayFailureResult | null>(null);

  const loadRazorpayScript = (): Promise<boolean> => {
    return new Promise((resolve) => {
      if (document.getElementById('razorpay-checkout-js')) {
        return resolve(true);
      }
      const script = document.createElement('script');
      script.id = 'razorpay-checkout-js';
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.body.appendChild(script);
    });
  };

  const handlePayWithRazorpay = async () => {
    setLoading(true);
    setErrorMsg(null);
    setVerifyResult(null);
    setFailureResult(null);

    try {
      const isLoaded = await loadRazorpayScript();
      if (!isLoaded) {
        throw new Error('Failed to load Razorpay Checkout SDK script.');
      }

      // 1. Create order on backend
      const order = await api.createRazorpayOrder(amount, 'INR', `rcpt_${Date.now()}`);

      // 2. Open Razorpay Checkout Modal (Test Mode)
      const options = {
        key: order.key_id, // Public Key ID only
        amount: order.amount_paise,
        currency: order.currency,
        name: 'RecoverAI Demo Merchant',
        description: 'Test Mode Transaction',
        order_id: order.order_id,
        prefill: {
          name: 'Razorpay Buildathon Tester',
          email: 'test@example.com',
          contact: '9999999999',
        },
        theme: {
          color: '#2563eb',
        },
        handler: async function (response: any) {
          try {
            setLoading(true);
            const verifyRes = await api.verifyRazorpayPayment({
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
            });
            setVerifyResult(verifyRes);
          } catch (err: any) {
            setErrorMsg(err?.response?.data?.detail || err.message || 'Payment signature verification failed.');
          } finally {
            setLoading(false);
          }
        },
        modal: {
          ondismiss: function () {
            setLoading(false);
          },
        },
      };

      const rzp = new (window as any).Razorpay(options);
      rzp.on('payment.failed', async function (response: any) {
        setLoading(true);
        try {
          const failRes = await api.reportRazorpayFailure({
            razorpay_order_id: order.order_id,
            razorpay_payment_id: response.error?.metadata?.payment_id,
            error_code: response.error?.code || 'BAD_REQUEST_ERROR',
            error_description: response.error?.description || 'Payment failed in Razorpay Checkout modal',
            error_reason: response.error?.reason || 'gateway_timeout',
            amount: amount,
            payment_method: 'razorpay',
          });
          setFailureResult(failRes);
        } catch (err: any) {
          setErrorMsg(err?.response?.data?.detail || err.message || 'Failed to process Razorpay failure telemetry.');
        } finally {
          setLoading(false);
        }
      });

      rzp.open();
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.detail || err.message || 'Error initializing Razorpay order.');
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateFailure = async (reason: string = 'gateway_timeout') => {
    setLoading(true);
    setErrorMsg(null);
    setVerifyResult(null);
    setFailureResult(null);

    try {
      const failRes = await api.reportRazorpayFailure({
        razorpay_order_id: `order_sim_${Date.now()}`,
        razorpay_payment_id: `pay_sim_${Date.now()}`,
        error_code: 'BAD_REQUEST_ERROR',
        error_description: `Simulated ${reason} during payment processing`,
        error_reason: reason,
        amount: amount,
        payment_method: 'razorpay',
      });
      setFailureResult(failRes);
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.detail || err.message || 'Simulation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel p-6 rounded-3xl border border-blue-500/30 bg-slate-900/60 shadow-2xl relative overflow-hidden space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-800 pb-4 gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-3 rounded-2xl bg-blue-600/20 border border-blue-500/30 text-blue-400">
            <CreditCard className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-bold text-white">Razorpay Test Mode Integration</h2>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                AI Buildathon Ready
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Execute live Razorpay Test Mode checkouts or simulate failures to observe RecoverAI's autonomous recovery pipeline.
            </p>
          </div>
        </div>

        {/* Input & Action controls */}
        <div className="flex items-center space-x-3">
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 font-mono">₹</span>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(Number(e.target.value))}
              className="w-28 pl-7 pr-3 py-2 text-xs font-mono font-bold bg-slate-950 border border-slate-800 rounded-xl text-white focus:outline-none focus:border-blue-500"
              placeholder="Amount"
            />
          </div>

          <button
            onClick={handlePayWithRazorpay}
            disabled={loading}
            className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-bold text-xs flex items-center space-x-2 transition shadow-lg shadow-blue-900/30"
          >
            {loading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Zap className="w-4 h-4 text-amber-300 fill-amber-300" />
            )}
            <span>Pay with Razorpay (Test)</span>
          </button>
        </div>
      </div>

      {/* Direct Failure Simulation Shortcuts */}
      <div className="bg-slate-950/60 p-4 rounded-2xl border border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
        <span className="text-xs font-semibold text-slate-400">Direct Test Failure Simulations:</span>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => handleSimulateFailure('gateway_timeout')}
            disabled={loading}
            className="px-3 py-1.5 rounded-lg bg-blue-950/40 hover:bg-blue-900/60 text-blue-300 border border-blue-800/50 text-xs font-mono transition flex items-center space-x-1"
          >
            <span>Network Timeout Failure</span>
          </button>
          <button
            onClick={() => handleSimulateFailure('insufficient_funds')}
            disabled={loading}
            className="px-3 py-1.5 rounded-lg bg-purple-950/40 hover:bg-purple-900/60 text-purple-300 border border-purple-800/50 text-xs font-mono transition flex items-center space-x-1"
          >
            <span>Insufficient Funds</span>
          </button>
          <button
            onClick={() => handleSimulateFailure('stolen_card')}
            disabled={loading}
            className="px-3 py-1.5 rounded-lg bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border border-rose-800/50 text-xs font-mono transition flex items-center space-x-1"
          >
            <span>Hard Decline / Stolen Card</span>
          </button>
        </div>
      </div>

      {/* Error Message Display */}
      {errorMsg && (
        <div className="p-4 rounded-2xl bg-rose-950/30 border border-rose-500/40 text-rose-300 text-xs flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Payment Success Verification Output */}
      {verifyResult && (
        <div className="glass-panel p-5 rounded-2xl border border-emerald-500/40 bg-emerald-950/20 space-y-3 animate-fadeIn">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <h4 className="font-bold text-white text-sm">Server-Side Signature Verified Successfully</h4>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Payment was completed in Razorpay Test Mode and verified via Razorpay SDK server-side HMAC check.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs font-mono">
            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-500 block text-[10px] uppercase">Razorpay Order ID</span>
              <span className="font-bold text-slate-200">{verifyResult.razorpay_order_id}</span>
            </div>
            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-500 block text-[10px] uppercase">Razorpay Payment ID</span>
              <span className="font-bold text-emerald-400">{verifyResult.razorpay_payment_id}</span>
            </div>
            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-500 block text-[10px] uppercase">Server Verification</span>
              <span className="font-bold text-emerald-400">PASSED (SDK Validated)</span>
            </div>
          </div>
        </div>
      )}

      {/* RecoverAI Autonomous Pipeline Output */}
      {failureResult && (
        <div className="glass-panel p-6 rounded-2xl border border-blue-500/40 bg-blue-950/20 space-y-4 animate-fadeIn">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <ShieldCheck className="w-5 h-5 text-blue-400" />
              <h4 className="font-bold text-white text-sm">RecoverAI Autonomous Recovery Pipeline Output</h4>
            </div>
            <Link
              href={`/workflows/${failureResult.workflow_id}`}
              className="text-xs px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold flex items-center space-x-1"
            >
              <span>Inspect Workflow</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
            <div className="bg-slate-900/90 p-3.5 rounded-xl border border-slate-800">
              <span className="text-slate-500 block text-[10px] uppercase mb-1">1. Failure Category</span>
              <span className="font-bold text-amber-400">{failureResult.failure_category}</span>
            </div>
            <div className="bg-slate-900/90 p-3.5 rounded-xl border border-slate-800">
              <span className="text-slate-500 block text-[10px] uppercase mb-1">2. AI Rec Strategy</span>
              <span className="font-bold text-indigo-400">{failureResult.recommended_strategy}</span>
              <span className="block text-[10px] text-slate-500 mt-1">
                Conf: {(failureResult.ai_confidence * 100).toFixed(0)}%
              </span>
            </div>
            <div className="bg-slate-900/90 p-3.5 rounded-xl border border-slate-800">
              <span className="text-slate-500 block text-[10px] uppercase mb-1">3. Policy Guardrail</span>
              <span className={`font-bold ${
                failureResult.policy_result === 'ALLOWED' ? 'text-emerald-400' :
                failureResult.policy_result === 'ESCALATED' ? 'text-amber-400' : 'text-rose-400'
              }`}>
                {failureResult.policy_result}
              </span>
              <span className="block text-[10px] text-slate-400 mt-1">Final: {failureResult.final_strategy}</span>
            </div>
            <div className="bg-slate-900/90 p-3.5 rounded-xl border border-slate-800">
              <span className="text-slate-500 block text-[10px] uppercase mb-1">4. Revenue Outcome</span>
              <span className={`font-bold ${failureResult.amount_recovered > 0 ? 'text-emerald-400' : 'text-slate-400'}`}>
                ₹{failureResult.amount_recovered.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
              <span className="block text-[10px] text-slate-500 mt-1">
                {failureResult.amount_recovered > 0 ? 'Attempt Succeeded' : 'Revenue at Risk'}
              </span>
            </div>
          </div>

          <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800 text-xs text-slate-300">
            <span className="font-bold text-slate-400 block mb-1">AI Reasoning Summary:</span>
            <p className="text-slate-300 leading-relaxed font-sans">{failureResult.ai_reasoning}</p>
          </div>
        </div>
      )}
    </div>
  );
}
