import type {
  Applicant,
  AssessmentPresetId,
  AssessmentState,
  DecisionMode,
  DecisionOutcome,
  Evidence,
  Finances,
  GateStatus,
} from '../types';

export function calculateEvidenceScore(
  historyMonths: number,
  aaPct: number,
  uliPct: number
): number {
  const historyComponent = 0.5 * (Math.min(historyMonths, 12) / 12);
  const aaComponent = 0.25 * Math.max(0, Math.min(1, aaPct));
  const uliComponent = 0.25 * Math.max(0, Math.min(1, uliPct));
  return Math.max(0, Math.min(1, historyComponent + aaComponent + uliComponent));
}

export function calculateFinancialRatios(
  income: number,
  expenses: number,
  debt: number
): { expRatio: number; debtRatio: number; surplus: number } {
  const safeIncome = income > 0 ? income : 1;
  const expRatio = expenses / safeIncome;
  const debtRatio = debt / safeIncome;
  const surplus = income - expenses - debt;
  return { expRatio, debtRatio, surplus };
}

export function calculateRiskScore(state: AssessmentState): number {
  const { applicant, finances } = state;

  let pd = 0.06;

  if (applicant.ageUnknown) {
    pd += 0.08;
  } else if (applicant.age < 22 || applicant.age > 58) {
    pd += 0.04;
  } else if (applicant.age >= 30 && applicant.age <= 45) {
    pd -= 0.02;
  }

  if (applicant.tenureMonths < 6) {
    pd += 0.1;
  } else if (applicant.tenureMonths < 12) {
    pd += 0.06;
  } else if (applicant.tenureMonths < 24) {
    pd += 0.03;
  } else if (applicant.tenureMonths >= 60) {
    pd -= 0.03;
  }

  if (!applicant.eshramRegistered) {
    pd += 0.025;
  } else {
    pd -= 0.015;
  }

  if (!applicant.multiPlatform) {
    pd += 0.02;
  } else {
    pd -= 0.01;
  }

  const { debtRatio, expRatio, surplus } = calculateFinancialRatios(
    finances.monthlyIncome,
    finances.monthlyExpenses,
    finances.monthlyDebt
  );

  if (debtRatio > 0.6) {
    pd += 0.12;
  } else if (debtRatio > 0.45) {
    pd += 0.07;
  } else if (debtRatio > 0.3) {
    pd += 0.03;
  } else if (debtRatio < 0.15) {
    pd -= 0.02;
  }

  if (expRatio > 0.85) {
    pd += 0.08;
  } else if (expRatio > 0.7) {
    pd += 0.04;
  } else if (expRatio < 0.55) {
    pd -= 0.02;
  }

  if (surplus < 0) {
    pd += 0.1;
  } else if (surplus < finances.monthlyIncome * 0.05) {
    pd += 0.04;
  }

  const liquidityMonths = finances.monthlyExpenses > 0
    ? finances.liquidityMean / finances.monthlyExpenses
    : 0;
  if (liquidityMonths < 0.5) {
    pd += 0.08;
  } else if (liquidityMonths < 1) {
    pd += 0.04;
  } else if (liquidityMonths >= 3) {
    pd -= 0.02;
  }

  const minLiquidityMonths = finances.monthlyExpenses > 0
    ? finances.liquidityMin / finances.monthlyExpenses
    : 0;
  if (minLiquidityMonths < 0.25) {
    pd += 0.06;
  } else if (minLiquidityMonths < 0.5) {
    pd += 0.03;
  }

  pd += finances.incomeVolatility * 0.22;

  return Math.max(0.001, Math.min(0.99, pd));
}

export interface PolicyResult {
  passed: boolean;
  reasons: string[];
  score: number;
}

