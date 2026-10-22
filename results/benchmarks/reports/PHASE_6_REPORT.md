# Phase 6 Report: Architecture and policy baselines

## (a) What ran
- Architecture and single-score evaluations: `python -u research/run_phase6_architecture_and_policy.py`
- Policy baseline re-run: `python -u research/run_phase6_policy_baselines.py`
- Rule scenarios: legacy, v2_unknown, v2_ineligible, v2_eligible

## (b) Files written
- `research/tables/benchmarks/architecture_model_agnostic.csv`
- `research/tables/benchmarks/architecture_model_agnostic_per_seed.csv`
- `research/tables/benchmarks/single_score_vs_pipeline.csv`
- `research/tables/benchmarks/single_score_vs_pipeline_per_seed.csv`
- `research/tables/benchmarks/policy_baselines.csv` and `policy_baselines_per_seed.csv`
- `research/tables/benchmarks/policy_qualitative.md`
- `results/benchmarks/phase6_policy_baselines/manifest.json`
- `results/benchmarks/phase6_architecture/manifest.json`

## (c) Key numbers
Results are in the aggregated and per-seed CSVs above; this report does not duplicate values.

## (d) Anomalies and deviations
- Architecture-model and single-score tables use the models and scenarios recorded by their runner; the policy table includes all five policy methods and four rule scenarios.
- WoE-LR was skipped because optbinning/ropwr crashes the interpreter on this Windows environment. Logistic regression emitted sklearn convergence warnings during Phase 6A; its measured results are retained and should be interpreted with that limitation.
- Policy rule v2 provenance remains UNVERIFIED. Requested loan amounts are absent from the DGP and therefore only tested in the versioning unit test.

## (e) Acceptance checks
| Check | Status |
|---|---|
| Per-seed raw table and aggregate written | PASS |
| LR, RF, LightGBM, CatBoost, and XGBoost across 20% and 30% budgets | PASS |
| A2 includes P1 and P2 with no evidence gate | PASS |
| Train-only P3 imputation | PASS |
| Four rule scenarios | PASS |
| Wrongful-decline and violation definitions computed from true states | PASS |

## (f) Open questions
- None blocking this phase; official policy provenance still requires human verification.
