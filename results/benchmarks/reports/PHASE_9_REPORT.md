# Phase 9 Report: Figures and paper tables

## (a) What ran
- `python -u research/make_figures.py`
- `python -u research/make_paper_tables.py`
- `python -u research/write_phase9_report.py`

## (b) Files written
- Figures: F1–F11 as PNG and PDF in `research/figures/` (22 expected files).
- LaTeX and Markdown tables: `research/paper_tables/` (33 generated files).
- Sources: 30 CSV files found in the benchmark/original aggregate table folders.

## (c) Key numbers
Figures and tables are generated from their source CSVs and prediction files; numeric values are not duplicated in this report.

## (d) Anomalies and deviations
- F5 suppresses rank-equivalent methods using `review_rank_equivalence.csv`.
- Synthetic data has no exposure field; V6 is omitted from the review frontier.
- F8 uses the rerun Phase 5 CSVs; logistic calibration-slope acceptance passed. WoE-LR was excluded because optbinning/ropwr crashes on this Windows environment.

## (e) Acceptance checks
| Check | Status |
|---|---|
| F1–F11 PNG and PDF files exist | PASS |
| LaTeX and Markdown tables generated from CSVs | PASS |
| F10 includes violation, wrongful-decline, and review rate across scenarios | PASS |

## (f) Open questions
- None for figure/table generation.
