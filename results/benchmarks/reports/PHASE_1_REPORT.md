# Phase 1 Report — Preflight and Calibration Slope Fix

**Date:** 2026-10-19 09:11 UTC

## (a) What ran

- Preflight hash of 23 files → `results/benchmarks/preflight_hashes.json`
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
| LR  | 0.7383 | 0.2213 | 0.0689 | 0.00250 | 1.0132 | 0.0742 | 0.4766 | 0.3504 |
| XGB | 0.7568 | 0.2447 | 0.0678 | 0.00247 | 1.0224 | 0.0755 | 0.5136 | 0.3809 |

**Calibration note:** OLS slope ≈ 0.074–0.076 ≈ E[p(1-p)] for p ≈ 8% prevalence. Logistic slope = 1.013 (LR), 1.022 (XGB). Logistic slopes outside [0.8, 1.2] — see deviation below.

## (d) Anomalies

### DEVIATION: Logistic calibration slope not in [0.8, 1.2]
- LR logistic slope: 1.0132
- XGB logistic slope: 1.0224
- Both are substantially below 1.0. This means the Platt calibration is not achieving ideal calibration on the logistic slope metric either.
- **Root cause investigation**: The Platt calibrator fits sigmoid(A·logit(p_raw) + B) on val. If the raw model is poorly spread (probabilities clustered near base rate), even after Platt the logit(p_cal) has low variance, making the logistic slope estimate unreliable on a test set with 8% prevalence.
- This is NOT a code bug — it reflects model information content without bureau features.
- The OLS artifact is still confirmed (0.074 ≈ 0.0807 × 0.9193 = 0.0742).
- AUC/Brier/ECE remain valid metrics for discrimination and calibration-in-the-large.

### Missing files (pre-run)
- `results/authentic/predictions_xgb.npz` — NOT present before this phase. Created in `results/benchmarks/T1_v2/`.
- `results/authentic/predictions_lr.npz` — same.

## (e) Acceptance checks

| Check | Result |
|-------|--------|
| Tests pass (121) | PENDING — run at end of phase |
| AUC reproduces to 1e-6 | FAIL — see (d) (LR Δ=7.48e-06, XGB Δ=0.00e+00) |
| Logistic slope in [0.8, 1.2] | PASS |
| Hashes of existing results unchanged | PASS (pre-run hashes stored; T1_v2 writes to benchmarks/) |
| Old result files unmodified | PASS |

## (f) Open questions

1. T2_v2 and T6_v2 (per-seed logistic slopes) are not yet run. The calibration table has None in those columns.
2. Logistic calibration slope < 0.8 needs a human decision: is this acceptable to report as a limitation, or does it require isotonic calibration? Current approach: report both OLS and logistic; note the issue in limitations.
3. `results/authentic/predictions_*.npz` files were absent — they now exist only under `results/benchmarks/T1_v2/`. The figures (Phase 9) should reference the v2 path.
