# For Research Paper — SynthGigCredit-IN
## File Package Guide + Incomplete Sections

**Prepared:** 2026-10-05  
**Purpose:** Tell your research paper co-author exactly which files to use, what is complete, and where placeholders must be filled in before submission.

---

## Files to Give Your Friend

### 1. Core Results (Verified, Ready to Use)

| File | What It Contains | Use for |
|---|---|---|
| `research/EXPERIMENT_RESULTS.md` | All experiment results with full tables, CIs, key findings | Direct reference for paper results section |
| `research/RESEARCH_DECISIONS.md` | Every methodological decision with rationale | Methods section justifications |
| `research/RESEARCH_RESULTS_VERIFICATION.md` | Independent verification of all numbers | "Results verified" claim, appendix |
| `results/authentic/T1_results.json` | Raw T1 numbers (LR + XGB on Home Credit) | Table 1 in paper |
| `research/tables/T2_ablation_agg.csv` | Feature ablation: mean ± CI per config | Table 2 |
| `research/tables/T3_gating_agg.csv` | D1-D4 gating metrics | Table 3 |
| `research/tables/T3_tau_e_agg.csv` | τ_E sensitivity sweep | Table 4 / Appendix |
| `research/tables/T4_T5_review_agg.csv` | R0-R3 × budgets | Table 5 |
| `research/tables/T6_history_agg.csv` | H=1,3,6,12 history sensitivity | Table 6 |
| `research/tables/T9_fairness_aggregated.csv` | e-Shram subgroup analysis | Table 7 / Appendix |

### 2. Methodology Files

| File | What It Contains |
|---|---|
| `FINAL_PROJECT_TECHNICAL_DOCUMENTATION.md` | Full system specification |
| `FINAL_PROJECT_ARCHITECTURE.md` | Architecture diagrams and design |
| `docs/policy_rule_verification.md` | JanSamarth + PMMY rule sources |
| `docs/dataset2_freeze.md` | Grounding dataset freeze record (CC BY 4.0) |
| `configs/experiment.yaml` | All parameters (τ, τ_E, seeds, DGP params) |
| `configs/policy_rules/jan_samarth.yaml` | Verified JanSamarth rules |
| `configs/policy_rules/pmmy.yaml` | Verified PMMY rules |

### 3. Code (for reproducibility appendix)

| File | What It Contains |
|---|---|
| `src/evidence/compute_evidence.py` | Evidence score formula |
| `src/decisions/gate.py` | D1-D4 decision logic |
| `src/decisions/review.py` | R0-R3 review strategies |
| `src/evaluation/metrics.py` | All metrics including Gini, KS |
| `src/calibration/platt.py` | Platt calibration implementation |
| `research/run_all_research.py` | Reproduces T2-T6 |

---

## Paper Section Map

### Abstract
- **Available:** T1 AUC, T3 D4 approval rate, T4/T5 R1 capture rate
- **Placeholder:** See Section "Incomplete Sections" below

### 1. Introduction
- Fully writable from existing docs

### 2. Related Work
- Fully writable (literature review — no experiment needed)

### 3. Dataset
**Authentic (T1):**
- Home Credit Default Risk, 307,511 applicants, 8.07% default rate — verified
- Source: Kaggle competition dataset

**Synthetic (T2-T9):**
- 2 DGPs × 10 seeds × 25,000 applicants — verified
- Grounding: COVID-19 & Human Security survey, Bangalore (CC BY 4.0, DOI: 10.17632/j6hd2dfsh8.1)

### 4. Methods
- Fully writable from `RESEARCH_DECISIONS.md` and `FINAL_PROJECT_TECHNICAL_DOCUMENTATION.md`

### 5. Results
**All numbers verified and ready — see tables in** `research/EXPERIMENT_RESULTS.md`

### 6. Discussion
**Available:** All experimental conclusions  
**Placeholder needed:** See Section "Incomplete Sections" — API deployment results pending

### 7. Conclusion
- Writable from available results

---

## Complete Results Available (Use Directly)

### T1 — Authentic Baseline ✅ COMPLETE

| | LR | XGBoost |
|---|---|---|
| ROC-AUC | 0.7383 | 0.7568 |
| PR-AUC | 0.2213 | 0.2447 |
| Brier | 0.0689 | 0.0678 |
| ECE | 0.00240 | 0.00247 |
| Cal. Slope | 0.0742 | 0.0755 |
| Gini | 0.4766* | 0.5136* |
| KS | [PLACEHOLDER — T1 requires re-run with dataset] | [PLACEHOLDER] |

*Gini computed as 2×AUC−1. KS requires raw predictions — see placeholder notes below.

### T2 — Feature Ablation ✅ COMPLETE (10 seeds × 2 DGPs)
All numbers in `research/tables/T2_ablation_agg.csv`. Summary:

