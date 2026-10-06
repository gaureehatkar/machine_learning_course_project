import { useMemo, useState } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import {
  Upload,
  Database,
  Table2,
  CheckCircle2,
  Loader2,
  XCircle,
  Filter,
  Search,
  MoreHorizontal,
  Download,
  Trash2,
  Eye,
  FileSpreadsheet,
  FileText,
  Activity,
  ShieldCheck,
  AlertTriangle,
  BarChart3,
  ArrowUpRight,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  Legend,
} from 'recharts';

type DatasetStatus = 'ready' | 'processing' | 'failed';
type DatasetType = 'Authentic' | 'Synthetic';

interface DatasetRow {
  id: string;
  name: string;
  type: DatasetType;
  rows: number;
  columns: number;
  status: DatasetStatus;
  uploadedAt: string;
  size: string;
  sizeBytes: number;
}

// Only DS-001 and DS-002 actually exist in the project.
// DS-003 through DS-006 are placeholders — not real datasets.
const mockDatasets: DatasetRow[] = [
  {
    id: 'DS-001',
    name: 'Home Credit Default Risk (authentic)',
    type: 'Authentic',
    rows: 307511,
    columns: 122,
    status: 'ready',
    uploadedAt: '2026-01-15T09:30:00Z',
    size: '~168 MB',
    sizeBytes: 168400000,
  },
  {
    id: 'DS-002',
    name: 'Afsharinia & Gurtoo Gig-Worker Survey (grounding)',
    type: 'Authentic',
    rows: 2830,
    columns: 30,
    status: 'ready',
    uploadedAt: '2026-01-15T09:30:00Z',
    size: '~1 MB',
    sizeBytes: 1000000,
  },
  {
    id: 'DS-003',
    name: 'SynthGigCredit-IN-v1 (generated — run make generate)',
    type: 'Synthetic',
    rows: 0,
    columns: 23,
    status: 'processing',
    uploadedAt: '',
    size: '—',
    sizeBytes: 0,
  },
];

const healthMetricsData = [
  { metric: 'Completeness', authentic: 94, synthetic: 98 },
  { metric: 'Consistency', authentic: 88, synthetic: 95 },
  { metric: 'Uniqueness', authentic: 96, synthetic: 92 },
  { metric: 'Timeliness', authentic: 82, synthetic: 99 },
  { metric: 'Validity', authentic: 91, synthetic: 97 },
];

const qualityTrendData = Array.from({ length: 8 }, (_, i) => {
  const months = ['Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'];
  return {
    month: months[i],
    score: 78 + i * 1.5 + (Math.random() * 4 - 2),
  };
});

function formatNumber(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1).replace(/\.0$/, '') + 'k';
  return n.toLocaleString();
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function StatusBadge({ status }: { status: DatasetStatus }) {
  const config = {
    ready: {
      surface: 'bg-[#EAF5EC]',
      border: 'border-[#3FB950]',
      text: 'text-[#0A3615]',
      label: 'READY',
      Icon: CheckCircle2,
    },
    processing: {
      surface: 'bg-[#F0F4FA]',
      border: 'border-[#2E5EAA]',
      text: 'text-[#0F2137]',
      label: 'PROCESSING',
      Icon: Loader2,
    },
    failed: {
      surface: 'bg-[#FDF0EF]',
      border: 'border-[#F85149]',
      text: 'text-[#5C0B11]',
      label: 'FAILED',
      Icon: XCircle,
    },
  };
  const c = config[status];
  const Icon = c.Icon;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-bold tracking-wide ${c.surface} ${c.border} ${c.text}`}
    >
      <Icon className={`h-3.5 w-3.5 ${status === 'processing' ? 'animate-spin' : ''}`} />
      {c.label}
    </span>
  );
}

function TypeBadge({ type }: { type: DatasetType }) {
  const isAuthentic = type === 'Authentic';
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-semibold ${
        isAuthentic
          ? 'bg-[#0E7C7E]/5 border-[#0E7C7E]/30 text-[#0E7C7E]'
          : 'bg-[#6B4C9A]/5 border-[#6B4C9A]/30 text-[#6B4C9A]'
      }`}
    >
      {isAuthentic ? <FileText className="h-3.5 w-3.5" /> : <FileSpreadsheet className="h-3.5 w-3.5" />}
      {type}
    </span>
  );
}

