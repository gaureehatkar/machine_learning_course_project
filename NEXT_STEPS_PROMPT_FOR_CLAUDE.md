# Prompt for Claude — SynthGigCredit-IN Next Steps

## Project Context

You are working on **SynthGigCredit-IN** — a research prototype for policy-constrained credit decisioning for thin-file gig workers in India (Zomato delivery, Ola drivers, freelancers, etc.).

**The core research question:**  
Does combining conventional credit features + gig-specific alternative features + evidence-quality gating + government policy constraints + targeted human review allocation produce better and safer credit decisioning than risk prediction alone?

**Repository:** `https://github.com/gaureehatkar/machine_learning_course_project`  
**Stack:** Python backend (FastAPI), React frontend (TypeScript + Vite), synthetic data generator (DGP), 121 unit tests.

---

## What Has Already Been Done (Do NOT redo these)

### Completed Experiments
- **T1** — Authentic baseline on Home Credit dataset (307,511 applicants, no bureau features)
  - LR: ROC-AUC 0.7383, PR-AUC 0.2213, Brier 0.0689, ECE 0.00240, Gini 0.4766, KS 0.350
  - XGB: ROC-AUC 0.7568, PR-AUC 0.2447, Brier 0.0678, ECE 0.00247, Gini 0.5136, KS 0.381
  - Results in: `results/authentic/T1_results.json`

- **T2** — Feature ablation (Set A = 7 conventional, Set B = 5 gig-specific, Set C = A+B)
  - Key finding: Set B alone has AUC ≈ 0.50 (random) — gig features structurally independent of default in the DGP
  - Set C ≈ Set A (no improvement from adding gig features)
  - Results in: `research/tables/T2_ablation_agg.csv`

- **T3** — Decision mode comparison (D1=risk only, D2=risk+policy, D3=risk+evidence, D4=all three)
  - Key finding: D1 has 7.4% policy violations; D4 has 0% (structural guarantee)
  - D4 approval rate: 41.2% (vs D1: 70.2%)
  - Results in: `research/tables/T3_gating_agg.csv`, `research/tables/T3_tau_e_agg.csv`

- **T4/T5** — Review allocation (R0=random, R1=entropy/highest-PD-first, R2=lowest-evidence, R3=combined)
  - Key finding: R1 captures 48.3% of defaulters at 20% budget vs R0 21.3% (2× better)
  - Results in: `research/tables/T4_T5_review_agg.csv`

- **T6** — History sensitivity (H=1, 3, 6, 12 months)
  - Key finding: AUC increases monotonically 0.892 (H=1) → 0.927 (H=12)
  - Results in: `research/tables/T6_history_agg.csv`

- **T9** — Fairness (e-Shram subgroup)
  - Key finding: No significant approval rate disparity (+0.53% ± 1.35%, CI crosses zero)
  - Results in: `research/tables/T9_fairness_aggregated.csv`

- **Gate G0** — DGP validation: PASS (all 8 checks)
  - Results in: `results/gate_g0_report.json`

### Completed Code
- `src/evaluation/metrics.py` — 15 metrics including Gini, KS, logistic calibration slope (correct version)
- `src/decisions/gate.py` — D1/D2/D3/D4 decision engine
- `src/decisions/review.py` — R0/R1/R2/R3 review allocation
- `src/decisions/tau.py` — threshold selection
- `src/benchmarks/risk_baselines.py` — WoELR, LGBMModel, CatBoostModel classes (written, NOT YET RUN)
- `src/benchmarks/abstention.py` — margin_to_threshold, SplitConformalClassifier (written, NOT YET RUN)
- `configs/benchmarks.yaml` — all benchmark hyperparameters

### Completed Frontend
- FastAPI backend at `app/api/main.py` (:8000)
- React frontend at `ML Froent end/ml-frontend/` (:5173)
- Assessment form → real 3-layer decision → result display
- Real T1 data shown on dashboard (AUC 0.757, real gate pass rates from T3)
- Models page shows real T1 results
- Datasets page shows real project datasets

