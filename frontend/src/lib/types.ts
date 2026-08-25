export interface RecoveryMetrics {
  revenue_at_risk: number;
  recovery_attempts: number;
  successful_recoveries: number;
  recovery_rate: number;
  revenue_recovered: number;
  total_failed_transactions: number;
}

export interface Transaction {
  id: string;
  customer_id: string;
  amount: number;
  currency: string;
  status: 'failed' | 'success' | 'abandoned' | 'pending';
  failure_reason: string | null;
  payment_method: string;
  attempt_number: number;
  created_at: string;
}

export interface Customer {
  id: string;
  name: string;
  email: string;
  total_transactions: number;
  successful_transactions: number;
  failed_transactions: number;
  lifetime_value: number;
  risk_score: number;
  created_at: string;
}

export interface Decision {
  id: string;
  workflow_id: string;
  failure_category: string;
  recommended_strategy: 'RETRY' | 'NOTIFY_CUSTOMER' | 'ESCALATE' | 'NO_ACTION';
  final_strategy: 'RETRY' | 'NOTIFY_CUSTOMER' | 'ESCALATE' | 'NO_ACTION';
  reason: string;
  policy_result: 'ALLOWED' | 'BLOCKED' | 'ESCALATED';
  confidence_score: number;
  explanation_details?: {
    engine_type?: string;
    provider?: string;
    model_name?: string;
    fallback_used?: boolean;
    fallback_reason?: string;
    primary_risk_factor?: string;
    recommended_delay_hours?: number;
    ai_confidence?: number;
    ai_reasoning?: string;
    rule_triggered?: string;
  };
  created_at: string;
}

export interface Action {
  id: string;
  transaction_id: string;
  workflow_id?: string;
  action_type: string;
  reason: string;
  ai_confidence?: number;
  policy_result: string;
  status: string;
  created_at: string;
}

export interface Attempt {
  id: string;
  recovery_action_id: string;
  workflow_id: string;
  attempt_number: number;
  status: string;
  success: boolean;
  amount_recovered: number;
  response_metadata?: Record<string, any>;
  executed_at: string;
}

export interface RecoveryWorkflow {
  id: string;
  transaction_id: string;
  status: 'INITIATED' | 'IN_PROGRESS' | 'RECOVERED' | 'FAILED' | 'ESCALATED' | 'ABORTED';
  failure_category: string;
  current_step: number;
  max_retries: number;
  next_retry_at?: string;
  created_at: string;
  updated_at: string;
  decisions: Decision[];
  actions: Action[];
  attempts: Attempt[];
}

export interface AuditLog {
  id: string;
  workflow_id?: string;
  transaction_id?: string;
  event_type: string;
  actor: string;
  decision: string;
  action?: string;
  reason: string;
  status_result?: string;
  metadata_json?: Record<string, any>;
  timestamp: string;
}
