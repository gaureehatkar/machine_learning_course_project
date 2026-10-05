import DashboardLayout from '@/components/layout/DashboardLayout';
import {
  Upload,
  RefreshCw,
  Cpu,
  Rocket,
  Target,
  TrendingUp,
  ArrowUpRight,
  ArrowDownRight,
  MoreHorizontal,
  Eye,
  Download,
  Archive,
  Play,
  Pause,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';

type ModelStatus = 'deployed' | 'training' | 'archived';

interface MLModel {
  id: string;
  name: string;
  type: string;
  version: string;
  accuracy: number;
  status: ModelStatus;
  lastTrained: string;
}

const mockModels: MLModel[] = [
  {
    id: 'mdl-001',
    name: 'Risk Scoring XGBoost',
    type: 'XGBoost',
    version: 'v2.4.1',
    accuracy: 0.892,
    status: 'deployed',
    lastTrained: '2026-09-22',
  },
  {
    id: 'mdl-002',
    name: 'Income Stability LogReg',
    type: 'Logistic Regression',
    version: 'v1.8.0',
    accuracy: 0.784,
    status: 'deployed',
    lastTrained: '2026-09-18',
  },
  {
    id: 'mdl-003',
    name: 'Evidence Quality Random Forest',
    type: 'Random Forest',
    version: 'v3.1.2',
    accuracy: 0.847,
    status: 'deployed',
    lastTrained: '2026-09-15',
  },
  {
    id: 'mdl-004',
    name: 'Volatility Stress Neural Net',
    type: 'Neural Network',
    version: 'v0.9.3',
    accuracy: 0.815,
    status: 'training',
    lastTrained: '2026-09-28',
  },
  {
    id: 'mdl-005',
    name: 'Policy Eligibility Gradient Boost',
    type: 'Gradient Boosting',
    version: 'v1.2.0',
    accuracy: 0.913,
    status: 'deployed',
    lastTrained: '2026-09-10',
  },
  {
    id: 'mdl-006',
    name: 'Legacy Fraud Detection SVM',
    type: 'SVM',
    version: 'v0.4.2',
    accuracy: 0.721,
    status: 'archived',
    lastTrained: '2026-06-03',
  },
];

const accuracyTrendData = [
  { week: 'W1', risk: 0.841, evidence: 0.802, policy: 0.878 },
  { week: 'W2', risk: 0.855, evidence: 0.815, policy: 0.884 },
  { week: 'W3', risk: 0.863, evidence: 0.828, policy: 0.891 },
  { week: 'W4', risk: 0.878, evidence: 0.836, policy: 0.902 },
  { week: 'W5', risk: 0.884, evidence: 0.841, policy: 0.905 },
  { week: 'W6', risk: 0.892, evidence: 0.847, policy: 0.913 },
];

const modelTypeDistribution = [
  { name: 'XGBoost', count: 2, color: '#0E7C7E' },
  { name: 'Logistic Reg.', count: 1, color: '#2E5EAA' },
  { name: 'Random Forest', count: 1, color: '#B9770E' },
  { name: 'Neural Net', count: 1, color: '#6B4C9A' },
  { name: 'Gradient Boost', count: 1, color: '#159A9C' },
];

function formatDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function ModelStatusBadge({ status }: { status: ModelStatus }) {
  const styles: Record<ModelStatus, string> = {
    deployed: 'bg-status-approve/surface text-status-approve border-status-approve/30',
    training: 'bg-status-review/surface text-status-review border-status-review/30',
    archived: 'bg-[#F1F5F9] text-text-muted border-[#CBD5E1]',
  };
  const labels: Record<ModelStatus, string> = {
    deployed: 'Deployed',
    training: 'Training',
    archived: 'Archived',
  };
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${styles[status]}`}>
      {labels[status]}
    </span>
  );
}

export default function ModelsPage() {
  const totalModels = mockModels.length;
  const deployedModels = mockModels.filter((m) => m.status === 'deployed').length;
  const avgAccuracy =
    mockModels.reduce((sum, m) => sum + m.accuracy, 0) / mockModels.length;
  const trainedThisMonth = mockModels.filter((m) => {
    const d = new Date(m.lastTrained);
    return d.getMonth() === new Date('2026-09-01').getMonth();
  }).length;

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-8">
          <div className="flex-1">
            <h1 className="font-bold tracking-tight text-text-primary" style={{ fontSize: '28px' }}>
              ML Models
            </h1>
            <p className="mt-2 text-[#5B6B7B]">
              Manage, deploy, and monitor machine learning models powering the SynthGigCredit decision engine across risk, evidence, and policy layers.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button className="inline-flex items-center gap-2 rounded-full border border-[#E2E8F0] bg-white px-4 py-2 text-sm font-medium text-text-secondary hover:bg-page-bg transition-colors">
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
            <button className="inline-flex items-center gap-2 rounded-full bg-[#0E7C7E] px-4 py-2 text-sm font-medium text-white hover:bg-[#0b6567] transition-colors">
              <Upload className="h-4 w-4" />
              Upload model
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          <div className="relative overflow-hidden rounded-lg border border-[#E2E8F0] bg-white p-5">
            <div className="absolute left-5 top-5 flex h-9 w-9 items-center justify-center rounded-md bg-[#0E7C7E]/10">
              <Cpu className="h-5 w-5 text-[#0E7C7E]" />
            </div>
            <div className="ml-12">
              <p className="text-sm text-text-secondary">Total models</p>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-text-primary">{totalModels}</span>
                <span className="inline-flex items-center gap-0.5 text-xs font-semibold text-status-approve">
                  <ArrowUpRight className="h-3.5 w-3.5" />
                  +2
                </span>
              </div>
              <p className="mt-1 text-xs text-text-muted">In registry</p>
            </div>
          </div>

          <div className="relative overflow-hidden rounded-lg border border-[#E2E8F0] bg-white p-5">
            <div className="absolute left-5 top-5 flex h-9 w-9 items-center justify-center rounded-md bg-[#2E5EAA]/10">
              <Rocket className="h-5 w-5 text-[#2E5EAA]" />
            </div>
            <div className="ml-12">
              <p className="text-sm text-text-secondary">Deployed models</p>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-text-primary">{deployedModels}</span>
                <span className="inline-flex items-center gap-0.5 text-xs font-semibold text-status-approve">
                  <ArrowUpRight className="h-3.5 w-3.5" />
                  +1
                </span>
              </div>
              <p className="mt-1 text-xs text-text-muted">Live in production</p>
            </div>
          </div>

          <div className="relative overflow-hidden rounded-lg border border-[#E2E8F0] bg-white p-5">
            <div className="absolute left-5 top-5 flex h-9 w-9 items-center justify-center rounded-md bg-[#B9770E]/10">
              <Target className="h-5 w-5 text-[#B9770E]" />
            </div>
            <div className="ml-12">
              <p className="text-sm text-text-secondary">Avg accuracy</p>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-text-primary">{(avgAccuracy * 100).toFixed(1)}%</span>
                <span className="inline-flex items-center gap-0.5 text-xs font-semibold text-status-approve">
                  <ArrowUpRight className="h-3.5 w-3.5" />
                  +3.2%
                </span>
              </div>
              <p className="mt-1 text-xs text-text-muted">Cross-model mean</p>
            </div>
          </div>

          <div className="relative overflow-hidden rounded-lg border border-[#E2E8F0] bg-white p-5">
            <div className="absolute left-5 top-5 flex h-9 w-9 items-center justify-center rounded-md bg-[#6B4C9A]/10">
              <TrendingUp className="h-5 w-5 text-[#6B4C9A]" />
            </div>
            <div className="ml-12">
              <p className="text-sm text-text-secondary">Trained this month</p>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-text-primary">{trainedThisMonth}</span>
                <span className="inline-flex items-center gap-0.5 text-xs font-semibold text-status-decline">
                  <ArrowDownRight className="h-3.5 w-3.5" />
                  -1
                </span>
              </div>
              <p className="mt-1 text-xs text-text-muted">September 2026</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3 mb-8">
          <div className="rounded-lg border border-[#E2E8F0] bg-white p-5 lg:col-span-2">
            <div className="mb-4">
              <h2 className="text-base font-semibold text-text-primary">Accuracy trend by domain</h2>
              <p className="text-sm text-text-secondary">6-week rolling model performance</p>
            </div>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={accuracyTrendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
                <XAxis
                  dataKey="week"
                  tick={{ fontSize: 12, fill: '#5B6B7B' }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: '#5B6B7B' }}
                  axisLine={false}
                  tickLine={false}
                  domain={[0.75, 0.95]}
                  tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                />
                <Tooltip
                  formatter={(value: any) => [`${(value * 100).toFixed(1)}%`, undefined]}
                  contentStyle={{
                    borderRadius: '8px',
                    border: '1px solid #E2E8F0',
                    boxShadow: '0 4px 6px -1px rgba(15, 33, 55, 0.08)',
                  }}
                />
                <Legend iconType="circle" wrapperStyle={{ paddingTop: 12 }} />
                <Line
                  type="monotone"
                  dataKey="risk"
                  name="Risk"
                  stroke="#2E5EAA"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#2E5EAA' }}
                  activeDot={{ r: 5 }}
                />
                <Line
                  type="monotone"
                  dataKey="evidence"
                  name="Evidence"
                  stroke="#B9770E"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#B9770E' }}
                  activeDot={{ r: 5 }}
                />
                <Line
                  type="monotone"
                  dataKey="policy"
                  name="Policy"
                  stroke="#6B4C9A"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#6B4C9A' }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="rounded-lg border border-[#E2E8F0] bg-white p-5">
            <div className="mb-4">
              <h2 className="text-base font-semibold text-text-primary">Model type distribution</h2>
              <p className="text-sm text-text-secondary">Registry composition</p>
            </div>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart
                data={modelTypeDistribution}
                layout="vertical"
                margin={{ top: 5, right: 20, left: 5, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" horizontal={false} />
                <XAxis
                  type="number"
                  tick={{ fontSize: 12, fill: '#5B6B7B' }}
                  axisLine={false}
                  tickLine={false}
                  allowDecimals={false}
                />
                <YAxis
                  dataKey="name"
                  type="category"
                  width={100}
                  tick={{ fontSize: 12, fill: '#486581' }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: '8px',
                    border: '1px solid #E2E8F0',
                    boxShadow: '0 4px 6px -1px rgba(15, 33, 55, 0.08)',
                  }}
                />
                <Bar dataKey="count" radius={[0, 6, 6, 0]} barSize={20}>
                  {modelTypeDistribution.map((entry, index) => (
                    <rect key={`bar-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-lg border border-[#E2E8F0] bg-white">
          <div className="flex items-center justify-between p-5 border-b border-[#E2E8F0]">
            <div>
              <h2 className="text-base font-semibold text-text-primary">Model registry</h2>
              <p className="text-sm text-text-secondary mt-0.5">All models across risk, evidence, and policy layers</p>
            </div>
            <div className="flex items-center gap-2">
              <div className="inline-flex items-center rounded-full border border-[#E2E8F0] bg-page-bg p-0.5 text-xs font-medium">
                <button className="rounded-full bg-white px-3 py-1 text-text-primary shadow-sm">
                  All ({totalModels})
                </button>
                <button className="rounded-full px-3 py-1 text-text-secondary hover:text-text-primary">
                  Deployed ({deployedModels})
                </button>
                <button className="rounded-full px-3 py-1 text-text-secondary hover:text-text-primary">
                  Archived ({mockModels.filter((m) => m.status === 'archived').length})
                </button>
              </div>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#E2E8F0] bg-[#F6F8FA]/50">
                  <th className="sticky top-0 px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Name
                  </th>
                  <th className="sticky top-0 px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Type
                  </th>
                  <th className="sticky top-0 px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Version
                  </th>
                  <th className="sticky top-0 px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Accuracy
                  </th>
                  <th className="sticky top-0 px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Status
                  </th>
                  <th className="sticky top-0 px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Last trained
                  </th>
                  <th className="sticky top-0 px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0]">
                {mockModels.map((model) => (
                  <tr key={model.id} className="hover:bg-[#F6F8FA]/40 transition-colors">
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-3">
                        <div
                          className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg"
                          style={{
                            backgroundColor:
                              model.type === 'XGBoost' || model.type === 'Gradient Boosting'
                                ? '#0E7C7E1A'
                                : model.type === 'Logistic Regression'
                                  ? '#2E5EAA1A'
                                  : model.type === 'Random Forest' || model.type === 'SVM'
                                    ? '#B9770E1A'
                                    : '#6B4C9A1A',
                          }}
                        >
                          <Cpu
                            className="h-4.5 w-4.5"
                            style={{
                              color:
                                model.type === 'XGBoost' || model.type === 'Gradient Boosting'
                                  ? '#0E7C7E'
                                  : model.type === 'Logistic Regression'
                                    ? '#2E5EAA'
                                    : model.type === 'Random Forest' || model.type === 'SVM'
                                      ? '#B9770E'
                                      : '#6B4C9A',
                              width: '18px',
                              height: '18px',
                            }}
                          />
                        </div>
                        <div className="min-w-0">
                          <div className="text-sm font-medium text-text-primary truncate max-w-xs">
                            {model.name}
                          </div>
                          <div className="text-xs text-text-muted font-mono">{model.id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3.5 text-sm text-text-secondary">{model.type}</td>
                    <td className="px-5 py-3.5">
                      <span className="inline-flex items-center rounded-md border border-[#E2E8F0] bg-page-bg px-2 py-0.5 font-mono text-xs text-text-secondary">
                        {model.version}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-2.5">
                        <div className="w-20 h-1.5 rounded-full bg-[#E2E8F0] overflow-hidden">
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${model.accuracy * 100}%`,
                              backgroundColor:
                                model.accuracy >= 0.85
                                  ? '#0E7C7E'
                                  : model.accuracy >= 0.75
                                    ? '#B9770E'
                                    : '#CF222E',
                            }}
                          />
                        </div>
                        <span className="tabular-nums text-sm font-semibold text-text-primary">
                          {(model.accuracy * 100).toFixed(1)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      <ModelStatusBadge status={model.status} />
                    </td>
                    <td className="px-5 py-3.5 text-sm text-text-secondary">
                      {formatDate(model.lastTrained)}
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          className="inline-flex h-8 w-8 items-center justify-center rounded-md text-text-muted hover:bg-page-bg hover:text-action-primary transition-colors"
                          title="View details"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <button
                          className="inline-flex h-8 w-8 items-center justify-center rounded-md text-text-muted hover:bg-page-bg hover:text-action-primary transition-colors"
                          title="Download artifact"
                        >
                          <Download className="h-4 w-4" />
                        </button>
                        {model.status === 'deployed' ? (
                          <button
                            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-text-muted hover:bg-page-bg hover:text-status-review transition-colors"
                            title="Pause deployment"
                          >
                            <Pause className="h-4 w-4" />
                          </button>
                        ) : model.status === 'training' ? (
                          <button
                            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-text-muted hover:bg-page-bg hover:text-status-decline transition-colors"
                            title="Stop training"
                          >
                            <Pause className="h-4 w-4" />
                          </button>
                        ) : (
                          <button
                            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-text-muted hover:bg-page-bg hover:text-action-primary transition-colors"
                            title="Redeploy"
                          >
                            <Play className="h-4 w-4" />
                          </button>
                        )}
                        {model.status !== 'archived' && (
                          <button
                            className="inline-flex h-8 w-8 items-center justify-center rounded-md text-text-muted hover:bg-page-bg hover:text-status-decline transition-colors"
                            title="Archive"
                          >
                            <Archive className="h-4 w-4" />
                          </button>
                        )}
                        <button
                          className="inline-flex h-8 w-8 items-center justify-center rounded-md text-text-muted hover:bg-page-bg hover:text-text-primary transition-colors"
                          title="More actions"
                        >
                          <MoreHorizontal className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between border-t border-[#E2E8F0] px-5 py-3.5">
            <p className="text-sm text-text-muted">
              Showing <span className="font-medium text-text-secondary">{mockModels.length}</span> of{' '}
              <span className="font-medium text-text-secondary">{mockModels.length}</span> models
            </p>
            <div className="flex items-center gap-2">
              <button className="inline-flex items-center rounded-md border border-[#E2E8F0] bg-white px-3 py-1.5 text-sm font-medium text-text-muted hover:text-text-secondary hover:bg-page-bg transition-colors">
                Previous
              </button>
              <button className="inline-flex h-8 w-8 items-center justify-center rounded-md bg-[#0E7C7E] text-sm font-semibold text-white">
                1
              </button>
              <button className="inline-flex h-8 w-8 items-center justify-center rounded-md text-sm font-medium text-text-secondary hover:bg-page-bg transition-colors">
                2
              </button>
              <button className="inline-flex items-center rounded-md border border-[#E2E8F0] bg-white px-3 py-1.5 text-sm font-medium text-text-secondary hover:bg-page-bg transition-colors">
                Next
              </button>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