---

## What Is Remaining — The Next Steps

### STEP 1 — Run Benchmark Experiments (Highest Priority)

**Purpose:** Show our solution is better than existing single-score systems.

**Context:** Single-score systems (WoE scorecard, LightGBM, CatBoost) produce a risk score but have NO evidence gating, NO policy checking, NO structured review allocation. They will have the same AUC (~0.75) but 7.4% policy violations and only 21% bad loan capture. Our D4+R1 architecture achieves 0% violations and 48% capture at the same AUC.

#### Baselines to implement and run:

**a) WoE Scorecard + Logistic Regression** (`woe_logreg` in `src/benchmarks/risk_baselines.py`)
- Traditional bank scorecard method used by Indian MFIs
- Uses optbinning BinningProcess for Weight-of-Evidence binning + LogisticRegression
- Hyperparameters in `configs/benchmarks.yaml`
- Run on: Home Credit (same features as T1) AND synthetic Feature Sets A and C (same protocol as T2)
- Report: ROC-AUC, PR-AUC, Brier, ECE, Gini, KS, logistic calibration slope

**b) LightGBM** (`lgbm` in `src/benchmarks/risk_baselines.py`)
- State-of-the-art gradient boosting, common in fintech
- Same features as T1 and T2 (Set A and C)
- Same Platt calibration on validation set
- Same 60/20/20 stratified split

**c) CatBoost** (`catboost` in `src/benchmarks/risk_baselines.py`)
- Handles categoricals natively, used by banks
- Same protocol

**Protocol for all baselines:**
- Fit on train only
- Platt-calibrate on validation only  
- Evaluate on test set (touch once)
- For synthetic: 10 seeds × 2 DGPs, report mean ± 95% CI using `scipy.stats.t.ppf(0.975, n-1)`
- For Home Credit: single run (same split as T1, seeds 42/43)
- Save to `results/benchmarks/` and `research/tables/benchmarks/`

**Output needed:**
```
Table: Risk Model Comparison
Method       | Dataset      | AUC    | PR-AUC | Brier  | Gini   | KS
-------------|--------------|--------|--------|--------|--------|------
WoE-LR       | Home Credit  | ?      | ?      | ?      | ?      | ?
LightGBM     | Home Credit  | ?      | ?      | ?      | ?      | ?  
CatBoost     | Home Credit  | ?      | ?      | ?      | ?      | ?
LR (ours)    | Home Credit  | 0.7383 | 0.2213 | 0.0689 | 0.4766 | 0.350
XGB (ours)   | Home Credit  | 0.7568 | 0.2447 | 0.0678 | 0.5136 | 0.381
```

**Statistical test:** For each baseline vs XGB-C, run paired seed-level t-test on 10 synthetic seeds. Apply Holm correction across baselines.

---

### STEP 2 — Review Allocation Benchmarks (Phase 3)

**Purpose:** Show our R1/R3 strategies beat existing abstention methods.

**Context:** The standard approaches for "when should a model abstain/refer" are:
1. Margin-to-threshold (closest to decision boundary)
2. Conformal prediction (prediction sets)

Both use the SAME pool and budget logic as our R0-R3.

**Baselines to run** (code in `src/benchmarks/abstention.py`):

**a) Margin-to-threshold:** Refer applicants whose |PD - τ| is smallest (most uncertain)

**b) Conformal prediction** (SplitConformalClassifier): Calibrate on validation, refer ambiguous prediction sets at α=0.10

**Protocol:**
- Same pool P = {PD < τ AND policy ≠ UNSATISFIED}
- Same budgets: 20% and 30%
- Same oracle review simulation
- Same 10 seeds × 2 DGPs
- Compare bad loan capture, default rate among approved, cost

