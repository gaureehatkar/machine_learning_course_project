import { create } from 'zustand';
import type {
  Applicant,
  AssessmentPresetId,
  AssessmentState,
  DecisionMode,
  DecisionOutcome,
  Evidence,
  Finances,
  HistoryEntry,
} from '@/types';
import { computeDecision, getPreset } from '@/utils/assessment';
import { adaptBackendResponse, assessmentApi } from '@/services/api';
import { useSettingsStore } from '@/store/useSettingsStore';

interface AssessmentStore {
  assessmentState: AssessmentState;
  decisionOutcome: DecisionOutcome | null;
  loading: boolean;
  error: string | null;
  history: HistoryEntry[];
  updateApplicant: (partial: Partial<Applicant>) => void;
  updateFinances: (partial: Partial<Finances>) => void;
  updateEvidence: (partial: Partial<Evidence>) => void;
  setHistoryDuration: (months: number) => void;
  setDecisionMode: (mode: DecisionMode) => void;
  loadPreset: (id: AssessmentPresetId) => void;
  runAssessment: () => Promise<void>;
  clearDecision: () => void;
}

export const useAssessmentStore = create<AssessmentStore>((set, get) => ({
  assessmentState: getPreset(1),
  decisionOutcome: null,
  loading: false,
  error: null,
  history: [],

  updateApplicant: (partial: Partial<Applicant>) => {
    set((state) => ({
      assessmentState: {
        ...state.assessmentState,
        applicant: { ...state.assessmentState.applicant, ...partial },
      },
      decisionOutcome: null,
    }));
  },

  updateFinances: (partial: Partial<Finances>) => {
    set((state) => ({
      assessmentState: {
        ...state.assessmentState,
        finances: { ...state.assessmentState.finances, ...partial },
      },
      decisionOutcome: null,
    }));
  },

  updateEvidence: (partial: Partial<Evidence>) => {
    set((state) => {
      const newEvidence = { ...state.assessmentState.evidence, ...partial };
      return {
        assessmentState: {
          ...state.assessmentState,
          evidence: newEvidence,
        },
        decisionOutcome: null,
      };
    });
  },

  setHistoryDuration: (months: number) => {
    set((state) => ({
      assessmentState: {
        ...state.assessmentState,
        evidence: { ...state.assessmentState.evidence, historyMonths: months },
      },
      decisionOutcome: null,
    }));
  },

  setDecisionMode: (mode: DecisionMode) => {
    set((state) => ({
      assessmentState: {
        ...state.assessmentState,
        decisionMode: mode,
      },
      decisionOutcome: null,
    }));
  },

  loadPreset: (id: AssessmentPresetId) => {
    set({
      assessmentState: getPreset(id),
      decisionOutcome: null,
      error: null,
    });
  },

  runAssessment: async () => {
    set({ loading: true, error: null });

    try {
      const { assessmentState } = get();
      let outcome: DecisionOutcome;
      const settings = useSettingsStore.getState();

      try {
        const backendResp = await assessmentApi.decide(assessmentState, {
          tau: settings.riskCutoffPct / 100,
          tau_e: settings.evidenceCutoff,
        });
        outcome = adaptBackendResponse(backendResp, assessmentState);
      } catch (apiErr) {
        console.warn('Backend unavailable, using local computation:', apiErr);
        outcome = computeDecision(
          assessmentState,
          settings.defaultDecisionMode,
          settings.riskCutoffPct / 100,
          settings.evidenceCutoff,
        );
      }

      const entry: HistoryEntry = {
        id: `HIST-${Date.now()}`,
        applicantId: assessmentState.applicant.id,
        applicantName: assessmentState.applicant.displayName,
        outcome: outcome.status,
        createdAt: new Date().toISOString(),
        decisionMode: assessmentState.decisionMode,
        scores: {
          riskScore: outcome.riskScore,
          policyScore: outcome.policyScore,
          evidenceScore: outcome.evidenceScore,
          finalScore: outcome.finalScore,
        },
      };

      set((state) => ({
        decisionOutcome: outcome,
        loading: false,
        history: [entry, ...state.history],
      }));
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : 'Assessment failed. Please try again.',
      });
    }
  },

  clearDecision: () => {
    set({
      decisionOutcome: null,
      error: null,
    });
  },
}));
