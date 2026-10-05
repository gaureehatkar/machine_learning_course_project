import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { useAssessmentStore } from '@/store/useAssessmentStore';
import {
  calculateEvidenceScore,
  calculateFinancialRatios,
} from '@/utils/assessment';
import type { DecisionMode } from '@/types';

const occupationOptions = [
  { value: 'ride-hailing', label: 'Ride-hailing' },
  { value: 'delivery', label: 'Delivery' },
  { value: 'freelance', label: 'Freelance services' },
  { value: 'retail', label: 'Retail / micro-business' },
  { value: 'agricultural', label: 'Agricultural labour' },
  { value: 'unknown', label: 'Unknown' },
];

const decisionModes: Array<{
  id: DecisionMode;
  title: string;
  desc: string;
  recommended?: boolean;
}> = [
  { id: 'D1', title: 'D1: Risk only', desc: 'Default risk cutoff alone' },
  { id: 'D2', title: 'D2: Risk + Policy', desc: 'Default risk plus scheme pre-qualification' },
  { id: 'D3', title: 'D3: Risk + Evidence', desc: 'Default risk gated by telemetry quality' },
  {
    id: 'D4',
    title: 'D4: All three layers',
    desc: 'Full multi-signal evaluation: Risk, Policy and Evidence',
    recommended: true,
  },
];

const historyOptions = [3, 6, 9, 12];

const modeLabels: Record<DecisionMode, string> = {
  D1: 'D1 (Risk only)',
  D2: 'D2 (Risk + Policy)',
  D3: 'D3 (Risk + Evidence)',
  D4: 'D4 (All three layers)',
};

function getOccupationLabel(value: string): string {
  const opt = occupationOptions.find((o) => o.value === value);
  return opt?.label ?? value;
}

