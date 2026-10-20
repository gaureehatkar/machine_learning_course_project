# Phase 9 Report: Figures and paper tables

## (a) What ran
- `python -u research/make_figures.py`
- `python -u research/make_paper_tables.py`
- `python -u research/write_phase9_report.py`

## (b) Files written
- Figures: F1–F11 as PNG and PDF in `research/figures/` (22 expected files).
- LaTeX and Markdown tables: `research/paper_tables/` (33 generated files).
- Sources: 27 CSV files found in the benchmark/original aggregate table folders.

## (c) Key numbers
Figures and tables are generated from their source CSVs and prediction files; numeric values are not duplicated in this report.

## (d) Anomalies and deviations
- F5 suppresses rank-equivalent methods using `review_rank_equivalence.csv`.
- Synthetic data has no exposure field; V6 is omitted from the review frontier.
- Phase 5 source tables remain the source of the displayed AUC/KS values; inspect the Phase 5 report for any unresolved metric caveat.

## (e) Acceptance checks
| Check | Status |
|---|---|
| F1–F11 PNG and PDF files exist | FAIL: F10.png, F10.pdf |
| LaTeX and Markdown tables generated from CSVs | PASS |
| F10 includes violation, wrongful-decline, and review rate across scenarios | FAIL: rule_scenario, wrongful_decline_rate_mean |

## (f) Open questions
- Resolve the failed acceptance checks listed above before treating Phase 9 as complete.
