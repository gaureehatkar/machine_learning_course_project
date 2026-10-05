# IMPLEMENTATION PLAN
## Policy-Constrained Credit Decisioning with Evidence-Quality Gating for Thin-File Gig/Platform Workers
**Version 1.2 — Existing-Project Status Plan (2026-09-22)**

This is an EXISTING project. Tasks are divided into: ALREADY IMPLEMENTED, CURRENTLY PARTIAL, REQUIRED TO COMPLETE, and OPTIONAL/FUTURE.

---

## ALREADY IMPLEMENTED ✅

Every item below is verified by repository inspection. Code exists and runs.

| Component | File/Module | Status | Tests | Notes |
|---|---|---|---|---|
| Repo structure, configs, utilities | `src/utils/`, `configs/`, `Makefile`, `setup.py`, `requirements.txt` | ✅ Complete | Config loader tests implicit | All __init__.py present |
| DGP-1 and DGP-2 generator | `src/data_generation/dgp.py`, `generate_data.py` | ✅ Complete | T-D1..T-D9 pass | Both DGPs, all distributions, RNG separation |
| Feature engineering (23 cols, 6 views) | `src/feature_engineering/build_features.py` | ✅ Complete | `tests/test_features.py` | All formulas, NaN rules, cutoff invariant |
| Evidence engine | `src/evidence/compute_evidence.py` | ✅ Complete | `tests/test_evidence.py` | Formula, threshold, NaN handling |
| Policy engine framework | `src/policy/kleene.py`, `rule_loader.py`, `versioning.py`, `rule_engine.py` | ✅ Complete | `tests/test_policy.py` | Framework only; rule content UNVERIFIED |
| Policy rule fixtures | `configs/policy_rules/jan_samarth.yaml`, `pmmy.yaml` | ✅ Placeholder present | Policy tests use these | ALL content is `<UNVERIFIED>` |
| LR + XGBoost models | `src/models/train_models.py`, `predict.py` | ✅ Complete | Implicit in T1 | Feature-set assertion enforced |
| Platt calibration | `src/calibration/platt.py` | ✅ Complete | Implicit in T1 | Custom implementation, no sklearn APIs |
| Decision engine D1–D4 | `src/decisions/gate.py`, `tau.py` | ✅ Complete | `tests/test_decisions.py` | All 5 D4 truth-table rows tested |
| Review allocation R0–R3 | `src/decisions/review.py` | ✅ Complete | `tests/test_decisions.py` | R0/R1/R2/R3, oracle simulation |
| Evaluation metrics | `src/evaluation/metrics.py` | ✅ Complete | Implicit in T1 | PR-AUC, ROC-AUC, Brier, ECE, calibration, coverage/risk |
| Statistical tests | `src/evaluation/statistical_tests.py` | ✅ Complete | — | Seed CI, paired bootstrap, Bonferroni |
| Result aggregation | `src/evaluation/evaluate.py`, `aggregate.py` | ✅ Complete | — | Aggregates over seeds |
| TreeSHAP explainability (XGB) | `src/explainability/shap_values.py` | ✅ Complete | — | XGB only; raises ValueError for LR |
| Explanation JSON | `src/explainability/explain.py` | ✅ Complete | — | Full schema with provenance |
| Gate G0 (partial) | `src/data_validation/gate_g0.py` | ✅ Partial | G0 test in test_dgp | 5 of 9 checks coded |
| Streamlit demo | `app/main.py` | ✅ Runs | — | Heuristic PD; needs trained model for real PD |
| Authentic experiment T1 | `experiments/authentic/run.py` | ✅ Complete + results | — | `results/authentic/T1_results.json` |
| Ablation runner T2 | `experiments/ablation/run.py` | ✅ Code ready | — | No results yet |
| Gating runner T3 | `experiments/gating/run.py` | ✅ Code ready | — | No results yet |
| Review runner T4/T5 | `experiments/review/run.py` | ✅ Code ready | — | No results yet |
| History runner T6 | `experiments/history/run.py` | ✅ Code ready | — | No results yet |
| Dataset 2 freeze record | `docs/dataset2_freeze.md` | ✅ Complete | — | CC BY 4.0 VERIFIED |
| Policy rule verification template | `docs/policy_rule_verification.md` | ✅ Template | — | Verification not complete |
| README | `README.md` | ✅ Complete | — | |