export function calculatePolicyScore(state: AssessmentState): PolicyResult {
  const { applicant, finances, evidence } = state;
  const reasons: string[] = [];
  let passed = true;

  if (applicant.tenureMonths < 6) {
    passed = false;
    reasons.push('Tenure below minimum 6 months');
  }

  const { debtRatio, expRatio, surplus } = calculateFinancialRatios(
    finances.monthlyIncome,
    finances.monthlyExpenses,
    finances.monthlyDebt
  );

  if (debtRatio > 0.5) {
    passed = false;
    reasons.push(`Debt-to-income ratio ${(debtRatio * 100).toFixed(1)}% exceeds 50% cap`);
  }

  if (expRatio > 0.85) {
    passed = false;
    reasons.push(`Expense ratio ${(expRatio * 100).toFixed(1)}% exceeds 85% limit`);
  }

  if (surplus < finances.monthlyIncome * 0.05) {
    passed = false;
    reasons.push('Net monthly surplus below 5% of income');
  }

  if (finances.monthlyIncome < 8000) {
    passed = false;
    reasons.push('Monthly income below minimum threshold (INR 8,000)');
  }

  if (evidence.historyMonths < 3) {
    passed = false;
    reasons.push('Evidence history shorter than 3 months');
  }

  const evScore = calculateEvidenceScore(
    evidence.historyMonths,
    evidence.aaCompleteness,
    evidence.uliCompleteness
  );
  if (evScore < 0.4) {
    passed = false;
    reasons.push(`Evidence score ${(evScore * 100).toFixed(1)}% below 40% minimum`);
  }

  const liquidityMonths = finances.monthlyExpenses > 0
    ? finances.liquidityMin / finances.monthlyExpenses
    : 0;
  if (liquidityMonths < 0.25) {
    passed = false;
    reasons.push('Minimum liquidity below 1 week of expenses');
  }

  const rawScore = passed ? 0.9 : Math.max(0.2, 0.65 - 0.08 * reasons.length);
  const score = Math.round(rawScore * 1000) / 1000;

  return { passed, reasons, score };
}

function computeGates(
  riskPD: number,
  _policy: PolicyResult,
  evidenceScore: number,
  finances: Finances
): GateStatus[] {
  const { debtRatio, expRatio } = calculateFinancialRatios(
    finances.monthlyIncome,
    finances.monthlyExpenses,
    finances.monthlyDebt
  );
  const liquidityMonths = finances.monthlyExpenses > 0
    ? finances.liquidityMin / finances.monthlyExpenses
    : 0;

  const gates: GateStatus[] = [];

  gates.push({
    name: 'Income Threshold',
    status: finances.monthlyIncome >= 8000 ? 'passed' : 'failed',
    score: Math.max(0, Math.min(1, finances.monthlyIncome / 50000)),
  });

  gates.push({
    name: 'Expense Ratio',
    status: expRatio <= 0.85 ? 'passed' : expRatio <= 0.92 ? 'pending' : 'failed',
    score: Math.max(0, Math.min(1, 1 - (expRatio - 0.5) * 1.2)),
  });

  gates.push({
    name: 'Debt Service Ratio',
    status: debtRatio <= 0.5 ? 'passed' : debtRatio <= 0.6 ? 'pending' : 'failed',
    score: Math.max(0, Math.min(1, 1 - (debtRatio - 0.2) * 1.5)),
  });

  gates.push({
    name: 'Liquidity Coverage',
    status: liquidityMonths >= 0.5 ? 'passed' : liquidityMonths >= 0.25 ? 'pending' : 'failed',
    score: Math.max(0, Math.min(1, liquidityMonths / 2)),
  });

  gates.push({
    name: 'Evidence Completeness',
    status: evidenceScore >= 0.6 ? 'passed' : evidenceScore >= 0.4 ? 'pending' : 'failed',
    score: evidenceScore,
  });

  gates.push({
    name: 'Risk PD Threshold',
    status: riskPD <= 0.15 ? 'passed' : riskPD <= 0.22 ? 'pending' : 'failed',
    score: Math.max(0, Math.min(1, 1 - (riskPD - 0.05) * 5)),
  });

  return gates;
}

