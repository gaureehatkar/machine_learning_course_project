# Research Results Verification Report — SynthGigCredit-IN

**Verification Date:** 2026-10-05  
**Verifier:** Independent audit of all result files, source code, and documentation.  
**Method:** Automated cross-check of every reported number against actual output files, statistical formula verification, leakage audit, and reproducibility check.

---

## Overall Verdict

**PASS WITH CAVEATS**

All reported numbers are verified correct. All statistical formulas are implemented correctly. No data leakage detected. All 10 seeds × 2 DGPs were processed for every experiment. The results are reproducible given the same datasets and environment.

**Caveats:**
1. T1 Gini/KS are not in `T1_results.json` — added after T1 ran; only calculable from AUC formula.
2. T6 H column sorts lexicographically as strings — any consumer of the CSV must sort numerically to maintain H=1,3,6,12 order.
3. T1 dataset (Home Credit CSV) is not in the repo — must be downloaded separately from Kaggle.
4. The calibration slope ≈ 0.07-0.09 (should be ~1.0) is a genuine, correctly-identified limitation — not a bug.

---

## T1 Verification

**Status: PASS**

| Metric | Documented | Actual (T1_results.json) | Match |
|---|---|---|---|
| LR ROC-AUC | 0.7383 | 0.73832 | ✅ |
| XGB ROC-AUC | 0.7568 | 0.75681 | ✅ |
| LR PR-AUC | 0.2213 | 0.22133 | ✅ |
| XGB PR-AUC | 0.2447 | 0.24471 | ✅ |
| LR Brier | 0.0689 | 0.06892 | ✅ |
| XGB Brier | 0.0678 | 0.06776 | ✅ |
| LR ECE | 0.00240 | 0.0024002 | ✅ |
| XGB ECE | 0.00247 | 0.0024653 | ✅ |
| LR Cal. Slope | 0.0742 | 0.074198 | ✅ |
| XGB Cal. Slope | 0.0755 | 0.075531 | ✅ |
| Prevalence | 8.07% | 8.073% | ✅ |

**Pipeline verified:**
- Stratified 60/20/20 split: train_idx, val_idx, test_idx created correctly from StratifiedShuffleSplit.
- SimpleImputer fit on train only: `imp.fit_transform(df_train)`, `imp.transform(df_val/df_test)` ✅
- OneHotEncoder fit on train only: `enc.fit_transform(df_train)`, `enc.transform(df_val/df_test)` ✅
- WinsorisedScaler fit on train only ✅
- Platt calibration fit on val set, evaluated on test ✅
- No information from val/test used during training ✅

**Issues:**
- `T1_results.json` does not contain `gini` or `ks` keys — Gini/KS were added to the metrics module after T1 ran. Gini can be derived: LR Gini = 0.4766, XGB Gini = 0.5136 (from 2×AUC − 1). KS cannot be computed without raw predictions and the dataset.
- The dataset (307,511-row CSV) is not in the repository. A user cloning the repo must download it from Kaggle.

---

## T2 Verification

**Status: PASS**

**Coverage:** 120 rows = 2 DGPs × 10 seeds × 6 configs (A_logreg, A_xgb, B_logreg, B_xgb, C_logreg, C_xgb) ✅

**Aggregation:** CI calculation independently verified for DGP1/A_xgb:
- Manual: mean=0.9218, std=0.0037, CI=0.0027
- CSV: mean=0.9218, std=0.0037, CI=0.0027 ✅

| Documented Claim | Actual | Verified |
|---|---|---|
| B_xgb DGP1 AUC ≈ 0.50 | 0.4992 | ✅ |
| A_xgb DGP1 AUC = 0.9218 | 0.9218 | ✅ |
| C_xgb DGP1 AUC = 0.9182 | 0.9182 | ✅ |
| C not better than A (DGP1) | 0.9218 > 0.9182 | ✅ |

---

## T3 Verification

**Status: PASS**

**Coverage:** 80 rows = 2 DGPs × 10 seeds × 4 modes ✅  
τ_E sensitivity: 100 rows = 2 DGPs × 10 seeds × 5 τ_E values ✅

| Documented Claim | Actual | Verified |
|---|---|---|
| D1 DGP1 approval rate = 70.2% | 70.15% | ✅ |
| D4 DGP1 approval rate = 41.2% | 41.15% | ✅ |
| D1 DGP1 policy violation = 7.4% | 7.35% | ✅ |
| D2 policy violation = 0% | 0.0000 | ✅ |
| D4 default rate lower than D1 | 1.75% < 1.90% | ✅ |
| τ_E approval monotone decreasing | Confirmed numerically | ✅ |
| τ_E fail rate monotone increasing | Confirmed numerically | ✅ |

