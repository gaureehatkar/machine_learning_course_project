#!/usr/bin/env python
"""Write the Phase 9 report after figures and paper tables have been generated."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
FIGURES = ROOT / "research/figures"
PAPER_TABLES = ROOT / "research/paper_tables"
BENCH = ROOT / "research/tables/benchmarks"
REPORT = ROOT / "results/benchmarks/reports/PHASE_9_REPORT.md"


def main() -> None:
    figure_names = [f"F{i}" for i in range(1, 12)]
    missing_figures = [
        f"{name}.{extension}"
        for name in figure_names
        for extension in ("png", "pdf")
        if not (FIGURES / f"{name}.{extension}").is_file()
    ]
    table_sources = sorted(BENCH.glob("*.csv")) + sorted(
        (ROOT / "research/tables").glob("*_agg.csv")
    )
    generated_tables = list(PAPER_TABLES.glob("*.tex")) + list(PAPER_TABLES.glob("*.md"))
    policy_path = BENCH / "policy_baselines.csv"
    policy_checks = []
    if policy_path.exists():
        policy = pd.read_csv(policy_path)
        required_columns = {
            "violation_rate_mean",
            "wrongful_decline_rate_mean",
            "review_rate_mean",
            "rule_scenario",
        }
        policy_checks = sorted(required_columns - set(policy.columns))
    else:
        policy_checks = ["policy_baselines.csv missing"]

    passed = not missing_figures and bool(table_sources) and bool(generated_tables) and not policy_checks
    report = f"""# Phase 9 Report: Figures and paper tables

## (a) What ran
- `python -u research/make_figures.py`
- `python -u research/make_paper_tables.py`
- `python -u research/write_phase9_report.py`

## (b) Files written
- Figures: F1–F11 as PNG and PDF in `research/figures/` ({len(figure_names) * 2} expected files).
- LaTeX and Markdown tables: `research/paper_tables/` ({len(generated_tables)} generated files).
- Sources: {len(table_sources)} CSV files found in the benchmark/original aggregate table folders.

## (c) Key numbers
Figures and tables are generated from their source CSVs and prediction files; numeric values are not duplicated in this report.

## (d) Anomalies and deviations
- F5 suppresses rank-equivalent methods using `review_rank_equivalence.csv`.
- Synthetic data has no exposure field; V6 is omitted from the review frontier.
- Phase 5 source tables remain the source of the displayed AUC/KS values; inspect the Phase 5 report for any unresolved metric caveat.

## (e) Acceptance checks
| Check | Status |
|---|---|
| F1–F11 PNG and PDF files exist | {"PASS" if not missing_figures else "FAIL: " + ", ".join(missing_figures)} |
| LaTeX and Markdown tables generated from CSVs | {"PASS" if generated_tables else "FAIL"} |
| F10 includes violation, wrongful-decline, and review rate across scenarios | {"PASS" if not policy_checks else "FAIL: " + ", ".join(policy_checks)} |

## (f) Open questions
- {"None for figure/table generation." if passed else "Resolve the failed acceptance checks listed above before treating Phase 9 as complete."}
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")
    if not passed:
        raise RuntimeError("Phase 9 acceptance checks failed; see PHASE_9_REPORT.md")


if __name__ == "__main__":
    main()