---

## CURRENTLY PARTIAL ⚠️

| Component | Current State | Completed Portion | Missing Portion | File | Completion % | Dependency |
|---|---|---|---|---|---|---|
| Gate G0 | 5 of 9 checks coded; preconditions met | Checks 2,4,5,7,8; all preconditions | Checks 1 (distributional vs Dataset2), 3 (temporal behaviour), 6 (no leakage formal), 9 (stability/sensitivity) | `src/data_validation/gate_g0.py` | 60% | None (can run now) |
| Synthetic data (seeds 1–10) | Only g0_seed=0 generated | g0_seed parquet files for DGP1 | Seeds 1–10 × DGP 1 and 2 | `data/synthetic/` | 5% | G0 PASS |
| Policy rule content | Framework done; all content UNVERIFIED | Rule engine, loader, versioning, Kleene | Verified JanSamarth/PMMY rules from official documents | `configs/policy_rules/`, `docs/policy_rule_verification.md` | 50% | Human verification (Task 10b) |
| Streamlit demo (real PD) | Heuristic PD works | All three layers functional; full explanation JSON | Load trained model from disk for real PD; wire SHAP values | `app/main.py` | 75% | Trained model artifact |
| Test suite | 69 unit tests pass; only core math modules | DGP, features, evidence, policy, decision tests | Calibration, model, metrics, SHAP, review allocation, integration tests | `tests/` | 55% | None |
| G0 checks 1,3,6,9 | Not coded; described in docstring | Precondition structure | Actual check logic | `src/data_validation/gate_g0.py` | 60% | None |

---

## REQUIRED TO COMPLETE CURRENT PROJECT

Items that are required to produce the synthetic experiment results (T2–T6) and a fully functional demo.

### Priority 1 — BLOCKING (must complete before synthetic results)

| Task | File/Module | Purpose | Dependency | Input | Output | Test Required | Priority | Blocks PPT? |
|---|---|---|---|---|---|---|---|---|
| Run G0 and verify PASS | `src/data_validation/gate_g0.py` | Validate DGP; unlock synthetic experiments | Dataset 2 FROZEN ✅; thresholds set ✅ | g0_seed=0 parquet files | `results/gate_g0_report.json` with outcome=PASS | G0 checks 2,4,5,7,8 | P1 | Yes — synthetic results need G0 PASS |
| Generate synthetic seeds 1–10 | `src/data_generation/generate_data.py` | Produce 20 experimental datasets | G0 PASS | `configs/experiment.yaml` | `data/synthetic/dgp{1,2}/seed{1..10}/` | T-D7 (reproducibility) | P1 | Yes |
| Build feature tables seeds 1–10 | `src/feature_engineering/build_features.py` | Features for experiments | Seeds 1–10 generated | monthly, applicants parquets | `features_full.parquet`, `features_visible.parquet` | Feature set assertion | P1 | Yes |
| Run ablation T2 | `experiments/ablation/run.py` | A/B/C feature comparison (RQ1) | Features ready | features_full/visible | `results/ablation/.../T2_results.json` | — | P1 | Yes — core result |
| Run gating T3 | `experiments/gating/run.py` | D1–D4 comparison (RQ2, RQ3) | Features ready | features + policy attrs | `results/gating/.../T3_results.json` | — | P1 | Yes — core result |
| Run review T4/T5 | `experiments/review/run.py` | R0–R3 at 20%/30% (RQ4) | Features ready | features + policy attrs | `results/review/.../T4_T5_results.json` | — | P1 | Yes — core result |
| Run history T6 | `experiments/history/run.py` | History H=1,3,6,12 (RQ5) | Features ready | features (all views) | `results/history/.../T6_results.json` | — | P1 | Yes — core result |

