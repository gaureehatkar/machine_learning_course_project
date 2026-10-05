import { CheckCircle2, AlertTriangle, XOctagon } from 'lucide-react';

interface StatusBadgeProps {
  status: 'approve' | 'review' | 'decline';
  score?: number;
  showIcon?: boolean;
}

const statusConfig = {
  approve: {
    surface: 'bg-[#EAF5EC]',
    border: 'border-[#3FB950]',
    text: 'text-[#0A3615]',
    label: 'APPROVED',
    Icon: CheckCircle2,
  },
  review: {
    surface: 'bg-[#FDF8E8]',
    border: 'border-[#E3B341]',
    text: 'text-[#412900]',
    label: 'REVIEW',
    Icon: AlertTriangle,
  },
  decline: {
    surface: 'bg-[#FDF0EF]',
    border: 'border-[#F85149]',
    text: 'text-[#5C0B11]',
    label: 'DECLINED',
    Icon: XOctagon,
  },
};

const thresholdMap: Record<'approve' | 'review' | 'decline', number> = {
  approve: 0.7,
  review: 0.5,
  decline: 0.4,
};

export default function StatusBadge({ status, score, showIcon = true }: StatusBadgeProps) {
  const config = statusConfig[status];
  const Icon = config.Icon;
  const threshold = thresholdMap[status];

  return (
    <div
      className={`inline-flex items-center gap-2 rounded-sm border px-3 py-1.5 ${config.surface} ${config.border} ${config.text}`}
      style={{ borderRadius: '6px' }}
    >
      {showIcon && <Icon className="h-4 w-4 flex-shrink-0" />}
      <span className="text-xs font-bold tracking-wide">{config.label}</span>
      {typeof score === 'number' && (
        <span className="font-mono text-[11px] opacity-80">
          {(score * 100).toFixed(0)}% / {(threshold * 100).toFixed(0)}%
        </span>
      )}
    </div>
  );
}
