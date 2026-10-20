# FINAL PROJECT TECHNICAL DOCUMENTATION v2

SynthGigCredit-IN: policy-constrained credit decisioning for thin-file gig workers (research prototype).

**Policy rules: UNVERIFIED.** Provenance in `configs/policy_rules/v2/` is placeholder text. Do not treat rule YAML as official PMMY/JanSamarth clauses.

## System

Three layers, combined by D1–D4 gates:

1. **Risk** — LR / XGBoost (and Phase 5 baselines) with Platt calibration on validation. Train on `features_full`, score val/test on `features_visible`.
2. **Evidence** — score from history length, AA completeness, ULI completeness; threshold τ_E.
3. **Policy** — Kleene three-valued engine. Legacy YAML in `configs/policy_rules/`; v2 in `configs/policy_rules/v2/` (PMMY only; no JanSamarth file — JanSamarth is a portal).

Decisions: APPROVE / REVIEW / DECLINE with reason codes. Review pool P = {PD < τ ∧ policy ≠ UNSATISFIED}; UNRESOLVED consumed first.

## Interfaces

- API: `app/api/` (if present in this copy).
- Frontend / Streamlit demo: `app/main.py`. Demo PD is **heuristic unless replaced** by a fitted model artifact; do not cite demo scores as T1/T2 numbers.
- Tests: `pytest tests/`.

## Experiments

T1–T9 originals remain in `research/tables/` and `results/authentic/`. Benchmark re-runs: `results/benchmarks/`, `research/tables/benchmarks/`. Paper-facing summary: `research/BENCHMARK_RESULTS.md`.

## Calibration

Use logistic slope (`calibration_slope_intercept`). The OLS slope (~0.075 on Home Credit) is a documented artifact. Phase 5 CSV slope columns were written with swapped arguments and are not usable until regenerated.

## What this document is not

Not a claim of field performance on Indian gig workers. Home Credit is a Kaggle consumer-loan dataset. Synthetic labels follow the generator.
