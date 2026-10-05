import type {
  AssessmentState,
  Dataset,
  DecisionOutcome,
  GateStatus,
  HistoryEntry,
  MLModel,
  User,
} from '@/types';
import {
  currentUser,
  mockDatasets,
  mockHistory,
  mockModels,
  mockAssess,
} from '@/data/mockData';

// ── Config ────────────────────────────────────────────────────────────────────

export const BASE_URL: string =
  (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000/api';

export const USE_MOCK: boolean =
  (import.meta.env.VITE_USE_MOCK as string) !== 'false';

// ── Backend response types ────────────────────────────────────────────────────

export interface BackendGateResult {
  gate_name: string;
  passed: boolean | null;
  reasoning: string;
  details: Record<string, unknown>;
}

export interface BackendDecisionResponse {
  applicant_id: string;
  decision_date: string;
  outcome: 'APPROVE' | 'REVIEW' | 'DECLINE';
  recommendation: string;
  evidence_gate: BackendGateResult;
  policy_gate: BackendGateResult;
  risk_rank: BackendGateResult;
  risk_score: number;
  credit_score: number;
  credit_score_display: {
    score: number;
    pd_percent: number;
    threshold_score: number;
    threshold_pd_percent: number;
    phase: string;
    disclaimer: string;
  } | null;
  explanation: Record<string, unknown> | null;
  model_version: string;
  mode: string;
}

// ── Adapter: BackendDecisionResponse → DecisionOutcome ────────────────────────

export function adaptBackendResponse(
  backendResp: BackendDecisionResponse,
  state: AssessmentState
): DecisionOutcome {
  const gates: GateStatus[] = [
    {
      name: 'Identity Check',
      status: 'passed',
      score: 1,
    },
    {
      name: 'Platform Income',
      status: Math.min(1, (state?.finances?.monthlyIncome ?? 0) / 50000) >= 0.16 ? 'passed' : 'failed',
      score: Math.min(1, (state?.finances?.monthlyIncome ?? 0) / 50000),
    },
    {
      name: 'Volatility Stress',
      status: (state?.finances?.incomeVolatility ?? 0) < 0.4 ? 'passed' : 'failed',
      score: Math.max(0, 1 - (state?.finances?.incomeVolatility ?? 0)),
    },
    {
      name: 'Evidence Quality',
      status: backendResp.evidence_gate.passed ? 'passed' : 'failed',
      score: backendResp.evidence_gate.details.score as number | undefined,
    },
    {
      name: 'Policy Eligibility',
      status: backendResp.policy_gate.passed === true
        ? 'passed'
        : backendResp.policy_gate.passed === null
        ? 'pending'
        : 'failed',
      score: backendResp.policy_gate.passed ? 0.9 : 0.4,
    },
    {
      name: 'Final Adjudication',
      status: backendResp.outcome === 'APPROVE'
        ? 'passed'
        : backendResp.outcome === 'REVIEW'
        ? 'pending'
        : 'failed',
      score: 1 - backendResp.risk_score,
    },
  ];

  return {
    status: backendResp.outcome.toLowerCase() as 'approve' | 'review' | 'decline',
    riskScore: 1 - backendResp.risk_score,
    policyScore: backendResp.policy_gate.passed ? 0.85 : 0.3,
    evidenceScore: (backendResp.evidence_gate.details.score as number) ?? 0,
    finalScore: 1 - backendResp.risk_score,
    riskPD: backendResp.risk_score,
    rationale: backendResp.recommendation,
    gates,
    creditScore: backendResp.credit_score ?? null,
    creditScoreDisplay: backendResp.credit_score_display ?? null,
  };
}

// ── HTTP helpers ──────────────────────────────────────────────────────────────

function mockDelay<T>(data: T, minMs = 300, maxMs = 800): Promise<T> {
  const delay = Math.floor(Math.random() * (maxMs - minMs + 1)) + minMs;
  return new Promise((resolve) => setTimeout(() => resolve(data), delay));
}

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface RequestOptions {
  headers?: Record<string, string>;
}

export async function request<T>(
  method: HttpMethod,
  path: string,
  body?: unknown,
  options?: RequestOptions
): Promise<T> {
  if (USE_MOCK) {
    return mockRoute<T>(method, path, body);
  }

  const url = `${BASE_URL}${path}`;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers ?? {}),
  };

  const token = localStorage.getItem('ml-auth-token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const init: RequestInit = { method, headers };

  if (body !== undefined && method !== 'GET') {
    init.body = JSON.stringify(body);
  }

  const res = await fetch(url, init);

  if (!res.ok) {
    let message = `Request failed: ${res.status}`;
    try {
      const err = await res.json();
      if (err && typeof err.detail === 'string') message = err.detail;
      else if (err && typeof err.message === 'string') message = err.message;
    } catch { /* ignore parse errors */ }
    throw new Error(message);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// ── Mock route handler ────────────────────────────────────────────────────────

function mockRoute<T>(method: HttpMethod, path: string, body?: unknown): Promise<T> {
  if (path === '/auth/login' && method === 'POST') {
    const p = body as { email: string; password: string };
    return mockDelay({ user: { ...currentUser, email: p?.email || currentUser.email }, token: 'mock-jwt-token' }) as Promise<T>;
  }
  if (path === '/auth/signup' && method === 'POST') {
    const p = body as { name: string; email: string };
    const user: User = { id: `USR-${Date.now()}`, email: p?.email || 'new@user.com', name: p?.name || 'New User', role: 'analyst', createdAt: new Date().toISOString() };
    return mockDelay({ user, token: 'mock-jwt-token' }) as Promise<T>;
  }
  if (path === '/auth/logout' && method === 'POST') {
    return mockDelay({ success: true }) as Promise<T>;
  }
  if (path === '/assessment/submit' && method === 'POST') {
    const state = body as AssessmentState;
    const outcome: DecisionOutcome = mockAssess(state);
    return mockDelay(outcome) as Promise<T>;
  }
  if (path === '/assessment/history' && method === 'GET') {
    return mockDelay(mockHistory as HistoryEntry[]) as Promise<T>;
  }
  if (path.startsWith('/assessment/presets') && method === 'GET') {
    const presets = [1, 2, 3, 4, 5].map((id) => ({ id, name: `Preset ${id}`, description: `Assessment preset #${id}` }));
    return mockDelay(presets) as Promise<T>;
  }
  if (path === '/models' && method === 'GET') {
    return mockDelay(mockModels as MLModel[]) as Promise<T>;
  }
  if (path.startsWith('/models/') && path.endsWith('/train') && method === 'POST') {
    const id = path.split('/')[2];
    const updated: MLModel = { ...(mockModels.find((m) => m.id === id) || mockModels[0]), lastTrained: new Date().toISOString() };
    return mockDelay(updated) as Promise<T>;
  }
  if (path.startsWith('/models/') && path.endsWith('/deploy') && method === 'POST') {
    const id = path.split('/')[2];
    const p = body as { deployed?: boolean };
    const updated: MLModel = { ...(mockModels.find((m) => m.id === id) || mockModels[0]), deployed: p?.deployed ?? true };
    return mockDelay(updated) as Promise<T>;
  }
  if (path === '/datasets' && method === 'GET') {
    return mockDelay(mockDatasets as Dataset[]) as Promise<T>;
  }
  if (path === '/datasets/upload' && method === 'POST') {
    const p = body as Partial<Dataset>;
    const ds: Dataset = { id: `DS-${Date.now()}`, name: p?.name || 'Uploaded Dataset', type: p?.type || 'Custom', rows: p?.rows || 0, columns: p?.columns || 0, uploadedAt: new Date().toISOString(), status: 'processing' };
    return mockDelay(ds) as Promise<T>;
  }
  if (path.startsWith('/datasets/') && method === 'DELETE') {
    return mockDelay({ success: true }) as Promise<T>;
  }
  return mockDelay({} as T);
}

// ── Named API objects ─────────────────────────────────────────────────────────

export const authApi = {
  login: (email: string, password: string) =>
    request<{ user: User; token: string }>('POST', '/auth/login', { email, password }),
  signup: (name: string, email: string, password: string) =>
    request<{ user: User; token: string }>('POST', '/auth/signup', { name, email, password }),
  logout: () => request<{ success: boolean }>('POST', '/auth/logout'),
};

export const assessmentApi = {
  /** Legacy mock-compatible submission (used by fallback) */
  submitAssessment: (state: AssessmentState) =>
    request<DecisionOutcome>('POST', '/assessment/submit', state),

  /** Real FastAPI POST /api/decide */
  decide: (state: AssessmentState, thresholds?: { tau?: number; tau_e?: number }): Promise<BackendDecisionResponse> => {
    const body = {
      applicant: {
        age: Math.max(18, state.applicant.ageUnknown ? 30 : state.applicant.age),
        platform_tenure: Math.max(1, Math.min(24, state.applicant.tenureMonths)),
        e_shram_registered: state.applicant.eshramRegistered ? 1 : 0,
        income_mean: Math.max(1, state.finances.monthlyIncome),
        income_volatility: Math.max(0, state.finances.incomeVolatility),
        expense_mean: Math.max(0, state.finances.monthlyExpenses),
        liquidity_current: state.finances.liquidityMean,
        history_length: Math.max(3, Math.min(12, state.evidence.historyMonths)),
        multi_platform: state.applicant.multiPlatform ? 1 : 0,
        emi_status: state.finances.monthlyDebt > 0 ? 1 : 0,
        aa_completeness: Math.max(0, Math.min(1, state.evidence.aaCompleteness)),
        uli_completeness: Math.max(0, Math.min(1, state.evidence.uliCompleteness)),
        age_policy: Math.max(18, state.applicant.ageUnknown ? 30 : state.applicant.age),
        income_policy: Math.max(1, state.finances.monthlyIncome),
        occupation: state.applicant.occupation || 'ride_hailing',
        nonfarm_engaged: 1,
        e_shram_policy: state.applicant.eshramRegistered ? 1 : 0,
        pd_lr: null,
        pd_xgb: null,
        applicant_id: state.applicant.id || `APP-${Date.now()}`,
        decision_date: new Date().toISOString().split('T')[0],
      },
      decision_mode: 'production',
      explain: true,
      // Pass user-defined thresholds when provided
      ...(thresholds?.tau !== undefined && { tau: thresholds.tau }),
      ...(thresholds?.tau_e !== undefined && { tau_e: thresholds.tau_e }),
    };

    return fetch(`${BASE_URL}/decide`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then(async (res) => {
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error((err as { detail?: string }).detail ?? `Request failed: ${res.status}`);
      }
      return res.json() as Promise<BackendDecisionResponse>;
    });
  },

  getHistory: () => request<HistoryEntry[]>('GET', '/assessment/history'),
  getPresets: () =>
    request<Array<{ id: number; name: string; description: string }>>('GET', '/assessment/presets'),
};

export const modelsApi = {
  getModels: () => request<MLModel[]>('GET', '/models'),
  trainModel: (id: string) => request<MLModel>('POST', `/models/${id}/train`),
  deployModel: (id: string, deployed = true) =>
    request<MLModel>('POST', `/models/${id}/deploy`, { deployed }),
};

export const datasetsApi = {
  getDatasets: () => request<Dataset[]>('GET', '/datasets'),
  uploadDataset: (data: Partial<Dataset>) => request<Dataset>('POST', '/datasets/upload', data),
  deleteDataset: (id: string) => request<{ success: boolean }>('DELETE', `/datasets/${id}`),
};
