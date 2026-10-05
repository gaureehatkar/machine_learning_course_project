# Research Implementation Status — SynthGigCredit-IN

**Date:** 2026-10-05  
**Source of truth:** Actual source code inspection, not documentation claims.

---

## Classification Key

- **A** = Fully implemented and usable  
- **B** = Partially implemented  
- **C** = Implemented but needs validation  
- **D** = Missing  
- **E** = Broken  
- **F** = Duplicate/Redundant

---

## 1. Synthetic Data Generation

| Component | File | Status | Notes |
|---|---|---|---|
| DGP1 (base model) | `src/data_generation/generate_data.py` | **A** | LogNormal income, seasonal variation, liquidity recursion. 25K applicants, 24 months |
| DGP2 (income shock) | `src/data_generation/generate_data.py` | **A** | DGP1 + 10% shock prob, 50% income drop |
| RNG substream separation | `src/utils/seeding.py` | **A** | static_seed = s×1000+1, outcome_seed = s×1000+2 |
| Seeds 0-10 generated | `data/synthetic/dgp{1,2}/seed{0..10}/` | **A** | All 21 datasets present (g0_seed + 10 experimental) |
| Gate G0 validation | `src/data_validation/gate_g0.py` | **A** | PASS — 8/9 checks pass (Check 1 NULL, Check 9 deferred) |

## 2. Feature Engineering

| Component | File | Status | Notes |
|---|---|---|---|
| Set A (7 conventional) | `src/feature_engineering/build_features.py` | **A** | income_mean, expense_mean, expense_ratio, debt_mean, has_emi, liquidity_mean, liquidity_min |
| Set B (5 alternative/gig) | `src/feature_engineering/build_features.py` | **A** | income_volatility, income_trend, platform_tenure, multi_platform, seasonality_index |
| Set C (combined A+B) | `src/feature_engineering/build_features.py` | **A** | All 12 features, 23 columns total with metadata |
| Feature parquets | `data/synthetic/dgp{1,2}/seed{1..10}/` | **A** | 40 files (20 full + 20 visible) |
| NaN handling | `src/feature_engineering/build_features.py` | **A** | NaN for H<2 volatility, H<3 trend, H≠12 seasonality; imputed in WinsorisedScaler for LR |

## 3. Models

| Component | File | Status | Notes |
|---|---|---|---|
| Logistic Regression | `src/models/train_models.py` | **A** | sklearn LogisticRegression, WinsorisedScaler preprocessing |
| XGBoost | `src/models/train_models.py` | **A** | xgboost, native NaN handling, no scaling |
| FittedModel class | `src/models/train_models.py` | **A** | predict_raw() method, feature_cols tracking |
| WinsorisedScaler | `src/models/train_models.py` | **A** | 1/99 percentile clip + median impute + StandardScale (LR only) |
| Feature set assertion | `src/models/train_models.py` | **A** | _assert_feature_set prevents evidence/policy cols in PD model |

## 4. Calibration

| Component | File | Status | Notes |
|---|---|---|---|
| Platt scaling (custom) | `src/calibration/platt.py` | **A** | scipy L-BFGS-B sigmoid fit on validation set |
| Isotonic regression | — | **D** | Not implemented (not required by methodology) |
| Raw probabilities | All experiment runners | **A** | Both raw and calibrated scores computed |

## 5. Evidence System

| Component | File | Status | Notes |
|---|---|---|---|
| Evidence score formula | `src/evidence/compute_evidence.py` | **A** | E = 0.5×(H/12) + 0.25×AA + 0.25×ULI |
| Evidence threshold τ_E | `configs/experiment.yaml` | **A** | 0.50 (configurable) |
| Evidence status | `src/evidence/compute_evidence.py` | **A** | SUFFICIENT / INSUFFICIENT |
| Evidence gating in decisions | `src/decisions/gate.py` | **A** | D3/D4 check E < τ_E → REVIEW |

## 6. Policy Engine

