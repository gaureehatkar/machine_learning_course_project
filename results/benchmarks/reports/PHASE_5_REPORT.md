# Phase 5 Report: Risk-model baselines

**Status: INCOMPLETE — protocol corrections are implemented but not yet rerun and validated.**

## (a) What ran

- The runner has been updated to read trial count, folds, seed, feature sets, and model search spaces from `configs/benchmarks.yaml`.
- It now tunes each DGP and each requested feature set separately, includes standalone median-imputed LR, and uses the full Home Credit training split.
- Tuned parameters are regenerated on each run rather than loaded from a stale cache, and Phase 6 consumers now read the feature-set-specific parameter layout.
- No corrected model rerun has completed. The previous global Python environment crashes while importing XGBoost (Windows access violation `-1073741819`); an isolated pinned environment is being prepared.

## (b) Existing outputs

- `results/benchmarks/tuned_params.json`
- `research/tables/benchmarks/risk_baselines_synthetic.csv`
- `research/tables/benchmarks/risk_baselines_synthetic_raw.csv`
- `research/tables/benchmarks/risk_baselines_home_credit.csv`

## (c) Key numbers

No new Phase 5 results were computed. Existing CSVs contain prior measurements and must not be described as results from the corrected protocol.

## (d) Anomalies and deviations

- The existing aggregate calibration-slope values were generated with an earlier argument-order defect and must not be reported as corrected logistic slopes.
- The corrected tuning and model-selection code has not yet been exercised end-to-end.
- No report numbers are repeated here because the prior report's inline values did not consistently match the CSVs.

## (e) Acceptance checks

| Check | Status |
|---|---|
| Equal 30-trial tuning per model, DGP, and feature set | NOT YET VERIFIED |
| Standalone LR included | IMPLEMENTED, NOT YET VERIFIED |
| Correct logistic slope/intercept outputs | NOT YET VERIFIED |
| Reproducible model rerun | BLOCKED pending isolated environment validation |

## (f) Open questions

- Validate the isolated pinned ML dependency environment, run Phase 5, and replace the stale baseline CSVs only after the run succeeds.