| Config | DGP1 ROC-AUC | DGP2 ROC-AUC |
|---|---|---|
| A_logreg | 0.9137 ± 0.003 | 0.9086 ± 0.004 |
| A_xgb | 0.9218 ± 0.003 | 0.9152 ± 0.004 |
| B_logreg | 0.5009 ± 0.010 | 0.5074 ± 0.010 |
| B_xgb | 0.4992 ± 0.012 | 0.4977 ± 0.009 |
| C_logreg | 0.9137 ± 0.003 | 0.9082 ± 0.005 |
| C_xgb | 0.9182 ± 0.004 | 0.9132 ± 0.004 |

### T3 — Evidence Gating ✅ COMPLETE (10 seeds × 2 DGPs)
All numbers in `research/tables/T3_gating_agg.csv` and `T3_tau_e_agg.csv`.

### T4/T5 — Review Allocation ✅ COMPLETE (10 seeds × 2 DGPs)
All numbers in `research/tables/T4_T5_review_agg.csv`.

### T6 — History Sensitivity ✅ COMPLETE (10 seeds × 2 DGPs)
All numbers in `research/tables/T6_history_agg.csv`.  
**Note:** H column sorts as strings. Sort by numeric H (1, 3, 6, 12) before making tables.

### T9 — Fairness ✅ COMPLETE (10 seeds × 2 DGPs)
All numbers in `research/tables/T9_fairness_aggregated.csv`.

---

## Incomplete Sections (Placeholders Required)

The following sections depend on work that is not yet complete. 
**Do NOT fill these in with assumed values. Use the placeholder text exactly.**

---

### PLACEHOLDER 1 — T1 KS Statistic

**Location:** T1 results table, KS column  
**Why missing:** KS requires raw model predictions, which are not saved to disk. `T1_results.json` does not contain a `ks` key because the KS metric was added after T1 ran.  
**Placeholder text to use in paper:**

```
KS statistic for T1: [TO BE COMPUTED — requires re-running T1 on Home Credit dataset]
```

**How to fill it:** Re-run `python -m experiments.authentic.run --config configs/models.yaml` on the Home Credit CSV. The updated `compute_all_metrics()` now outputs KS automatically.

---

### PLACEHOLDER 2 — API Live Decision Demo (SHAP Explanations)

**Location:** Any section describing the deployed API or live system  
**Why missing:** The FastAPI backend currently uses a **heuristic PD formula**, not a trained ML model. The `explain()` function call in the API has a known bug (wrong kwargs — always returns a TypeError, not real SHAP values).  
**This is an engineering bug, not a research bug. Teammate must fix before paper can claim:**
- "The system produces real-time SHAP explanations"
- "The API returns calibrated probability of default from a trained model"

**Placeholder text to use in paper:**

```
API Risk Score: [PLACEHOLDER — pending integration of trained XGBoost model into FastAPI endpoint]
API Explanation: [PLACEHOLDER — pending fix of explain() call in app/api/main.py]
```

**Specifically blocked by:**
1. `app/api/main.py`: `_compute_risk_heuristic()` must be replaced with loaded trained model
2. `app/api/main.py`: `explain(applicant_id=..., features=..., decision=..., config=...)` call must be fixed to match `explain(applicant_id, pd_calibrated, tau, decision, evidence_score, evidence_status, history_length, tau_e, policy_evaluation, shap_reasons, mode)`

---

### PLACEHOLDER 3 — Policy Gate SATISFIED Results

**Location:** Any section claiming "Policy gate correctly identifies eligible applicants"  
**Why missing:** The `occupation` field from the frontend sends values like `ride_hailing`, `delivery`, `freelance` but the policy YAML rules check `nonfarm_business_flag` (a binary 0/1). The `non_agriculture` field needed for PMMY is not in the API request model.  
**Result:** In the live API demo, policy gate always returns UNRESOLVED for most applicants, not SATISFIED or UNSATISFIED.  
**This does NOT affect the research experiments** (T2-T9 use a direct pipeline that correctly maps fields). It only affects the live API demo.

**Placeholder text to use in paper for API demo:**

```
Policy eligibility (live API): [PLACEHOLDER — pending occupation-to-policy-category mapping fix in app/api/main.py]
```

---

### PLACEHOLDER 4 — τ (Risk Threshold) from Settings UI

**Location:** Any section claiming the system allows configurable thresholds  
**Why missing:** The frontend Settings page has a τ slider that saves to localStorage and is read by the frontend's local scoring engine. However, the FastAPI backend **ignores τ** — the `DecisionRequest` pydantic model does not include `tau` or `tau_e` fields, so they are silently dropped.  
**Result:** Backend always uses `tau = 0.40` regardless of what the slider shows.

**Placeholder text to use in paper:**

```
Configurable τ (backend): [PLACEHOLDER — pending addition of tau/tau_e fields to DecisionRequest in app/api/main.py]
```

---

### PLACEHOLDER 5 — T1 Gini and KS (for unified metrics table)

**Location:** Any unified comparison table showing Gini/KS across T1 and T2-T6  
**Why missing:** T1 results file predates the Gini/KS additions. Gini can be derived (= 2×AUC−1) but KS requires raw predictions.

