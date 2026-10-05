import { useMemo, useState } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import StatusBadge from '@/components/ui/StatusBadge';
import { useAssessmentStore } from '@/store/useAssessmentStore';
import { mockHistory, mockApplicants } from '@/data/mockData';
import type { HistoryEntry } from '@/types';
import {
  Search,
  Calendar,
  Filter,
  ChevronDown,
  FileCheck2,
  ShieldCheck,
  AlertTriangle,
  XOctagon,
  Eye,
  Copy,
  Download,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

function formatDateTime(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) +
    ' ' + d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}

function occupationForApplicant(applicantId: string): string {
  const app = mockApplicants.find((a) => a.id === applicantId);
  return app?.occupation ?? 'Unknown';
}

function assessedByForMode(mode: string): string {
  const mapping: Record<string, string> = {
    D1: 'Risk Engine',
    D2: 'Policy Engine',
    D3: 'Evidence Engine',
    D4: 'Full Stack AI',
  };
  return mapping[mode] ?? 'System';
}

const modeColors: Record<string, { bg: string; fg: string }> = {
  D1: { bg: '#2E5EAA1A', fg: '#2E5EAA' },
  D2: { bg: '#B9770E1A', fg: '#B9770E' },
  D3: { bg: '#6B4C9A1A', fg: '#6B4C9A' },
  D4: { bg: '#0E7C7E1A', fg: '#0E7C7E' },
};

