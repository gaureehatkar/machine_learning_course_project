import type {
  Applicant,
  AssessmentState,
  Dataset,
  DecisionMode,
  DecisionOutcome,
  GateStatus,
  HistoryEntry,
  MLModel,
  User,
} from '../types';

export const mockApplicants: Applicant[] = [
  {
    id: 'APP-001',
    displayName: 'Rajesh Kumar',
    age: 34,
    ageUnknown: false,
    occupation: 'Delivery Partner',
    tenureMonths: 18,
    multiPlatform: true,
    eshramRegistered: true,
  },
  {
    id: 'APP-002',
    displayName: 'Priya Sharma',
    age: 29,
    ageUnknown: false,
    occupation: 'Street Vendor',
    tenureMonths: 36,
    multiPlatform: false,
    eshramRegistered: true,
  },
  {
    id: 'APP-003',
    displayName: 'Amit Patel',
    age: 45,
    ageUnknown: false,
    occupation: 'Small Business Owner',
    tenureMonths: 60,
    multiPlatform: true,
    eshramRegistered: false,
  },
  {
    id: 'APP-004',
    displayName: 'Sunita Devi',
    age: 0,
    ageUnknown: true,
    occupation: 'Domestic Worker',
    tenureMonths: 6,
    multiPlatform: false,
    eshramRegistered: false,
  },
  {
    id: 'APP-005',
    displayName: 'Mohammed Iqbal',
    age: 52,
    ageUnknown: false,
    occupation: 'Auto Rickshaw Driver',
    tenureMonths: 120,
    multiPlatform: false,
    eshramRegistered: true,
  },
];

export const mockDatasets: Dataset[] = [
  {
    id: 'DS-001',
    name: 'Income Verification Dataset 2024',
    type: 'Financial',
    rows: 150000,
    columns: 42,
    uploadedAt: '2026-01-15T09:30:00Z',
    status: 'ready',
  },
  {
    id: 'DS-002',
    name: 'e-NAM Transaction History',
    type: 'Agricultural',
    rows: 285000,
    columns: 28,
    uploadedAt: '2026-02-03T14:20:00Z',
    status: 'ready',
  },
  {
    id: 'DS-003',
    name: 'GSTIN Compliance Records',
    type: 'Tax',
    rows: 92000,
    columns: 18,
    uploadedAt: '2026-02-18T11:45:00Z',
    status: 'ready',
  },
  {
    id: 'DS-004',
    name: 'UPI Merchant Transactions Q1',
    type: 'Payments',
    rows: 1250000,
    columns: 35,
    uploadedAt: '2026-03-22T08:10:00Z',
    status: 'processing',
  },
  {
    id: 'DS-005',
    name: 'Credit Bureau Dedupe Sample',
    type: 'Credit',
    rows: 45000,
    columns: 22,
    uploadedAt: '2026-03-28T16:55:00Z',
    status: 'failed',
  },
];

export const mockModels: MLModel[] = [
  {
    id: 'MDL-001',
    name: 'Income Estimator v3',
    version: '3.2.1',
    accuracy: 0.874,
    deployed: true,
    lastTrained: '2026-02-10T06:00:00Z',
    type: 'Regression',
  },
  {
    id: 'MDL-002',
    name: 'Default Risk Classifier',
    version: '2.1.0',
    accuracy: 0.912,
    deployed: true,
    lastTrained: '2026-01-28T18:30:00Z',
    type: 'Classification',
  },
  {
    id: 'MDL-003',
    name: 'Evidence Completeness Scorer',
    version: '1.5.3',
    accuracy: 0.841,
    deployed: true,
    lastTrained: '2026-03-05T12:15:00Z',
    type: 'Scoring',
  },
  {
    id: 'MDL-004',
    name: 'Occupation Classification BERT',
    version: '0.9.0',
    accuracy: 0.768,
    deployed: false,
    lastTrained: '2026-03-20T09:45:00Z',
    type: 'NLP',
  },
];

const outcomes: Array<'approve' | 'review' | 'decline'> = ['approve', 'review', 'decline'];
const modes: DecisionMode[] = ['D1', 'D2', 'D3', 'D4'];
const names: string[] = mockApplicants.map((a) => a.displayName);
const ids: string[] = mockApplicants.map((a) => a.id);

