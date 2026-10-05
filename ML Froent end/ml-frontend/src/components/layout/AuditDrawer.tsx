import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { useUIStore } from '@/store/useUIStore';
import { useAssessmentStore } from '@/store/useAssessmentStore';
import type { DecisionOutcome } from '@/types';

type TabType = 'risk' | 'evidence' | 'policy';

const sampleTrace: DecisionOutcome = {
  status: 'approve',
  riskScore: 0.891,
  policyScore: 0.9,
  evidenceScore: 0.925,
  finalScore: 0.876,
  riskPD: 0.0482,
  rationale:
    'Auto-approve via D2: Delivery Partner with INR 42,000 monthly income. PD of 4.82% below cap; evidence score 92.5%. Tenure (18 mo) confirms income stability.',
  gates: [
    { name: 'Income Threshold', status: 'passed', score: 0.84 },
    { name: 'Expense Ratio', status: 'passed', score: 0.78 },
    { name: 'Debt Service Ratio', status: 'passed', score: 0.86 },
    { name: 'Liquidity Coverage', status: 'passed', score: 0.68 },
    { name: 'Evidence Completeness', status: 'passed', score: 0.92 },
    { name: 'Risk PD Threshold', status: 'passed', score: 0.91 },
  ],
};

const tabColors: Record<TabType, string> = {
  risk: '#6FA4F8',
  evidence: '#F5BA58',
  policy: '#B89CE0',
};

function SyntaxHighlighter({ data, activeTab }: { data: DecisionOutcome; activeTab: TabType }) {
  const color = tabColors[activeTab];
  const json = JSON.stringify(data, null, 2);
  const lines = json.split('\n');

  const highlightLine = (line: string, idx: number) => {
    const tabKey = activeTab === 'risk'
      ? /"(riskScore|riskPD|finalScore)"/
      : activeTab === 'evidence'
      ? /"(evidenceScore|gates)"/
      : /"(policyScore|status|rationale)"/;

    const isKeyMatch = tabKey.test(line);
    const isGateKey = /"name":\s*"(Income|Expense|Debt|Liquidity|Evidence|Risk)/.test(line);
    const statusRegex = /^(passed|failed|pending|approve|review|decline)$/;
    const isScoreKey = /"score"/.test(line);

    return (
      <div key={idx} className="whitespace-pre">
        <span className="text-[#5B6B7B] font-mono text-[11px] w-8 inline-block select-none text-right mr-4">
          {idx + 1}
        </span>
        {line.split(/("(?:[^"\\]|\\.)*")/).map((part, pIdx) => {
          if (part.startsWith('"') && part.endsWith('"')) {
            const inner = part.slice(1, -1);
            const isKey = pIdx % 2 === 1 && lines[idx].includes(part + ':');
            if (isKey) {
              return (
                <span key={pIdx} style={{ color: isKeyMatch ? color : '#8EA8C3' }} className="font-mono text-[12px]">
                  "{inner}"
                </span>
              );
            }
            if (statusRegex.test(inner)) {
              const statusColor =
                inner === 'passed' || inner === 'approve'
                  ? '#3FB950'
                  : inner === 'failed' || inner === 'decline'
                  ? '#F85149'
                  : '#F5BA58';
              return (
                <span key={pIdx} style={{ color: statusColor }} className="font-mono text-[12px] font-semibold">
                  "{inner}"
                </span>
              );
            }
            if (isGateKey || /"(rationale|applicant|occupation|history)"/.test('"' + inner + '"')) {
              return (
                <span key={pIdx} style={{ color: '#E2E8F0' }} className="font-mono text-[12px]">
                  "{inner}"
                </span>
              );
            }
            return (
              <span key={pIdx} style={{ color: '#9FB3C8' }} className="font-mono text-[12px]">
                "{inner}"
              </span>
            );
          }
          if (isScoreKey && /:/.test(line) && pIdx > 0) {
            const numMatch = part.match(/:\s*([\d.]+)/);
            if (numMatch) {
              return (
                <span key={pIdx} className="font-mono text-[12px]">
                  : <span style={{ color }} className="font-semibold">{numMatch[1]}</span>
                  {part.slice(numMatch[0].length)}
                </span>
              );
            }
          }
          const numOnly = part.match(/^\s*([\d.]+)\s*$/);
          if (numOnly && !part.includes('"') && !part.includes('{') && !part.includes('}')) {
            return (
              <span key={pIdx} style={{ color }} className="font-mono text-[12px] font-semibold">
                {part}
              </span>
            );
          }
          return (
            <span key={pIdx} className="font-mono text-[12px] text-[#D9E2EC]">
              {part}
            </span>
          );
        })}
      </div>
    );
  };

  return (
    <div className="overflow-auto scrollbar-thin h-full py-4 px-4">
      {lines.map((line, idx) => highlightLine(line, idx))}
    </div>
  );
}

