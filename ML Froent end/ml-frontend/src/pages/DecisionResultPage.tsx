import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  CheckCircle2,
  XOctagon,
  AlertTriangle,
  FileText,
  Download,
  Play,
  ArrowLeft,
  ArrowUpRight,
  ArrowDownRight,
  Mail,
  FileJson,
  Copy,
  Settings2,
  User,
  Clock,
  ShieldCheck,
  TrendingUp,
  BarChart3,
  Activity,
  FileCheck2,
  Gauge,
  CreditCard,
  Wallet,
  PiggyBank,
  Waves,
  Building2,
  FileBadge,
  CircleDot,
} from 'lucide-react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import StatusBadge from '@/components/ui/StatusBadge';
import DomainCard from '@/components/ui/DomainCard';
import { useAssessmentStore } from '@/store/useAssessmentStore';
import { useUIStore } from '@/store/useUIStore';
import { calculateFinancialRatios } from '@/utils/assessment';

const GATE_NAMES = [
  'Identity Check',
  'Platform Income',
  'Volatility Stress',
  'Evidence Quality',
  'Policy Eligibility',
  'Final Adjudication',
];

const PILL_COLORS: Record<string, { bg: string; text: string }> = {
  approve: { bg: 'bg-[#EAF5EC]', text: 'text-[#1A6F31]' },
  passed: { bg: 'bg-[#EAF5EC]', text: 'text-[#1A6F31]' },
  review: { bg: 'bg-[#FDF8E8]', text: 'text-[#8A5D00]' },
  pending: { bg: 'bg-[#FDF8E8]', text: 'text-[#8A5D00]' },
  decline: { bg: 'bg-[#FDF0EF]', text: 'text-[#911A20]' },
  failed: { bg: 'bg-[#FDF0EF]', text: 'text-[#911A20]' },
};

function GateIcon({ status, size = 18 }: { status: 'passed' | 'failed' | 'pending'; size?: number }) {
  if (status === 'passed') return <CheckCircle2 style={{ height: size, width: size, color: '#0E7C7E' }} />;
  if (status === 'failed') return <XOctagon style={{ height: size, width: size, color: '#CF222E' }} />;
  return <CircleDot style={{ height: size, width: size, color: '#9FB3C8' }} />;
}

function GateNode({
  name,
  status,
  isLast,
}: {
  name: string;
  status: 'passed' | 'failed' | 'pending';
  isLast: boolean;
}) {
  const ringStyle: React.CSSProperties = {};
  if (status === 'passed') {
    ringStyle.backgroundColor = '#FFFFFF';
    ringStyle.border = `2px solid #0E7C7E`;
    ringStyle.boxShadow = '0 0 0 2px rgba(14, 124, 126, 0.1)';
  } else if (status === 'failed') {
    ringStyle.backgroundColor = '#FFFFFF';
    ringStyle.border = `2px solid #CF222E`;
  } else {
    ringStyle.backgroundColor = '#FFFFFF';
    ringStyle.border = `2px dashed #D9E2EC`;
  }

  const lineColor =
    status === 'passed' && !isLast ? '#0E7C7E' : !isLast ? '#D9E2EC' : 'transparent';

  return (
    <div className="flex flex-1 items-start relative">
      <div className="flex flex-col items-center z-10 min-w-[90px]">
        <div
          className="h-12 w-12 flex items-center justify-center rounded-full ring-offset-2"
          style={ringStyle}
        >
          <GateIcon status={status} />
        </div>
        <div className="mt-3 text-center">
          <div
            className="text-[12px] font-semibold"
            style={{ color: status === 'pending' ? '#8EA8C3' : '#0F2137' }}
          >
            {name}
          </div>
          <div
            className={`text-[11px] font-medium mt-1 inline-flex items-center rounded-sm px-1.5 py-0.5 ${
              PILL_COLORS[status]?.bg || 'bg-gray-100'
            } ${PILL_COLORS[status]?.text || 'text-gray-600'}`}
            style={{ borderRadius: '4px' }}
          >
            {status === 'passed' ? 'Passed' : status === 'failed' ? 'Failed' : 'Pending'}
          </div>
        </div>
      </div>
      {!isLast && (
        <div
          className="absolute top-6 left-1/2 h-[2px] w-full"
          style={{ backgroundColor: lineColor, opacity: status === 'passed' ? 0.5 : 0.5 }}
        />
      )}
    </div>
  );
}