export const mockHistory: HistoryEntry[] = Array.from({ length: 10 }, (_, i) => {
  const outcomeIdx = i % 3;
  const modeIdx = i % 4;
  const appIdx = i % 5;
  const baseScore = 0.4 + Math.random() * 0.55;
  return {
    id: `HIST-${String(1000 + i)}`,
    applicantId: ids[appIdx],
    applicantName: names[appIdx],
    outcome: outcomes[outcomeIdx],
    createdAt: new Date(Date.now() - (i + 1) * 86400000 * (1 + Math.random())).toISOString(),
    decisionMode: modes[modeIdx],
    scores: {
      riskScore: Math.round((0.3 + Math.random() * 0.6) * 1000) / 1000,
      policyScore: outcomes[outcomeIdx] === 'approve' ? 1 : outcomes[outcomeIdx] === 'review' ? 0.6 : 0.3,
      evidenceScore: Math.round((0.5 + Math.random() * 0.45) * 1000) / 1000,
      finalScore: Math.round(baseScore * 1000) / 1000,
    },
  };
});

export const currentUser: User = {
  id: 'USR-001',
  email: 'analyst@microfinance.in',
  name: 'Ananya Menon',
  role: 'analyst',
  createdAt: '2025-06-12T10:00:00Z',
};

export const monthlyIncomeData: Array<{ month: string; income: number; expenses: number; surplus: number }> = [
  { month: 'Apr 2025', income: 32000, expenses: 24000, surplus: 8000 },
  { month: 'May 2025', income: 38500, expenses: 25500, surplus: 13000 },
  { month: 'Jun 2025', income: 35000, expenses: 26000, surplus: 9000 },
  { month: 'Jul 2025', income: 42000, expenses: 27500, surplus: 14500 },
  { month: 'Aug 2025', income: 39000, expenses: 26800, surplus: 12200 },
  { month: 'Sep 2025', income: 45000, expenses: 28000, surplus: 17000 },
  { month: 'Oct 2025', income: 41000, expenses: 29500, surplus: 11500 },
  { month: 'Nov 2025', income: 48000, expenses: 31000, surplus: 17000 },
  { month: 'Dec 2025', income: 52000, expenses: 34000, surplus: 18000 },
  { month: 'Jan 2026', income: 44000, expenses: 30500, surplus: 13500 },
  { month: 'Feb 2026', income: 40000, expenses: 29000, surplus: 11000 },
  { month: 'Mar 2026', income: 46500, expenses: 30000, surplus: 16500 },
];

export const confusionMatrix = {
  labels: ['Approve', 'Review', 'Decline'],
  matrix: [
    [412, 28, 14],
    [31, 189, 22],
    [12, 25, 268],
  ],
};

export const precisionRecallData = [
  { threshold: 0.1, precision: 0.62, recall: 0.95 },
  { threshold: 0.2, precision: 0.71, recall: 0.89 },
  { threshold: 0.3, precision: 0.78, recall: 0.82 },
  { threshold: 0.4, precision: 0.83, recall: 0.75 },
  { threshold: 0.5, precision: 0.88, recall: 0.68 },
  { threshold: 0.6, precision: 0.91, recall: 0.58 },
  { threshold: 0.7, precision: 0.94, recall: 0.45 },
  { threshold: 0.8, precision: 0.97, recall: 0.32 },
  { threshold: 0.9, precision: 0.99, recall: 0.18 },
];

export const rocData = [
  { fpr: 0.0, tpr: 0.0 },
  { fpr: 0.02, tpr: 0.25 },
  { fpr: 0.05, tpr: 0.45 },
  { fpr: 0.08, tpr: 0.6 },
  { fpr: 0.12, tpr: 0.72 },
  { fpr: 0.18, tpr: 0.82 },
  { fpr: 0.25, tpr: 0.89 },
  { fpr: 0.35, tpr: 0.93 },
  { fpr: 0.5, tpr: 0.96 },
  { fpr: 0.7, tpr: 0.98 },
  { fpr: 1.0, tpr: 1.0 },
];

function buildGates(riskPassed: boolean, policyPassed: boolean, evidencePassed: boolean): GateStatus[] {
  const gates: GateStatus[] = [];
  gates.push({ name: 'Income Stability', status: policyPassed ? 'passed' : 'failed', score: policyPassed ? 0.82 : 0.48 });
  gates.push({ name: 'Debt Service Ratio', status: policyPassed ? 'passed' : riskPassed ? 'pending' : 'failed', score: 0.71 });
  gates.push({ name: 'Liquidity Coverage', status: evidencePassed ? 'passed' : 'failed', score: evidencePassed ? 0.88 : 0.52 });
  gates.push({ name: 'Evidence Completeness', status: evidencePassed ? 'passed' : 'pending', score: evidencePassed ? 0.79 : 0.58 });
  gates.push({ name: 'Risk PD Threshold', status: riskPassed ? 'passed' : 'failed', score: riskPassed ? 0.91 : 0.34 });
  return gates;
}

