import DashboardLayout from '@/components/layout/DashboardLayout';
import { Database, CheckCircle2, ExternalLink, Info } from 'lucide-react';

const datasets = [
  {
    id: 'DS-001',
    name: 'Home Credit Default Risk',
    type: 'Authentic',
    rows: 307511,
    columns: 122,
    status: 'ready',
    usedFor: 'T1 — LR/XGBoost baseline experiment',
    source: 'Kaggle competition dataset',
    url: 'https://www.kaggle.com/competitions/home-credit-default-risk/data',
    defaultRate: '8.07%',
    split: '60% train / 20% val / 20% test (stratified)',
    notes: 'Russian consumer loans. Population mismatch with Indian gig workers — used for model validation only.',
  },
  {
    id: 'DS-002',
    name: 'COVID-19 & Human Security (Bangalore Gig Workers)',
    type: 'Grounding',
    rows: 2830,
    columns: null,
    status: 'ready',
    usedFor: 'G0 grounding — validates synthetic data distributions',
    source: 'Mendeley Data (CC BY 4.0)',
    url: 'https://data.mendeley.com/datasets/j6hd2dfsh8/1',
    defaultRate: 'N/A (no default labels)',
    split: 'N/A',
    notes: 'Bangalore gig workers survey. Used to confirm synthetic DGP is plausible for Indian context.',
  },
  {
    id: 'DS-003',
    name: 'SynthGigCredit-IN DGP1 (Base)',
    type: 'Synthetic',
    rows: 25000 * 11,
    columns: 23,
    status: 'ready',
    usedFor: 'T2-T9 experiments (seeds 0-10)',
    source: 'Generated — src/data_generation/generate_data.py',
    url: null,
    defaultRate: '12-15% (target range)',
    split: '60% train / 20% val / 20% test (stratified)',
    notes: 'LogNormal income, seasonal variation, liquidity recursion. Seed 0 = G0 validation only.',
  },
  {
    id: 'DS-004',
    name: 'SynthGigCredit-IN DGP2 (Income Shock)',
    type: 'Synthetic',
    rows: 25000 * 11,
    columns: 23,
    status: 'ready',
    usedFor: 'T2-T9 robustness experiments (seeds 0-10)',
    source: 'Generated — src/data_generation/generate_data.py',
    url: null,
    defaultRate: '12-15% (target range)',
    split: '60% train / 20% val / 20% test (stratified)',
    notes: 'DGP1 + 10% probability of 50% income drop (platform deactivation shock).',
  },
];

const typeStyle: Record<string, string> = {
  Authentic:  'bg-blue-100 text-blue-800',
  Grounding:  'bg-amber-100 text-amber-800',
  Synthetic:  'bg-purple-100 text-purple-800',
};

function fmt(n: number): string {
  return n.toLocaleString('en-IN');
}

export default function DatasetsPage() {
  return (
    <DashboardLayout>
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h1 className="font-bold text-[#0F2137] tracking-tight" style={{ fontSize: '28px' }}>
            Datasets
          </h1>
          <p className="text-[15px] text-[#5B6B7B] mt-1.5">
            All datasets used in the SynthGigCredit research pipeline.
          </p>
        </div>

        {/* Info banner */}
        <div className="flex items-start gap-3 p-4 mb-6 rounded-lg border border-[#0E7C7E33] bg-[#F0FAFA]">
          <Info className="h-5 w-5 text-[#0E7C7E] flex-shrink-0 mt-0.5" />
          <p className="text-[13px] text-[#0E7C7E]">
            Authentic and grounding datasets must be downloaded separately (see links below).
            Synthetic datasets are generated locally via <code>python generate_all_seeds.py</code>.
          </p>
        </div>

        <div className="space-y-4">
          {datasets.map((ds) => (
            <div key={ds.id} className="bg-white rounded-lg border border-[#E2E8F0] p-5">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="h-9 w-9 flex items-center justify-center rounded-md bg-[#0E7C7E1A]">
                    <Database className="h-4 w-4 text-[#0E7C7E]" />
                  </div>
                  <div>
                    <h2 className="text-[15px] font-semibold text-[#0F2137]">{ds.name}</h2>
                    <p className="text-[12px] text-[#5B6B7B]">{ds.usedFor}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${typeStyle[ds.type]}`}>
                    {ds.type}
                  </span>
                  <span className="flex items-center gap-1 text-[11px] text-[#3FB950] font-medium">
                    <CheckCircle2 className="h-3.5 w-3.5" /> ready
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
                <div className="p-2 bg-[#F8FAFC] rounded text-center">
                  <div className="text-[10px] text-[#5B6B7B]">Rows</div>
                  <div className="font-mono text-[13px] font-bold text-[#0F2137]">{fmt(ds.rows)}</div>
                </div>
                <div className="p-2 bg-[#F8FAFC] rounded text-center">
                  <div className="text-[10px] text-[#5B6B7B]">Columns</div>
                  <div className="font-mono text-[13px] font-bold text-[#0F2137]">{ds.columns ?? '—'}</div>
                </div>
                <div className="p-2 bg-[#F8FAFC] rounded text-center">
                  <div className="text-[10px] text-[#5B6B7B]">Default Rate</div>
                  <div className="font-mono text-[13px] font-bold text-[#0F2137]">{ds.defaultRate}</div>
                </div>
                <div className="p-2 bg-[#F8FAFC] rounded text-center">
                  <div className="text-[10px] text-[#5B6B7B]">Split</div>
                  <div className="text-[11px] font-medium text-[#0F2137]">{ds.split}</div>
                </div>
              </div>

              <div className="flex items-center justify-between text-[12px] text-[#5B6B7B]">
                <span>{ds.notes}</span>
                {ds.url && (
                  <a href={ds.url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1 text-[#0E7C7E] hover:underline flex-shrink-0 ml-4">
                    <ExternalLink className="h-3.5 w-3.5" /> Download
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