export default function HistoryPage() {
  const { history } = useAssessmentStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [outcomeFilter, setOutcomeFilter] = useState<'all' | 'approve' | 'review' | 'decline'>('all');
  const [dateRange, setDateRange] = useState('30');
  const [nowTimestamp] = useState(() => Date.now());

  const combinedHistory = useMemo<HistoryEntry[]>(() => {
    return [...history, ...mockHistory];
  }, [history]);

  const filteredHistory = useMemo(() => {
    return combinedHistory.filter((entry) => {
      const matchesSearch =
        searchQuery === '' ||
        entry.applicantId.toLowerCase().includes(searchQuery.toLowerCase()) ||
        entry.applicantName.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesOutcome = outcomeFilter === 'all' || entry.outcome === outcomeFilter;

      const entryDate = new Date(entry.createdAt).getTime();
      const daysRange = parseInt(dateRange, 10);
      const threshold = nowTimestamp - daysRange * 86400000;
      const matchesDate = entryDate >= threshold;

      return matchesSearch && matchesOutcome && matchesDate;
    });
  }, [combinedHistory, searchQuery, outcomeFilter, dateRange, nowTimestamp]);

  const kpis = useMemo(() => {
    const total = filteredHistory.length;
    const approved = filteredHistory.filter((e) => e.outcome === 'approve').length;
    const review = filteredHistory.filter((e) => e.outcome === 'review').length;
    const declined = filteredHistory.filter((e) => e.outcome === 'decline').length;

    return {
      total,
      approvalRate: total > 0 ? (approved / total) * 100 : 0,
      reviewRate: total > 0 ? (review / total) * 100 : 0,
      declineRate: total > 0 ? (declined / total) * 100 : 0,
    };
  }, [filteredHistory]);

  const trendData = useMemo(() => {
    const monthMap = new Map<string, { month: string; approve: number; review: number; decline: number }>();
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    filteredHistory.forEach((entry) => {
      const d = new Date(entry.createdAt);
      const key = `${monthNames[d.getMonth()]} ${d.getFullYear()}`;
      if (!monthMap.has(key)) {
        monthMap.set(key, { month: key, approve: 0, review: 0, decline: 0 });
      }
      const bucket = monthMap.get(key)!;
      if (entry.outcome === 'approve') bucket.approve++;
      else if (entry.outcome === 'review') bucket.review++;
      else bucket.decline++;
    });

    const sortedKeys = Array.from(monthMap.keys()).sort((a, b) => {
      const [ma, ya] = a.split(' ');
      const [mb, yb] = b.split(' ');
      const yearDiff = parseInt(ya, 10) - parseInt(yb, 10);
      if (yearDiff !== 0) return yearDiff;
      return monthNames.indexOf(ma) - monthNames.indexOf(mb);
    });

    return sortedKeys.map((k) => monthMap.get(k)!);
  }, [filteredHistory]);

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between mb-8">
          <div className="flex-1">
            <h1 className="font-bold tracking-tight text-text-primary" style={{ fontSize: '28px' }}>
              Assessment History
            </h1>
            <p className="mt-2 text-[#5B6B7B]">
              Complete audit trail of all credit assessments, decisions, and risk scores across decision modes.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button className="inline-flex items-center gap-2 rounded-md border border-[#E2E8F0] bg-white px-4 py-2 text-sm font-medium text-text-secondary hover:bg-page-bg">
              <Download className="h-4 w-4" />
              Export CSV
            </button>
          </div>
        </div>

        <div className="rounded-lg border border-[#E2E8F0] bg-white p-5 mb-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
              <input
                type="text"
                placeholder="Search by Applicant ID or name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-md border border-[#E2E8F0] bg-white py-2 pl-10 pr-4 text-sm text-text-primary placeholder:text-text-muted focus:border-action-primary focus:outline-none focus:ring-2 focus:ring-action-primary/20"
              />
            </div>

            <div className="relative">
              <button
                className="inline-flex items-center gap-2 rounded-md border border-[#E2E8F0] bg-white px-4 py-2 text-sm font-medium text-text-secondary hover:bg-page-bg"
                onClick={() => {}}
              >
                <Calendar className="h-4 w-4" />
                Last {dateRange} days
                <ChevronDown className="h-4 w-4" />
              </button>
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                className="absolute inset-0 opacity-0 cursor-pointer"
              >
                <option value="7">Last 7 days</option>
                <option value="30">Last 30 days</option>
                <option value="90">Last 90 days</option>
                <option value="180">Last 6 months</option>
                <option value="365">Last 12 months</option>
              </select>
            </div>

            <div className="relative">
              <button
                className="inline-flex items-center gap-2 rounded-md border border-[#E2E8F0] bg-white px-4 py-2 text-sm font-medium text-text-secondary hover:bg-page-bg"
              >
                <Filter className="h-4 w-4" />
                {outcomeFilter === 'all' ? 'All outcomes' : outcomeFilter.charAt(0).toUpperCase() + outcomeFilter.slice(1)}
                <ChevronDown className="h-4 w-4" />
              </button>
              <select
                value={outcomeFilter}
                onChange={(e) => setOutcomeFilter(e.target.value as 'all' | 'approve' | 'review' | 'decline')}
                className="absolute inset-0 opacity-0 cursor-pointer"
              >
                <option value="all">All outcomes</option>
                <option value="approve">Approved</option>
                <option value="review">Review</option>
                <option value="decline">Declined</option>
              </select>
            </div>
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
                <span className="text-2xl font-bold text-text-primary">{kpis.total.toLocaleString()}</span>
              </div>
              <p className="mt-1 text-xs text-text-muted">Matching filters</p>
            </div>
          </div>

          <div className="relative overflow-hidden rounded-lg border border-[#E2E8F0] bg-white p-5">
            <div className="absolute left-5 top-5 flex h-9 w-9 items-center justify-center rounded-md bg-status-approve/10">
              <ShieldCheck className="h-5 w-5 text-status-approve-bright" />
            </div>
            <div className="ml-12">
              <p className="text-sm text-text-secondary">Approval Rate</p>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-text-primary">{kpis.approvalRate.toFixed(1)}%</span>
              </div>
              <p className="mt-1 text-xs text-text-muted">Auto-approve decisions</p>
            </div>
          </div>

          <div className="relative overflow-hidden rounded-lg border border-[#E2E8F0] bg-white p-5">
            <div className="absolute left-5 top-5 flex h-9 w-9 items-center justify-center rounded-md bg-status-review/10">
              <AlertTriangle className="h-5 w-5 text-status-review-alt" />
            </div>
            <div className="ml-12">
              <p className="text-sm text-text-secondary">Review Rate</p>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-text-primary">{kpis.reviewRate.toFixed(1)}%</span>
              </div>
              <p className="mt-1 text-xs text-text-muted">Refer to analyst</p>
            </div>
          </div>

          <div className="relative overflow-hidden rounded-lg border border-[#E2E8F0] bg-white p-5">
            <div className="absolute left-5 top-5 flex h-9 w-9 items-center justify-center rounded-md bg-status-decline/10">
              <XOctagon className="h-5 w-5 text-status-decline-alt" />
            </div>
            <div className="ml-12">
              <p className="text-sm text-text-secondary">Decline Rate</p>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-text-primary">{kpis.declineRate.toFixed(1)}%</span>
              </div>
              <p className="mt-1 text-xs text-text-muted">Auto-decline decisions</p>
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-[#E2E8F0] bg-white p-5 mb-8">
          <div className="mb-4">
            <h2 className="text-base font-semibold text-text-primary">Outcome Trend</h2>
            <p className="text-sm text-text-secondary">Monthly breakdown of decisions by outcome</p>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={trendData}>
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
                allowDecimals={false}
              />
              <Tooltip
                contentStyle={{
                  borderRadius: '8px',
                  border: '1px solid #E2E8F0',
                  boxShadow: '0 4px 6px -1px rgba(15, 33, 55, 0.08)',
                }}
              />
              <Legend iconType="circle" wrapperStyle={{ paddingTop: 16 }} />
              <Bar
                dataKey="approve"
                name="Approved"
                stackId="a"
                fill="#3FB950"
                radius={[0, 0, 0, 0]}
              />
              <Bar
                dataKey="review"
                name="Review"
                stackId="a"
                fill="#E3B341"
                radius={[0, 0, 0, 0]}
              />
              <Bar
                dataKey="decline"
                name="Declined"
                stackId="a"
                fill="#F85149"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-lg border border-[#E2E8F0] bg-white">
          <div className="flex items-center justify-between p-5 border-b border-[#E2E8F0]">
            <div>
              <h2 className="text-base font-semibold text-text-primary">Assessment Records</h2>
              <p className="text-sm text-text-secondary mt-0.5">
                Showing {filteredHistory.length} of {combinedHistory.length} entries
              </p>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#E2E8F0] bg-page-bg/50">
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
                    Evidence Score
                  </th>
                  <th className="sticky top-0 px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Outcome
                  </th>
                  <th className="sticky top-0 px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Assessed By
                  </th>
                  <th className="sticky top-0 px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Date
                  </th>
                  <th className="sticky top-0 px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0]">
                {filteredHistory.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="px-5 py-12 text-center">
                      <div className="flex flex-col items-center gap-2">
                        <FileCheck2 className="h-10 w-10 text-text-muted" />
                        <p className="text-sm font-medium text-text-primary">No records found</p>
                        <p className="text-xs text-text-muted">Try adjusting your filters or search query.</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  filteredHistory.map((row) => {
                    const modeStyle = modeColors[row.decisionMode] ?? modeColors.D4;
                    const riskPD = (1 - (row.scores.riskScore ?? 0.5)) * 100;
                    return (
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
                              backgroundColor: modeStyle.bg,
                              color: modeStyle.fg,
                            }}
                          >
                            {row.decisionMode}
                          </span>
                        </td>
                        <td className="px-5 py-3.5 tabular-nums text-sm text-text-secondary">
                          {riskPD.toFixed(1)}%
                        </td>
                        <td className="px-5 py-3.5 tabular-nums text-sm text-text-secondary">
                          {((row.scores.evidenceScore ?? 0) * 100).toFixed(0)}%
                        </td>
                        <td className="px-5 py-3.5">
                          <StatusBadge status={row.outcome} />
                        </td>
                        <td className="px-5 py-3.5 text-sm text-text-secondary">
                          {assessedByForMode(row.decisionMode)}
                        </td>
                        <td className="px-5 py-3.5 text-sm text-text-muted">
                          {formatDateTime(row.createdAt)}
                        </td>
                        <td className="px-5 py-3.5">
                          <div className="flex items-center gap-1">
                            <button
                              title="View details"
                              className="inline-flex items-center gap-1.5 rounded-md border border-[#E2E8F0] bg-white px-2.5 py-1.5 text-xs font-medium text-text-secondary hover:bg-page-bg hover:text-action-primary hover:border-action-primary/30"
                            >
                              <Eye className="h-3.5 w-3.5" />
                              Details
                            </button>
                            <button
                              title="Duplicate assessment"
                              className="inline-flex items-center gap-1.5 rounded-md border border-[#E2E8F0] bg-white px-2.5 py-1.5 text-xs font-medium text-text-secondary hover:bg-page-bg hover:text-action-primary hover:border-action-primary/30"
                            >
                              <Copy className="h-3.5 w-3.5" />
                              Duplicate
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
