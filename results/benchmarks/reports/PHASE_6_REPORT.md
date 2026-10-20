# Phase 6 Report: Architecture and policy baselines

**Status: INCOMPLETE — acceptance checks failed during audit.**

## (a) What ran

- Existing outputs and `research/run_phase6_architecture_and_policy.py` were inspected.
- Attempted `python -u research/run_phase6_policy_baselines.py`; the installed XGBoost native extension terminated Python with Windows access-violation exit code `-1073741819` before the run produced output.

## (b) Files written

- No Phase 6 result files were written by the attempted rerun.
- Existing artifacts are `research/tables/benchmarks/architecture_model_agnostic.csv`, `single_score_vs_pipeline.csv`, and `policy_baselines.csv`; their source script writes policy metrics for the legacy scenario only.

## (c) Key numbers

No new Phase 6 numbers were computed. The existing CSVs are the source of any previously reported values and are not represented here as completing this phase.

## (d) Anomalies and deviations

- The architecture runner evaluates five families but omits the requested standalone LR model.
- The single-score runner includes an evidence threshold, although the requested A2 baseline excludes the evidence gate.
- The existing policy baseline table lacks `wrongful_decline_rate`, `referred_truly_eligible_share`, and `recovered`, and does not cover the three v2 agri scenarios.
- Existing P3 code derives imputation values from the test attributes rather than fitting them on train.
- The new policy baseline runner and its metric unit tests are present, but execution is blocked by the installed XGBoost stack. Installed NumPy/XGBoost versions do not match `requirements.lock`.

## (e) Acceptance checks

| Check | Status |
|---|---|
| Architecture includes LR | FAIL |
| A2 excludes evidence gate | FAIL |
| Policy metrics and all four rule scenarios | FAIL |
| P3 imputation fitted on train only | FAIL in existing output runner |
| New policy metric unit tests | PASS (2 tests) |
| End-to-end policy baseline rerun | BLOCKED by native XGBoost access violation |

## (f) Open questions

- Restore the dependency environment from `requirements.lock` and rerun Phase 6 before using the new Phase 6C results.
- Official policy-rule provenance remains UNVERIFIED.