function ScoreMeter({ pd }: { pd: number }) {
  const pdPct = Math.min(100, pd * 100);
  const segments = [
    { upTo: 10, color: '#3FB950', label: 'Low' },
    { upTo: 20, color: '#F5BA58', label: 'Medium' },
    { upTo: 100, color: '#F85149', label: 'High' },
  ];
  const currentSegment = segments.find((s) => pdPct <= s.upTo) || segments[segments.length - 1];

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Gauge className="h-4 w-4" style={{ color: '#2E5EAA' }} />
          <span className="text-[13px] font-medium text-[#0F2137]">Probability of Default</span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className="font-mono text-[18px] font-bold"
            style={{ color: currentSegment.color }}
          >
            {pdPct.toFixed(1)}%
          </span>
          <span
            className={`text-[10px] font-bold tracking-wider px-2 py-0.5 rounded-sm ${
              PILL_COLORS[
                currentSegment.label === 'Low'
                  ? 'approve'
                  : currentSegment.label === 'Medium'
                  ? 'review'
                  : 'decline'
              ].bg
            } ${
              PILL_COLORS[
                currentSegment.label === 'Low'
                  ? 'approve'
                  : currentSegment.label === 'Medium'
                  ? 'review'
                  : 'decline'
              ].text
            }`}
            style={{ borderRadius: '4px' }}
          >
            {currentSegment.label.toUpperCase()}
          </span>
        </div>
      </div>
      <div className="relative h-3 rounded-sm overflow-hidden bg-[#D9E2EC]" style={{ borderRadius: '6px' }}>
        <div className="absolute inset-0 flex">
          <div
            className="h-full"
            style={{ width: '25%', backgroundColor: segments[0].color, opacity: 0.35 }}
          />
          <div
            className="h-full"
            style={{ width: '25%', backgroundColor: segments[1].color, opacity: 0.35 }}
          />
          <div
            className="h-full"
            style={{ width: '50%', backgroundColor: segments[2].color, opacity: 0.35 }}
          />
        </div>
        <div
          className="absolute left-0 top-0 h-full transition-all"
          style={{
            width: `${pdPct}%`,
            background: `linear-gradient(90deg, ${currentSegment.color}, ${currentSegment.color}cc)`,
          }}
        />
        <div
          className="absolute top-1/2 -translate-y-1/2 h-5 w-[3px] bg-white border border-[#0F2137]"
          style={{ left: `${pdPct}%`, borderRadius: '2px' }}
        />
      </div>
      <div className="flex justify-between mt-1.5 text-[10px] font-mono text-[#5B6B7B]">
        <span>0%</span>
        <span>10%</span>
        <span>20%</span>
        <span>τ=25%</span>
      </div>
    </div>
  );
}