### Priority 2 — IMPORTANT (improves project quality and demo)

| Task | File/Module | Purpose | Dependency | Priority | Blocks PPT? |
|---|---|---|---|---|---|
| Verify JanSamarth/PMMY rules (Task 10b) | `configs/policy_rules/`, `docs/policy_rule_verification.md` | Replace UNVERIFIED placeholders with real rules | Human verification of official documents | P2 | Partial (T3/T4/T5 results provisional without this) |
| Aggregate all results | `src/evaluation/aggregate.py` | Seed-level CIs for T2–T6 | T2–T6 complete | P2 | Yes |
| Connect trained model to Streamlit | `app/main.py` | Replace heuristic PD with real XGB-C | Trained model artifact from T2 | P2 | Improves demo |
| Add remaining G0 checks (1,3,6,9) | `src/data_validation/gate_g0.py` | Complete DGP validation | None | P2 | No |
| Add calibration and model tests | `tests/test_calibration.py`, `tests/test_models.py` | Full test coverage | None | P2 | No |

### Priority 3 — OPTIONAL / FUTURE

| Task | File/Module | Purpose | Priority | Notes |
|---|---|---|---|---|
| Fairness experiment T9 | `experiments/fairness/run.py` | e-Shram and AA subgroup analysis | P3 | Not blocking; currently empty __init__.py |
| Methodology validation | `experiments/methodology_validation/run.py` | policy_effect_delta recovery check | P3 | NEVER feeds main tables |
| Cost-function analysis | New experiment file | Expected cost grid L∈{3,5,10}, c_rev∈{0.1,0.2} | P3 | Config has parameters; no code |
| LR explainability | `src/explainability/shap_values.py` or new module | Odds ratios / coefficients for LR | P3 | Currently raises ValueError for LR |
| NLP policy extraction | `src/policy/nlp_extract/` | Automated rule extraction from PDF | Future | Currently empty — CONCEPTUAL |
| SHAP integration in Streamlit | `app/main.py` | Display real SHAP values | P3 | Needs trained model first |

---

## EXPERIMENT MATRIX

| Experiment | Dataset | Model | Feature Set | Decision System | Primary Metric | Result Location | Status | Completion |
|---|---|---|---|---|---|---|---|---|
| T1 — Authentic | Home Credit 307k | LR + XGBoost | HC-specific (not set C) | None | ROC-AUC, PR-AUC, Brier, ECE | `results/authentic/T1_results.json` | ✅ COMPLETE | 100% |
| T2 — Ablation | SynthGigCredit seeds 1–10 | LR + XGB | A, B, C | None | ROC-AUC per DGP (paired, seed-level CI) | `results/ablation/` | ⚠️ CODE READY | 50% |
| T3 — Gating | SynthGigCredit seeds 1–10 | XGB-C (LR-C robustness) | C | D1, D2, D3, D4 | Approval rate, default rate among approved, review rate, policy violation rate | `results/gating/` | ⚠️ CODE READY | 50% |
| T4 — Review 20% | SynthGigCredit seeds 1–10 | XGB-C | C | D4 pool | bad_loan_capture, risk_reduction vs R0 | `results/review/` | ⚠️ CODE READY | 50% |
| T5 — Review 30% | SynthGigCredit seeds 1–10 | XGB-C | C | D4 pool | bad_loan_capture, risk_reduction vs R0 | `results/review/` | ⚠️ CODE READY | 50% |
| T6 — History | SynthGigCredit seeds 1–10 | XGB-C (no refit) | C | None | ROC-AUC at H=1,3,6,12 | `results/history/` | ⚠️ CODE READY | 50% |
| T7 — DGP robustness | Both DGPs | All | C | All | All — per-DGP comparison | Embedded in T2–T5 | ⚠️ Implicit | 40% |
| T8 — Calibration | Both DGPs | LR+XGB | C | None | ECE, slope/intercept | Embedded in T2 | ⚠️ Metrics ready | 40% |
| T9 — Fairness | Both DGPs | XGB-C | C + e_shram | D4 | Approval parity, subgroup default rates | — | ❌ NOT IMPLEMENTED | 0% |
| T10 — Policy correctness | UNVERIFIED fixtures | N/A | Policy attrs | Policy engine | Rule execution, provenance completeness | — | ⚠️ Framework works; no runner | 30% |

