/**
 * Settings store — persisted to localStorage.
 *
 * Thresholds defined here flow into:
 *   1. assessmentApi.decide() — sends riskCutoffPct / 100 as `tau` override (future backend arg)
 *   2. computeDecision() local fallback — uses these thresholds instead of hardcoded ones
 *   3. DecisionResultPage threshold display labels
 *
 * Note: The backend currently uses its own config tau (0.40). When the backend exposes
 * a `tau` query param, `assessmentApi.decide()` will pass `riskCutoffPct / 100` directly.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { DecisionMode } from '@/types';

export interface SettingsState {
  // Decision engine thresholds
  riskCutoffPct: number;        // displayed as % e.g. 25 → τ = 0.25
  evidenceCutoff: number;       // 0–1 e.g. 0.50
  defaultDecisionMode: DecisionMode;

  // Policy toggles
  enableJanSamarth: boolean;
  enablePMMY: boolean;
  displayNotices: boolean;

  // Appearance
  theme: 'light' | 'dark';

  // Notifications
  emailNotifications: boolean;
  desktopNotifications: boolean;
  auditLogFrequency: 'daily' | 'weekly' | 'monthly';

  // Actions
  applySettings: (patch: Partial<Omit<SettingsState, 'applySettings'>>) => void;
  reset: () => void;
}

const DEFAULTS: Omit<SettingsState, 'applySettings' | 'reset'> = {
  riskCutoffPct: 25,
  evidenceCutoff: 0.50,
  defaultDecisionMode: 'D4',
  enableJanSamarth: true,
  enablePMMY: true,
  displayNotices: true,
  theme: 'light',
  emailNotifications: true,
  desktopNotifications: false,
  auditLogFrequency: 'weekly',
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      ...DEFAULTS,

      applySettings: (patch) => set((s) => ({ ...s, ...patch })),

      reset: () => set((s) => ({ ...s, ...DEFAULTS })),
    }),
    {
      name: 'ml-settings-storage',
      // Only persist the data fields, not the action functions
      partialize: (s) => ({
        riskCutoffPct: s.riskCutoffPct,
        evidenceCutoff: s.evidenceCutoff,
        defaultDecisionMode: s.defaultDecisionMode,
        enableJanSamarth: s.enableJanSamarth,
        enablePMMY: s.enablePMMY,
        displayNotices: s.displayNotices,
        theme: s.theme,
        emailNotifications: s.emailNotifications,
        desktopNotifications: s.desktopNotifications,
        auditLogFrequency: s.auditLogFrequency,
      }),
    }
  )
);