function KPICard({
  icon: Icon,
  label,
  value,
  subtext,
  accent,
  trend,
}: {
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties; color?: string }>;
  label: string;
  value: string;
  subtext?: string;
  accent: string;
  trend?: { value: string; positive: boolean };
}) {
  return (
    <div className="relative overflow-hidden rounded-lg border border-[#E2E8F0] bg-white p-5">
      <div
        className="absolute left-5 top-5 flex h-9 w-9 items-center justify-center rounded-md"
        style={{ backgroundColor: `${accent}1A` }}
      >
        <Icon className="h-5 w-5" color={accent} />
      </div>
      <div className="ml-12">
        <p className="text-sm text-text-secondary">{label}</p>
        <div className="mt-1 flex items-baseline gap-2">
          <span className="text-2xl font-bold text-text-primary">{value}</span>
          {trend && (
            <span
              className={`inline-flex items-center gap-0.5 text-xs font-semibold ${
                trend.positive ? 'text-status-approve' : 'text-status-decline'
              }`}
            >
              <ArrowUpRight
                className={`h-3.5 w-3.5 ${trend.positive ? '' : 'rotate-180'}`}
              />
              {trend.value}
            </span>
          )}
        </div>
        {subtext && <p className="mt-1 text-xs text-text-muted">{subtext}</p>}
      </div>
    </div>
  );
}