function buildRationale(status: 'approve' | 'review' | 'decline', state: AssessmentState): string {
  if (status === 'approve') {
    return `Auto-approve: ${state.applicant.occupation} with ${state.finances.monthlyIncome.toLocaleString()} income meets all policy gates. Evidence score above threshold; stable 12+ month tenure.`;
  }
  if (status === 'review') {
    return `Refer to review: marginal risk profile. ${state.applicant.ageUnknown ? 'Age unconfirmed; ' : ''}${!state.applicant.eshramRegistered ? 'e-Shram not registered; ' : ''}Income volatility slightly elevated — analyst sign-off required.`;
  }
  return `Decline: fails policy gates. DTI ratio exceeds threshold, evidence completeness below minimum, and tenure (${state.applicant.tenureMonths} mo) insufficient for risk tier.`;
}

export function mockAssess(state: AssessmentState): DecisionOutcome {
  const f = state.finances;
  const e = state.evidence;
  const a = state.applicant;

  const expRatio = f.monthlyExpenses / f.monthlyIncome;
  const debtRatio = f.monthlyDebt / f.monthlyIncome;
  const surplusRatio = (f.monthlyIncome - f.monthlyExpenses - f.monthlyDebt) / f.monthlyIncome;

  const basePD = 0.05;
  const agePenalty = a.ageUnknown ? 0.08 : (a.age < 22 || a.age > 55 ? 0.04 : 0);
  const tenurePenalty = a.tenureMonths < 12 ? 0.07 : a.tenureMonths < 24 ? 0.03 : 0;
  const debtPenalty = Math.max(0, debtRatio - 0.4) * 0.35;
  const volatilityPenalty = f.incomeVolatility * 0.18;
  const liquidityPenalty = f.liquidityMean < 2 * f.monthlyExpenses ? 0.05 : 0;
  const platformBonus = a.multiPlatform ? -0.02 : 0;
  const eshramBonus = a.eshramRegistered ? -0.02 : 0;

  const riskPD = Math.max(0.005, Math.min(0.95,
    basePD + agePenalty + tenurePenalty + debtPenalty + volatilityPenalty + liquidityPenalty + platformBonus + eshramBonus
  ));
  const riskScore = 1 - riskPD;

  const policyPass = expRatio < 0.8 && debtRatio < 0.5 && surplusRatio > 0.05;
  const policyScore = policyPass ? 0.9 : Math.max(0.2, 0.6 - (expRatio - 0.7) * 2 - (debtRatio - 0.4) * 2);

  const evidencePass = e.historyMonths >= 9 && e.aaCompleteness >= 0.7 && e.uliCompleteness >= 0.6;
  const evidenceScore = 0.5 * (e.historyMonths / 12) + 0.25 * e.aaCompleteness + 0.25 * e.uliCompleteness;

  const modeBoost = state.decisionMode === 'D1' ? 0.0 : state.decisionMode === 'D2' ? 0.03 : state.decisionMode === 'D3' ? 0.06 : 0.1;
  const finalScore = Math.max(0, Math.min(1, (riskScore * 0.4 + policyScore * 0.35 + evidenceScore * 0.25 + modeBoost)));

  let status: 'approve' | 'review' | 'decline';
  const riskPassed = riskPD < 0.15;
  const policyPassed = policyPass;
  const evidencePassed = evidencePass;

  if (finalScore >= 0.72 && riskPassed && policyPassed && evidencePassed) {
    status = 'approve';
  } else if (finalScore >= 0.5 && (riskPD < 0.22 || evidenceScore >= 0.65)) {
    status = 'review';
  } else {
    status = 'decline';
  }

  return {
    status,
    riskScore: Math.round(riskScore * 1000) / 1000,
    policyScore: Math.round(policyScore * 1000) / 1000,
    evidenceScore: Math.round(evidenceScore * 1000) / 1000,
    finalScore: Math.round(finalScore * 1000) / 1000,
    riskPD: Math.round(riskPD * 10000) / 10000,
    rationale: buildRationale(status, state),
    gates: buildGates(riskPassed, policyPassed, evidencePassed),
  };
}