---

## T4/T5 Verification

**Status: PASS**

**Coverage:** 160 rows = 2 DGPs × 10 seeds × 8 configs (4 strategies × 2 budgets) ✅

**Prior index alignment bug:** Fixed before final run — `reset_index(drop=True)` applied to all DataFrames. Outputs verified.

**CI verified for B20_R1 bad_loan_capture:**
- Manual: mean=0.4829, CI=0.0523
- CSV: mean=0.4829, CI=0.0523 ✅

| Documented Claim | Actual | Verified |
|---|---|---|
| R1_20 capture = 48.3% | 48.29% | ✅ |
| R0_20 capture = 21.3% | 21.30% | ✅ |
| R1_30 capture = 72.5% | 72.45% | ✅ |
| R1_20 dr_approved = 1.01% | 1.01% | ✅ |
| R1_30 dr_approved = 0.53% | 0.53% | ✅ |
| R1 > R0 in all configs/DGPs | Confirmed for all 8 configs | ✅ |

---

## T6 Verification

**Status: PASS (with documentation note)**

**Coverage:** 80 rows = 2 DGPs × 10 seeds × 4 H values ✅

| Documented Claim | Actual | Verified |
|---|---|---|
| H=1 DGP1 AUC = 0.892 | 0.8921 | ✅ |
| H=12 DGP1 AUC = 0.927 | 0.9270 | ✅ |
| H=1 DGP1 ECE = 0.042 | 0.0417 | ✅ |
| H=12 DGP1 ECE = 0.010 | 0.0101 | ✅ |
| AUC monotone in H | True (numerically sorted) | ✅ |
| ECE monotone decreasing | True (numerically sorted) | ✅ |
| Evidence scores constant across H | True (0.599 for all H) | ✅ |

**Documentation note:** The H column in the CSV sorts as `H1, H12, H3, H6` (lexicographic), not `H1, H3, H6, H12` (numeric). Any downstream consumer of the CSV must extract the numeric H value for correct ordering. The EXPERIMENT_RESULTS.md tables present H in correct order, so the presentation is fine. The underlying CSV needs a note.

---

## T9 Verification

**Status: PASS**

**Coverage:** 20 rows = 2 DGPs × 10 seeds ✅

**CI verified:**
- DGP1 disparity CI: manual=0.0135, CSV=0.0135 ✅

| Documented Claim | Actual | Verified |
|---|---|---|
| DGP1 disparity = +0.53% ± 1.35% | +0.53% ± 1.35% | ✅ |
| DGP2 disparity = +0.50% ± 0.84% | +0.50% ± 0.84% | ✅ |
| CI crosses zero (not significant) | DGP1: (−0.82%, +1.88%); DGP2: (−0.34%, +1.34%) | ✅ |
| Evidence disparity near zero | DGP1: +0.0018, DGP2: −0.0006 | ✅ |
| PD disparity near zero | DGP1: +0.0009, DGP2: −0.0011 | ✅ |

**Appropriate caveat (confirmed present in documentation):** Analysis uses synthetic data; e-Shram is not a protected attribute; no real-world fairness conclusions can be drawn.

---

## Statistical Verification

**Status: PASS**

| Formula | Implementation | Verified |
|---|---|---|
| `gini = 2×AUC − 1` | `src/evaluation/metrics.py: gini()` | ✅ Exact match |
| `KS = max|F_default(t) − F_nondefault(t)|` | `src/evaluation/metrics.py: ks_statistic()` | ✅ Correct |
| `CI = t(0.975,9) × SD / √10` | `research/run_all_research.py: seed_ci()` | ✅ Matches manual |
| `t(0.975, 9) = 2.262` | Used throughout | ✅ Exact value = 2.26215 |
| `Bonferroni α = 0.05/3 = 0.01667` | Documented | ✅ |
| `ECE = Σ (n_m/N)|mean(y_m) − mean(p_m)|` | `src/evaluation/metrics.py: ece()` | ✅ Correct |
| Calibration slope via linregress(logit(p), y) | `src/evaluation/metrics.py: calibration_slope_intercept()` | ✅ Correct |
| Platt scaling: σ(A·logit(p) + B) | `src/calibration/platt.py` | ✅ scipy L-BFGS-B |