function EvidenceCompositionBar({
  historyMonths,
  aaCompleteness,
  uliCompleteness,
}: {
  historyMonths: number;
  aaCompleteness: number;
  uliCompleteness: number;
}) {
  const hPct = (Math.min(historyMonths, 12) / 12) * 100;
  const aaPct = aaCompleteness * 100;
  const uliPct = uliCompleteness * 100;
  const weighted = 0.5 * hPct + 0.25 * aaPct + 0.25 * uliPct;

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[12px] font-medium text-[#0F2137]">Evidence composition</span>
        <span className="font-mono text-[12px] font-bold text-[#B9770E]">{weighted.toFixed(1)}%</span>
      </div>
      <div className="space-y-1.5">
        <div>
          <div className="flex justify-between text-[11px] mb-0.5">
            <span className="text-[#5B6B7B]">History (w=0.50)</span>
            <span className="font-mono text-[#B9770E]">{hPct.toFixed(0)}%</span>
          </div>
          <div className="h-1.5 bg-[#F5E6CC] rounded-sm overflow-hidden" style={{ borderRadius: '3px' }}>
            <div
              className="h-full transition-all"
              style={{ width: `${hPct}%`, backgroundColor: '#D4A448' }}
            />
          </div>
        </div>
        <div>
          <div className="flex justify-between text-[11px] mb-0.5">
            <span className="text-[#5B6B7B]">AA (w=0.25)</span>
            <span className="font-mono text-[#B9770E]">{aaPct.toFixed(0)}%</span>
          </div>
          <div className="h-1.5 bg-[#F5E6CC] rounded-sm overflow-hidden" style={{ borderRadius: '3px' }}>
            <div
              className="h-full transition-all"
              style={{ width: `${aaPct}%`, backgroundColor: '#E8B85C' }}
            />
          </div>
        </div>
        <div>
          <div className="flex justify-between text-[11px] mb-0.5">
            <span className="text-[#5B6B7B]">ULI (w=0.25)</span>
            <span className="font-mono text-[#B9770E]">{uliPct.toFixed(0)}%</span>
          </div>
          <div className="h-1.5 bg-[#F5E6CC] rounded-sm overflow-hidden" style={{ borderRadius: '3px' }}>
            <div
              className="h-full transition-all"
              style={{ width: `${uliPct}%`, backgroundColor: '#F5BA58' }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function DecisionResultContent() {
  const { id: _id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { decisionOutcome, assessmentState, history: _history, clearDecision } = useAssessmentStore();
  const { toggleAuditDrawer } = useUIStore();

  const { applicant, finances, evidence, decisionMode } = assessmentState;
  const { debtRatio, expRatio } = calculateFinancialRatios(
    finances.monthlyIncome,
    finances.monthlyExpenses,
    finances.monthlyDebt
  );
  const liquidityMonths =
    finances.monthlyExpenses > 0 ? finances.liquidityMean / finances.monthlyExpenses : 0;
  const dtiPct = debtRatio * 100;
  const tenureYears = (applicant.tenureMonths / 12).toFixed(1);

  const gateStatuses = decisionOutcome
    ? GATE_NAMES.map((_, i) => decisionOutcome.gates[i]?.status || 'passed')
    : GATE_NAMES.map(() => 'passed' as const);

  if (!decisionOutcome) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="mx-auto max-w-md text-center py-16">
          <div className="mx-auto h-20 w-20 flex items-center justify-center rounded-full bg-[#F0F4F8] mb-6">
            <FileText className="h-10 w-10 text-[#8EA8C3]" />
          </div>
          <h1 className="text-[24px] font-bold text-[#0F2137] mb-2">No assessment results yet</h1>
          <p className="text-[15px] text-[#5B6B7B] mb-8">
            Run a credit assessment to see the decision outcome with detailed gate analysis.
          </p>
          <Link
            to="/assessment"
            className="inline-flex items-center gap-2 px-5 py-2.5 text-[14px] font-semibold text-white rounded-sm transition-colors hover:opacity-90"
            style={{ backgroundColor: '#0E7C7E', borderRadius: '8px' }}
          >
            <Play className="h-4 w-4" />
            Go to Assessment
          </Link>
        </div>
      </div>
    );
  }

  const { status, riskScore, policyScore, evidenceScore, finalScore, riskPD, rationale: _rationale, gates, creditScore, creditScoreDisplay } =
    decisionOutcome;

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      {/* Navigation Tabs */}
      <div className="mb-6 border-b border-[#E2E8F0]">
        <div className="flex gap-1">
          <Link
            to="/assessment"
            className="flex items-center gap-2 px-5 py-3 text-[14px] font-medium text-[#5B6B7B] border-b-2 border-transparent hover:text-[#0F2137] transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Assessment
          </Link>
          <button
            className="flex items-center gap-2 px-5 py-3 text-[14px] font-semibold border-b-2"
            style={{
              color: '#0E7C7E',
              borderColor: '#0E7C7E',
              backgroundColor: 'rgba(14, 124, 126, 0.10)',
            }}
          >
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: '#0E7C7E' }}
            />
            Decision Result
          </button>
        </div>
      </div>

      {/* Page Header */}
      <div className="flex flex-wrap justify-between items-start gap-4 mb-8">
        <div>
          <h1 className="text-[28px] font-bold text-[#0F2137] leading-tight">Decision Result</h1>
          <div className="flex items-center gap-2 mt-1 text-[14px] text-[#5B6B7B]">
            <span className="font-mono font-medium">{applicant.id}</span>
            <span>·</span>
            <span>{applicant.displayName}</span>
            <span>·</span>
            <span className="flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" />
              Assessed just now
            </span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <StatusBadge status={status} score={finalScore} />
          <div className="flex items-center gap-2">
            <button
              onClick={toggleAuditDrawer}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-[13px] font-medium text-[#0F2137] bg-white border border-[#E2E8F0] rounded-sm hover:bg-[#F6F8FA] transition-colors"
              style={{ borderRadius: '8px' }}
            >
              <FileCheck2 className="h-4 w-4" />
              View audit trace
            </button>
            <button
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-[13px] font-medium text-[#0F2137] bg-white border border-[#E2E8F0] rounded-sm hover:bg-[#F6F8FA] transition-colors"
              style={{ borderRadius: '8px' }}
            >
              <Download className="h-4 w-4" />
              Export PDF
            </button>
            <button
              onClick={() => {
                clearDecision();
                navigate('/assessment');
              }}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-[13px] font-semibold text-white rounded-sm transition-colors hover:opacity-90"
              style={{ backgroundColor: '#0E7C7E', borderRadius: '8px' }}
            >
              <Play className="h-4 w-4" />
              Run new assessment
            </button>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="lg:grid lg:grid-cols-12 gap-8">
        {/* LEFT COLUMN */}
        <div className="lg:col-span-8 space-y-6">
          {/* GATE FLOW PIPELINE CARD */}
          <div className="bg-white rounded-sm border border-[#E2E8F0] p-6" style={{ borderRadius: '12px' }}>
            <div className="mb-6">
              <h2 className="text-[18px] font-semibold text-[#0F2137]">Decision pipeline</h2>
              <p className="text-[13px] text-[#5B6B7B] mt-1">6 gate evaluation with layered logic</p>
            </div>
            <div className="flex items-start justify-between px-4">
              {GATE_NAMES.map((name, idx) => (
                <GateNode
                  key={name}
                  name={name}
                  status={(gateStatuses[idx] || 'passed') as 'passed' | 'failed' | 'pending'}
                  isLast={idx === GATE_NAMES.length - 1}
                />
              ))}
            </div>
          </div>

          {/* DOMAIN CARDS SECTION */}
          <div className="grid md:grid-cols-1 gap-4">
            {/* RISK DomainCard */}
            <DomainCard domain="risk" title="Risk Metrics" score={riskScore}>
              <ScoreMeter pd={riskPD} />
              <div
                className="grid grid-cols-2 gap-3 p-3 border border-[#E2E8F0] bg-white"
                style={{ borderRadius: '10px' }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Activity className="h-4 w-4" style={{ color: '#2E5EAA' }} />
                    <span className="text-[12px] text-[#5B6B7B]">Probability of Default</span>
                  </div>
                </div>
                <div className="text-right">
                  <span
                    className="font-mono text-[16px] font-bold"
                    style={{
                      color: riskPD < 0.1 ? '#3FB950' : riskPD < 0.2 ? '#F5BA58' : '#F85149',
                    }}
                  >
                    {(riskPD * 100).toFixed(1)}%
                  </span>
                  <span
                    className={`ml-2 text-[10px] font-bold px-1.5 py-0.5 rounded-sm ${
                      riskPD < 0.1
                        ? `${PILL_COLORS.approve.bg} ${PILL_COLORS.approve.text}`
                        : riskPD < 0.2
                        ? `${PILL_COLORS.review.bg} ${PILL_COLORS.review.text}`
                        : `${PILL_COLORS.decline.bg} ${PILL_COLORS.decline.text}`
                    }`}
                    style={{ borderRadius: '4px' }}
                  >
                    τ=25%
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <Wallet className="h-4 w-4" style={{ color: '#2E5EAA' }} />
                  <span className="text-[12px] text-[#5B6B7B]">Expected Loss Rate</span>
                </div>
                <div className="text-right">
                  <span className="font-mono text-[14px] font-bold text-[#0F2137]">
                    {(riskPD * 0.35 * 100).toFixed(2)}%
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <CreditCard className="h-4 w-4" style={{ color: '#2E5EAA' }} />
                  <span className="text-[12px] text-[#5B6B7B]">Debt-to-Income ratio</span>
                </div>
                <div className="text-right">
                  <span
                    className="font-mono text-[14px] font-bold"
                    style={{
                      color: dtiPct < 40 ? '#3FB950' : dtiPct < 55 ? '#F5BA58' : '#F85149',
                    }}
                  >
                    {dtiPct.toFixed(1)}%
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <PiggyBank className="h-4 w-4" style={{ color: '#2E5EAA' }} />
                  <span className="text-[12px] text-[#5B6B7B]">Liquidity buffer</span>
                </div>
                <div className="text-right">
                  <span
                    className="font-mono text-[14px] font-bold"
                    style={{
                      color: liquidityMonths >= 3 ? '#3FB950' : liquidityMonths >= 1 ? '#F5BA58' : '#F85149',
                    }}
                  >
                    {liquidityMonths.toFixed(1)} mo
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <Waves className="h-4 w-4" style={{ color: '#2E5EAA' }} />
                  <span className="text-[12px] text-[#5B6B7B]">Income volatility score</span>
                </div>
                <div className="text-right">
                  <span
                    className="font-mono text-[14px] font-bold"
                    style={{
                      color:
                        finances.incomeVolatility < 0.15
                          ? '#3FB950'
                          : finances.incomeVolatility < 0.25
                          ? '#F5BA58'
                          : '#F85149',
                    }}
                  >
                    {(finances.incomeVolatility * 100).toFixed(0)}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <Building2 className="h-4 w-4" style={{ color: '#2E5EAA' }} />
                  <span className="text-[12px] text-[#5B6B7B]">Tenure stability index</span>
                </div>
                <div className="text-right">
                  <span
                    className="font-mono text-[14px] font-bold"
                    style={{
                      color: applicant.tenureMonths >= 24 ? '#3FB950' : applicant.tenureMonths >= 12 ? '#F5BA58' : '#F85149',
                    }}
                  >
                    {Math.min(100, Math.round((applicant.tenureMonths / 60) * 100))}/100
                  </span>
                </div>
              </div>

              <div className="mt-4">
                <div className="text-[12px] font-semibold text-[#0F2137] mb-2">Top contributing factors</div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="flex items-start gap-2 p-2.5 bg-white border border-[#E2E8F0]" style={{ borderRadius: '8px' }}>
                    <ArrowUpRight className="h-4 w-4 mt-0.5 flex-shrink-0" style={{ color: '#3FB950' }} />
                    <div>
                      <div className="text-[12px] font-medium text-[#0F2137]">Multi-platform income</div>
                      <div className="text-[11px] text-[#5B6B7B]">Diversified revenue streams · -0.02 PD</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2 p-2.5 bg-white border border-[#E2E8F0]" style={{ borderRadius: '8px' }}>
                    <ArrowUpRight className="h-4 w-4 mt-0.5 flex-shrink-0" style={{ color: '#3FB950' }} />
                    <div>
                      <div className="text-[12px] font-medium text-[#0F2137]">Stable tenure ({applicant.tenureMonths} mo)</div>
                      <div className="text-[11px] text-[#5B6B7B]">Seasoned platform presence</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2 p-2.5 bg-white border border-[#E2E8F0]" style={{ borderRadius: '8px' }}>
                    <ArrowDownRight className="h-4 w-4 mt-0.5 flex-shrink-0" style={{ color: '#F5BA58' }} />
                    <div>
                      <div className="text-[12px] font-medium text-[#0F2137]">Income volatility</div>
                      <div className="text-[11px] text-[#5B6B7B]">Above baseline +{(finances.incomeVolatility * 0.18 * 100).toFixed(1)}pp PD</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-2 p-2.5 bg-white border border-[#E2E8F0]" style={{ borderRadius: '8px' }}>
                    <ArrowDownRight className="h-4 w-4 mt-0.5 flex-shrink-0" style={{ color: '#F85149' }} />
                    <div>
                      <div className="text-[12px] font-medium text-[#0F2137]">Thin liquidity tail</div>
                      <div className="text-[11px] text-[#5B6B7B]">Min buffer close to threshold</div>
                    </div>
                  </div>
                </div>
              </div>
            </DomainCard>

            {/* EVIDENCE DomainCard */}
            <DomainCard domain="evidence" title="Evidence & Stability" score={evidenceScore}>
              <div className="flex flex-wrap gap-2 mb-4">
                <div className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-[#E2E8F0]" style={{ borderRadius: '6px' }}>
                  <Clock className="h-3.5 w-3.5" style={{ color: '#B9770E' }} />
                  <span className="text-[11px] font-medium text-[#5B6B7B]">History</span>
                  <span className="font-mono text-[12px] font-bold text-[#B9770E]">{evidence.historyMonths} mo</span>
                </div>
                <div className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-[#E2E8F0]" style={{ borderRadius: '6px' }}>
                  <FileBadge className="h-3.5 w-3.5" style={{ color: '#B9770E' }} />
                  <span className="text-[11px] font-medium text-[#5B6B7B]">AA complete</span>
                  <span className="font-mono text-[12px] font-bold text-[#B9770E]">
                    {(evidence.aaCompleteness * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-[#E2E8F0]" style={{ borderRadius: '6px' }}>
                  <ShieldCheck className="h-3.5 w-3.5" style={{ color: '#B9770E' }} />
                  <span className="text-[11px] font-medium text-[#5B6B7B]">ULI complete</span>
                  <span className="font-mono text-[12px] font-bold text-[#B9770E]">
                    {(evidence.uliCompleteness * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              <EvidenceCompositionBar
                historyMonths={evidence.historyMonths}
                aaCompleteness={evidence.aaCompleteness}
                uliCompleteness={evidence.uliCompleteness}
              />

              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="p-3 bg-white border border-[#E2E8F0]" style={{ borderRadius: '8px' }}>
                  <div className="flex items-center gap-1.5 mb-1">
                    <TrendingUp className="h-3.5 w-3.5" style={{ color: '#3FB950' }} />
                    <span className="text-[11px] font-medium text-[#5B6B7B]">Trend indicator</span>
                  </div>
                  <div className="font-mono text-[14px] font-bold text-[#0F2137]">Available</div>
                  <div className="text-[11px] font-medium text-[#3FB950]">+0.04 monthly stability</div>
                </div>
                <div className="p-3 bg-white border border-[#E2E8F0]" style={{ borderRadius: '8px' }}>
                  <div className="flex items-center gap-1.5 mb-1">
                    <BarChart3 className="h-3.5 w-3.5" style={{ color: '#B9770E' }} />
                    <span className="text-[11px] font-medium text-[#5B6B7B]">Seasonality index</span>
                  </div>
                  <div className="font-mono text-[14px] font-bold text-[#0F2137]">Moderate</div>
                  <div className="font-mono text-[12px] text-[#5B6B7B]">
                    σ = {(finances.incomeVolatility * 1.3).toFixed(2)} (Q4 bias)
                  </div>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[12px] font-medium text-[#0F2137]">Model confidence</span>
                  <span className="font-mono text-[12px] font-bold text-[#B9770E]">
                    {(evidenceScore * 95).toFixed(0)}%
                  </span>
                </div>
                <div className="h-2.5 bg-[#F5E6CC] rounded-sm overflow-hidden" style={{ borderRadius: '6px' }}>
                  <div
                    className="h-full transition-all"
                    style={{
                      width: `${evidenceScore * 95}%`,
                      background: 'linear-gradient(90deg, #D4A448, #B9770E)',
                    }}
                  />
                </div>
                <div className="flex justify-between mt-1 text-[10px] font-mono text-[#5B6B7B]">
                  <span>Low</span>
                  <span>τ=50%</span>
                  <span>High</span>
                </div>
              </div>
            </DomainCard>

            {/* POLICY DomainCard */}
            <DomainCard domain="policy" title="Policy Enforcement" score={policyScore}>
              <div className="space-y-2">
                {[
                  {
                    id: 'R-POL-001',
                    desc: 'Age requirement ≥ 21 years',
                    passed: !applicant.ageUnknown && applicant.age >= 21,
                  },
                  {
                    id: 'R-POL-002',
                    desc: `Tenure minimum ≥ 6 months (actual: ${applicant.tenureMonths} mo)`,
                    passed: applicant.tenureMonths >= 6,
                  },
                  {
                    id: 'R-POL-003',
                    desc: 'Occupation eligibility: Approved category',
                    passed: true,
                  },
                  {
                    id: 'R-POL-004',
                    desc: applicant.eshramRegistered
                      ? 'e-Shram registration verified'
                      : 'e-Shram not registered (flagged)',
                    passed: applicant.eshramRegistered,
                  },
                  {
                    id: 'R-POL-005',
                    desc: `Thin-file override · DTI ${dtiPct.toFixed(1)}% vs 50% cap`,
                    passed: dtiPct <= 50,
                  },
                  {
                    id: 'R-POL-006',
                    desc: `Expense ratio ${(expRatio * 100).toFixed(1)}% ≤ 85%`,
                    passed: expRatio <= 0.85,
                  },
                ].map((rule) => (
                  <div
                    key={rule.id}
                    className="flex items-start gap-3 p-3 bg-white border border-[#E2E8F0]"
                    style={{ borderRadius: '8px' }}
                  >
                    <span
                      className="font-mono text-[11px] font-bold tracking-wide px-2 py-0.5 flex-shrink-0"
                      style={{
                        backgroundColor: 'rgba(107, 76, 154, 0.10)',
                        color: '#6B4C9A',
                        borderRadius: '4px',
                        fontFamily: "'JetBrains Mono', ui-monospace, monospace",
                      }}
                    >
                      {rule.id}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="text-[13px] text-[#0F2137]">{rule.desc}</div>
                    </div>
                    {rule.passed ? (
                      <CheckCircle2 className="h-4 w-4 flex-shrink-0 mt-0.5" style={{ color: '#3FB950' }} />
                    ) : (
                      <AlertTriangle className="h-4 w-4 flex-shrink-0 mt-0.5" style={{ color: '#F5BA58' }} />
                    )}
                  </div>
                ))}
              </div>
            </DomainCard>
          </div>

          {/* CREDIT SCORE PANEL */}
          {(creditScore != null || creditScoreDisplay != null) && (
            <div className="bg-white rounded-sm border border-[#E2E8F0] p-6" style={{ borderRadius: '12px' }}>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-[18px] font-semibold text-[#0F2137]">Credit Score</h2>
                <span className="text-[11px] text-[#5B6B7B] bg-[#F0F4F8] px-2 py-0.5 rounded">
                  {creditScoreDisplay?.phase ?? 'Phase 1 heuristic (demo)'}
                </span>
              </div>
              <div className="flex flex-col items-center py-4">
                <div className="font-mono text-[64px] font-bold leading-none" style={{ color: (creditScore ?? 0) >= 700 ? '#3FB950' : (creditScore ?? 0) >= 550 ? '#F5BA58' : '#F85149' }}>
                  {creditScore ?? '—'}
                </div>
                <div className="text-[15px] text-[#5B6B7B] mt-2">
                  PD {creditScoreDisplay?.pd_percent?.toFixed(1) ?? (riskPD * 100).toFixed(1)}%
                </div>
              </div>
              <div className="border-t border-[#E2E8F0] pt-4 flex items-center justify-between text-[13px]">
                <span className="text-[#5B6B7B]">Approval threshold</span>
                <span className="font-mono font-bold text-[#0F2137]">
                  {creditScoreDisplay?.threshold_score ?? '—'} ({creditScoreDisplay?.threshold_pd_percent?.toFixed(1) ?? '—'}% PD)
                </span>
              </div>
              <p className="mt-3 text-[11px] text-[#8EA8C3] leading-relaxed">
                {creditScoreDisplay?.disclaimer ?? 'Illustrative score derived from default probability. Not comparable to bureau scores.'}
              </p>
            </div>
          )}

          {/* DECISION RATIONALE CARD */}
          <div className="bg-white rounded-sm border border-[#E2E8F0] p-6" style={{ borderRadius: '12px' }}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-[18px] font-semibold text-[#0F2137]">Decision rationale</h2>
              <div className="flex items-center gap-1.5 text-[11px] text-[#5B6B7B]">
                <Clock className="h-3.5 w-3.5" />
                <span>Last recomputed just now</span>
              </div>
            </div>
            <div className="space-y-4 text-[14px] leading-relaxed text-[#2D3E50]">
              <p>
                <strong className="text-[#0F2137]">Risk assessment (weight 42%):</strong> The applicant
                shows a Probability of Default of {(riskPD * 100).toFixed(1)}%, which is{' '}
                {riskPD < 0.1
                  ? 'well below the 25% acceptance threshold'
                  : riskPD < 0.2
                  ? 'within the acceptable range'
                  : 'above the typical threshold but compensated by other factors'}{' '}
                under the current risk model. Key positives include{' '}
                {applicant.tenureMonths >= 12
                  ? `${tenureYears} years of platform tenure`
                  : applicant.multiPlatform
                  ? 'multi-platform revenue diversification'
                  : 'e-Shram registration status'}
                , while{' '}
                {finances.incomeVolatility > 0.2
                  ? 'income volatility remains a monitoring point'
                  : dtiPct > 35
                  ? `DTI of ${dtiPct.toFixed(1)}% warrants attention`
                  : 'the liquidity position is stable'}
                .
              </p>
              <p>
                <strong className="text-[#0F2137]">Evidence validation (weight 25%):</strong> Evidence
                scoring reached {(evidenceScore * 100).toFixed(1)}%, supported by{' '}
                {evidence.historyMonths}-month transaction history with AA completeness of{' '}
                {(evidence.aaCompleteness * 100).toFixed(0)}%. The model confidence of{' '}
                {(evidenceScore * 95).toFixed(0)}% is{' '}
                {evidenceScore >= 0.65
                  ? 'robust and above the 50% minimum'
                  : 'moderate — thin-file considerations were applied'}
                . Seasonality is {finances.incomeVolatility > 0.18 ? 'noticeable' : 'low'} with Q4
                income bias factored into the PD adjustment.
              </p>
              <p>
                <strong className="text-[#0F2137]">Policy gate (weight 33%):</strong> Running in{' '}
                {decisionMode} mode, the policy layer evaluated 6 mandatory rules.{' '}
                {policyScore >= 0.85
                  ? 'All critical requirements passed including age, tenure minimums, and income threshold.'
                  : policyScore >= 0.55
                  ? 'Most rules passed; marginal flags were weighed against compensating factors.'
                  : 'Several policy amber flags exist and were routed for manual review.'}{' '}
                The composite score of {(finalScore * 100).toFixed(0)} / 100 resulted in a{' '}
                <strong
                  style={{
                    color:
                      status === 'approve'
                        ? '#1A6F31'
                        : status === 'review'
                        ? '#8A5D00'
                        : '#911A20',
                  }}
                >
                  {status.toUpperCase()}
                </strong>{' '}
                outcome.
              </p>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN */}
        <div className="lg:col-span-4 space-y-6">
          <div className="sticky top-24 space-y-6">
            {/* Summary Card */}
            <div
              className="bg-white rounded-sm border border-[#E2E8F0] shadow-sm p-6"
              style={{ borderRadius: '12px' }}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-[16px] font-semibold text-[#0F2137]">Decision summary</h3>
                <span
                  className="font-mono text-[10px] font-bold px-2 py-0.5 tracking-wider text-[#5B6B7B] border border-[#E2E8F0]"
                  style={{ borderRadius: '4px' }}
                >
                  {decisionMode}
                </span>
              </div>

              <div className="flex justify-center mb-4">
                <StatusBadge status={status} score={finalScore} />
              </div>

              <div className="grid grid-cols-2 gap-3 my-5">
                <div
                  className="p-3 border border-[#E2E8F0]"
                  style={{
                    borderRadius: '8px',
                    backgroundColor: 'rgba(46, 94, 170, 0.04)',
                    borderLeft: '3px solid #2E5EAA',
                  }}
                >
                  <div className="font-mono text-[18px] font-bold text-[#2E5EAA]">
                    {(riskScore * 100).toFixed(0)}
                  </div>
                  <div className="text-[11px] text-[#5B6B7B] mt-0.5">Risk score</div>
                </div>
                <div
                  className="p-3 border border-[#E2E8F0]"
                  style={{
                    borderRadius: '8px',
                    backgroundColor: 'rgba(185, 119, 14, 0.04)',
                    borderLeft: '3px solid #B9770E',
                  }}
                >
                  <div className="font-mono text-[18px] font-bold text-[#B9770E]">
                    {(evidenceScore * 100).toFixed(0)}
                  </div>
                  <div className="text-[11px] text-[#5B6B7B] mt-0.5">Evidence score</div>
                </div>
                <div
                  className="p-3 border border-[#E2E8F0]"
                  style={{
                    borderRadius: '8px',
                    backgroundColor: 'rgba(107, 76, 154, 0.04)',
                    borderLeft: '3px solid #6B4C9A',
                  }}
                >
                  <div className="font-mono text-[18px] font-bold text-[#6B4C9A]">
                    {(policyScore * 100).toFixed(0)}
                  </div>
                  <div className="text-[11px] text-[#5B6B7B] mt-0.5">Policy score</div>
                </div>
                <div
                  className="p-3 border border-[#E2E8F0]"
                  style={{
                    borderRadius: '8px',
                    backgroundColor: 'rgba(14, 124, 126, 0.04)',
                    borderLeft: '3px solid #0E7C7E',
                  }}
                >
                  <div className="font-mono text-[18px] font-bold text-[#0E7C7E]">
                    {(finalScore * 100).toFixed(0)}
                  </div>
                  <div className="text-[11px] text-[#5B6B7B] mt-0.5">Composite score</div>
                </div>
              </div>

              <div className="border-t border-[#E2E8F0] pt-4">
                <div className="text-[12px] font-semibold text-[#0F2137] mb-2">Threshold checks</div>
                <div className="space-y-2">
                  {[
                    {
                      label: 'Risk PD',
                      cutoff: 'τ = 25.0%',
                      actual: `${(riskPD * 100).toFixed(1)}%`,
                      pass: riskPD < 0.25,
                    },
                    {
                      label: 'Evidence score',
                      cutoff: 'τ = 0.50',
                      actual: evidenceScore.toFixed(2),
                      pass: evidenceScore >= 0.5,
                    },
                    {
                      label: 'Policy gates',
                      cutoff: `${gates.filter((g) => g.status === 'passed').length}/${gates.length}`,
                      actual: 'all required',
                      pass: gates.filter((g) => g.status === 'passed').length >= 4,
                    },
                  ].map((t) => (
                    <div
                      key={t.label}
                      className="flex items-center justify-between py-1.5 text-[12px]"
                    >
                      <span className="text-[#5B6B7B]">{t.label}</span>
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-[11px] text-[#8EA8C3]">{t.cutoff}</span>
                        <span
                          className={`font-mono font-bold ${
                            t.pass ? 'text-[#1A6F31]' : 'text-[#911A20]'
                          }`}
                        >
                          {t.actual}
                        </span>
                        {t.pass ? (
                          <CheckCircle2 className="h-3.5 w-3.5" style={{ color: '#3FB950' }} />
                        ) : (
                          <XOctagon className="h-3.5 w-3.5" style={{ color: '#F85149' }} />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="border-t border-[#E2E8F0] mt-4 pt-4">
                <div className="flex items-center justify-between text-[12px] mb-3">
                  <span className="text-[#5B6B7B]">Decision mode used</span>
                  <span
                    className="font-mono text-[11px] font-bold px-2 py-0.5"
                    style={{
                      backgroundColor:
                        decisionMode === 'D1'
                          ? 'rgba(248, 81, 73, 0.12)'
                          : decisionMode === 'D2'
                          ? 'rgba(245, 186, 88, 0.15)'
                          : decisionMode === 'D3'
                          ? 'rgba(63, 185, 80, 0.12)'
                          : 'rgba(14, 124, 126, 0.12)',
                      color:
                        decisionMode === 'D1'
                          ? '#911A20'
                          : decisionMode === 'D2'
                          ? '#8A5D00'
                          : decisionMode === 'D3'
                          ? '#1A6F31'
                          : '#0E7C7E',
                      borderRadius: '4px',
                    }}
                  >
                    {decisionMode} ·{' '}
                    {decisionMode === 'D1'
                      ? 'Strict'
                      : decisionMode === 'D2'
                      ? 'Standard'
                      : decisionMode === 'D3'
                      ? 'Lenient'
                      : 'Expansion'}
                  </span>
                </div>
                <div className="flex gap-2">
                  <button
                    className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 text-[13px] font-medium text-[#0F2137] bg-white border border-[#E2E8F0] rounded-sm hover:bg-[#F6F8FA] transition-colors"
                    style={{ borderRadius: '8px' }}
                  >
                    <Download className="h-4 w-4" />
                    Save to history
                  </button>
                  <Link
                    to="/assessment"
                    className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 text-[13px] font-semibold text-white rounded-sm transition-colors hover:opacity-90"
                    style={{ backgroundColor: '#0E7C7E', borderRadius: '8px' }}
                  >
                    <ArrowLeft className="h-4 w-4" />
                    Back
                  </Link>
                </div>
              </div>
            </div>

            {/* Applicant Snapshot Card */}
            <div
              className="bg-white rounded-sm border border-[#E2E8F0] p-5"
              style={{ borderRadius: '12px' }}
            >
              <h3 className="text-[15px] font-semibold text-[#0F2137] mb-4">Applicant snapshot</h3>
              <div className="flex items-center gap-3 mb-4 pb-4 border-b border-[#E2E8F0]">
                <div
                  className="h-11 w-11 rounded-full flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: 'rgba(14, 124, 126, 0.12)' }}
                >
                  <User className="h-5 w-5" style={{ color: '#0E7C7E' }} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-[14px] font-semibold text-[#0F2137] truncate">
                    {applicant.displayName}
                  </div>
                  <div className="font-mono text-[12px] text-[#5B6B7B]">{applicant.id}</div>
                </div>
              </div>
              <div className="space-y-3 text-[13px]">
                {[
                  { label: 'Age', value: applicant.ageUnknown ? 'Unverified' : `${applicant.age} yrs` },
                  { label: 'Occupation', value: applicant.occupation, mono: false },
                  {
                    label: 'Tenure',
                    value: `${applicant.tenureMonths} mo (${tenureYears} yrs)`,
                    mono: true,
                  },
                  {
                    label: 'Platforms',
                    value: applicant.multiPlatform ? 'Multi-platform' : 'Single platform',
                  },
                  {
                    label: 'Monthly income',
                    value: `₹${finances.monthlyIncome.toLocaleString()}`,
                    mono: true,
                  },
                ].map((item) => (
                  <div
                    key={item.label}
                    className="flex items-center justify-between"
                  >
                    <span className="text-[#5B6B7B]">{item.label}</span>
                    <span
                      className={`font-semibold text-[#0F2137] ${item.mono !== false ? 'font-mono' : ''}`}
                      style={item.mono !== false ? { fontFamily: "'JetBrains Mono', ui-monospace, monospace" } : {}}
                    >
                      {item.value}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Actions Card */}
            <div
              className="bg-white rounded-sm border border-[#E2E8F0]"
              style={{ borderRadius: '12px' }}
            >
              <button
                className="w-full flex items-center gap-3 px-5 py-3.5 text-[14px] font-medium text-[#0F2137] hover:bg-[#F6F8FA] transition-colors text-left border-b border-[#F0F4F8]"
                onClick={() => {
                  const mailto = `mailto:ops@synthgigcredit.in?subject=Decision Report ${applicant.id}&body=Applicant: ${applicant.displayName}%0AOutcome: ${status.toUpperCase()}%0ARisk PD: ${(riskPD * 100).toFixed(1)}%25%0AEvidence: ${(evidenceScore * 100).toFixed(0)}%25%0APolicy score: ${(policyScore * 100).toFixed(0)}%25`;
                  window.location.href = mailto;
                }}
              >
                <Mail className="h-4 w-4 flex-shrink-0 text-[#5B6B7B]" />
                <span>Email report to ops</span>
                <ArrowUpRight className="h-4 w-4 ml-auto text-[#8EA8C3]" />
              </button>
              <button
                className="w-full flex items-center gap-3 px-5 py-3.5 text-[14px] font-medium text-[#0F2137] hover:bg-[#F6F8FA] transition-colors text-left border-b border-[#F0F4F8]"
                onClick={() => {
                  const payload = {
                    applicant_id: applicant.id,
                    applicant_name: applicant.displayName,
                    assessed_at: new Date().toISOString(),
                    outcome: status,
                    risk_pd: riskPD,
                    credit_score: creditScore,
                    evidence_score: evidenceScore,
                    policy_score: policyScore,
                    final_score: finalScore,
                    decision_mode: decisionMode,
                    gates: gates.map(g => ({ name: g.name, status: g.status, score: g.score })),
                    credit_score_display: creditScoreDisplay,
                  };
                  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `decision_${applicant.id}_${Date.now()}.json`;
                  a.click();
                  URL.revokeObjectURL(url);
                }}
              >
                <FileJson className="h-4 w-4 flex-shrink-0 text-[#5B6B7B]" />
                <span>Download JSON</span>
                <ArrowUpRight className="h-4 w-4 ml-auto text-[#8EA8C3]" />
              </button>
              <button
                className="w-full flex items-center gap-3 px-5 py-3.5 text-[14px] font-medium text-[#0F2137] hover:bg-[#F6F8FA] transition-colors text-left border-b border-[#F0F4F8]"
                onClick={() => navigate('/assessment')}
              >
                <Copy className="h-4 w-4 flex-shrink-0 text-[#5B6B7B]" />
                <span>Duplicate assessment</span>
                <ArrowUpRight className="h-4 w-4 ml-auto text-[#8EA8C3]" />
              </button>
              <button
                className="w-full flex items-center gap-3 px-5 py-3.5 text-[14px] font-medium text-[#5B6B7B] hover:bg-[#F6F8FA] transition-colors text-left"
                style={{ borderRadius: '12px' }}
                disabled
                title="Override requires admin role"
              >
                <Settings2 className="h-4 w-4 flex-shrink-0 text-[#BCCCDC]" />
                <span className="text-[#BCCCDC]">Override decision</span>
                <span className="ml-auto text-[10px] font-bold uppercase tracking-wider text-[#BCCCDC] bg-[#F0F4F8] px-1.5 py-0.5 rounded">Admin</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function DecisionResultPage() {
  return (
    <DashboardLayout>
      <DecisionResultContent />
    </DashboardLayout>
  );
}
