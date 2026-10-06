import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { useAssessmentStore } from '@/store/useAssessmentStore';
import {
  mockHistory,
  rocData,
  mockApplicants,
} from '@/data/mockData';
import type { HistoryEntry } from '@/types';
import {
  ArrowUpRight,
  ArrowDownRight,
  FileCheck2,
  ShieldCheck,
  AlertTriangle,
  FolderCheck,
  Calendar,
  Download,
  ChevronDown,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  BarChart,
  Bar,
  ReferenceLine,
  LabelList,
} from 'recharts';

// NOTE: Monthly assessment trend is from session history only — no historical backend data.
// These are placeholder zeros until backend exposes a history endpoint.
const assessmentMonths = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'];

const monthlyAssessmentData = assessmentMonths.map((m) => ({
  month: m,
  Approved: 0,
  Review: 0,
  Declined: 0,
}));

// Decision mode usage — illustrative placeholder, not from live backend
const decisionModeData = [
  { name: 'D1 Risk only', value: 12, color: '#2E5EAA' },
  { name: 'D2 Risk+Policy', value: 23, color: '#B9770E' },
  { name: 'D3 Risk+Evidence', value: 31, color: '#6B4C9A' },
  { name: 'D4 All layers', value: 34, color: '#0E7C7E' },
];

// NOTE: Gate pass rates below are illustrative placeholders — not from live backend.
// Connect to /api/evaluate_batch when batch history is available.
const gatePassData = [
  { gate: 'Evidence Quality', pass: 71 },   // ~29% fail rate from G0 report
  { gate: 'Policy Eligibility', pass: 85 },
  { gate: 'Risk (PD < τ)', pass: 70 },       // design target: 70% approval
];

