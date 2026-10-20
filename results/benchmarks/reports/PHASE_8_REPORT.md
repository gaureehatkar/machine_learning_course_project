# Phase 8 Report: Statistical Tests

**Date**: 2026-10-20
**Status**: COMPLETE

## (a) What ran
- Command: `python -u research/run_phase8_statistical_tests.py`
- Module: `src/evaluation/paired_tests.py` (t.ppf from n, Holm, Bonferroni)
- Primary Bonferroni α = 0.05/3 = 0.016667 (3 contrasts per DGP)
- Confidence critical values are computed from each observed seed count with `scipy.stats.t.ppf`.

## (b) Files written
- `research/tables/benchmarks/statistical_tests.csv`
- `research/tables/benchmarks/T6_history_agg_v2_Hnum.csv` (copy; original T6 CSV untouched)

## (c) Primary contrasts

| dgp | contrast | mean_diff | ci_lo | ci_hi | t | p | p_adjusted | significant |
|---|---|---:|---:|---:|---:|---:|---:|---|
| DGP1 | A_vs_C_XGB_ROC_AUC | -0.003587 | -0.005987 | -0.001186 | -3.380 | 0.008129 | 0.02439 | True |
| DGP1 | D1_vs_D4_matched_coverage_DR | -0.014240 | -0.016008 | -0.012472 | -18.222 | 2.061e-08 | 6.182e-08 | True |
| DGP1 | R0_vs_R3_capture_B20 | 0.194974 | 0.151312 | 0.238637 | 10.102 | 3.289e-06 | 9.867e-06 | True |
| DGP2 | A_vs_C_XGB_ROC_AUC | -0.002000 | -0.003489 | -0.000511 | -3.039 | 0.01405 | 0.04214 | True |
| DGP2 | D1_vs_D4_matched_coverage_DR | -0.020130 | -0.022613 | -0.017647 | -18.342 | 1.945e-08 | 5.835e-08 | True |
| DGP2 | R0_vs_R3_capture_B20 | 0.158297 | 0.119302 | 0.197292 | 9.183 | 7.239e-06 | 2.172e-05 | True |

Total rows: 19; significant at family-wise rule: 16

## (d) Anomalies / deviations
- Primary 1 uses original T2 per-seed AUC (A_xgb vs C_xgb), not Phase 5 (Phase 5 slopes are a known arg-order artifact).
- Primary 2 uses Phase 4 legacy matched-coverage per-seed DRs; mean_diff = D1 − D4.
- Primary 3 uses Phase 7 V0_random vs V1_R3_hybrid at B=0.20, legacy rules.
- Rank-equivalence (Phase 7): V2/V3/V4 referred sets identical to R1 at B=0.20; they are not separate wins.

## (e) Acceptance checks
| Check | Status |
|---|---|
| Paired t from n seeds | PASS |
| Primary Bonferroni m=3 per DGP | PASS |
| T_CRIT hardcode removed | PASS |
| T6 H_num on a new copy | PASS |

## (f) Open questions
- Phase 5 logistic slopes remain the inverted-argument values until a re-run; AUC/PR/Brier in those CSVs are still usable.