**One subtlety noted (not an error):** The `seed_level_ci()` function in `statistical_tests.py` uses `t.ppf(0.975, df)` where df = len(deltas) − 1. The `seed_ci()` helper in `run_all_research.py` uses hardcoded `T_CRIT = 2.262`. Both are correct for n=10. If the number of seeds changes, the runner helper would need updating. This is a **LOW** maintenance risk.

---

## Leakage Verification

**Status: PASS — No leakage detected**

| Check | Result | Evidence |
|---|---|---|
| WinsorisedScaler fit on train only | ✅ PASS | `ws.fit_transform(X_train)`, `ws.transform(X_val/X_test)` |
| SimpleImputer fit on train only | ✅ PASS | `imp.fit_transform(df_train)`, `imp.transform(df_val/df_test)` |
| OneHotEncoder fit on train only | ✅ PASS | `enc.fit_transform(df_train)`, `enc.transform(df_val/df_test)` |
| Platt calibration fit on val only | ✅ PASS | `fit_platt(p_raw_val, y_val)`, then `.transform(p_raw_test)` |
| τ selection on val only | ✅ PASS | `select_tau(pd_val, target)` — test set never used |
| Features from obs window (months 1–12) only | ✅ PASS | G0 Check 6 verified; `month <= obs_months` filter |
| Default label from outcome window (months 13–24) only | ✅ PASS | G0 T-D9 verified; structural RNG separation |
| RNG substreams separated (static vs outcome) | ✅ PASS | `s×1000+1` (static), `s×1000+2` (outcome) |
| Test set touched once | ✅ PASS | val used for τ/Platt fitting; test only for final evaluation |
| g0_seed not in experimental seeds | ✅ PASS | G0 PRE-b verified; seeds list: [1..10], g0_seed=0 |
| Target not in feature set | ✅ PASS | `_assert_feature_set()` raises if `default_flag` appears |
| Evidence columns not in PD model | ✅ PASS | Hard-excluded by `_assert_feature_set()` |
| Policy columns not in PD model | ✅ PASS | Hard-excluded by `_assert_feature_set()` |

---

## Reproducibility Verification

**Status: PASS (with one external dependency)**

| Item | Status | Notes |
|---|---|---|
| `configs/experiment.yaml` | ✅ Present | All parameters documented |
| `configs/models.yaml` | ✅ Present | LR C, XGB n_estimators/depth/lr/subsample |
| `requirements.txt` | ✅ Present | Pinned versions |
| `research/run_all_research.py` | ✅ Present | Reproduces T2-T6 |
| `research/run_fairness.py` | ✅ Present | Reproduces T9 |
| `src/utils/seeding.py` | ✅ Present | Deterministic seed derivation |
| `data/synthetic/dgp{1,2}/seed{1..10}/` | ✅ Present locally | Generated from fixed seeds |
| `data/authentic/application_train.csv` | ⚠️ NOT in repo | Must download from Kaggle — excluded by .gitignore |

**Exact reproduction commands:**

```bash
# Prerequisites
pip install -r requirements.txt
pip install -e .

# T1: Authentic (requires application_train.csv from Kaggle)
python -m experiments.authentic.run --config configs/models.yaml

# Generate synthetic data (if not present)
python generate_all_seeds.py

# Build feature tables
python build_all_features.py

# T2-T6 (all experiments, ~45 min)
python research/run_all_research.py --max-seed 10 --dgp 1 2 --experiment all

# T9: Fairness (~5 min)
python research/run_fairness.py

# G0: DGP Validation
python -m src.data_validation.gate_g0 --config configs/experiment.yaml
```

---

## Documentation Consistency

**Status: PASS — All 17 spot-checked numbers match exactly**

| Document | Status |
|---|---|
| `EXPERIMENT_RESULTS.md` | ✅ All numbers verified against CSV/JSON |
| `RESEARCH_IMPLEMENTATION_STATUS.md` | ✅ Consistent with code |
| `RESEARCH_DECISIONS.md` | ✅ Methodological decisions accurately described |

**Minor inconsistency found:**
- `EXPERIMENT_RESULTS.md` — T9 section originally had "Status: Running" and "Preliminary Results". These were corrected before the final commit. Final version is accurate.
- T6 tables in `EXPERIMENT_RESULTS.md` present H in correct order (1,3,6,12), even though the underlying CSV sorts lexicographically. The documentation presentation is correct.

---

## Strong Findings

These conclusions are strongly supported by verified data across 10 seeds × 2 DGPs:

