# Phase 1 Report: Preflight and calibration-slope correction

**Status: INCOMPLETE — file-integrity preflight is complete; model reruns were not reproducible in the current environment.**

## (a) What ran

- Existing Phase 1 artifacts were inspected.
- The previous preflight file recorded only 23 entries: 18 result/table files and five synthetic `applicants.parquet` files. It did not hash every file required by the prompt.
- The preflight manifest was regenerated with 414 entries across `data/synthetic/`, `results/`, and `research/tables/`, excluding its own output. The script was also corrected to use this full-file behavior.
- Three hashes did not match the previous manifest: `research/tables/T2_ablation_agg_v2.csv`, `research/tables/T6_history_agg_v2.csv`, and `data/synthetic/dgp1/seed1/applicants.parquet`. Their modification timestamps are from 2026-10-19, before this audit; the exact historical operation is not recoverable from Git because these files are ignored.
- The repository test suite passed: 140 tests.
- The full Phase 1 ML rerun was not completed in this audit. XGBoost import terminated Python with Windows access-violation exit code `-1073741819`; installed NumPy 2.2.6 differs from the pinned NumPy 1.26.4 in `requirements.lock`.

## (b) Existing outputs

- `results/benchmarks/T1_v2/T1_results_v2.json`
- `results/benchmarks/T1_v2/predictions_lr.npz`
- `results/benchmarks/T1_v2/predictions_xgb.npz`
- 120 T2 and 80 T6 `.npz` files are present in their v2 output folders.
- `research/tables/benchmarks/calibration_old_vs_new.csv`

These are prior artifacts; they were not regenerated during this audit.

## (c) Key numbers

No new Phase 1 model metrics were computed. Use the files listed above as the source of the previously recorded values.

## (d) Anomalies and deviations

- The old preflight manifest did not satisfy the required full-file hash coverage.
- Existing T1/T2/T6 metrics and calibration-slope reproductions were not independently rerun here.
- The v2 prediction files exist; the original `results/authentic/predictions_*.npz` files remain separate and were not changed.

## (e) Acceptance checks

| Check | Status |
|---|---|
| Hash every file under all three required roots | PASS (manifest regenerated) |
| Logistic calibration slope implementation/tests | PASS in code; prior test suite plus current suite passed |
| T1/T2/T6 rerun and reproduction checks | BLOCKED by XGBoost native access violation |
| Previous manifest entries unchanged | FAIL (three pre-existing differences from the stale manifest) |

## (f) Open questions

- Decide whether the three hash-mismatched files are an accepted pre-existing baseline or require investigation/restoration before rerunning the experiments.
- Install/restore the pinned dependency environment from `requirements.lock`, then rerun T1/T2/T6 and their metric-reproduction checks.
