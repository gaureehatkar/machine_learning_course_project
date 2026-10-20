#!/usr/bin/env python
"""Emit LaTeX booktabs + Markdown paper tables from existing CSVs only."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
OUT = ROOT / "research/paper_tables"
BENCH = ROOT / "research/tables/benchmarks"
TABLES = ROOT / "research/tables"
OUT.mkdir(parents=True, exist_ok=True)

SPECS = [
    ("T1_calibration_old_vs_new", BENCH / "calibration_old_vs_new.csv",
     "T1/T2/T6 old OLS vs logistic calibration slope and reproduced AUC/Brier/ECE."),
    ("T2_ablation", TABLES / "T2_ablation_agg.csv",
     "Feature-set ablation A/B/C × LR/XGB (original T2 aggregate)."),
    ("T3_gating", TABLES / "T3_gating_agg.csv",
     "D1–D4 gating rates (original T3)."),
    ("T3_tau_e", TABLES / "T3_tau_e_agg.csv",
     "Evidence threshold sensitivity."),
    ("T4_matched_coverage", BENCH / "matched_coverage.csv",
     "Matched-coverage default-rate differences (D1 − Dx)."),
    ("T5_risk_baselines_synthetic", BENCH / "risk_baselines_synthetic.csv",
     "Equal-tuning risk baselines on synthetic data (AUC usable; slope column is an arg-order artifact)."),
    ("T5_risk_baselines_home_credit", BENCH / "risk_baselines_home_credit.csv",
     "Equal-tuning risk baselines on Home Credit."),
    ("T6_history", BENCH / "T6_history_agg_v2_Hnum.csv",
     "History-length sensitivity with numeric H_num (copy of T6 v2)."),
    ("T6A_architecture", BENCH / "architecture_model_agnostic.csv",
     "D4+R1 pipeline across risk-model families."),
    ("T6C_policy_baselines", BENCH / "policy_baselines.csv",
     "Policy handling baselines P0–P4."),
    ("T7_review_baselines", BENCH / "review_baselines.csv",
     "Review-allocation strategies (Phase 7)."),
    ("T7_rank_equivalence", BENCH / "review_rank_equivalence.csv",
     "Spearman of priority vs PD; fraction identical to R1 at B=20%."),
    ("T7_cost_sensitivity", BENCH / "cost_sensitivity.csv",
     "Cost per applicant on C_FN/C_FP × C_R grid."),
    ("T8_statistical_tests", BENCH / "statistical_tests.csv",
     "Paired tests: primary Bonferroni, secondary Holm."),
    ("T2_policy_v2_vs_legacy", BENCH / "policy_v2_vs_legacy.csv",
     "Policy v2 agri scenarios vs legacy D4 metrics."),
    ("T3_dgp_latent", BENCH / "dgp_latent_diagnostic.csv",
     "Latent vs default_flag AUC and Spearman (analysis only)."),
]


def latex_escape(s: str) -> str:
    return (
        str(s)
        .replace("\\", "\\textbackslash{}")
        .replace("_", "\\_")
        .replace("%", "\\%")
        .replace("&", "\\&")
    )


def df_to_latex(df: pd.DataFrame, caption: str, label: str) -> str:
    cols = [latex_escape(c) for c in df.columns]
    col_fmt = "l" + "r" * (len(df.columns) - 1)
    lines = [
        "\\begin{table}[htbp]",
        "  \\centering",
        f"  \\caption{{{latex_escape(caption)}}}",
        f"  \\label{{tab:{label}}}",
        "  \\small",
        "  \\begin{tabular}{" + col_fmt + "}",
        "    \\toprule",
        "    " + " & ".join(cols) + " \\\\",
        "    \\midrule",
    ]
    for _, row in df.iterrows():
        vals = []
        for v in row.values:
            if isinstance(v, float):
                vals.append(f"{v:.4g}")
            else:
                vals.append(latex_escape(v))
        lines.append("    " + " & ".join(vals) + " \\\\")
    lines += [
        "    \\bottomrule",
        "  \\end{tabular}",
        "\\end{table}",
        "",
    ]
    return "\n".join(lines)


def main():
    missing = []
    bundle = ["# Paper tables (generated from CSVs)\n"]
    for name, path, caption in SPECS:
        if not path.exists():
            missing.append(str(path))
            print(f"  SKIP missing {path}")
            continue
        df = pd.read_csv(path)
        # keep tables printable
        if len(df) > 80:
            df = df.head(80)
        tex = df_to_latex(df, caption, name)
        (OUT / f"{name}.tex").write_text(tex, encoding="utf-8")
        md = f"### {name}\n\n{caption}\n\nSource: `{path.relative_to(ROOT)}`\n\n"
        try:
            md += df.to_markdown(index=False) + "\n"
        except Exception:
            md += df.to_csv(index=False) + "\n"
        (OUT / f"{name}.md").write_text(md, encoding="utf-8")
        bundle.append(md)
        print(f"  {name}")
    (OUT / "ALL_TABLES.md").write_text("\n".join(bundle), encoding="utf-8")
    if missing:
        print("Missing sources:", missing)
        sys.exit(1)
    print("paper_tables written")


if __name__ == "__main__":
    main()
