import DashboardLayout from '@/components/layout/DashboardLayout';
import { BarChart3, CheckCircle2, Info } from 'lucide-react';

// Real model results from results/authentic/T1_results.json
const realModels = [
  {
    name: 'XGBoost (Feature Set C)',
    description: 'Gradient boosted trees on 12 features (conventional + gig-specific). Trained on Home Credit (307,511 applicants).',
    auc: 0.7568,
    prauc: 0.2447,
    brier: 0.0678,
    ece: 0.00247,
    gini: 0.5136,
    ks: 0.381,
    status: 'deployed',
    dataset: 'Home Credit Default Risk',
    split: '60/20/20 stratified',
  },
  {
    name: 'Logistic Regression (Feature Set C)',
    description: 'L2-regularised logistic regression with WoE-style winsorisation + StandardScaler. Same 12 features.',
    auc: 0.7383,
    prauc: 0.2213,
    brier: 0.0689,
    ece: 0.00240,
    gini: 0.4766,
    ks: 0.350,
    status: 'available',
    dataset: 'Home Credit Default Risk',
    split: '60/20/20 stratified',
  },
];

const statusStyle: Record<string, string> = {
  deployed: 'bg-green-100 text-green-800',
  available: 'bg-blue-100 text-blue-800',
};

export default function ModelsPage() {
  return (
    <DashboardLayout>
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h1 className="font-bold text-[#0F2137] tracking-tight" style={{ fontSize: '28px' }}>
            Models
          </h1>
          <p className="text-[15px] text-[#5B6B7B] mt-1.5">
            Verified model results from T1 experiment — Home Credit Default Risk dataset (307,511 applicants).
          </p>
        </div>

        {/* Disclaimer banner */}
        <div className="flex items-start gap-3 p-4 mb-6 rounded-lg border border-[#B9770E33] bg-[#FDF8F0]">
          <Info className="h-5 w-5 text-[#B9770E] flex-shrink-0 mt-0.5" />
          <p className="text-[13px] text-[#8A5D00]">
            These results are from the authentic T1 experiment. The synthetic experiments (T2-T9)
            used 10 seeds × 2 DGPs — see <code>research/EXPERIMENT_RESULTS.md</code> for full tables.
            Calibration slope uses logistic regression on logit(p) — ideal value is 1.0.
          </p>
        </div>

        {/* Model cards */}
        <div className="space-y-5">
          {realModels.map((m) => (
            <div key={m.name} className="bg-white rounded-lg border border-[#E2E8F0] p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 flex items-center justify-center rounded-md bg-[#0E7C7E1A]">
                    <BarChart3 className="h-5 w-5 text-[#0E7C7E]" />
                  </div>
                  <div>
                    <h2 className="text-[16px] font-semibold text-[#0F2137]">{m.name}</h2>
                    <p className="text-[13px] text-[#5B6B7B] mt-0.5">{m.description}</p>
                  </div>
                </div>
                <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-full ${statusStyle[m.status]}`}>
                  {m.status}
                </span>
              </div>

              {/* Metrics grid */}
              <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
                {[
                  { label: 'ROC-AUC', value: m.auc.toFixed(4) },
                  { label: 'PR-AUC', value: m.prauc.toFixed(4) },
                  { label: 'Brier', value: m.brier.toFixed(4) },
                  { label: 'ECE', value: m.ece.toFixed(5) },
                  { label: 'Gini', value: m.gini.toFixed(4) },
                  { label: 'KS', value: m.ks.toFixed(3) },
                ].map((metric) => (
                  <div key={metric.label} className="p-3 bg-[#F8FAFC] rounded-lg text-center">
                    <div className="text-[11px] text-[#5B6B7B] mb-1">{metric.label}</div>
                    <div className="font-mono text-[15px] font-bold text-[#0F2137]">{metric.value}</div>
                  </div>
                ))}
              </div>

              {/* Dataset info */}
              <div className="mt-4 flex items-center gap-4 text-[12px] text-[#5B6B7B]">
                <span className="flex items-center gap-1">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#3FB950]" />
                  Dataset: {m.dataset}
                </span>
                <span>Split: {m.split}</span>
                <span>Platt calibration on validation set</span>
              </div>
            </div>
          ))}
        </div>

        {/* Calibration note */}
        <div className="mt-6 p-4 rounded-lg border border-[#E2E8F0] bg-[#F8FAFC]">
          <h3 className="text-[14px] font-semibold text-[#0F2137] mb-2">Note on calibration</h3>
          <p className="text-[13px] text-[#5B6B7B]">
            ECE ≈ 0.0024 (very low) reflects good bin-level calibration, but the calibration slope ≈ 0.075
            indicates predicted probabilities are compressed around the base rate (8%). This is a known
            limitation caused by missing bureau features — the model ranks applicants well (AUC 0.757)
            but absolute PD values should be interpreted with caution.
          </p>
        </div>
      </div>
    </DashboardLayout>
  );
}