function buildRationale(
  status: 'approve' | 'review' | 'decline',
  state: AssessmentState,
  policy: PolicyResult,
  riskPD: number,
  evidenceScore: number
): string {
  const { applicant } = state;

  if (status === 'approve') {
    return [
      `Auto-approve via ${state.decisionMode}:`,
      `${applicant.occupation} with INR ${state.finances.monthlyIncome.toLocaleString()} monthly income.`,
      `PD of ${(riskPD * 100).toFixed(2)}% below cap; evidence score ${(evidenceScore * 100).toFixed(1)}%.`,
      applicant.tenureMonths >= 12
        ? `Tenure (${applicant.tenureMonths} mo) confirms income stability.`
        : `Tenure borderline but compensated by liquidity and e-Shram registration.`,
    ].join(' ');
  }

  if (status === 'review') {
    const flags: string[] = [];
    if (applicant.ageUnknown) flags.push('age not verified');
    if (!applicant.eshramRegistered) flags.push('e-Shram absent');
    if (state.finances.incomeVolatility > 0.25) flags.push('income volatility elevated');
    if (!policy.passed) flags.push(`${policy.reasons.length} policy amber flags`);

    return [
      `Refer to analyst review (${state.decisionMode}):`,
      flags.length > 0 ? `${flags.join(', ')}.` : 'Marginal combined score.',
      `PD ${(riskPD * 100).toFixed(2)}%, evidence ${(evidenceScore * 100).toFixed(1)}%.`,
      'Requires human sign-off before disbursement.',
    ].join(' ');
  }

  return [
    `Decline per ${state.decisionMode} policy:`,
    policy.reasons.length > 0
      ? `${policy.reasons.join('; ')}.`
      : `Composite score below decline threshold.`,
    `Risk PD ${(riskPD * 100).toFixed(2)}%, evidence ${(evidenceScore * 100).toFixed(1)}%.`,
    applicant.tenureMonths < 12
      ? `Tenure ${applicant.tenureMonths} mo insufficient for tier.`
      : '',
  ]
    .filter(Boolean)
    .join(' ');
}

export function computeDecision(
  state: AssessmentState,
  mode: DecisionMode,
  tauRisk: number = 0.25,
  tauEvidence: number = 0.50,
): DecisionOutcome {
  const evidenceScore = calculateEvidenceScore(
    state.evidence.historyMonths,
    state.evidence.aaCompleteness,
    state.evidence.uliCompleteness
  );

  const riskPD = calculateRiskScore({ ...state, decisionMode: mode });
  const riskScore = 1 - riskPD;

  const policy = calculatePolicyScore(state);

  const modeWeight =
    mode === 'D1' ? 0 : mode === 'D2' ? 0.025 : mode === 'D3' ? 0.05 : 0.09;

  const finalRaw =
    riskScore * 0.42 +
    policy.score * 0.33 +
    evidenceScore * 0.25 +
    modeWeight;

  const finalScore = Math.max(0, Math.min(1, finalRaw));

  const strict = mode === 'D1';
  const lenient = mode === 'D4';

  const approveThreshold = strict ? 0.78 : lenient ? 0.62 : 0.7;
  const declineThreshold = strict ? 0.58 : lenient ? 0.42 : 0.5;

  let status: 'approve' | 'review' | 'decline';
  if (finalScore >= approveThreshold && policy.passed && riskPD < tauRisk && evidenceScore >= tauEvidence) {
    status = 'approve';
  } else if (finalScore <= declineThreshold || riskPD > (tauRisk * 1.12) || (!policy.passed && finalScore < 0.55)) {
    status = 'decline';
  } else {
    status = 'review';
  }

  return {
    status,
    riskScore: Math.round(riskScore * 1000) / 1000,
    policyScore: policy.score,
    evidenceScore: Math.round(evidenceScore * 1000) / 1000,
    finalScore: Math.round(finalScore * 1000) / 1000,
    riskPD: Math.round(riskPD * 10000) / 10000,
    rationale: buildRationale(status, state, policy, riskPD, evidenceScore),
    gates: computeGates(riskPD, policy, evidenceScore, state.finances),
  };
}

