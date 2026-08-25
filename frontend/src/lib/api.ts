import axios from 'axios';
import {
  RecoveryMetrics, Transaction, Customer, RecoveryWorkflow, Decision, Attempt, AuditLog,
  RazorpayOrder, RazorpayVerifyResult, RazorpayFailureResult
} from './types';

const getApiBaseUrl = (): string => {
  const rawUrl = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
  const cleanUrl = rawUrl.trim().replace(/\/+$/, '');
  if (cleanUrl.endsWith('/api/v1')) {
    return cleanUrl;
  }
  return `${cleanUrl}/api/v1`;
};

const API_BASE_URL = getApiBaseUrl();

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});


export const api = {
  // Health
  checkHealth: async () => {
    const res = await apiClient.get('/health');
    return res.data;
  },

  // Metrics
  getMetrics: async (): Promise<RecoveryMetrics> => {
    const res = await apiClient.get('/metrics/recovery');
    return res.data;
  },

  // Transactions
  getTransactions: async (params?: { skip?: number; limit?: number; status?: string }): Promise<Transaction[]> => {
    const res = await apiClient.get('/transactions', { params });
    return res.data;
  },

  getTransaction: async (id: string): Promise<Transaction> => {
    const res = await apiClient.get(`/transactions/${id}`);
    return res.data;
  },

  createTransaction: async (data: Partial<Transaction>): Promise<Transaction> => {
    const res = await apiClient.post('/transactions', data);
    return res.data;
  },

  // Customers
  getCustomers: async (): Promise<Customer[]> => {
    const res = await apiClient.get('/customers');
    return res.data;
  },

  // Workflows
  getWorkflows: async (params?: { status?: string; failure_category?: string; skip?: number; limit?: number }): Promise<RecoveryWorkflow[]> => {
    const res = await apiClient.get('/workflows', { params });
    return res.data;
  },

  getWorkflow: async (id: string): Promise<RecoveryWorkflow> => {
    const res = await apiClient.get(`/workflows/${id}`);
    return res.data;
  },

  createWorkflow: async (transaction_id: string, max_retries?: number): Promise<RecoveryWorkflow> => {
    const res = await apiClient.post('/workflows', { transaction_id, max_retries });
    return res.data;
  },

  triggerDecision: async (workflow_id: string): Promise<Decision> => {
    const res = await apiClient.post(`/workflows/${workflow_id}/decide`);
    return res.data;
  },

  recordAttempt: async (workflow_id: string, payload: { success: boolean; amount_recovered?: number; response_metadata?: any }): Promise<Attempt> => {
    const res = await apiClient.post(`/workflows/${workflow_id}/attempt`, payload);
    return res.data;
  },

  // Audit Logs (Read-only)
  getAuditLogs: async (params?: { workflow_id?: string; event_type?: string; actor?: string }): Promise<AuditLog[]> => {
    const res = await apiClient.get('/audit-logs', { params });
    return res.data;
  },

  // Demo Studio
  seedDemoData: async () => {
    const res = await apiClient.post('/demo/seed');
    return res.data;
  },

  simulateScenario: async (scenario_type: string) => {
    const res = await apiClient.post('/demo/simulate-scenario', { scenario_type });
    return res.data;
  },

  // Razorpay Test Mode Integration
  createRazorpayOrder: async (amount: number, currency: string = "INR", receipt?: string): Promise<RazorpayOrder> => {
    const res = await apiClient.post('/razorpay/orders', { amount, currency, receipt });
    return res.data;
  },

  verifyRazorpayPayment: async (payload: { razorpay_order_id: string; razorpay_payment_id: string; razorpay_signature: string }): Promise<RazorpayVerifyResult> => {
    const res = await apiClient.post('/razorpay/verify', payload);
    return res.data;
  },

  reportRazorpayFailure: async (payload: {
    razorpay_order_id?: string;
    razorpay_payment_id?: string;
    error_code?: string;
    error_description?: string;
    error_reason?: string;
    amount?: number;
    payment_method?: string;
  }): Promise<RazorpayFailureResult> => {
    const res = await apiClient.post('/razorpay/report-failure', payload);
    return res.data;
  }
};

