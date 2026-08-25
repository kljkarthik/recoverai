import React from 'react';
import { CheckCircle2, Circle, AlertTriangle, ArrowRight } from 'lucide-react';

interface WorkflowStepperProps {
  currentStep: number;
  status: string;
  hasDecision: boolean;
  hasAttempt: boolean;
}

export const WorkflowStepper: React.FC<WorkflowStepperProps> = ({
  currentStep,
  status,
  hasDecision,
  hasAttempt,
}) => {
  const steps = [
    { title: 'Failure Ingested', desc: 'Classified failure category', completed: true },
    { title: 'AI Recommendation', desc: 'LLM strategy evaluated', completed: hasDecision },
    { title: 'Policy Guardrail', desc: 'PolicyEngine evaluated safety', completed: hasDecision },
    { title: 'Recovery Action', desc: 'Simulated attempt executed', completed: hasAttempt || status === 'RECOVERED' },
  ];

  return (
    <div className="glass-panel p-6 rounded-2xl border border-slate-800 mb-6">
      <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-4">
        Workflow Lifecycle Progression
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {steps.map((step, idx) => {
          const isDone = step.completed;
          const isCurrent = idx === currentStep && !isDone;

          return (
            <div
              key={idx}
              className={`p-4 rounded-xl border transition-all ${
                isDone
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                  : isCurrent
                  ? 'bg-blue-500/10 border-blue-500/30 text-blue-400 animate-pulse'
                  : 'bg-slate-900/40 border-slate-800 text-slate-500'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono font-bold">STEP 0{idx + 1}</span>
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : isCurrent ? (
                  <ArrowRight className="w-4 h-4 text-blue-400" />
                ) : (
                  <Circle className="w-4 h-4 text-slate-600" />
                )}
              </div>
              <h4 className="font-bold text-sm text-slate-200">{step.title}</h4>
              <p className="text-xs text-slate-400 mt-1">{step.desc}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