function StatusBadge({ status }: { status: 'approve' | 'review' | 'decline' }) {
  const styles = {
    approve: 'bg-status-approve/surface text-status-approve border-status-approve/20',
    review: 'bg-status-review/surface text-status-review border-status-review/20',
    decline: 'bg-status-decline/surface text-status-decline border-status-decline/20',
  };
  const labels = {
    approve: 'Approved',
    review: 'Review',
    decline: 'Declined',
  };
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${styles[status]}`}>
      {labels[status]}
    </span>
  );
}

function formatDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function occupationForApplicant(applicantId: string): string {
  const app = mockApplicants.find((a) => a.id === applicantId);
  return app?.occupation ?? 'Unknown';
}

export default function DashboardPage() {
  const { history } = useAssessmentStore();

  // ── Computed KPIs from real session history + mock baseline ──────────────
  const allHistory = useMemo(() => [...history, ...mockHistory], [history]);

  const totalAssessments = allHistory.length;
  const approvalRate = totalAssessments > 0
    ? ((allHistory.filter(h => h.outcome === 'approve').length / totalAssessments) * 100).toFixed(1)
    : '—';
  const avgRiskPD = totalAssessments > 0
    ? ((allHistory.reduce((sum, h) => sum + (1 - (h.scores.riskScore ?? 0.5)), 0) / totalAssessments) * 100).toFixed(1)
    : '—';
  const avgEvidenceCoverage = totalAssessments > 0
    ? ((allHistory.reduce((sum, h) => sum + (h.scores.evidenceScore ?? 0), 0) / totalAssessments) * 100).toFixed(1)
    : '—';

  // Count change vs previous half (compare first vs second half)
  const half = Math.floor(allHistory.length / 2);
  const recent = allHistory.slice(0, half);
  const older = allHistory.slice(half);
  const recentApproval = recent.length > 0 ? recent.filter(h => h.outcome === 'approve').length / recent.length * 100 : 0;
  const olderApproval = older.length > 0 ? older.filter(h => h.outcome === 'approve').length / older.length * 100 : 0;
  const approvalDelta = (recentApproval - olderApproval).toFixed(1);
  const approvalUp = recentApproval >= olderApproval;

  const tableRows = useMemo<HistoryEntry[]>(() => {
    const combined = [...history, ...mockHistory];
    return combined.slice(0, 6);
  }, [history]);

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-8">
          <div className="flex-1">
            <h1 className="font-bold tracking-tight text-text-primary" style={{ fontSize: '28px' }}>
              Dashboard Overview
            </h1>
            <p className="mt-2 text-[#5B6B7B]">
              Operational overview of the SynthGigCredit decision engine across applicants, models and dataset health.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button className="inline-flex items-center gap-2 rounded-full border border-border-subtle bg-white px-4 py-2 text-sm font-medium text-text-secondary hover:bg-page-bg">
              <Calendar className="h-4 w-4" />
              Last 30 days
              <ChevronDown className="h-4 w-4" />
            </button>
            <button className="inline-flex items-center gap-2 rounded-full bg-action-primary px-4 py-2 text-sm font-medium text-white hover:bg-action-primary-hover">
              <Download className="h-4 w-4" />
              Export
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          <div className="relative overflow-hidden rounded-lg border border-[#E2E8F0] bg-white p-5">
            <div className="absolute left-5 top-5 flex h-9 w-9 items-center justify-center rounded-md bg-action-primary/10">
              <FileCheck2 className="h-5 w-5 text-action-primary" />
            </div>
            <div className="ml-12">
              <p className="text-sm text-text-secondary">Total Assessments</p>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-text-primary">{totalAssessments.toLocaleString()}</span>
                <span className="inline-flex items-center gap-0.5 text-xs font-semibold text-status-approve">
                  <ArrowUpRight className="h-3.5 w-3.5" />
                  This session
                </span>
              </div>
              <p className="mt-1 text-xs text-text-muted">All time</p>
            </div>
          </div>

          <div className="relative overflow-hidden rounded-lg border border-[#E2E8F0] bg-white p-5">
            <div className="absolute left-5 top-5 flex h-9 w-9 items-center justify-center rounded-md bg-status-approve/10">
              <ShieldCheck className="h-5 w-5 text-status-approve" />
            </div>
            <div className="ml-12">
              <p className="text-sm text-text-secondary">Approval Rate</p>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-text-primary">{approvalRate}%</span>
                <span className={`inline-flex items-center gap-0.5 text-xs font-semibold ${approvalUp ? 'text-status-approve' : 'text-status-decline'}`}>
                  {approvalUp ? <ArrowUpRight className="h-3.5 w-3.5" /> : <ArrowDownRight className="h-3.5 w-3.5" />}
                  {approvalDelta}%
                </span>
              </div>
              <p className="mt-1 text-xs text-text-muted">Pass threshold</p>
            </div>
          </div>

          <div className="relative overflow-hidden rounded-lg border border-[#E2E8F0] bg-white p-5">
            <div className="absolute left-5 top-5 flex h-9 w-9 items-center justify-center rounded-md bg-domain-risk/10">
              <AlertTriangle className="h-5 w-5 text-domain-risk" />
            </div>
            <div className="ml-12">
              <p className="text-sm text-text-secondary">Average Risk PD</p>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-text-primary">{avgRiskPD}%</span>
              </div>
              <p className="mt-1 text-xs text-text-muted">Probability of default</p>
            </div>
          </div>

          <div className="relative overflow-hidden rounded-lg border border-[#E2E8F0] bg-white p-5">
            <div className="absolute left-5 top-5 flex h-9 w-9 items-center justify-center rounded-md bg-domain-evidence/10">
              <FolderCheck className="h-5 w-5 text-domain-evidence" />
            </div>
            <div className="ml-12">
              <p className="text-sm text-text-secondary">Evidence Coverage</p>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-text-primary">{avgEvidenceCoverage}%</span>
              </div>
              <p className="mt-1 text-xs text-text-muted">Median E-score submitted</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3 mb-8">
          <div className="rounded-lg border border-[#E2E8F0] bg-white p-5 lg:col-span-2">
            <div className="mb-4">
              <h2 className="text-base font-semibold text-text-primary">Monthly Assessments Trend</h2>
              <p className="text-sm text-text-secondary">Volume &amp; outcome mix — <span className="text-[#9AABB7] text-xs">session history only; no historical backend data</span></p>
            </div>
            <ResponsiveContainer width="100%" height={288}>
              <AreaChart data={monthlyAssessmentData}>
                <defs>
                  <linearGradient id="approvedGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3FB950" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#3FB950" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="reviewGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#E3B341" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#E3B341" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="declinedGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#F85149" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#F85149" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 12, fill: '#5B6B7B' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: '#5B6B7B' }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    borderRadius: '8px',
                    border: '1px solid #E2E8F0',
                    boxShadow: '0 4px 6px -1px rgba(15, 33, 55, 0.08)',
                  }}
                />
                <Legend iconType="circle" wrapperStyle={{ paddingTop: 16 }} />
                <Area type="monotone" dataKey="Approved" stackId="1" stroke="#3FB950" strokeWidth={2} fill="url(#approvedGrad)" />
                <Area type="monotone" dataKey="Review" stackId="1" stroke="#E3B341" strokeWidth={2} fill="url(#reviewGrad)" />
                <Area type="monotone" dataKey="Declined" stackId="1" stroke="#F85149" strokeWidth={2} fill="url(#declinedGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="rounded-lg border border-[#E2E8F0] bg-white p-5">
            <div className="mb-4">
              <h2 className="text-base font-semibold text-text-primary">Decision mode usage</h2>
            </div>
            <ResponsiveContainer width="100%" height={288}>
              <PieChart>
                <Pie
                  data={decisionModeData}
                  cx="50%"
                  cy="45%"
                  innerRadius={50}
                  outerRadius={85}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {decisionModeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} strokeWidth={0} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: any) => [`${value}%`, 'Usage']}
                  contentStyle={{
                    borderRadius: '8px',
                    border: '1px solid #E2E8F0',
                    boxShadow: '0 4px 6px -1px rgba(15, 33, 55, 0.08)',
                  }}
                />
                <Legend
                  layout="horizontal"
                  verticalAlign="bottom"
                  align="center"
                  iconType="circle"
                  formatter={(value, entry) => (
                    <span className="text-xs text-text-secondary">
                      {value} <span className="text-text-muted">({(entry as any).payload.value}%)</span>
                    </span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 mb-8">
          <div className="rounded-lg border border-[#E2E8F0] bg-white p-5">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-base font-semibold text-text-primary">Risk model — ROC curve (T1 Home Credit)</h2>
                <p className="text-xs text-[#5B6B7B] mt-0.5">XGBoost-C authentic experiment result</p>
              </div>
              <span className="inline-flex items-center rounded-full bg-domain-risk/tint border border-domain-risk-border px-2.5 py-1 text-xs font-semibold text-domain-risk">
                AUC 0.7568
              </span>
            </div>
            <ResponsiveContainer width="100%" height={256}>
              <LineChart data={rocData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis
                  dataKey="fpr"
                  tick={{ fontSize: 12, fill: '#5B6B7B' }}
                  axisLine={false}
                  tickLine={false}
                  domain={[0, 1]}
                  tickFormatter={(v) => v.toFixed(1)}
                  label={{ value: 'FPR', position: 'insideBottom', offset: -5, fontSize: 12, fill: '#5B6B7B' }}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: '#5B6B7B' }}
                  axisLine={false}
                  tickLine={false}
                  domain={[0, 1]}
                  tickFormatter={(v) => v.toFixed(1)}
                  label={{ value: 'TPR', angle: -90, position: 'insideLeft', fontSize: 12, fill: '#5B6B7B' }}
                />
                <Tooltip
                  formatter={(value: any, name: any) => [
                    Number(value).toFixed(2),
                    name === 'tpr' ? 'TPR' : 'FPR',
                  ]}
                  contentStyle={{
                    borderRadius: '8px',
                    border: '1px solid #E2E8F0',
                    boxShadow: '0 4px 6px -1px rgba(15, 33, 55, 0.08)',
                  }}
                />
                <ReferenceLine
                  segment={[
                    { x: 0, y: 0 },
                    { x: 1, y: 1 },
                  ]}
                  stroke="#BCCCDC"
                  strokeDasharray="5 5"
                />
                <Line
                  type="monotone"
                  dataKey="tpr"
                  stroke="#0E7C7E"
                  strokeWidth={2.5}
                  dot={false}
                  activeDot={{ r: 5, fill: '#0E7C7E' }}
                />
              </LineChart>
            </ResponsiveContainer>
            {/* Real T1 metrics from results/authentic/T1_results.json */}
            <div className="mt-3 pt-3 border-t border-[#F1F5F9] grid grid-cols-3 gap-3 text-center">
              <div>
                <p className="text-[11px] text-[#5B6B7B]">XGBoost ROC-AUC</p>
                <p className="text-[14px] font-bold text-[#0F2137]">0.7568</p>
              </div>
              <div>
                <p className="text-[11px] text-[#5B6B7B]">LR ROC-AUC</p>
                <p className="text-[14px] font-bold text-[#0F2137]">0.7383</p>
              </div>
              <div>
                <p className="text-[11px] text-[#5B6B7B]">Prevalence (T1)</p>
                <p className="text-[14px] font-bold text-[#0F2137]">8.07%</p>
              </div>
            </div>
            <p className="text-[10px] text-[#9AABB7] mt-1 text-center">
              Source: results/authentic/T1_results.json — Home Credit authentic experiment
            </p>
          </div>

          <div className="rounded-lg border border-[#E2E8F0] bg-white p-5">
            <div className="mb-4">
              <h2 className="text-base font-semibold text-text-primary">Gate-level pass rates</h2>
              <p className="text-xs text-[#9AABB7]">Illustrative — connect /api/evaluate_batch for live rates</p>
            </div>
            <ResponsiveContainer width="100%" height={256}>
              <BarChart
                data={gatePassData}
                layout="vertical"
                margin={{ top: 5, right: 40, left: 10, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" horizontal={false} />
                <XAxis
                  type="number"
                  domain={[0, 100]}
                  tick={{ fontSize: 12, fill: '#5B6B7B' }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => `${v}%`}
                />
                <YAxis
                  dataKey="gate"
                  type="category"
                  width={120}
                  tick={{ fontSize: 12, fill: '#486581' }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  formatter={(value: any) => [`${value}%`, 'Pass rate']}
                  contentStyle={{
                    borderRadius: '8px',
                    border: '1px solid #E2E8F0',
                    boxShadow: '0 4px 6px -1px rgba(15, 33, 55, 0.08)',
                  }}
                />
                <Bar dataKey="pass" fill="#0E7C7E" radius={[0, 6, 6, 0]} barSize={18}>
                  <LabelList
                    dataKey="pass"
                    position="right"
                    formatter={(v: any) => `${v}%`}
                    style={{ fontSize: 12, fill: '#486581', fontWeight: 600 }}
                  />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-lg border border-[#E2E8F0] bg-white">
          <div className="flex items-center justify-between p-5 border-b border-border-subtle">
            <h2 className="text-base font-semibold text-text-primary">Recent decisions</h2>
            <Link
              to="/history"
              className="text-sm font-medium text-action-primary hover:text-action-primary-hover"
            >
              View all
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border-subtle bg-page-bg/50">
                  <th className="sticky top-0 px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Applicant ID
                  </th>
                  <th className="sticky top-0 px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Name
                  </th>
                  <th className="sticky top-0 px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Occupation
                  </th>
                  <th className="sticky top-0 px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Mode
                  </th>
                  <th className="sticky top-0 px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Risk PD
                  </th>
                  <th className="sticky top-0 px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Evidence
                  </th>
                  <th className="sticky top-0 px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Outcome
                  </th>
                  <th className="sticky top-0 px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Date
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {tableRows.map((row) => (
                  <tr
                    key={row.id}
                    className="hover:bg-page-bg/40 transition-colors"
                  >
                    <td className="px-5 py-3.5 font-mono text-xs text-text-secondary">
                      {row.applicantId}
                    </td>
                    <td className="px-5 py-3.5 text-sm font-medium text-text-primary">
                      {row.applicantName}
                    </td>
                    <td className="px-5 py-3.5 text-sm text-text-secondary">
                      {occupationForApplicant(row.applicantId)}
                    </td>
                    <td className="px-5 py-3.5">
                      <span
                        className="inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold"
                        style={{
                          backgroundColor:
                            row.decisionMode === 'D1'
                              ? '#2E5EAA1A'
                              : row.decisionMode === 'D2'
                                ? '#B9770E1A'
                                : row.decisionMode === 'D3'
                                  ? '#6B4C9A1A'
                                  : '#0E7C7E1A',
                          color:
                            row.decisionMode === 'D1'
                              ? '#2E5EAA'
                              : row.decisionMode === 'D2'
                                ? '#B9770E'
                                : row.decisionMode === 'D3'
                                  ? '#6B4C9A'
                                  : '#0E7C7E',
                        }}
                      >
                        {row.decisionMode}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 tabular-nums text-sm text-text-secondary">
                      {((1 - (row.scores.riskScore ?? 0.5)) * 100).toFixed(1)}%
                    </td>
                    <td className="px-5 py-3.5 tabular-nums text-sm text-text-secondary">
                      {((row.scores.evidenceScore ?? 0) * 100).toFixed(0)}%
                    </td>
                    <td className="px-5 py-3.5">
                      <StatusBadge status={row.outcome} />
                    </td>
                    <td className="px-5 py-3.5 text-sm text-text-muted">
                      {formatDate(row.createdAt)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