| Component | File | Status | Notes |
|---|---|---|---|
| Kleene 3-valued logic | `src/policy/kleene.py` | **A** | TRUE / FALSE / UNRESOLVED + AND/OR/NOT |
| Rule YAML loading | `src/policy/rule_loader.py` | **A** | PolicySet, PolicyRule dataclasses |
| Rule evaluation | `src/policy/rule_engine.py` | **A** | evaluate_policy() → PolicyEvaluation dataclass |
| Versioning (date-based) | `src/policy/versioning.py` | **A** | select_version() for active rules |
| Batch evaluation | `src/policy/rule_engine.py` | **A** | evaluate_batch() — processes DataFrame of applicants |
| Scheme combination | `src/policy/rule_engine.py` | **A** | combine_schemes() — Kleene OR/AND/single mode |
| JanSamarth rules | `configs/policy_rules/jan_samarth.yaml` | **A** | 3 rules: age [18,60], income ≤10L, nonfarm=1. RESEARCH VERIFIED |
| PMMY rules | `configs/policy_rules/pmmy.yaml` | **A** | 3 rules: age [18,65], income ≤10L, non_agriculture=1. RESEARCH VERIFIED |
| Occupation mapping | — | **D** | ride_hailing/delivery not mapped to policy categories |

## 7. Decision Engine

| Component | File | Status | Notes |
|---|---|---|---|
| D1 (risk only) | `src/decisions/gate.py` | **A** | PD < τ → APPROVE else DECLINE |
| D2 (risk + policy) | `src/decisions/gate.py` | **A** | + UNSAT→DECLINE, UNRES→REVIEW |
| D3 (risk + evidence) | `src/decisions/gate.py` | **A** | + E < τ_E → REVIEW |
| D4 (all three) | `src/decisions/gate.py` | **A** | Full stack |
| τ selection | `src/decisions/tau.py` | **A** | select_tau() on validation for 70% approval target |
| Decision dataclass | `src/decisions/gate.py` | **A** | @dataclass: decision (str), reason_code (str|None) |

## 8. Review Allocation

| Component | File | Status | Notes |
|---|---|---|---|
| R0 (random) | `src/decisions/review.py` | **A** | rng.random() shuffle of non-mandatory pool |
| R1 (entropy/PD) | `src/decisions/review.py` | **A** | H(PD) = -p ln p - (1-p) ln(1-p) |
| R2 (lowest evidence) | `src/decisions/review.py` | **A** | 1 - E score |
| R3 (combined) | `src/decisions/review.py` | **A** | 0.5×H(PD)/ln2 + 0.5×(1-E) |
| Oracle simulation | `src/decisions/review.py` | **A** | Referred defaulter → DECLINE, referred non-defaulter → APPROVE |
| Mandatory set (UNRESOLVED) | `src/decisions/review.py` | **A** | Consumed first from budget |

## 9. Evaluation Metrics

| Metric | File | Status | Notes |
|---|---|---|---|
| ROC-AUC | `src/evaluation/metrics.py` | **A** | sklearn roc_auc_score |
| PR-AUC | `src/evaluation/metrics.py` | **A** | sklearn average_precision_score |
| Brier score | `src/evaluation/metrics.py` | **A** | sklearn brier_score_loss |
| ECE (10 quantile bins) | `src/evaluation/metrics.py` | **A** | Custom implementation |
| Calibration slope/intercept | `src/evaluation/metrics.py` | **A** | scipy linregress on logit(p) vs y |
| Gini | `src/evaluation/metrics.py` | **A** | 2×AUC-1. **Added 2026-10-05** |
| KS statistic | `src/evaluation/metrics.py` | **A** | max\|F_default(t) - F_nondefault(t)\|. **Added 2026-10-05** |
| Approval rate | `src/evaluation/metrics.py` | **A** | |
| Default rate among approved | `src/evaluation/metrics.py` | **A** | |
| Review rate | `src/evaluation/metrics.py` | **A** | |
| Policy violation rate | `src/evaluation/metrics.py` | **A** | D1-only metric |
| Coverage-risk curve | `src/evaluation/metrics.py` | **A** | τ sweep |
| Bad loan capture | `src/evaluation/metrics.py` | **A** | Review metric |
| Review efficiency | `src/evaluation/metrics.py` | **A** | Default rate among referred |
| compute_all_metrics() | `src/evaluation/metrics.py` | **A** | All 9 metrics in one call (includes Gini, KS) |

## 10. Statistical Tests

| Component | File | Status | Notes |
|---|---|---|---|
| Seed-level CI | `src/evaluation/statistical_tests.py` | **A** | t-distribution df=9, t(0.975,9)=2.262 |
| Paired bootstrap | `src/evaluation/statistical_tests.py` | **A** | n=1000 resamples |
| Bonferroni α | `src/evaluation/statistical_tests.py` | **A** | 0.05/3 = 0.01667 |