const presetApplicants: Record<AssessmentPresetId, Applicant> = {
  1: {
    id: 'APP-001',
    displayName: 'Rajesh Kumar',
    age: 34,
    ageUnknown: false,
    occupation: 'Delivery Partner',
    tenureMonths: 18,
    multiPlatform: true,
    eshramRegistered: true,
  },
  2: {
    id: 'APP-002',
    displayName: 'Priya Sharma',
    age: 29,
    ageUnknown: false,
    occupation: 'Street Vendor',
    tenureMonths: 36,
    multiPlatform: false,
    eshramRegistered: true,
  },
  3: {
    id: 'APP-003',
    displayName: 'Amit Patel',
    age: 45,
    ageUnknown: false,
    occupation: 'Small Business Owner',
    tenureMonths: 60,
    multiPlatform: true,
    eshramRegistered: false,
  },
  4: {
    id: 'APP-004',
    displayName: 'Sunita Devi',
    age: 0,
    ageUnknown: true,
    occupation: 'Domestic Worker',
    tenureMonths: 6,
    multiPlatform: false,
    eshramRegistered: false,
  },
  5: {
    id: 'APP-005',
    displayName: 'Mohammed Iqbal',
    age: 52,
    ageUnknown: false,
    occupation: 'Auto Rickshaw Driver',
    tenureMonths: 120,
    multiPlatform: false,
    eshramRegistered: true,
  },
};

const presetFinances: Record<AssessmentPresetId, Finances> = {
  1: {
    monthlyIncome: 42000,
    monthlyExpenses: 28000,
    monthlyDebt: 4500,
    liquidityMean: 72000,
    liquidityMin: 38000,
    incomeVolatility: 0.14,
  },
  2: {
    monthlyIncome: 28000,
    monthlyExpenses: 22000,
    monthlyDebt: 2000,
    liquidityMean: 55000,
    liquidityMin: 32000,
    incomeVolatility: 0.09,
  },
  3: {
    monthlyIncome: 85000,
    monthlyExpenses: 58000,
    monthlyDebt: 18000,
    liquidityMean: 220000,
    liquidityMin: 120000,
    incomeVolatility: 0.22,
  },
  4: {
    monthlyIncome: 12000,
    monthlyExpenses: 10500,
    monthlyDebt: 3000,
    liquidityMean: 6000,
    liquidityMin: 1200,
    incomeVolatility: 0.35,
  },
  5: {
    monthlyIncome: 36000,
    monthlyExpenses: 24000,
    monthlyDebt: 5000,
    liquidityMean: 180000,
    liquidityMin: 95000,
    incomeVolatility: 0.07,
  },
};

const presetEvidence: Record<AssessmentPresetId, Evidence> = {
  1: {
    historyMonths: 12,
    aaCompleteness: 0.88,
    uliCompleteness: 0.82,
    evidenceScore: 0.925,
  },
  2: {
    historyMonths: 11,
    aaCompleteness: 0.72,
    uliCompleteness: 0.68,
    evidenceScore: 0.81,
  },
  3: {
    historyMonths: 8,
    aaCompleteness: 0.65,
    uliCompleteness: 0.52,
    evidenceScore: 0.627,
  },
  4: {
    historyMonths: 3,
    aaCompleteness: 0.38,
    uliCompleteness: 0.22,
    evidenceScore: 0.275,
  },
  5: {
    historyMonths: 12,
    aaCompleteness: 0.95,
    uliCompleteness: 0.91,
    evidenceScore: 0.965,
  },
};

export function getPreset(id: AssessmentPresetId): AssessmentState {
  const applicant = presetApplicants[id];
  const finances = presetFinances[id];
  const evidence = presetEvidence[id];
  evidence.evidenceScore = calculateEvidenceScore(
    evidence.historyMonths,
    evidence.aaCompleteness,
    evidence.uliCompleteness
  );
  return {
    applicant,
    finances,
    evidence,
    decisionMode: 'D4',
  };
}