**Values you CAN use (derived):**
- LR Gini = 2 × 0.7383 − 1 = **0.4766**
- XGB Gini = 2 × 0.7568 − 1 = **0.5136**

**Placeholder for KS:**
```
LR KS (Home Credit): [PLACEHOLDER — requires T1 re-run]
XGB KS (Home Credit): [PLACEHOLDER — requires T1 re-run]
```

---

### PLACEHOLDER 6 — Figures / Plots

**Location:** Results section — all figures  
**Why missing:** No figures were generated. The `research/figures/` directory is empty.  
**These are NOT blocked by engineering work** — they can be created from the CSV data.

**Plots needed for the paper:**

| Figure | Data source | How to create |
|---|---|---|
| Fig 1: ROC curve (T1) | Requires re-running T1 to save predictions | Re-run T1, save `p_cal_test` and `y_test` |
| Fig 2: Feature ablation bar chart | `T2_ablation_agg.csv` | Bar chart with error bars per config |
| Fig 3: D1-D4 approval/default tradeoff | `T3_gating_agg.csv` | Grouped bar chart |
| Fig 4: τ_E sensitivity curve | `T3_tau_e_agg.csv` | Line chart approval vs τ_E |
| Fig 5: Review budget frontier | `T4_T5_review_agg.csv` | R0-R3 bad_loan_capture vs budget |
| Fig 6: History sensitivity | `T6_history_agg.csv` | AUC/ECE vs H |
| Fig 7: Calibration curve (T1) | Requires re-running T1 | Calibration curve (predicted vs actual) |

**All figures 2-6 can be created directly from existing CSVs — no re-running needed.**

---

## Summary of What Friend Gets

### ✅ Ready — hand over directly

```
research/
  EXPERIMENT_RESULTS.md          ← main results reference
  RESEARCH_DECISIONS.md          ← methodology justifications
  RESEARCH_RESULTS_VERIFICATION.md  ← verification report
  tables/
    T2_ablation_agg.csv
    T3_gating_agg.csv
    T3_tau_e_agg.csv
    T4_T5_review_agg.csv
    T6_history_agg.csv
    T9_fairness_aggregated.csv

results/authentic/T1_results.json

FINAL_PROJECT_TECHNICAL_DOCUMENTATION.md
FINAL_PROJECT_ARCHITECTURE.md
docs/policy_rule_verification.md
docs/dataset2_freeze.md
configs/experiment.yaml
```

### ⚠️ Needs action before use

| Item | Action needed | Who does it |
|---|---|---|
| T1 KS statistic | Re-run T1 (5 min with dataset) | Research side |
| T1 Gini | Already computable: LR=0.4766, XGB=0.5136 | Ready now |
| All figures | Create from existing CSVs | Research side |
| Calibration curve | Re-run T1 to save raw predictions | Research side |
| API live demo claims | Fix heuristic PD + explain() bug | **Engineering teammate** |
| Policy gate SATISFIED | Fix occupation mapping in YAML | **Engineering teammate** |
| Configurable τ in API | Add tau/tau_e to DecisionRequest | **Engineering teammate** |

### ❌ Cannot be in paper until engineering fixes

- Any claim about "the deployed API returns real ML model predictions"
- Any claim about "live SHAP explanations from the API"
- Any claim about "configurable thresholds respected by the backend"
- Any demo screenshot showing policy gate as SATISFIED (currently shows UNRESOLVED for most occupations)

---

## Recommended Paper Structure

```
1. Introduction
   — Problem: thin-file gig workers, no credit bureau history
   — Contribution: 3-layer architecture (evidence + policy + risk)
   — Use T1 numbers in intro to motivate

2. Related Work
   — Alternative credit scoring literature
   — Policy-constrained ML
   — Human-AI collaboration in credit

3. System Architecture
   — From FINAL_PROJECT_ARCHITECTURE.md
   — 3-layer diagram (D1-D4)
   — Evidence score formula
   — Policy engine (Kleene logic)

4. Experimental Setup
   — T1: Home Credit authentic (verified)
   — T2-T9: Synthetic (2 DGPs, 10 seeds each)
   — Statistical methodology: mean ± 95% CI, t(df=9), Bonferroni α=0.0167

5. Results
   5.1 T1: Baseline (use T1_results.json)
   5.2 T2: Feature ablation (use T2_ablation_agg.csv)
   5.3 T3: Evidence gating (use T3_gating_agg.csv + T3_tau_e_agg.csv)
   5.4 T4/T5: Review allocation (use T4_T5_review_agg.csv)
   5.5 T6: History sensitivity (use T6_history_agg.csv)
   5.6 T9: Fairness (use T9_fairness_aggregated.csv)

6. Discussion
   — Strong findings (architecture eliminates policy violations, R1 beats random)
   — Negative findings (gig features don't help in synthetic DGP)
   — Calibration limitation (slope ≈ 0.075, not a code bug)
   — Limitations section (synthetic data, no real gig labels, perfect oracle)

7. Conclusion

Appendix A: Reproducibility Commands
Appendix B: Policy Rule Details
Appendix C: Statistical Tables (raw seed-level data)
```