**Output needed:**
```
Table: Review Strategy Comparison (DGP1, 20% budget)
Strategy              | Bad Loan Capture | DR Among Approved | Cost/Applicant
----------------------|-----------------|-------------------|---------------
R0 (random)           | 21.3% ± 3.6%   | 1.52% ± 0.19%    | 0.264
Margin-to-threshold   | ?               | ?                 | ?
Conformal prediction  | ?               | ?                 | ?
R1 (entropy, ours)    | 48.3% ± 5.2%   | 1.01% ± 0.18%    | 0.261
R3 (combined, ours)   | 40.6% ± 3.9%   | 1.15% ± 0.12%    | 0.262
```

---

### STEP 3 — Matched-Coverage Comparison (Phase 1)

**Purpose:** Fair comparison of D1 vs D4 at the same approval rate.

**Context:** D4 has lower approval rate (41%) than D1 (70%). A reviewer will say "of course D4 has fewer defaults — it approves fewer people." To rebut this, we show: even when D1 is tuned to match D4's approval rate, D4 still has lower default rate among approved.

**Method:**
- For each seed/DGP, get D4's approval rate on the test set
- Re-tune τ for D1 on the VALIDATION set to hit that same approval rate
- Compare default rate among approved on the TEST set between D1 and D4 at matched coverage
- Run paired t-test on the 10 per-seed differences
- Also do D2, D3 vs D1 at their own matched coverage

**Output:**
```
Table: Matched-Coverage Comparison (DGP1)
Comparison      | Coverage | D1 DR (matched) | Dx DR | Difference | p-value
----------------|----------|-----------------|-------|------------|--------
D1 vs D4        | 41.2%    | ?               | 1.75% | ?          | ?
D1 vs D3        | 49.4%    | ?               | 1.72% | ?          | ?
D1 vs D2        | 58.4%    | ?               | 1.91% | ?          | ?
```

---

### STEP 4 — Generate All Research Figures

**Purpose:** Required for paper submission. Figures tell the story visually.

Generate these 7 figures in `research/figures/` as both PNG and PDF:

1. **ROC curve** — from `results/authentic/predictions_xgb.npz` (y_test, p_cal_test). Show both LR and XGB. Mark AUC 0.7383 and 0.7568.

2. **Feature ablation bar chart** — from `research/tables/T2_ablation_agg.csv`. Grouped bars (A/B/C × LR/XGB) with 95% CI error bars. Show both DGP1 and DGP2.

3. **D1-D4 tradeoff plot** — from `research/tables/T3_gating_agg.csv`. Scatter plot: x=approval rate, y=default rate among approved. Each mode is a point with CI. Show the safety-coverage tradeoff.

4. **τ_E sensitivity curve** — from `research/tables/T3_tau_e_agg.csv`. Line chart: x=τ_E, y=approval rate and evidence fail rate on same axes.

5. **Review budget frontier** — from `research/tables/T4_T5_review_agg.csv`. x=budget (20%/30%), y=bad loan capture for R0/R1/R2/R3. Error bars. This is the most visually compelling figure.

6. **History sensitivity** — from `research/tables/T6_history_agg.csv`. x=H (1,3,6,12 — sorted numerically), y=AUC and ECE on dual y-axis. Shows monotone improvement.

7. **Calibration curve** — from `results/authentic/predictions_xgb.npz`. Plot predicted probability bins vs actual default rate. Show the compression issue (slope ≈ 0.075 visually).

**Figure requirements:**
- matplotlib + seaborn
- Clean academic style (no decorative colors)
- Labeled axes with units
- Confidence intervals shown
- Legends inside figure
- Save as PNG (300 dpi) and PDF

---

### STEP 5 — Fix T_CRIT Hardcode in run_all_research.py