export default function DatasetsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<'all' | DatasetType>('all');
  const [statusFilter, setStatusFilter] = useState<'all' | DatasetStatus>('all');
  const [isDragging, setIsDragging] = useState(false);

  const filteredDatasets = useMemo(() => {
    return mockDatasets.filter((d) => {
      const matchesSearch = d.name.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesType = typeFilter === 'all' || d.type === typeFilter;
      const matchesStatus = statusFilter === 'all' || d.status === statusFilter;
      return matchesSearch && matchesType && matchesStatus;
    });
  }, [searchQuery, typeFilter, statusFilter]);

  const kpis = useMemo(() => {
    const total = mockDatasets.length;
    const totalRows = mockDatasets.reduce((sum, d) => sum + d.rows, 0);
    const ready = mockDatasets.filter((d) => d.status === 'ready').length;
    const processing = mockDatasets.filter((d) => d.status === 'processing').length;
    return { total, totalRows, ready, processing };
  }, []);

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between mb-8">
          <div className="flex-1">
            <h1
              className="font-bold tracking-tight text-text-primary"
              style={{ fontSize: '28px' }}
            >
              Datasets
            </h1>
            <p className="mt-2 text-[#5B6B7B] max-w-2xl">
              Upload, organize, and monitor training datasets for the SynthGigCredit decision
              engine. Manage authentic historical records and synthetic data variants used to
              train risk, policy, and evidence scoring models.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button className="inline-flex items-center gap-2 rounded-full border border-[#E2E8F0] bg-white px-4 py-2 text-sm font-medium text-text-secondary hover:bg-[#F6F8FA]">
              <Filter className="h-4 w-4" />
              Filter
            </button>
            <button className="inline-flex items-center gap-2 rounded-full bg-[#0E7C7E] px-4 py-2 text-sm font-medium text-white hover:bg-[#0b6567]">
              <Upload className="h-4 w-4" />
              Upload Dataset
            </button>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          <KPICard
            icon={Database}
            label="Total datasets"
            value={kpis.total.toString()}
            subtext="Across all categories"
            accent="#0E7C7E"
            trend={{ value: '+12.4%', positive: true }}
          />
          <KPICard
            icon={Table2}
            label="Total rows"
            value={formatNumber(kpis.totalRows)}
            subtext="Training samples available"
            accent="#2E5EAA"
            trend={{ value: '+8.1%', positive: true }}
          />
          <KPICard
            icon={CheckCircle2}
            label="Ready datasets"
            value={kpis.ready.toString()}
            subtext="Available for training"
            accent="#3FB950"
            trend={{ value: '+2 this week', positive: true }}
          />
          <KPICard
            icon={Loader2}
            label="Processing datasets"
            value={kpis.processing.toString()}
            subtext="Validation in progress"
            accent="#E3B341"
          />
        </div>

        {/* File Upload Area */}
        <div className="mb-8">
          <div
            className={`relative rounded-lg border-2 border-dashed bg-white p-10 transition-all ${
              isDragging
                ? 'border-[#0E7C7E] bg-[#0E7C7E]/5'
                : 'border-[#E2E8F0] hover:border-[#0E7C7E]/50 hover:bg-[#F6F8FA]/50'
            }`}
            onDragEnter={() => setIsDragging(true)}
            onDragLeave={() => setIsDragging(false)}
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragging(false);
            }}
          >
            <div className="flex flex-col items-center justify-center text-center">
              <div
                className={`mb-4 flex h-14 w-14 items-center justify-center rounded-full transition-colors ${
                  isDragging ? 'bg-[#0E7C7E] text-white' : 'bg-[#0E7C7E]/10 text-[#0E7C7E]'
                }`}
              >
                <Upload className="h-7 w-7" />
              </div>
              <h3 className="text-base font-semibold text-text-primary">
                Drag and drop your dataset files here
              </h3>
              <p className="mt-1 text-sm text-text-secondary">
                or click to browse from your computer
              </p>
              <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
                <span className="inline-flex items-center rounded-md bg-[#F6F8FA] px-2 py-1 text-xs font-medium text-text-muted">
                  .CSV
                </span>
                <span className="inline-flex items-center rounded-md bg-[#F6F8FA] px-2 py-1 text-xs font-medium text-text-muted">
                  .PARQUET
                </span>
                <span className="inline-flex items-center rounded-md bg-[#F6F8FA] px-2 py-1 text-xs font-medium text-text-muted">
                  .JSON
                </span>
                <span className="inline-flex items-center rounded-md bg-[#F6F8FA] px-2 py-1 text-xs font-medium text-text-muted">
                  .XLSX
                </span>
              </div>
              <p className="mt-4 text-xs text-text-muted">
                Max file size: 500MB · Auto-profiling &amp; quality checks on upload
              </p>
              <button className="mt-6 inline-flex items-center gap-2 rounded-md border border-[#E2E8F0] bg-white px-5 py-2.5 text-sm font-medium text-text-primary hover:bg-[#F6F8FA]">
                <Upload className="h-4 w-4" />
                Choose files
              </button>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
            <input
              type="text"
              placeholder="Search datasets..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-md border border-[#E2E8F0] bg-white py-2 pl-10 pr-4 text-sm text-text-primary placeholder:text-text-muted focus:border-[#0E7C7E] focus:outline-none focus:ring-1 focus:ring-[#0E7C7E]"
            />
          </div>
          <div className="flex items-center gap-2">
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value as 'all' | DatasetType)}
              className="rounded-md border border-[#E2E8F0] bg-white px-3 py-2 text-sm text-text-secondary focus:border-[#0E7C7E] focus:outline-none focus:ring-1 focus:ring-[#0E7C7E]"
            >
              <option value="all">All types</option>
              <option value="Authentic">Authentic</option>
              <option value="Synthetic">Synthetic</option>
            </select>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as 'all' | DatasetStatus)}
              className="rounded-md border border-[#E2E8F0] bg-white px-3 py-2 text-sm text-text-secondary focus:border-[#0E7C7E] focus:outline-none focus:ring-1 focus:ring-[#0E7C7E]"
            >
              <option value="all">All statuses</option>
              <option value="ready">Ready</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </div>

        {/* Data Table */}
        <div className="rounded-lg border border-[#E2E8F0] bg-white mb-8">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#E2E8F0] bg-[#F6F8FA]/50">
                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Dataset name
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Type
                  </th>
                  <th className="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Rows
                  </th>
                  <th className="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Columns
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Status
                  </th>
                  <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Uploaded date
                  </th>
                  <th className="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Size
                  </th>
                  <th className="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0]">
                {filteredDatasets.map((row) => (
                  <tr
                    key={row.id}
                    className="hover:bg-[#F6F8FA]/40 transition-colors"
                  >
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md bg-[#0E7C7E]/10">
                          <Database className="h-4 w-4 text-[#0E7C7E]" />
                        </div>
                        <div>
                          <div className="text-sm font-medium text-text-primary">{row.name}</div>
                          <div className="text-xs text-text-muted font-mono">{row.id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      <TypeBadge type={row.type} />
                    </td>
                    <td className="px-5 py-3.5 text-right tabular-nums text-sm text-text-secondary">
                      {formatNumber(row.rows)}
                    </td>
                    <td className="px-5 py-3.5 text-right tabular-nums text-sm text-text-secondary">
                      {row.columns}
                    </td>
                    <td className="px-5 py-3.5">
                      <StatusBadge status={row.status} />
                    </td>
                    <td className="px-5 py-3.5 text-sm text-text-muted">
                      {formatDate(row.uploadedAt)}
                    </td>
                    <td className="px-5 py-3.5 text-right tabular-nums text-sm text-text-secondary">
                      {row.size}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          className="rounded-md p-1.5 text-text-muted hover:bg-[#F6F8FA] hover:text-[#0E7C7E]"
                          title="Preview"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <button
                          className="rounded-md p-1.5 text-text-muted hover:bg-[#F6F8FA] hover:text-[#2E5EAA]"
                          title="Download"
                        >
                          <Download className="h-4 w-4" />
                        </button>
                        <button
                          className="rounded-md p-1.5 text-text-muted hover:bg-[#F6F8FA] hover:text-status-decline"
                          title="Delete"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                        <button
                          className="rounded-md p-1.5 text-text-muted hover:bg-[#F6F8FA] hover:text-text-primary"
                          title="More"
                        >
                          <MoreHorizontal className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {filteredDatasets.length === 0 && (
                  <tr>
                    <td colSpan={8} className="px-5 py-10 text-center">
                      <Database className="mx-auto mb-3 h-10 w-10 text-text-muted opacity-40" />
                      <p className="text-sm font-medium text-text-secondary">No datasets found</p>
                      <p className="mt-1 text-xs text-text-muted">
                        Try adjusting your filters or upload a new dataset
                      </p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between border-t border-[#E2E8F0] px-5 py-3">
            <p className="text-xs text-text-muted">
              Showing {filteredDatasets.length} of {mockDatasets.length} datasets
            </p>
            <div className="flex items-center gap-2">
              <button className="rounded-md border border-[#E2E8F0] bg-white px-3 py-1.5 text-xs font-medium text-text-secondary hover:bg-[#F6F8FA]">
                Previous
              </button>
              <button className="rounded-md border border-[#E2E8F0] bg-white px-3 py-1.5 text-xs font-medium text-text-secondary hover:bg-[#F6F8FA]">
                Next
              </button>
            </div>
          </div>
        </div>

        {/* Dataset Health / Quality Metrics */}
        <div>
          <div className="mb-4">
            <h2 className="text-base font-semibold text-text-primary">
              Dataset Health &amp; Quality Metrics
            </h2>
            <p className="text-sm text-text-secondary">
              Overall quality scores across all active datasets by dimension and trend
            </p>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3 mb-6">
            <div className="rounded-lg border border-[#E2E8F0] bg-white p-5">
              <div className="flex items-center gap-3 mb-4">
                <div className="flex h-9 w-9 items-center justify-center rounded-md bg-[#0E7C7E]/10">
                  <Activity className="h-5 w-5 text-[#0E7C7E]" />
                </div>
                <div>
                  <p className="text-sm text-text-secondary">Overall Quality Score</p>
                  <p className="text-xs text-text-muted">Rolling 30-day average</p>
                </div>
              </div>
              <div className="flex items-baseline gap-2 mb-2">
                <span className="text-3xl font-bold text-text-primary">89.4%</span>
                <span className="inline-flex items-center gap-0.5 text-xs font-semibold text-status-approve">
                  <ArrowUpRight className="h-3.5 w-3.5" />
                  +3.2%
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-[#F6F8FA]">
                <div
                  className="h-full rounded-full bg-[#0E7C7E]"
                  style={{ width: '89.4%' }}
                />
              </div>
            </div>

            <div className="rounded-lg border border-[#E2E8F0] bg-white p-5">
              <div className="flex items-center gap-3 mb-4">
                <div className="flex h-9 w-9 items-center justify-center rounded-md bg-[#3FB950]/10">
                  <ShieldCheck className="h-5 w-5 text-[#3FB950]" />
                </div>
                <div>
                  <p className="text-sm text-text-secondary">Datasets Passing QA</p>
                  <p className="text-xs text-text-muted">Ready for model training</p>
                </div>
              </div>
              <div className="flex items-baseline gap-2 mb-2">
                <span className="text-3xl font-bold text-text-primary">
                  {kpis.ready}/{kpis.total}
                </span>
                <span className="text-xs font-semibold text-status-approve">
                  {((kpis.ready / kpis.total) * 100).toFixed(0)}% pass rate
                </span>
              </div>
              <div className="space-y-1.5">
                {[
                  { label: 'Schema validation', pct: 96 },
                  { label: 'Null threshold', pct: 91 },
                  { label: 'Uniqueness check', pct: 94 },
                ].map((item) => (
                  <div key={item.label} className="flex items-center gap-2">
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-[#F6F8FA]">
                      <div
                        className="h-full rounded-full bg-[#3FB950]"
                        style={{ width: `${item.pct}%` }}
                      />
                    </div>
                    <span className="w-8 text-right text-xs font-medium text-text-muted tabular-nums">
                      {item.pct}%
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-lg border border-[#E2E8F0] bg-white p-5">
              <div className="flex items-center gap-3 mb-4">
                <div className="flex h-9 w-9 items-center justify-center rounded-md bg-[#E3B341]/10">
                  <AlertTriangle className="h-5 w-5 text-[#E3B341]" />
                </div>
                <div>
                  <p className="text-sm text-text-secondary">Active Quality Alerts</p>
                  <p className="text-xs text-text-muted">Requiring attention</p>
                </div>
              </div>
              <div className="flex items-baseline gap-2 mb-4">
                <span className="text-3xl font-bold text-text-primary">3</span>
                <span className="text-xs font-semibold text-status-review">2 warning · 1 critical</span>
              </div>
              <ul className="space-y-2">
                <li className="flex items-start gap-2">
                  <AlertTriangle className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-[#E3B341]" />
                  <div>
                    <p className="text-xs font-medium text-text-primary">
                      Gig Worker Income Panel
                    </p>
                    <p className="text-[11px] text-text-muted">Upload failed — schema mismatch</p>
                  </div>
                </li>
                <li className="flex items-start gap-2">
                  <AlertTriangle className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-[#E3B341]" />
                  <div>
                    <p className="text-xs font-medium text-text-primary">
                      RBI Credit Bureau Sample
                    </p>
                    <p className="text-[11px] text-text-muted">7.2% missing values in column FICO</p>
                  </div>
                </li>
              </ul>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="rounded-lg border border-[#E2E8F0] bg-white p-5 lg:col-span-2">
              <div className="mb-4">
                <h3 className="text-base font-semibold text-text-primary">
                  Quality Dimensions — Authentic vs Synthetic
                </h3>
                <p className="text-sm text-text-secondary">
                  Side-by-side comparison across data quality pillars (score %)
                </p>
              </div>
              <ResponsiveContainer width="100%" height={288}>
                <BarChart data={healthMetricsData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
                  <XAxis
                    dataKey="metric"
                    tick={{ fontSize: 12, fill: '#5B6B7B' }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 12, fill: '#5B6B7B' }}
                    axisLine={false}
                    tickLine={false}
                    domain={[0, 100]}
                    tickFormatter={(v) => `${v}%`}
                  />
                  <Tooltip
                    formatter={(value: any) => [`${value}%`]}
                    contentStyle={{
                      borderRadius: '8px',
                      border: '1px solid #E2E8F0',
                      boxShadow: '0 4px 6px -1px rgba(15, 33, 55, 0.08)',
                    }}
                  />
                  <Legend iconType="circle" wrapperStyle={{ paddingTop: 16 }} />
                  <Bar dataKey="authentic" name="Authentic" fill="#0E7C7E" radius={[4, 4, 0, 0]} barSize={20} />
                  <Bar dataKey="synthetic" name="Synthetic" fill="#6B4C9A" radius={[4, 4, 0, 0]} barSize={20} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="rounded-lg border border-[#E2E8F0] bg-white p-5">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h3 className="text-base font-semibold text-text-primary">Quality Score Trend</h3>
                  <p className="text-sm text-text-secondary">Overall score, last 8 months</p>
                </div>
                <span className="inline-flex items-center gap-1 rounded-full bg-[#0E7C7E]/5 border border-[#0E7C7E]/20 px-2.5 py-1 text-xs font-semibold text-[#0E7C7E]">
                  <BarChart3 className="h-3.5 w-3.5" />
                  Improving
                </span>
              </div>
              <ResponsiveContainer width="100%" height={288}>
                <LineChart data={qualityTrendData} margin={{ top: 10, right: 10, left: 0, bottom: 5 }}>
                  <defs>
                    <linearGradient id="qualityGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0E7C7E" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#0E7C7E" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
                  <XAxis
                    dataKey="month"
                    tick={{ fontSize: 12, fill: '#5B6B7B' }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 12, fill: '#5B6B7B' }}
                    axisLine={false}
                    tickLine={false}
                    domain={[70, 100]}
                    tickFormatter={(v) => `${v}%`}
                  />
                  <Tooltip
                    formatter={(value: any) => [`${Number(value).toFixed(1)}%`, 'Quality score']}
                    contentStyle={{
                      borderRadius: '8px',
                      border: '1px solid #E2E8F0',
                      boxShadow: '0 4px 6px -1px rgba(15, 33, 55, 0.08)',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="score"
                    name="Quality"
                    stroke="#0E7C7E"
                    strokeWidth={2.5}
                    dot={{ fill: '#0E7C7E', r: 4, strokeWidth: 2, stroke: '#fff' }}
                    activeDot={{ r: 6, fill: '#0E7C7E', stroke: '#fff', strokeWidth: 2 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