export default function AssessmentPage() {
  const navigate = useNavigate();
  const {
    assessmentState,
    loading,
    updateApplicant,
    updateFinances,
    updateEvidence,
    setHistoryDuration,
    setDecisionMode,
    runAssessment,
  } = useAssessmentStore();

  const { applicant, finances, evidence, decisionMode } = assessmentState;

  const evidenceScore = useMemo(
    () => calculateEvidenceScore(evidence.historyMonths, evidence.aaCompleteness, evidence.uliCompleteness),
    [evidence.historyMonths, evidence.aaCompleteness, evidence.uliCompleteness]
  );

  const financialRatios = useMemo(
    () => calculateFinancialRatios(finances.monthlyIncome, finances.monthlyExpenses, finances.monthlyDebt),
    [finances.monthlyIncome, finances.monthlyExpenses, finances.monthlyDebt]
  );

  const subH = 0.5 * (Math.min(evidence.historyMonths, 12) / 12);
  const subAA = 0.25 * evidence.aaCompleteness;
  const subULI = 0.25 * evidence.uliCompleteness;

  const evidenceSufficient = evidenceScore >= 0.5;

  const expRatioPct = (financialRatios.expRatio * 100).toFixed(1);
  const debtRatioPct = (financialRatios.debtRatio * 100).toFixed(1);
  const surplusStr =
    (financialRatios.surplus >= 0 ? '+₹' : '-₹') +
    Math.abs(Math.round(financialRatios.surplus)).toLocaleString('en-IN');

  const trendText =
    evidence.historyMonths < 3
      ? 'Trend indicator: Unavailable with under 3 months of history'
      : 'Trend indicator: Available (+0.04 monthly stability)';

  const seasonText =
    evidence.historyMonths < 12
      ? 'Seasonality index: Unavailable unless 12 months of history'
      : 'Seasonality index: Available (0.12 baseline volatility)';

  const ageStr = applicant.ageUnknown ? 'Age unknown' : `${applicant.age} years`;
  const schemeSummary = `${ageStr} · ${getOccupationLabel(applicant.occupation)}`;

  const handleAssess = async () => {
    await runAssessment();
    navigate('/decision/latest');
  };

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto w-full px-6 py-8">
        <div className="mb-8">
          <h1
            className="font-bold text-[#0F2137] tracking-tight leading-tight"
            style={{ fontSize: '28px' }}
          >
            Assess an applicant
          </h1>
          <p className="text-[15px] text-[#5B6B7B] mt-1.5 max-w-3xl leading-relaxed">
            Enter what is known about the applicant. The system scores risk, evidence quality and
            policy eligibility separately, then combines them into one decision.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          <div className="lg:col-span-8 bg-white rounded-lg border border-[#E2E8F0]">
            {/* Section 1: Applicant */}
            <section style={{ padding: '28px 32px' }}>
              <div className="flex items-center justify-between mb-5">
                <h2 className="text-[18px] font-semibold text-[#0F2137]">1. Applicant</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-5 gap-y-4">
                <div>
                  <label
                    className="block text-[13px] font-medium text-[#0F2137] mb-1.5"
                    htmlFor="applicant-id"
                  >
                    Applicant ID
                  </label>
                  <input
                    id="applicant-id"
                    type="text"
                    value={applicant.id}
                    onChange={(e) => updateApplicant({ id: e.target.value })}
                    className="w-full text-[14px] bg-white text-[#0F2137] border border-[#D1D9E0] rounded-lg px-3 py-2 focus:outline-none focus:border-[#0E7C7E] focus:ring-1 focus:ring-[#0E7C7E]"
                  />
                </div>

                <div>
                  <label
                    className="block text-[13px] font-medium text-[#0F2137] mb-1.5"
                    htmlFor="display-name"
                  >
                    Display name
                  </label>
                  <input
                    id="display-name"
                    type="text"
                    value={applicant.displayName}
                    onChange={(e) => updateApplicant({ displayName: e.target.value })}
                    className="w-full text-[14px] bg-white text-[#0F2137] border border-[#D1D9E0] rounded-lg px-3 py-2 focus:outline-none focus:border-[#0E7C7E] focus:ring-1 focus:ring-[#0E7C7E]"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-[13px] font-medium text-[#0F2137]" htmlFor="applicant-age">
                      Age
                    </label>
                    <label className="flex items-center gap-1.5 text-[12px] text-[#5B6B7B] cursor-pointer hover:text-[#0F2137]">
                      <input
                        id="age-unknown-toggle"
                        type="checkbox"
                        checked={applicant.ageUnknown}
                        onChange={(e) => {
                          const checked = e.target.checked;
                          updateApplicant({
                            ageUnknown: checked,
                            age: checked ? 0 : 30,
                          });
                        }}
                        className="w-3.5 h-3.5 rounded border-[#D1D9E0] text-[#0E7C7E] focus:ring-[#0E7C7E]"
                      />
                      <span>Age unknown</span>
                    </label>
                  </div>
                  <input
                    id="applicant-age"
                    type="number"
                    min={18}
                    max={75}
                    disabled={applicant.ageUnknown}
                    value={applicant.ageUnknown ? '' : applicant.age}
                    onChange={(e) =>
                      updateApplicant({ age: e.target.value ? Number(e.target.value) : 0 })
                    }
                    className="w-full text-[14px] bg-white text-[#0F2137] border border-[#D1D9E0] rounded-lg px-3 py-2 focus:outline-none focus:border-[#0E7C7E] focus:ring-1 focus:ring-[#0E7C7E] disabled:bg-[#F1F5F9] disabled:text-[#5B6B7B]"
                  />
                </div>

                <div>
                  <label
                    className="block text-[13px] font-medium text-[#0F2137] mb-1.5"
                    htmlFor="occupation-select"
                  >
                    Occupation
                  </label>
                  <select
                    id="occupation-select"
                    value={applicant.occupation}
                    onChange={(e) => updateApplicant({ occupation: e.target.value })}
                    className="w-full text-[14px] bg-white text-[#0F2137] border border-[#D1D9E0] rounded-lg px-3 py-2 focus:outline-none focus:border-[#0E7C7E] focus:ring-1 focus:ring-[#0E7C7E] cursor-pointer"
                  >
                    {occupationOptions.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label
                    className="block text-[13px] font-medium text-[#0F2137] mb-1.5"
                    htmlFor="tenure-months"
                  >
                    Months on platform
                  </label>
                  <input
                    id="tenure-months"
                    type="number"
                    min={1}
                    max={48}
                    value={applicant.tenureMonths}
                    onChange={(e) =>
                      updateApplicant({
                        tenureMonths: e.target.value ? Number(e.target.value) : 0,
                      })
                    }
                    className="w-full text-[14px] bg-white text-[#0F2137] border border-[#D1D9E0] rounded-lg px-3 py-2 focus:outline-none focus:border-[#0E7C7E] focus:ring-1 focus:ring-[#0E7C7E]"
                  />
                </div>

                <div className="flex items-center justify-between pt-6">
                  <div>
                    <span className="block text-[13px] font-medium text-[#0F2137]">
                      Multi-platform worker
                    </span>
                    <span className="block text-[12px] text-[#5B6B7B]">
                      Active across two or more gig applications
                    </span>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      id="multi-platform-toggle"
                      type="checkbox"
                      className="sr-only peer"
                      checked={applicant.multiPlatform}
                      onChange={(e) => updateApplicant({ multiPlatform: e.target.checked })}
                    />
                    <div className="w-10 h-5 bg-[#CBD5E1] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#0E7C7E]"></div>
                  </label>
                </div>
              </div>
            </section>

            <hr className="border-t border-[#E2E8F0] m-0" />

            {/* Section 2: Finances */}
            <section style={{ padding: '28px 32px' }}>
              <div className="flex items-center justify-between mb-5">
                <h2 className="text-[18px] font-semibold text-[#0F2137]">2. Finances</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-5 gap-y-4">
                <div>
                  <label
                    className="block text-[13px] font-medium text-[#0F2137] mb-1.5"
                    htmlFor="monthly-income"
                  >
                    Monthly income (₹)
                  </label>
                  <input
                    id="monthly-income"
                    type="number"
                    step={500}
                    value={finances.monthlyIncome}
                    onChange={(e) =>
                      updateFinances({
                        monthlyIncome: e.target.value ? Number(e.target.value) : 0,
                      })
                    }
                    className="w-full text-[14px] bg-white text-[#0F2137] border border-[#D1D9E0] rounded-lg px-3 py-2 focus:outline-none focus:border-[#0E7C7E] focus:ring-1 focus:ring-[#0E7C7E]"
                  />
                </div>

                <div>
                  <label
                    className="block text-[13px] font-medium text-[#0F2137] mb-1.5"
                    htmlFor="monthly-expenses"
                  >
                    Monthly core expenses (₹)
                  </label>
                  <input
                    id="monthly-expenses"
                    type="number"
                    step={500}
                    value={finances.monthlyExpenses}
                    onChange={(e) =>
                      updateFinances({
                        monthlyExpenses: e.target.value ? Number(e.target.value) : 0,
                      })
                    }
                    className="w-full text-[14px] bg-white text-[#0F2137] border border-[#D1D9E0] rounded-lg px-3 py-2 focus:outline-none focus:border-[#0E7C7E] focus:ring-1 focus:ring-[#0E7C7E]"
                  />
                </div>

                <div>
                  <label
                    className="block text-[13px] font-medium text-[#0F2137] mb-1.5"
                    htmlFor="monthly-debt"
                  >
                    Monthly debt / EMI (₹)
                  </label>
                  <input
                    id="monthly-debt"
                    type="number"
                    step={100}
                    value={finances.monthlyDebt}
                    onChange={(e) =>
                      updateFinances({
                        monthlyDebt: e.target.value ? Number(e.target.value) : 0,
                      })
                    }
                    className="w-full text-[14px] bg-white text-[#0F2137] border border-[#D1D9E0] rounded-lg px-3 py-2 focus:outline-none focus:border-[#0E7C7E] focus:ring-1 focus:ring-[#0E7C7E]"
                  />
                </div>

                <div>
                  <label
                    className="block text-[13px] font-medium text-[#0F2137] mb-1.5"
                    htmlFor="liquidity-mean"
                  >
                    Average liquid balance (₹)
                  </label>
                  <input
                    id="liquidity-mean"
                    type="number"
                    step={500}
                    value={finances.liquidityMean}
                    onChange={(e) =>
                      updateFinances({
                        liquidityMean: e.target.value ? Number(e.target.value) : 0,
                      })
                    }
                    className="w-full text-[14px] bg-white text-[#0F2137] border border-[#D1D9E0] rounded-lg px-3 py-2 focus:outline-none focus:border-[#0E7C7E] focus:ring-1 focus:ring-[#0E7C7E]"
                  />
                </div>

                <div>
                  <label
                    className="block text-[13px] font-medium text-[#0F2137] mb-1.5"
                    htmlFor="liquidity-min"
                  >
                    Lowest balance (₹)
                  </label>
                  <input
                    id="liquidity-min"
                    type="number"
                    step={500}
                    value={finances.liquidityMin}
                    onChange={(e) =>
                      updateFinances({
                        liquidityMin: e.target.value ? Number(e.target.value) : 0,
                      })
                    }
                    className="w-full text-[14px] bg-white text-[#0F2137] border border-[#D1D9E0] rounded-lg px-3 py-2 focus:outline-none focus:border-[#0E7C7E] focus:ring-1 focus:ring-[#0E7C7E]"
                  />
                  <span className="block text-[12px] text-[#5B6B7B] mt-1">
                    Must not exceed the average
                  </span>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-[13px] font-medium text-[#0F2137]" htmlFor="vol-slider">
                      Income volatility
                    </label>
                    <span className="text-[13px] font-semibold text-[#0F2137]">
                      {finances.incomeVolatility.toFixed(2)}
                    </span>
                  </div>
                  <input
                    id="vol-slider"
                    type="range"
                    min={0.05}
                    max={0.8}
                    step={0.01}
                    value={finances.incomeVolatility}
                    onChange={(e) =>
                      updateFinances({ incomeVolatility: Number(e.target.value) })
                    }
                    className="w-full h-1.5 bg-[#E2E8F0] rounded-lg cursor-pointer"
                  />
                  <span className="block text-[12px] text-[#5B6B7B] mt-1">
                    Variation of monthly income relative to its average
                  </span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-[#F1F5F9] text-[13px] text-[#5B6B7B]">
                UI hints: Expense ratio {expRatioPct}% · Debt ratio {debtRatioPct}% · Monthly surplus{' '}
                {surplusStr}
              </div>

              <details className="mt-4 pt-2 group">
                <summary className="text-[13px] font-medium text-[#5B6B7B] hover:text-[#0F2137] cursor-pointer flex items-center gap-1 select-none">
                  <span className="material-symbols-outlined text-[16px] transition-transform group-open:rotate-90">
                    chevron_right
                  </span>
                  Trend and seasonality indicators
                </summary>
                <div className="mt-2.5 pl-5 text-[12px] text-[#5B6B7B] space-y-1">
                  <p>{trendText}</p>
                  <p>{seasonText}</p>
                </div>
              </details>
            </section>

            <hr className="border-t border-[#E2E8F0] m-0" />

            {/* Section 3: Evidence available */}
            <section style={{ padding: '28px 32px' }}>
              <div className="flex items-center justify-between mb-5">
                <h2 className="text-[18px] font-semibold text-[#0F2137]">3. Evidence available</h2>
              </div>

              <div className="mb-5">
                <label className="block text-[13px] font-medium text-[#0F2137] mb-2">
                  History duration observed (H)
                </label>
                <div className="grid grid-cols-4 gap-2 bg-[#F1F5F9] p-1 rounded-lg">
                  {historyOptions.map((m) => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => setHistoryDuration(m)}
                      className={clsx(
                        'py-1.5 text-center rounded-md text-[13px] font-medium transition-all',
                        evidence.historyMonths === m
                          ? 'bg-white text-[#0F2137] font-semibold shadow-sm border border-[#E2E8F0]'
                          : 'text-[#5B6B7B] hover:text-[#0F2137]'
                      )}
                    >
                      {m} months
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-5 gap-y-4 mb-5">
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-[13px] font-medium text-[#0F2137]" htmlFor="aa-slider">
                      Account Aggregator (AA) completeness
                    </label>
                    <span className="text-[13px] font-semibold text-[#0F2137]">
                      {Math.round(evidence.aaCompleteness * 100)}%
                    </span>
                  </div>
                  <input
                    id="aa-slider"
                    type="range"
                    min={0}
                    max={100}
                    value={Math.round(evidence.aaCompleteness * 100)}
                    onChange={(e) =>
                      updateEvidence({ aaCompleteness: Number(e.target.value) / 100 })
                    }
                    className="w-full h-1.5 bg-[#E2E8F0] rounded-lg cursor-pointer"
                  />
                  <span className="block text-[12px] text-[#5B6B7B] mt-1">
                    Bank transaction verification depth
                  </span>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-[13px] font-medium text-[#0F2137]" htmlFor="uli-slider">
                      Unified Lending Interface (ULI) completeness
                    </label>
                    <span className="text-[13px] font-semibold text-[#0F2137]">
                      {Math.round(evidence.uliCompleteness * 100)}%
                    </span>
                  </div>
                  <input
                    id="uli-slider"
                    type="range"
                    min={0}
                    max={100}
                    value={Math.round(evidence.uliCompleteness * 100)}
                    onChange={(e) =>
                      updateEvidence({ uliCompleteness: Number(e.target.value) / 100 })
                    }
                    className="w-full h-1.5 bg-[#E2E8F0] rounded-lg cursor-pointer"
                  />
                  <span className="block text-[12px] text-[#5B6B7B] mt-1">
                    Cross-registry verified data
                  </span>
                </div>
              </div>

              <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg p-3.5">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[12px] text-[#5B6B7B]">
                    E = 0.50 · (H / 12) + 0.25 · AA + 0.25 · ULI
                  </span>
                  <span className="text-[13px] font-semibold text-[#0F2137]">
                    Live evidence score:{' '}
                    <strong className="font-bold text-[#0E7C7E]">
                      {evidenceScore.toFixed(3)}
                    </strong>
                    <span
                      className={clsx(
                        'text-[12px] font-medium ml-1.5',
                        evidenceSufficient ? 'text-[#1E8A3E]' : 'text-[#9A6700]'
                      )}
                    >
                      {' '}
                      · {evidenceSufficient ? 'Sufficient' : 'Insufficient'}
                    </span>
                  </span>
                </div>
                <div className="w-full h-2 bg-[#E2E8F0] rounded-full overflow-hidden flex">
                  <div
                    className="h-full bg-[#0E7C7E] transition-all duration-200"
                    style={{ width: `${subH * 100}%` }}
                  />
                  <div
                    className="h-full bg-[#B9770E] transition-all duration-200"
                    style={{ width: `${subAA * 100}%` }}
                  />
                  <div
                    className="h-full bg-[#6B4C9A] transition-all duration-200"
                    style={{ width: `${subULI * 100}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-[12px] text-[#5B6B7B] mt-2">
                  <span>
                    H: <strong className="text-[#0F2137]">{subH.toFixed(3)}</strong>
                  </span>
                  <span>
                    AA: <strong className="text-[#0F2137]">{subAA.toFixed(3)}</strong>
                  </span>
                  <span>
                    ULI: <strong className="text-[#0F2137]">{subULI.toFixed(3)}</strong>
                  </span>
                  <span>
                    Threshold: <strong>0.50</strong>
                  </span>
                </div>
              </div>
            </section>

            <hr className="border-t border-[#E2E8F0] m-0" />

            {/* Section 4: Scheme eligibility */}
            <section style={{ padding: '28px 32px' }}>
              <div className="flex items-center justify-between mb-5">
                <h2 className="text-[18px] font-semibold text-[#0F2137]">4. Scheme eligibility</h2>
              </div>

              <div className="mb-4 text-[12px] text-[#5B6B7B] bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg px-3.5 py-2.5">
                Rules are prototype placeholders, not official criteria.
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-5 gap-y-4 mb-4">
                <div className="bg-white border border-[#E2E8F0] rounded-lg p-3">
                  <span className="block text-[12px] text-[#5B6B7B]">
                    Age &amp; activity summary
                  </span>
                  <span className="block text-[14px] font-semibold text-[#0F2137] mt-0.5">
                    {schemeSummary}
                  </span>
                </div>

                <div className="flex items-center justify-between bg-white border border-[#E2E8F0] rounded-lg p-3">
                  <div>
                    <span className="block text-[13px] font-medium text-[#0F2137]">
                      e-Shram registered
                    </span>
                    <span className="block text-[12px] text-[#5B6B7B]">
                      Context only, does not change the decision
                    </span>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer ml-3">
                    <input
                      id="eshram-toggle"
                      type="checkbox"
                      className="sr-only peer"
                      checked={applicant.eshramRegistered}
                      onChange={(e) => updateApplicant({ eshramRegistered: e.target.checked })}
                    />
                    <div className="w-10 h-5 bg-[#CBD5E1] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#0E7C7E]"></div>
                  </label>
                </div>
              </div>
            </section>

            <hr className="border-t border-[#E2E8F0] m-0" />

            {/* Section 5: Decision mode */}
            <section style={{ padding: '28px 32px' }}>
              <div className="flex items-center justify-between mb-5">
                <h2 className="text-[18px] font-semibold text-[#0F2137]">5. Decision mode</h2>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-5">
                {decisionModes.map((mode) => {
                  const isActive = decisionMode === mode.id;
                  return (
                    <label
                      key={mode.id}
                      className={clsx(
                        'rounded-lg p-3.5 cursor-pointer transition-all flex flex-col justify-between',
                        isActive
                          ? 'border-2 border-[#0E7C7E] bg-[#0E7C7E]/5'
                          : 'border border-[#D1D9E0] hover:border-[#0E7C7E]'
                      )}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <span
                            className={clsx(
                              'text-[14px] font-semibold',
                              isActive ? 'text-[#0E7C7E]' : 'text-[#0F2137]'
                            )}
                          >
                            {mode.title}
                          </span>
                          {mode.recommended && (
                            <span className="text-[11px] font-semibold bg-[#0E7C7E] text-white px-1.5 py-0.5 rounded">
                              Recommended
                            </span>
                          )}
                        </div>
                        <input
                          type="radio"
                          name="decision-mode"
                          value={mode.id}
                          checked={isActive}
                          onChange={() => setDecisionMode(mode.id)}
                          className="text-[#0E7C7E] focus:ring-[#0E7C7E]"
                        />
                      </div>
                      <span className="text-[12px] text-[#5B6B7B]">{mode.desc}</span>
                    </label>
                  );
                })}
              </div>

              <details className="group mb-6">
                <summary className="text-[13px] font-medium text-[#5B6B7B] hover:text-[#0F2137] cursor-pointer flex items-center gap-1 select-none">
                  <span className="material-symbols-outlined text-[16px] transition-transform group-open:rotate-90">
                    chevron_right
                  </span>
                  Thresholds
                </summary>
                <div className="mt-3 pl-5 grid grid-cols-1 sm:grid-cols-2 gap-4 text-[12px] text-[#5B6B7B] bg-[#F8FAFC] border border-[#E2E8F0] p-3 rounded-lg">
                  <div>
                    <span className="block font-medium text-[#0F2137]">Risk cutoff (τ)</span>
                    <span className="text-[#5B6B7B]">25.0% probability of default</span>
                  </div>
                  <div>
                    <span className="block font-medium text-[#0F2137]">Evidence cutoff (τ_E)</span>
                    <span className="text-[#5B6B7B]">0.50 score minimum</span>
                  </div>
                </div>
              </details>

              <div className="pt-2">
                <button
                  type="button"
                  onClick={handleAssess}
                  disabled={loading}
                  className="w-full py-3 px-5 rounded-lg bg-[#0E7C7E] hover:bg-[#0b6567] text-white font-semibold text-[15px] transition-colors flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  <span>{loading ? 'Assessing…' : 'Assess applicant'}</span>
                  <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                </button>
              </div>
            </section>
          </div>

          {/* RIGHT: Sticky Side Panel */}
          <div className="lg:col-span-4 sticky top-24">
            <div className="bg-white rounded-lg border border-[#E2E8F0] p-6 shadow-sm">
              <div className="flex items-center justify-between pb-3.5 mb-5 border-b border-[#E2E8F0]">
                <h3 className="text-[16px] font-bold text-[#0F2137]">Live preview</h3>
                <span className="w-2 h-2 rounded-full bg-[#0E7C7E]"></span>
              </div>

              <div className="mb-6 p-4 rounded-lg bg-[#F8FAFC] border border-[#E2E8F0]">
                <span className="block text-[12px] font-medium text-[#5B6B7B] uppercase tracking-wider mb-1">
                  Evidence score
                </span>
                <div className="flex items-baseline gap-2.5">
                  <span
                    className="font-bold text-[#0F2137] leading-none"
                    style={{ fontSize: '32px' }}
                  >
                    {evidenceScore.toFixed(3)}
                  </span>
                  <span
                    className={clsx(
                      'inline-flex items-center text-[12px] font-medium px-2 py-0.5 rounded',
                      evidenceSufficient
                        ? 'bg-[#EAF5EC] text-[#1E8A3E]'
                        : 'bg-[#FFF4D6] text-[#9A6700]'
                    )}
                  >
                    {evidenceSufficient
                      ? 'Sufficient (score ≥ 0.50)'
                      : 'Insufficient (score < 0.50)'}
                  </span>
                </div>
              </div>

              <div className="space-y-3 mb-6 text-[13px] border-b border-[#E2E8F0] pb-5">
                <div className="flex items-center justify-between">
                  <span className="text-[#5B6B7B]">Risk:</span>
                  <span className="font-medium text-[#5B6B7B]">Available after assessment</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#5B6B7B]">Policy:</span>
                  <span className="font-medium text-[#5B6B7B]">Available after assessment</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#5B6B7B]">Mode:</span>
                  <span className="font-medium text-[#0F2137]">{modeLabels[decisionMode]}</span>
                </div>
              </div>

              <button
                type="button"
                onClick={handleAssess}
                disabled={loading}
                className="w-full py-3 px-4 rounded-lg bg-[#0E7C7E] hover:bg-[#0b6567] text-white font-semibold text-[14px] transition-colors flex items-center justify-center gap-1.5 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                <span>{loading ? 'Assessing…' : 'Assess applicant'}</span>
                <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