---

## REMAINING WORK SUMMARY TABLE

| Remaining Task | Priority | Blocking? | Completion Impact | Dependency | Status |
|---|---|---|---|---|---|
| Run G0; get PASS | P1 | YES — blocks T2–T6 | +5% overall | Thresholds set ✅ | Ready to run |
| Generate seeds 1–10 (both DGPs) | P1 | YES — blocks T2–T6 | +5% overall | G0 PASS | Waiting |
| Build feature tables seeds 1–10 | P1 | YES — blocks T2–T6 | +3% overall | Seeds generated | Waiting |
| Run T2 ablation | P1 | YES — core result | +4% overall | Feature tables | Waiting |
| Run T3 gating (D1–D4) | P1 | YES — core result | +4% overall | Feature tables + policy | Waiting |
| Run T4/T5 review | P1 | YES — core result | +4% overall | Feature tables + policy | Waiting |
| Run T6 history | P1 | Core result | +3% overall | Feature tables | Waiting |
| Aggregate results (seed-level CI) | P2 | No | +2% | T2–T6 done | Waiting |
| Verify policy rules Task 10b | P2 | Partial (T3/T4/T5 stay provisional) | +4% | Human verification | EXTERNAL |
| Connect trained model to demo | P2 | No | +2% | Trained artifact | Waiting |
| Add calibration/model/SHAP tests | P2 | No | +3% | None | Ready |
| Complete G0 checks 1,3,6,9 | P2 | No | +1% | None | Ready |
| Fairness experiment T9 | P3 | No | +2% | Feature tables | Not started |
| Final PPT | P1 | YES — review | N/A | All results | Not started |

**To reach ~90% completion: complete P1 items above (≈ 4–5 hours of compute + coding).**

---

## QUICK START COMMANDS (in order)

```bash
# 1. Install dependencies (if not done)
pip install -r requirements.txt
pip install -e .

# 2. Run tests
pytest tests/ -v

# 3. Run Gate G0 (g0_seed=0)
python -m src.data_validation.gate_g0 --config configs/experiment.yaml

# 4. If G0 = PASS — generate seeds 1-10
for dgp in 1 2:
  for seed in 1 2 3 4 5 6 7 8 9 10:
    python -m src.data_generation.generate_data --config configs/experiment.yaml --dgp {dgp} --seed {seed}
    python -m src.feature_engineering.build_features --config configs/experiment.yaml --dgp {dgp} --seed {seed} --view full
    python -m src.feature_engineering.build_features --config configs/experiment.yaml --dgp {dgp} --seed {seed} --view visible

# 5. Run experiments
python -m experiments.ablation.run --config configs/experiment.yaml --dgp 1 --seed 1
python -m experiments.gating.run   --config configs/experiment.yaml --dgp 1 --seed 1
python -m experiments.review.run   --config configs/experiment.yaml --dgp 1 --seed 1
python -m experiments.history.run  --config configs/experiment.yaml --dgp 1 --seed 1

# 6. Launch demo
python -m streamlit run app/main.py
```

---

**METHODOLOGY FROZEN — READY FOR IMPLEMENTATION**
**PROJECT IMPLEMENTATION STATUS: RESEARCH PROTOTYPE**
**PROJECT COMPLETION: 72%**