In `research/run_all_research.py`, find `T_CRIT = 2.262` (hardcoded) and replace with:
```python
from scipy.stats import t as t_dist
# ... inside seed_ci function:
n_seeds = len(gdf)
t_crit = float(t_dist.ppf(0.975, n_seeds - 1)) if n_seeds > 1 else 0.0
```
This is correct for any number of seeds, not just 10.

---

### STEP 6 — Write BENCHMARK_RESULTS.md

After running steps 1-3, write `research/BENCHMARK_RESULTS.md` containing:

1. **Executive summary** — what was run, what the main finding is
2. **Risk model comparison table** (Step 1 results)
3. **Review strategy comparison table** (Step 2 results)
4. **Matched-coverage table** (Step 3 results)
5. **Old vs new calibration slope** (OLS ≈ 0.075 was wrong; logistic ≈ ? is correct)
6. **Statistical tests** — which comparisons are significant at Bonferroni α=0.0167
7. **Limitations** — what cannot be claimed
8. **Stale documents** — note that FINAL_PROJECT_TECHNICAL_DOCUMENTATION.md and FINAL_PROJECT_ARCHITECTURE.md predate the calibration slope fix

---

## Global Rules (MUST follow)

1. **Never modify existing result files** — T1_results.json, T2-T9 CSVs. Write all new results to `results/benchmarks/` and `research/tables/benchmarks/`.

2. **Same protocol as existing experiments** — fit on train only, Platt calibrate on validation only, touch test set once. Split seeds: `split_seed = 1000 + dataset_seed`. Home Credit seeds: 42/43.

3. **Report mean ± 95% CI using `scipy.stats.t.ppf(0.975, n-1)`** — never hardcode 2.262.

4. **Put all hyperparameters in `configs/benchmarks.yaml`** — already created.

5. **Never invent numbers.** If a run fails, say why and what is missing.

6. **After each phase, summarize:** what ran, what the numbers are, any anomalies.

---

## Key Files to Understand Before Starting

| File | What it contains |
|---|---|
| `src/benchmarks/risk_baselines.py` | WoELR, LGBMModel, CatBoostModel classes — ready to use |
| `src/benchmarks/abstention.py` | margin_to_threshold, SplitConformalClassifier — ready to use |
| `src/evaluation/metrics.py` | All metrics including Gini, KS, logistic calibration slope |
| `src/calibration/platt.py` | Platt calibration — use for ALL models |
| `src/decisions/gate.py` | Decision engine D1-D4 |
| `src/decisions/review.py` | R0-R3 review strategies |
| `src/decisions/tau.py` | select_tau() — threshold selection on validation |
| `configs/benchmarks.yaml` | Hyperparameters for all benchmarks |
| `configs/experiment.yaml` | Main experiment config (seeds, DGPs, τ_E, etc.) |
| `research/tables/T2_ablation_agg.csv` | T2 results — feature ablation |
| `research/tables/T3_gating_agg.csv` | T3 results — D1-D4 |
| `research/tables/T4_T5_review_agg.csv` | T4/T5 results — R0-R3 |
| `research/tables/T6_history_agg.csv` | T6 results — history sensitivity |
| `results/authentic/T1_results.json` | T1 results — do NOT overwrite |
| `results/authentic/predictions_xgb.npz` | XGB predictions for figures |

---

## The Paper's Core Argument (Do Not Lose Sight of This)

**We are NOT claiming higher AUC than existing methods.**

**We ARE claiming:**

1. Comparable AUC (0.757) WITHOUT bureau data — making credit possible for thin-file gig workers
2. Zero policy violations (structural guarantee) — impossible with single-score systems
3. 2× better bad loan capture with targeted review — demonstrating value of the architecture beyond the risk score
4. Separable, auditable layers — each of risk, evidence, policy can be independently tuned and regulated

The benchmark comparison (Step 1) shows: WoE/LightGBM/CatBoost all get similar AUC but ALL have 7.4% policy violations and 21% bad loan capture. Our architecture achieves 0% violations and 48% capture at the same AUC. That is the paper's main result.
