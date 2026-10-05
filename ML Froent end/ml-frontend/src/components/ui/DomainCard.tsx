import type { ReactNode } from 'react';

interface DomainCardProps {
  domain: 'risk' | 'evidence' | 'policy';
  title: string;
  children: ReactNode;
  score?: number;
}

const domainConfig = {
  risk: {
    accent: '#2E5EAA',
    tint: '#FAFCFF',
    pillBg: 'bg-[#E8F0FB]',
    pillText: 'text-[#2E5EAA]',
    label: 'RISK',
  },
  evidence: {
    accent: '#B9770E',
    tint: '#FFF9F0',
    pillBg: 'bg-[#FBEED7]',
    pillText: 'text-[#B9770E]',
    label: 'EVIDENCE',
  },
  policy: {
    accent: '#6B4C9A',
    tint: '#FAF7FD',
    pillBg: 'bg-[#EEE7F7]',
    pillText: 'text-[#6B4C9A]',
    label: 'POLICY',
  },
};

export default function DomainCard({ domain, title, children, score }: DomainCardProps) {
  const config = domainConfig[domain];

  return (
    <div
      className="relative overflow-hidden border border-[#E2E8F0] p-5"
      style={{
        borderRadius: '12px',
        backgroundColor: config.tint,
      }}
    >
      <div
        className="absolute left-0 top-0 h-full w-[3px]"
        style={{ backgroundColor: config.accent }}
      />
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span
            className={`inline-flex items-center rounded-sm px-2 py-1 text-[10px] font-bold tracking-wider ${config.pillBg} ${config.pillText}`}
            style={{ borderRadius: '6px' }}
          >
            {config.label}
          </span>
          <h3 className="text-sm font-semibold text-[#0F2137]">{title}</h3>
        </div>
        {typeof score === 'number' && (
          <div
            className="flex-shrink-0 rounded-sm border border-[#E2E8F0] bg-white px-2.5 py-1"
            style={{ borderRadius: '6px' }}
          >
            <span
              className="font-mono text-sm font-bold"
              style={{ color: config.accent }}
            >
              {(score * 100).toFixed(0)}
            </span>
            <span className="ml-0.5 font-mono text-[11px] text-[#5B6B7B]">/100</span>
          </div>
        )}
      </div>
      <div>{children}</div>
    </div>
  );
}