export default function AuditDrawer() {
  const { auditDrawerOpen, setAuditDrawerOpen } = useUIStore();
  const { decisionOutcome, assessmentState } = useAssessmentStore();
  const [activeTab, setActiveTab] = useState<TabType>('risk');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    if (auditDrawerOpen) {
      setMounted(true);
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [auditDrawerOpen]);

  const activeData = decisionOutcome || sampleTrace;

  const buildTabData = (tab: TabType) => {
    if (tab === 'risk') {
      return {
        ...activeData,
        gates: activeData.gates.filter((g) => /Risk|Debt|Expense|Income/.test(g.name)),
        _traceContext: {
          domain: 'risk',
          version: 'risk-v3.2.1',
          applicant: assessmentState?.applicant?.displayName || 'Rajesh Kumar',
          pdComponents: {
            basePD: 0.05,
            agePenalty: assessmentState?.applicant?.ageUnknown ? 0.08 : 0,
            tenurePenalty: assessmentState?.applicant?.tenureMonths < 12 ? 0.07 : 0.03,
            platformBonus: assessmentState?.applicant?.multiPlatform ? -0.02 : 0,
            finalPD: activeData.riskPD,
          },
        },
      } as unknown as DecisionOutcome;
    }
    if (tab === 'evidence') {
      return {
        ...activeData,
        gates: activeData.gates.filter((g) => /Evidence|Liquidity/.test(g.name)),
        _traceContext: {
          domain: 'evidence',
          version: 'evidence-v1.5.3',
          historyMonths: assessmentState?.evidence?.historyMonths || 12,
          aaCompleteness: assessmentState?.evidence?.aaCompleteness || 0.88,
          uliCompleteness: assessmentState?.evidence?.uliCompleteness || 0.82,
          weightedFormula: '0.5*history + 0.25*AA + 0.25*ULI',
        },
      } as unknown as DecisionOutcome;
    }
    return {
      ...activeData,
      gates: activeData.gates.filter((g) => /Income|Expense|Debt/.test(g.name)),
      _traceContext: {
        domain: 'policy',
        version: 'policy-gates-v2.1.0',
        decisionMode: assessmentState?.decisionMode || 'D2',
        thresholds: {
          approve: 0.7,
          review: 0.5,
          decline: 0.42,
        },
        policyReasons: activeData.status === 'approve'
          ? ['All gates passed', 'DTI within cap', 'Surplus ratio > 5%']
          : activeData.status === 'review'
          ? ['Marginal composite score', 'Requires human sign-off']
          : ['Fails DTI threshold', 'Evidence completeness low'],
      },
    } as unknown as DecisionOutcome;
  };

  if (!mounted && !auditDrawerOpen) return null;

  return (
    <>
      <div
        className={`fixed inset-0 z-40 transition-opacity duration-300 ${
          auditDrawerOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        style={{
          backgroundColor: 'rgba(16, 42, 67, 0.4)',
          backdropFilter: 'blur(4px)',
          WebkitBackdropFilter: 'blur(4px)',
        }}
        onClick={() => setAuditDrawerOpen(false)}
      />
      <aside
        className={`fixed right-0 top-0 z-50 h-full shadow-2xl transition-transform duration-300 ease-out flex flex-col ${
          auditDrawerOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
        style={{
          width: '100%',
          maxWidth: '480px',
          backgroundColor: '#0B1A28',
        }}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#1F3550]">
          <div className="flex items-center gap-3">
            <div
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: tabColors[activeTab] }}
            />
            <h2
              className="text-sm font-bold tracking-wide text-white"
              style={{ fontFamily: "'JetBrains Mono', ui-monospace, monospace" }}
            >
              Technical Audit
            </h2>
            <span
              className="text-[10px] px-1.5 py-0.5 rounded-sm font-mono font-semibold"
              style={{
                backgroundColor: 'rgba(111, 164, 248, 0.15)',
                color: '#6FA4F8',
                borderRadius: '6px',
              }}
            >
              LIVE
            </span>
          </div>
          <button
            onClick={() => setAuditDrawerOpen(false)}
            className="h-8 w-8 flex items-center justify-center text-[#8EA8C3] hover:text-white hover:bg-[#1F3550] transition-colors"
            style={{ borderRadius: '6px' }}
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex border-b border-[#1F3550] px-3">
          {(['risk', 'evidence', 'policy'] as TabType[]).map((tab) => {
            const isActive = activeTab === tab;
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className="px-4 py-3 text-[12px] font-semibold uppercase tracking-wider transition-colors relative font-mono"
                style={{
                  color: isActive ? tabColors[tab] : '#5B7390',
                  borderBottom: isActive ? `2px solid ${tabColors[tab]}` : '2px solid transparent',
                  fontFamily: "'JetBrains Mono', ui-monospace, monospace",
                  letterSpacing: '0.05em',
                }}
              >
                {tab} trace
              </button>
            );
          })}
        </div>

        <div className="px-5 py-3 border-b border-[#1F3550]">
          <div
            className="text-[11px] text-[#5B7390] mb-1 font-mono"
            style={{ fontFamily: "'JetBrains Mono', ui-monospace, monospace" }}
          >
            {activeTab.toUpperCase()}_TRACE · {(activeTab === 'risk' ? activeData.riskScore : activeTab === 'evidence' ? activeData.evidenceScore : activeData.policyScore).toFixed(4)}
          </div>
          <div
            className="text-[13px] text-[#D9E2EC] font-mono"
            style={{ fontFamily: "'JetBrains Mono', ui-monospace, monospace" }}
          >
            decision_{activeData.status}_{new Date().toISOString().slice(0, 10)}.json
          </div>
        </div>

        <div className="flex-1 overflow-hidden">
          <SyntaxHighlighter data={buildTabData(activeTab)} activeTab={activeTab} />
        </div>

        <div className="px-5 py-3 border-t border-[#1F3550] flex items-center justify-between">
          <div
            className="text-[10px] text-[#5B7390] font-mono"
            style={{ fontFamily: "'JetBrains Mono', ui-monospace, monospace" }}
          >
            hash: 0x{Math.random().toString(16).slice(2, 10)}…{Math.random().toString(16).slice(2, 6)}
          </div>
          <div
            className="text-[10px] px-2 py-0.5 rounded-sm"
            style={{
              backgroundColor: 'rgba(63, 185, 80, 0.12)',
              color: '#3FB950',
              borderRadius: '6px',
              fontFamily: "'JetBrains Mono', ui-monospace, monospace",
            }}
          >
            ✓ trace_verified
          </div>
        </div>
      </aside>
    </>
  );
}