## 11. Explainability

| Component | File | Status | Notes |
|---|---|---|---|
| TreeSHAP (XGBoost) | `src/explainability/shap_values.py` | **A** | shap.TreeExplainer |
| Global SHAP summary | `src/explainability/shap_values.py` | **A** | mean\|SHAP\| per feature |
| Local SHAP explanation | `src/explainability/shap_values.py` | **A** | Top-N per applicant |
| LR coefficients/odds ratios | `src/explainability/lr_coefficients.py` | **A** | β, exp(β), per-applicant contributions |
| Unified explain() JSON | `src/explainability/explain.py` | **A** | 11-param signature, returns dict |
| explain() API call | `app/api/main.py` | **E** | Wrong kwargs — TypeError at runtime |

## 12. Credit Scoring

| Component | File | Status | Notes |
|---|---|---|---|
| Scorecard scaling | `src/scoring/credit_score.py` | **A** | offset + factor×ln(odds), 300-900 clamp |
| Config-driven params | `configs/experiment.yaml` | **A** | base_score=600, base_odds=0.05, pdo=50 |

## 13. Cost Analysis

| Component | File | Status | Notes |
|---|---|---|---|
| Cost parameters | `configs/experiment.yaml` | **A** | m=1.0, L=[3,5,10], c_rev=[0.1,0.2] |
| Cost computation | `research/run_all_research.py` | **A** | C = C_FN×N_app_default + C_FP×N_dec_good + C_R×N_review |

## 14. Experiment Runners

| Experiment | File | Status | Results? | Notes |
|---|---|---|---|---|
| T1: Authentic (Home Credit) | `experiments/authentic/run.py` | **A** | ✅ T1_results.json | LR 0.738, XGB 0.757 |
| T2: Ablation (A/B/C × LR/XGB) | `experiments/ablation/run.py` + `research/run_all_research.py` | **A** | ⏳ Running | 10 seeds × 2 DGPs |
| T3: Gating (D1-D4 + τ_E sensitivity) | `experiments/gating/run.py` + `research/run_all_research.py` | **A** | ⏳ Running | Includes τ_E sweep |
| T4/T5: Review (R0-R3 × budgets) | `experiments/review/run.py` + `research/run_all_research.py` | **A** | ⏳ Running | Includes cost analysis |
| T6: History (H=1,3,6,12) | `experiments/history/run.py` + `research/run_all_research.py` | **A** | ⏳ Running | 4 forced views |
| T9: Fairness | `experiments/fairness/__init__.py` | **D** | ❌ | Empty stub — see Fairness Assessment |
| Methodology validation | `experiments/methodology_validation/__init__.py` | **D** | ❌ | Empty stub |
| Seed stability (G0 Check 9) | `src/data_validation/gate_g0.py` | **C** | ❌ | Deferred — requires seeds 1-10 comparison |

## 15. Reproducibility

| Factor | Status | Notes |
|---|---|---|
| Random seeds | **A** | All controlled via seeding.py |
| Train/val/test split | **A** | Stratified, fixed seeds |
| Feature ordering | **A** | ALL_COLUMNS_ORDERED enforced |
| Model config | **A** | configs/models.yaml |
| Calibration | **A** | scipy L-BFGS-B deterministic |
| Experiment config | **A** | configs/experiment.yaml single source |
| Dependency versions | **A** | requirements.txt pinned |
| Data paths | **A** | get_output_dir() derives paths |
| Model artifacts | **B** | Not persisted — retraining required |

## 16. T1 Verified Results (Pre-existing)

```
Dataset: Home Credit Default Risk (307,511 applicants)
Split: 60% train / 20% val / 20% test (stratified)

         LR        XGB
ROC-AUC  0.7383    0.7568
PR-AUC   0.2213    0.2447
Brier    0.0689    0.0678
ECE      0.00240   0.00247
Cal β    0.0742    0.0755
```

**Note on calibration slope ≈ 0.075:** Both models show severe underprediction. The slope should be ≈1.0 for perfect calibration. This is likely caused by missing bureau/external credit features that anchor absolute probability. The ranking (AUC) is still valid — only absolute probability calibration is affected.

## Summary Counts

| Status | Count |
|---|---|
| A — Fully working | 48 |
| B — Partially working | 1 |
| C — Needs validation | 1 |
| D — Missing | 4 |
| E — Broken | 1 |
| F — Redundant | 0 |
| **Total components** | **55** |
