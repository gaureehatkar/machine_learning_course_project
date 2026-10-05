import DashboardLayout from '@/components/layout/DashboardLayout';
import {
  Upload,
  RefreshCw,
  Cpu,
  Rocket,
  Target,
  TrendingUp,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

type ModelStatus = 'available' | 'not_trained' | 'heuristic_fallback';

interface MLModel {
  id: string;
  name: string;
  type: string;
  featureSet: string;
  version: string;
  rocAuc: number | null;
  prAuc: number | null;
  brier: number | null;
  status: ModelStatus;
  lastTrained: string | null;
  artifactPath: string;
}

// Real models from the SynthGigCredit project
// Metrics sourced from results/authentic/T1_results.json (Home Credit T1 experiment)
const realModels: MLModel[] = [
  {
    id: 'xgb-c',
    name: 'XGBoost — Feature Set C',
    type: 'XGBoost',
    featureSet: 'C (12 features: A∪B)',
    version: '1.0 (T1)',
    rocAuc: 0.7568,
    prAuc: 0.2447,
    brier: 0.0678,
    status: 'not_trained',
    lastTrained: null,
    artifactPath: 'results/authentic/xgb_c_model.pkl',
  },
  {
    id: 'lr-c',
    name: 'Logistic Regression — Feature Set C',
    type: 'Logistic Regression',
    featureSet: 'C (12 features: A∪B)',
    version: '1.0 (T1)',
    rocAuc: 0.7383,
    prAuc: 0.2213,
    brier: 0.0689,
    status: 'not_trained',
    lastTrained: null,
    artifactPath: 'results/authentic/lr_c_model.pkl',
  },
  {
    id: 'xgb-a',
    name: 'XGBoost — Feature Set A',
    type: 'XGBoost',
    featureSet: 'A (7 conventional features)',
    version: '1.0 (ablation)',
    rocAuc: null,
    prAuc: null,
    brier: null,
    status: 'not_trained',
    lastTrained: null,
    artifactPath: 'results/synthetic/xgb_a_model.pkl',
  },
  {
    id: 'lr-a',
    name: 'Logistic Regression — Feature Set A',
    type: 'Logistic Regression',
    featureSet: 'A (7 conventional features)',
    version: '1.0 (ablation)',
    rocAuc: null,
    prAuc: null,
    brier: null,
    status: 'not_trained',
    lastTrained: null,
    artifactPath: 'results/synthetic/lr_a_model.pkl',
  },
  {
    id: 'xgb-b',
    name: 'XGBoost — Feature Set B',
    type: 'XGBoost',
    featureSet: 'B (5 alternative features)',
    version: '1.0 (ablation)',
    rocAuc: null,
    prAuc: null,
    brier: null,
    status: 'not_trained',
    lastTrained: null,
    artifactPath: 'results/synthetic/xgb_b_model.pkl',
  },
  {
    id: 'lr-b',
    name: 'Logistic Regression — Feature Set B',
    type: 'Logistic Regression',
    featureSet: 'B (5 alternative features)',
    version: '1.0 (ablation)',
    rocAuc: null,
    prAuc: null,
    brier: null,
    status: 'not_trained',
    lastTrained: null,
    artifactPath: 'results/synthetic/lr_b_model.pkl',
  },
];

// T1 authentic results — from results/authentic/T1_results.json
const t1MetricsData = [
  { model: 'XGBoost-C', rocAuc: 0.7568, prAuc: 0.2447, brier: 0.0678 },
  { model: 'LR-C',      rocAuc: 0.7383, prAuc: 0.2213, brier: 0.0689 },
];

const modelTypeDistribution = [
  { name: 'XGBoost', count: 3, color: '#0E7C7E' },
  { name: 'Logistic Reg.', count: 3, color: '#2E5EAA' },
];

function ModelStatusBadge({ status }: { status: ModelStatus }) {
  const styles: Record<ModelStatus, string> = {
    available:            'bg-status-approve/surface text-status-approve border-status-approve/30',
    not_trained:          'bg-[#F1F5F9] text-text-muted border-[#CBD5E1]',
    heuristic_fallback:   'bg-status-review/surface text-status-review border-status-review/30',
  };
  const labels: Record<ModelStatus, string> = {
    available:          'Artifact available',
    not_trained:        'Not trained yet',
    heuristic_fallback: 'Heuristic fallback',
  };
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${styles[status]}`}>
      {labels[status]}
    </span>
  );
}

export default function ModelsPage() {
  const totalModels = realModels.length;
  const availableModels = realModels.filter((m) => m.status === 'available').length;
  const t1XgbAuc = 0.7568;
  const t1LrAuc = 0.7383;

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-8">
          <div className="flex-1">
            <h1 className="font-bold tracking-tight text-text-primary" style={{ fontSize: '28px' }}>
              ML Models
            </h1>
            <p className="mt-2 text-[#5B6B7B]">
              LR and XGBoost models for risk scoring (feature sets A, B, C). Train artifacts
              with <code className="text-xs bg-[#F1F5F9] px-1 py-0.5 rounded">python -m experiments.authentic.run</code> and
              save to <code className="text-xs bg-[#F1F5F9] px-1 py-0.5 rounded">results/authentic/</code>.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button disabled className="inline-flex items-center gap-2 rounded-full border border-[#E2E8F0] bg-[#F6F8FA] px-4 py-2 text-sm font-medium text-text-muted cursor-not-allowed" title="Training is run via CLI — see experiments/authentic/run.py">
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
            <button disabled className="inline-flex items-center gap-2 rounded-full bg-[#CBD5E1] px-4 py-2 text-sm font-medium text-white cursor-not-allowed" title="Upload not supported — use CLI training">
              <Upload className="h-4 w-4" />
              Upload model
            </button>
          </div>
        </div>

        {/* Notice banner */}
        <div className="mb-6 rounded-lg border border-[#E3B341]/40 bg-[#FFF9E6] px-4 py-3 text-sm text-[#92600A]">
          <strong>Note:</strong> Training and deployment are CLI operations, not UI actions. The buttons above are
          disabled. To train models, run <code className="text-xs bg-[#FFF0C0] px-1 rounded">make generate</code> then{' '}
          <code className="text-xs bg-[#FFF0C0] px-1 rounded">python -m experiments.authentic.run --config configs/models.yaml</code>.
          Artifact paths are shown in the table below.
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          <div className="relative overflow-hidden rounded-lg border border-[#E2E8F0] bg-white p-5">
            <div className="absolute left-5 top-5 flex h-9 w-9 items-center justify-center rounded-md bg-[#0E7C7E]/10">
              <Cpu className="h-5 w-5 text-[#0E7C7E]" />
            </div>
            <div className="ml-12">
              <p className="text-sm text-text-secondary">Total models</p>
              <p className="text-2xl font-bold text-text-primary mt-1">{totalModels}</p>
              <p className="mt-1 text-xs text-text-muted">LR + XGBoost × 3 feature sets</p>
            </div>
          </div>
          <div className="relative overflow-hidden rounded-lg border border-[#E2E8F0] bg-white p-5">
            <div className="absolute left-5 top-5 flex h-9 w-9 items-center justify-center rounded-md bg-[#2E5EAA]/10">
              <Rocket className="h-5 w-5 text-[#2E5EAA]" />
            </div>
            <div className="ml-12">
              <p className="text-sm text-text-secondary">Artifact available</p>
              <p className="text-2xl font-bold text-text-primary mt-1">{availableModels}</p>
              <p className="mt-1 text-xs text-text-muted">Trained .pkl files present</p>
            </div>
          </div>
          <div className="relative overflow-hidden rounded-lg border border-[#E2E8F0] bg-white p-5">
            <div className="absolute left-5 top-5 flex h-9 w-9 items-center justify-center rounded-md bg-[#B9770E]/10">
              <Target className="h-5 w-5 text-[#B9770E]" />
            </div>
            <div className="ml-12">
              <p className="text-sm text-text-secondary">XGBoost-C ROC-AUC</p>
              <p className="text-2xl font-bold text-text-primary mt-1">{t1XgbAuc}</p>
              <p className="mt-1 text-xs text-text-muted">T1 Home Credit (authentic)</p>
            </div>
          </div>
          <div className="relative overflow-hidden rounded-lg border border-[#E2E8F0] bg-white p-5">
            <div className="absolute left-5 top-5 flex h-9 w-9 items-center justify-center rounded-md bg-[#6B4C9A]/10">
              <TrendingUp className="h-5 w-5 text-[#6B4C9A]" />
            </div>
            <div className="ml-12">
              <p className="text-sm text-text-secondary">LR-C ROC-AUC</p>
              <p className="text-2xl font-bold text-text-primary mt-1">{t1LrAuc}</p>
              <p className="mt-1 text-xs text-text-muted">T1 Home Credit (authentic)</p>
            </div>
          </div>
        </div>

        {/* T1 Results Panel */}
        <div className="rounded-lg border border-[#E2E8F0] bg-white p-5 mb-8">
          <div className="mb-4">
            <h2 className="text-base font-semibold text-text-primary">T1 Authentic Experiment Results</h2>
            <p className="text-sm text-text-secondary">Source: <code className="text-xs bg-[#F1F5F9] px-1 rounded">results/authentic/T1_results.json</code> — Home Credit application_train.csv</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#E2E8F0] bg-[#F6F8FA]">
                  <th className="px-4 py-2 text-left text-xs font-semibold text-text-muted uppercase">Model</th>
                  <th className="px-4 py-2 text-left text-xs font-semibold text-text-muted uppercase">ROC-AUC</th>
                  <th className="px-4 py-2 text-left text-xs font-semibold text-text-muted uppercase">PR-AUC</th>
                  <th className="px-4 py-2 text-left text-xs font-semibold text-text-muted uppercase">Brier Score</th>
                  <th className="px-4 py-2 text-left text-xs font-semibold text-text-muted uppercase">Prevalence</th>
                </tr>
              </thead>
              <tbody>
                {t1MetricsData.map((row) => (
                  <tr key={row.model} className="border-b border-[#F1F5F9]">
                    <td className="px-4 py-2 font-medium text-text-primary">{row.model}</td>
                    <td className="px-4 py-2 tabular-nums font-semibold text-[#0E7C7E]">{row.rocAuc.toFixed(4)}</td>
                    <td className="px-4 py-2 tabular-nums">{row.prAuc.toFixed(4)}</td>
                    <td className="px-4 py-2 tabular-nums">{row.brier.toFixed(4)}</td>
                    <td className="px-4 py-2 tabular-nums">8.07%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Model Registry */}
        <div className="rounded-lg border border-[#E2E8F0] bg-white">
          <div className="flex items-center justify-between p-5 border-b border-[#E2E8F0]">
            <div>
              <h2 className="text-base font-semibold text-text-primary">Model registry</h2>
              <p className="text-sm text-text-secondary mt-0.5">All LR + XGBoost models across feature sets A, B, C</p>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#E2E8F0] bg-[#F6F8FA]/50">
                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">Name</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">Type</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">Feature Set</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">ROC-AUC (T1)</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">Status</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">Artifact path</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0]">
                {realModels.map((model) => (
                  <tr key={model.id} className="hover:bg-[#F6F8FA]/40 transition-colors">
                    <td className="px-5 py-3.5">
                      <div className="text-sm font-medium text-text-primary">{model.name}</div>
                      <div className="text-xs text-text-muted font-mono">{model.id}</div>
                    </td>
                    <td className="px-5 py-3.5 text-sm text-text-secondary">{model.type}</td>
                    <td className="px-5 py-3.5 text-xs text-text-secondary font-mono">{model.featureSet}</td>
                    <td className="px-5 py-3.5 tabular-nums text-sm font-semibold text-text-primary">
                      {model.rocAuc !== null ? model.rocAuc.toFixed(4) : <span className="text-text-muted text-xs">—</span>}
                    </td>
                    <td className="px-5 py-3.5">
                      <ModelStatusBadge status={model.status} />
                    </td>
                    <td className="px-5 py-3.5 font-mono text-xs text-text-muted">{model.artifactPath}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-5 py-3 border-t border-[#E2E8F0]">
            <p className="text-xs text-[#9AABB7]">
              Train/Deploy/Archive actions are CLI operations. See <code>experiments/authentic/run.py</code>.
              ROC-AUC metrics for sets A and B available after running ablation experiments.
            </p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
