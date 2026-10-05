export interface Applicant {
  id: string;
  displayName: string;
  age: number;
  ageUnknown: boolean;
  occupation: string;
  tenureMonths: number;
  multiPlatform: boolean;
  eshramRegistered: boolean;
}

export interface Finances {
  monthlyIncome: number;
  monthlyExpenses: number;
  monthlyDebt: number;
  liquidityMean: number;
  liquidityMin: number;
  incomeVolatility: number;
}

export interface Evidence {
  historyMonths: number;
  aaCompleteness: number;
  uliCompleteness: number;
  evidenceScore: number;
}

export type DecisionMode = 'D1' | 'D2' | 'D3' | 'D4';

export type AssessmentPresetId = 1 | 2 | 3 | 4 | 5;

export interface AssessmentState {
  applicant: Applicant;
  finances: Finances;
  evidence: Evidence;
  decisionMode: DecisionMode;
}

export interface GateStatus {
  name: string;
  status: 'passed' | 'failed' | 'pending';
  score?: number;
}

export interface DecisionOutcome {
  status: 'approve' | 'review' | 'decline';
  riskScore: number;
  policyScore: number;
  evidenceScore: number;
  finalScore: number;
  riskPD: number;
  rationale: string;
  gates: GateStatus[];
  creditScore?: number | null;
  creditScoreDisplay?: {
    score: number;
    pd_percent: number;
    threshold_score: number;
    threshold_pd_percent: number;
    phase: string;
    disclaimer: string;
  } | null;
}

export interface Dataset {
  id: string;
  name: string;
  type: string;
  rows: number;
  columns: number;
  uploadedAt: string;
  status: 'processing' | 'ready' | 'failed';
}

export interface MLModel {
  id: string;
  name: string;
  version: string;
  accuracy: number;
  deployed: boolean;
  lastTrained: string;
  type: string;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'analyst' | 'reviewer';
  createdAt: string;
}

export interface HistoryScores {
  riskScore: number;
  policyScore: number;
  evidenceScore: number;
  finalScore: number;
}

export interface HistoryEntry {
  id: string;
  applicantId: string;
  applicantName: string;
  outcome: 'approve' | 'review' | 'decline';
  createdAt: string;
  decisionMode: DecisionMode;
  scores: HistoryScores;
}

export interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadedAt: string;
  status: 'uploading' | 'processing' | 'ready' | 'failed';
  percent?: number;
}