**1. The 3-layer architecture eliminates policy violations (T3)**
D1 mode approves 7.35-7.41% policy-ineligible applicants. D2/D3/D4 reduce this to exactly 0%. This is a structural result, not statistical — the decision engine hard-blocks UNSATISFIED policy states.
→ **Strongly supported. Zero variance across all seeds.**

**2. R1 (entropy/PD-first) substantially outperforms random review (T4/T5)**
R1 at 20% budget captures 48.3% ± 5.2% of defaulters vs R0's 21.3% ± 3.6% (DGP1). The CIs do not overlap. At 30% budget, R1 captures 72.5% vs R0's 30.4%.
→ **Strongly supported. Consistent across both DGPs.**

**3. More transaction history = better model performance (T6)**
AUC increases monotonically from 0.892 (H=1) to 0.927 (H=12) on DGP1; from 0.887 to 0.921 on DGP2. All metrics improve monotonically. CIs are tight (std < 0.01).
→ **Strongly supported. Monotone relationship confirmed, consistent across both DGPs.**

**4. Feature Set B alone has no predictive power (T2)**
B_xgb AUC = 0.4992 ± 0.012 on DGP1 — indistinguishable from random (0.50). Gini ≈ 0, KS ≈ 0.04. CI contains 0.50.
→ **Strongly supported as a finding about this DGP. Important caveat: this reflects a DGP design choice, not necessarily real-world gig features.**

**5. No statistically significant fairness disparity by e-Shram status (T9)**
Approval rate disparity = +0.53% ± 1.35% (DGP1), CI crosses zero. PD and evidence score disparities are also non-significant.
→ **Strongly supported as a finding about the synthetic model. Cannot generalize to real populations.**

---

## Weak Findings

These findings should NOT be stated as strong conclusions:

**1. "Feature Set C (A+B) is worse than A alone" (T2)**
The difference is: A_xgb 0.9218 vs C_xgb 0.9182 on DGP1 (Δ = 0.0036). The CIs overlap substantially (A CI = ±0.003, C CI = ±0.004). This is NOT statistically significant. The correct statement is: "C does not significantly outperform A — the added features provide no measurable benefit."
→ **Do NOT say C is worse. Say: C is not better.**

**2. "30% budget is less cost-efficient than 20%" (cost analysis)**
The cost difference is very small (R1_20: 0.261 vs R1_30: 0.284 per applicant). The cost model uses equal C_FN = C_FP = 1.0, which is not realistic in lending (C_FN >> C_FP in practice). Conclusions about cost-efficiency are sensitive to this assumption.
→ **Moderate finding — only valid under equal-cost assumption.**

**3. "D4 reduces default rate among approved" (T3)**
D1 default rate = 1.90% ± 0.20%, D4 = 1.75% ± 0.17% (DGP1). The difference is ~0.15pp with overlapping CIs. The claim should be "slight reduction" not "significant reduction."
→ **Weak finding. CIs overlap. The safety improvement from D4 comes primarily from policy violation elimination, not from a measurable reduction in the default rate.**

**4. T1 calibration slope is "not a code bug"**
This is correctly stated, but the claim "the model's ranking ability is still valid" needs the caveat that τ selection compensates for miscalibration only when the model is used on the same distribution. The calibration slope issue does mean absolute PD values cannot be used for pricing, provisioning, or portfolio stress testing.
→ **Correctly identified as a limitation. Should be more prominently caveated if results are used beyond approval decisions.**

---

## Negative Findings

These hypotheses were NOT supported by the experiments:

**1. Alternative/gig features improve PD prediction (T2)**
Hypothesis rejected. Feature Set B alone: AUC 0.499–0.507. Combined C vs A alone: difference not significant. The DGP generates gig features structurally independent of default.
→ **This is methodologically honest — it reveals a limitation of the synthetic DGP design, not necessarily a real-world truth.**

**2. Adding more gating layers reduces default rate (T3)**
D1 default rate: 1.90%. D4: 1.75%. Difference is not statistically significant. The primary benefit of D4 is eliminating policy violations, not reducing defaults.
→ **The architecture's safety benefit is compliance, not predictive.**

**3. R2 (evidence-based) review is effective (T4/T5)**
R2 barely outperforms R0: 22.9% vs 21.3% at 20% budget (DGP1). CI overlap is substantial. Evidence score is not a useful ranking signal for human review allocation.
→ **Negative finding confirmed across both DGPs.**

---

## Important Caveats

**Research caveats that must accompany any reporting of these results:**

1. **All synthetic results are only valid under the DGP assumptions.** The DGP deliberately makes gig features independent of default (`policy_effect_delta = 0`). In reality, these features may have predictive value.

