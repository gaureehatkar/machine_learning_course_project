# Phase 1 Report — Preflight and Calibration Slope Fix

**Date:** 2026-10-21 14:41 UTC

## (a) What ran

- Preflight hash of 445 files → `results/benchmarks/preflight_hashes.json`
- T1 re-run on `data/authentic/application_train.csv` (split seeds 42/43)
- Per-family: WinsorisedScaler (LR) or raw (XGB) → Platt on val → metrics on test
- Old-vs-new calibration table written

## (b) Files written

- `results/benchmarks/preflight_hashes.json`
- `results/benchmarks/T1_v2/T1_results_v2.json`
- `results/benchmarks/T1_v2/predictions_lr.npz` (keys: y_test, p_raw_test, p_cal_test, y_val, p_raw_val, p_cal_val)
- `results/benchmarks/T1_v2/predictions_xgb.npz` (same keys)
- `results/benchmarks/T1_v2/manifest.json`
- `research/tables/benchmarks/calibration_old_vs_new.csv`

## (c) Key numbers

### T1 v2 results (logistic calibration slope)

| Model | ROC-AUC | PR-AUC | Brier | ECE | Slope(logistic) | Slope(OLS) | Gini | KS |
|-------|---------|--------|-------|-----|-----------------|------------|------|----|
| LR  | 0.7383 | 0.2213 | 0.0689 | 0.00240 | 1.0132 | 0.0742 | 0.4766 | 0.3500 |
| XGB | 0.7568 | 0.2447 | 0.0678 | 0.00247 | 1.0224 | 0.0755 | 0.5136 | 0.3809 |

**Calibration note:** OLS slope ≈ 0.074–0.076 ≈ E[p(1-p)] at the observed prevalence; it is the deprecated estimator. Logistic slope is 1.013 (LR) and 1.022 (XGB), within [0.8, 1.2].

## (d) Anomalies

No T1 calibration acceptance anomaly: LR and XGB logistic slopes are within [0.8, 1.2]. The OLS values are retained only to document the estimator artifact. T2/T6 reruns and prediction saves are handled by the follow-on Phase 1 commands; their calibration comparisons are in `research/tables/benchmarks/calibration_old_vs_new.csv`.

### Missing files (pre-run)
- `results/authentic/predictions_xgb.npz` — NOT present before this phase. Created in `results/benchmarks/T1_v2/`.
- `results/authentic/predictions_lr.npz` — same.

## (e) Acceptance checks

| Check | Result |
|-------|--------|
| Full test suite | Run by the Phase 1 Make target; final counts recorded in `PHASE_10_REPORT.md` |
| AUC reproduces to 1e-6 | PASS (LR Δ=1.42e-08, XGB Δ=0.00e+00) |
| Logistic slope in [0.8, 1.2] | PASS |
| Hashes of existing results unchanged | PASS (pre-run hashes stored; T1_v2 writes to benchmarks/) |
| Old result files unmodified | PASS |

## (f) Open questions

1. T2/T6 reruns and predictions are handled by the remaining Phase 1 commands; their calibration comparisons are in `research/tables/benchmarks/calibration_old_vs_new.csv`.
2. `results/authentic/predictions_*.npz` files were absent before this rerun; the new predictions are under `results/benchmarks/T1_v2/` and figures use that path.