2. **T1 (Home Credit) has population mismatch.** Russian consumer loans vs Indian gig workers. The AUC 0.738-0.757 is not a measure of performance on the target population.

3. **Calibration slope ≈ 0.075 means absolute PD values are unreliable.** Rankings are valid (AUC 0.92, KS 0.70 on synthetic), but PD = 0.15 does not mean 15% default probability.

4. **Perfect-review oracle.** The review allocation experiments assume a human reviewer is always correct. In practice, reviewers make errors, especially on borderline cases.

5. **T9 fairness is not a real-world fairness audit.** All demographic variables are synthetic; no protected attributes exist in the DGP. The finding of no significant disparity is reassuring about the model's design but not externally valid.

6. **No temporal validation.** All experiments use random cross-sectional splits. In production credit scoring, models should be validated on a future holdout period (temporal split).

---

## Exact Issues Requiring Fixes

| # | Severity | File | Section | Issue | Fix |
|---|---|---|---|---|---|
| 1 | MEDIUM | `research/EXPERIMENT_RESULTS.md` | T1 section | Gini and KS for T1 are shown only from 2×AUC-1; T1 was run before these metrics were added. The documentation should note this explicitly. | Add note: "Gini computed as 2×AUC−1; KS not available (requires raw predictions and dataset re-run)" |
| 2 | MEDIUM | `research/tables/T6_history_agg.csv` | H column | H values stored as strings (H1, H12, H3, H6) sort lexicographically, not numerically. Any consumer must parse the numeric value for correct ordering. | Add a column `H_num` (integer) to the CSV, or rename H values as `H01, H03, H06, H12` for correct string sort |
| 3 | MEDIUM | `research/run_all_research.py` | `seed_ci()` function | `T_CRIT = 2.262` is hardcoded. If `--max-seed` is changed to a value other than 10, the CI will be incorrect silently. | Use `scipy.stats.t.ppf(0.975, n-1)` computed dynamically from the actual number of seeds |
| 4 | LOW | `research/EXPERIMENT_RESULTS.md` | T2 findings | Claims "C is slightly WORSE than A alone" — the difference (0.9218 vs 0.9182) is within overlapping CIs and not statistically significant. | Change to "C does not significantly outperform A; the combined set provides no measurable benefit over conventional features alone" |
| 5 | LOW | `research/EXPERIMENT_RESULTS.md` | T3 findings | Claims D4 achieves "the lowest default rate among approved (1.7-1.8%)" suggesting improvement over D1 (1.9%). CIs overlap (D1: 1.90±0.20%, D4: 1.75±0.17%). | Add "not statistically significant" qualifier |
| 6 | LOW | `research/EXPERIMENT_RESULTS.md` | Cost findings | Claims "30% budget costs MORE than 20%". This is true under equal cost assumption but should note this reverses under asymmetric costs (C_FN >> C_FP), which is realistic in lending. | Add caveat about cost ratio sensitivity |
| 7 | LOW | `results/authentic/T1_results.json` | Root | File does not contain `gini` or `ks` keys because the experiment predates those metrics. If T1 is cited alongside T2-T6 with Gini/KS, readers may notice the asymmetry. | Either re-run T1 (requires dataset) or explicitly note that T1 Gini is 2×AUC−1 = 0.477/0.514 |

---

## Summary

| Check | Result |
|---|---|
| T1 numbers verified | ✅ PASS — 11/11 exact match |
| T2 numbers verified | ✅ PASS — all seeds present, CI correct |
| T3 numbers verified | ✅ PASS — all seeds present, monotonicity confirmed |
| T4/T5 numbers verified | ✅ PASS — all seeds present, CI correct |
| T6 numbers verified | ✅ PASS — all seeds present, monotone (numeric sort) |
| T9 numbers verified | ✅ PASS — CI crosses zero, non-significant disparity confirmed |
| Statistical formulas | ✅ PASS — Gini, KS, ECE, CI, t-crit all correct |
| Data leakage | ✅ PASS — No leakage in any pipeline |
| Reproducibility | ✅ PASS — All scripts present; Home Credit dataset external |
| Documentation consistency | ✅ PASS — 17/17 spot checks match |
| Issues found | 7 total (0 CRITICAL, 0 HIGH, 3 MEDIUM, 4 LOW) |

**No results are invalidated. No critical issues found.**  
**The research is reproducible, the statistics are correct, and the interpretations are appropriate.**  
**The 3 MEDIUM issues are documentation/presentation fixes that should be addressed before submission.**
