# FINAL PROJECT TECHNICAL DOCUMENTATION
## Policy-Constrained Credit Decisioning with Evidence-Quality Gating for Thin-File Gig/Platform Workers
**Version 1.2 — Repository-Based Reconstruction (2026-09-22)**

---

## 1. PROBLEM STATEMENT

### 1.1 Academic
Conventional credit underwriting relies on bureau history, salary documentation, and stable employment records. Gig/platform workers often have irregular income, multiple income sources, limited formal history, and incomplete conventional documentation — leaving them thin-file or no-file for automated decisions.

This project builds and evaluates a decision pipeline that explicitly integrates:
- A calibrated ML risk model estimating probability of default
- An evidence-quality gate scoring data sufficiency
- A policy/scheme eligibility constraint with clause-level provenance

Evaluated on: authentic credit-risk data (Home Credit benchmark), Indian gig-worker population grounding (Afsharinia & Gurtoo, CC BY 4.0), and a controlled synthetic longitudinal dataset (SynthGigCredit-IN-v1).

### 1.2 Practical
Indian lenders rely on bureau data, bank statements, and Account Aggregator cash-flow data. Gig workers often lack sufficient evidence, so lenders trade off approving on thin evidence (higher uncertainty) against manual review (higher cost). This system measures **evidence sufficiency separately from credit risk**, treats **scheme eligibility as a separate constraint with an audit trail**, and tests what this does to approval, default rate, and review efficiency at fixed review budgets.

### 1.3 One-Sentence Summary
A credit decision system for gig workers that estimates default probability via ML, separately scores data confidence via an evidence formula, separately checks government-scheme eligibility via a rule engine, and combines them into an auditable approve/review/decline decision — evaluated on authentic credit data and controlled synthetic experiments.

---

## 2. MOTIVATION

1. **Thin files**: A large unorganised workforce with limited bureau history.
2. **Income volatility**: Gig income is irregular; volatility in literature is typically 20–40%.
3. **Fragmented evidence**: Data sits across platforms, bank accounts, UPI, AA, ULI registries.
4. **Eligibility is separate from risk**: Government-scheme eligibility is rule-based; it should not be learned by the default model.
5. **Review bottleneck**: Manual review is scarce; *whom* to review matters at fixed budgets.

---

## 3. EXISTING SYSTEMS AND PRIOR ART

| System / Paper | What Exists | Our Contribution | Classification |
|---|---|---|---|
| LR + gradient boosting + calibration | Standard models, PR-AUC/Brier metrics | Applied to gig-worker synthetic data with evidence/policy layers | Established |
| Alternative credit scoring (FinRegLab, KarmaLife) | Cash-flow / alternative-data underwriting | Evidence-quality gating kept separate from risk | Empirical extension |
| IBM US10853736B2 | Deterministic eligibility rule evaluation | Coupled to ML risk + evidence layers | Adaptation |
| Palantir US11461847B2 | Multi-source integration, provenance | Indian scheme rules, clause-level provenance | Adaptation |
| Capital One US10242324B2 | ML + rules in credit decisions | Evidence sufficiency as separate gate | Engineering integration |
| Kleene / three-valued logic in policy engines | Prior art in legal DSLs | Thin-file gig workers with UNRESOLVED on missing attributes | Adaptation |
| **Integration: risk + evidence gate + policy rule engine + fixed-budget review in one evaluated pipeline** | — | **Potential technical contribution** | Not demonstrated end-to-end in reviewed sources |

**No individual component is claimed as novel.**

---

## 4. INDIAN LENDING CONTEXT

| Evidence Type | Typical Purpose | Documented Industry Practice | Status in This Project |
|---|---|---|---|
| Credit bureau (CIBIL, Experian) | Default risk | ✅ Documented | Used conceptually (not in dataset) |
| Bank statements (6–12 months) | Cash-flow verification | ✅ Documented | `income_mean`, `liquidity` features |
| Account Aggregator data | Consent-based cash-flow | ✅ Documented (emerging) | `aa_completeness` as evidence variable |
| UPI transactions | Income verification | Emerging practice | `uli_completeness` as evidence variable |
| Platform earnings | Income verification | Single pilot only (Source B) | `income_volatility`, `platform_tenure` as gig features |
| e-Shram registration | Worker identification | ✅ Documented | `e_shram_registered` — contextual/reporting only |
| JanSamarth / PMMY | Scheme access | **UNVERIFIED** — must be replaced with verified official source | Policy layer (Task 10b incomplete) |

**Do NOT claim**: "banks currently use exactly these features" — only some are documented industry practice.

---

## 5. DATASETS

### Dataset 1 — Home Credit Default Risk (AUTHENTIC)
- **File**: `data/authentic/application_train.csv` (158 MB, 307,511 rows)
- **Nature**: Authentic, labelled (Russian consumer loans, 2016–2018; 8.07% default)
- **Used for**: Validating LR/XGBoost/calibration/metrics pipeline (T1 experiment)
- **NOT used for**: Indian gig-worker characteristics, policy/evidence features
- **Features used**: 10 numeric + 5 categorical + 6 derived (credit/income ratio, annuity/income ratio, credit term, age_years, years_employed, employed_flag)
- **Split**: Stratified 60/20/20, seed=42

### Dataset 2 — Afsharinia & Gurtoo COVID-19 Gig Workers (GROUNDING ONLY)
- **File**: `data/authentic/Dataset -COVID-19 and Human Security.xlsx` (1.4 MB)
- **Nature**: Cross-sectional survey, 2,830 gig workers, Bangalore India
- **DOI**: 10.17632/j6hd2dfsh8.1 | **Licence**: CC BY 4.0 (VERIFIED 2026-09-22)
- **Used for**: DGP parameter grounding only (income scale, age distribution, occupation types)
- **NOT used for**: Training, default labels, performance claims
- **Default labels**: ABSENT (only a 5-point Likert "loan repayment ability" fear measure — NOT a binary outcome)
- **Grounded parameters**: `mu_income` (income scale ≈ ₹18,903 household mean), `age` distribution (mean=37, SD=10), occupation categories
- **Provisional parameters (not grounded)**: volatility, tenure, multi-platform, expense ratio, liquidity, seasonality, EMI, e-Shram — all labelled "literature-informed (provisional)"
- **Freeze record**: `docs/dataset2_freeze.md` — STATUS: FROZEN ✅

### Dataset 3 — SynthGigCredit-IN-v1 (SYNTHETIC)
- **Generator**: `src/data_generation/dgp.py` + `generate_data.py`
- **Scale**: 25,000 applicants × 24 months × 2 DGPs × 10 seeds = 20 experimental datasets
- **Currently generated**: g0_seed=0 only; seeds 1–10 pending G0 PASS
- **Target**: Structural default from liquidity mechanism — not from policy/evidence
- **Key outputs**: `monthly.parquet`, `applicants.parquet`, `policy_attributes.parquet`, `latent_params.parquet`

---

## 6. SYNTHETIC DGP — EXACT SPECIFICATION

### 6.1 Per-Applicant Draws (Static RNG substream: `seed×1000+1`)

| Parameter | Distribution | Class |
|---|---|---|
| Baseline income `b` | LogNormal(μ=9.9, σ=0.4), median ≈ ₹19,900 | Literature-informed (provisional) |
| Platform tenure at cutoff | U{1..24} integer months — static, no accrual post-cutoff | Methodological |
| Multi-platform | Bernoulli(0.60) | Methodological |
| Volatility `σ_m` | `U(0.15,0.40) × (1−0.15·multi) × (1−0.15·tenure/24)` | Range literature-informed; hooks methodological |
| Income growth `g` | N(0, 0.01) | Methodological |
| Seasonal amplitude | U(0.05, 0.35), phase U(0, 2π) | Literature-informed (provisional) |
| Expense ratio `ρ` | U(0.45, 0.85) | Methodological |
| EMI holder | Bernoulli(0.30); amount U(3000, 8000), re-drawn monthly | Methodological |
| Initial liquidity `L₀` | LogNormal(μ_L0=10.5, σ=0.8) — prevalence tuning knob | Methodological |
| Visible history `H_i` | {3,6,9,12} w.p. {0.15,0.25,0.25,0.35} | Methodological |
| AA / ULI completeness | U(0,1) each, independent of H_i and Y | Methodological (strong assumption) |
| e-Shram registration | Bernoulli(0.64) | Methodological assumption |
| Age | Normal(34,11) clipped [18,70], 5% MCAR → NaN | Provisional (UNVERIFIED rule dependency) |
| Occupation | ride_hailing 0.30, delivery 0.30, freelance 0.20, retail_micro 0.12, agri 0.08; 5% MCAR | Provisional |

### 6.2 Monthly Simulation Formula

**Observation window (months 1–12), using static_rng:**
```
ε_t = exp(N(−σ_m²/2, σ_m))            [lognormal noise, mean ≈ 1]
Income_t = b·(1+g)^t · (1 + amp·sin(2πt/12 + φ)) · ε_t · lvl_t · shock_t
Expense_t = max(ρ·b + N(0, 2000), 0)
Debt_t = U(3000,8000) if has_emi else 0    [re-drawn each month]
L_t = L_{t-1} + Income_t − Expense_t − Debt_t
```

**Outcome window (months 13–24), using outcome_rng (SEPARATE substream: `seed×1000+2`):**
```
lvl_out = exp(N(−s_inc²/2, s_inc))     [s_inc=0.40, per-applicant income shock]
ρ_out = ρ + N(0, s_rho)               [s_rho=0.20, expense ratio shift]
[DGP-2 only: × (1 − 0.5·Bernoulli(0.10)) monthly income shocks]
```

### 6.3 Default Rule
**DGP-1**: `L_t < 0 for 2 consecutive months` within t=13..24
**DGP-2**: same **OR** `L_t < −₹10,000` in any month of t=13..24

Target prevalence: 12–18% per DGP (tuned by `mu_L0`).

### 6.4 Why Structural Default
Default is purely from `income → expenses + debt → liquidity → distress`. Policy and evidence variables are **independent of default by design** — any finding that "policy reduces default" would be circular. Policy value is compliance, not risk reduction.

### 6.5 RNG Separation (Cutoff Invariance)
Two separate `numpy.random.Generator` instances per seed:
- `static_rng` → all months 1–12 draws
- `outcome_rng` → all months 13–24 draws

Perturbing the outcome window leaves every feature column **bit-identical** (T-D9, verified by tests).

---

## 7. FEATURE ENGINEERING — EXACT IMPLEMENTATION

**Source**: `src/feature_engineering/build_features.py`
**Total columns**: 23 = 4 metadata + 12 features (set C) + 3 evidence + 2 policy + 1 contextual + 1 target

### 7.1 Set A — Conventional Features (7)

| Feature | Formula | Window | NaN Rule |
|---|---|---|---|
| `income_mean` | `Ī = (1/H)ΣI_t` | H visible months | Never (H≥1) |
| `expense_mean` | `Ē = (1/H)ΣE_t` | H visible months | Never |
| `expense_ratio` | `Ē / Ī` | H visible months | NaN if Ī=0 |
| `debt_mean` | `(1/H)ΣD_t` (₹/month) | H visible months | Never |
| `has_emi` | `1 if any(D_t > 0)` | H visible months | Never |
| `liquidity_mean` | `mean(L_t)` | H visible months | Never |
| `liquidity_min` | `min(L_t)` | H visible months | Never |

### 7.2 Set B — Alternative / Gig Features (5)

| Feature | Formula | Window | NaN Rule |
|---|---|---|---|
| `income_volatility` | `σ_I(ddof=1) / Ī` | H visible months | **NaN if H < 2** |
| `income_trend` | `β₁ / Ī` from OLS `I_t = β₀ + β₁t + ε` | H visible months | **NaN if H < 3** |
| `platform_tenure` | Integer months on platform at cutoff; U{1..24}; static | As-of-cutoff | Never (static) |
| `multi_platform` | Binary: 1 if ≥2 platforms at cutoff; static | As-of-cutoff | Never (static) |
| `seasonality_index` | `√(a²+b²)/Ī` from OLS `I_t = β₀+β₁t+a·sin(2πt/12)+b·cos(2πt/12)` | H visible months | **NaN if H ≠ 12** |

### 7.3 Set C = A ∪ B (12 columns) — ONLY THESE ENTER THE PD MODEL

### 7.4 Evidence, Policy, Contextual (3+2+1 = 6)
None of these enter the PD model. Evidence feeds the evidence engine. Policy feeds the decision engine. Contextual feeds reporting only.

### 7.5 Views
- `full`: H=12 always (training — uses all observation months)
- `visible`: H = applicant's own `history_length` (val/test/decisions)
- `H1`, `H3`, `H6`, `H12`: Forced windows for history experiment (no refit)

**Cutoff invariant**: static attributes (`platform_tenure`, `multi_platform`, AA/ULI completeness, `e_shram_registered`) are taken directly from `applicants.parquet` and never re-derived from forced-H windows.

---

## 8. ML RISK MODELS — EXACT IMPLEMENTATION

**Source**: `src/models/train_models.py`

### 8.1 Feature Set Assertion
`_assert_feature_set()` verifies:
- Input columns == exactly the named set (A, B, or C)
- Forbidden columns never appear in model input: `history_length`, `aa_completeness`, `uli_completeness`, `jan_samarth_state`, `pmmy_state`, `e_shram_registered`

### 8.2 Logistic Regression
- **Preprocessing**: `WinsorisedScaler` — clip at train 1st/99th percentile → impute NaN with train-column median → `StandardScaler`
- **Model**: `LogisticRegression(C=1.0, max_iter=1000, solver='lbfgs', penalty='l2')`
- **Interpretation**: coefficient β_j gives odds ratio `exp(β_j)` per SD unit after scaling
- **Missing values**: imputed with train-median (cannot handle NaN natively)

### 8.3 XGBoost
- **Model**: `XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8, eval_metric='logloss')`
- **No `scale_pos_weight`** — explicit design decision to avoid calibration distortion
- **Missing values**: XGBoost handles NaN natively via learned default directions
- **Interpretability**: TreeSHAP post-hoc

### 8.4 Training Protocol
- Train on `features_full` (all 12 observation months) — training rows only
- Validate on `features_visible` (applicant's H_i months) — val rows only
- Test on `features_visible` — test rows only, touched once per experiment
- Split: stratified 60/20/20; split_seed = 1000 + dataset_seed

---

## 9. CALIBRATION — EXACT IMPLEMENTATION

**Source**: `src/calibration/platt.py`

**Platt scaling**: `p_cal = σ(A · logit(p_raw) + B)`
- Fit by minimising negative log-likelihood on the **validation set only** via `scipy.optimize.minimize` (L-BFGS-B), starting from A=1.0, B=0.0
- `logit(p) = log(p/(1-p))`, with p clipped to `[1e-6, 1−1e-6]`
- Applied to test set via `calibrator.transform()`

**Why Platt over isotonic**: 5,000 validation applicants with ≈15% positives → isotonic overfitting risk.

**Calibration metrics**:
- ECE: `Σ_m (n_m/N)·|mean(y_m) − mean(p_m)|` over 10 equal-frequency quantile bins
- Calibration slope/intercept: OLS regression of y on logit(p_cal); ideal slope=1, intercept=0

**T1 Result note**: Calibration slope ≈ 0.075 on Home Credit test set (ideal = 1.0) indicates systematic underprediction. This is a known limitation — bureau tables are absent; only `application_train.csv` used.

---

## 10. EVIDENCE-QUALITY LAYER — EXACT IMPLEMENTATION

**Source**: `src/evidence/compute_evidence.py`

### Formula
`E_i = 0.5·(H_i/12) + 0.25·AA_i + 0.25·ULI_i`

- `H_i` = visible history length in months (1–12)
- `AA_i` = Account Aggregator completeness ∈ [0,1]
- `ULI_i` = ULI completeness ∈ [0,1]
- Missing AA or ULI → treated as 0.0 (most conservative)
- Result clamped to [0,1]

### Threshold
`τ_E = 0.5`

- `E ≥ 0.5` → **SUFFICIENT** (can auto-approve in D3/D4)
- `E < 0.5` → **INSUFFICIENT** (→ REVIEW in D3/D4; higher referral priority in R2/R3)

At H=12, AA=0, ULI=0: E = 0.5 exactly (borderline sufficient). Gate only bites for H < 12 — which is exactly the thin-file target population.

### Important Caveats
- Weights and threshold are **designed experimental assumptions**, not industry standards
- E measures **confidence in the PD estimate**, NOT creditworthiness
- AA/ULI completeness are assumed independent of each other, of history, and of default — this is a simplifying assumption (documented in limitations)

### Analytic check
At the specified history distribution ({3:0.15, 6:0.25, 9:0.25, 12:0.35}) with AA/ULI ∈ U(0,1): approximately **29% of applicants are INSUFFICIENT** (verified in G0 check 8).

---

## 11. POLICY ENGINE — EXACT IMPLEMENTATION

**Source**: `src/policy/kleene.py`, `rule_loader.py`, `versioning.py`, `rule_engine.py`

### 11.1 What Is Implemented
**Manually transcribed rule engine framework** — NOT automated NLP policy extraction.

The NLP extraction pipeline (`src/policy/nlp_extract/`) is an **empty directory — NOT IMPLEMENTED**.

| Component | Status |
|---|---|
| Kleene three-valued logic | ✅ IMPLEMENTED |
| Rule loader / validator | ✅ IMPLEMENTED |
| Version selector | ✅ IMPLEMENTED |
| Rule engine (condition tree evaluator) | ✅ IMPLEMENTED |
| Provenance metadata in PolicyEvaluation | ✅ IMPLEMENTED (fields present; content UNVERIFIED) |
| JanSamarth/PMMY rule content | ⚠️ UNVERIFIED PLACEHOLDER |
| NLP policy extraction | ❌ NOT IMPLEMENTED |

### 11.2 Three-Valued Logic
`State ∈ {SATISFIED, UNSATISFIED, UNRESOLVED}`

Stored as full canonical names (never abbreviated). SAT/UNSAT/UNRES are shorthand in tables only.

**Kleene AND**: any UNSATISFIED → UNSATISFIED; else any UNRESOLVED → UNRESOLVED; else SATISFIED
**Kleene OR**: any SATISFIED → SATISFIED; else any UNRESOLVED → UNRESOLVED; else UNSATISFIED
**Kleene NOT**: SATISFIED ↔ UNSATISFIED; UNRESOLVED → UNRESOLVED

Missing attribute → UNRESOLVED (on_missing = "UNKNOWN").

### 11.3 Rule Representation
Each rule has: `rule_id`, `policy_id`, `policy_version`, `effective_from/to`, `priority`, `group`, `condition` (tree), `on_missing`, `source` (provenance).

Condition operators supported: `==`, `!=`, `<`, `<=`, `>`, `>=`, `IN`, `NOT_IN`, `BETWEEN`.

Compound conditions: `all_of`, `any_of`, `not`.

Conflict resolution: same group + same priority + both SAT and UNSAT → UNRESOLVED (RULE_CONFLICT).

### 11.4 Version Selection
Candidates: `effective_from ≤ decision_date < effective_to`. Highest priority, then latest effective_from. Tie or none → `PolicyVersionError`.

### 11.5 Current Rule Fixtures (UNVERIFIED)

**JanSamarth** (3 rules, effective 2023-01-01):
- age BETWEEN [18, 60]
- annual_income ≤ 1,000,000 (₹10L)
- nonfarm_business_flag == 1

**PMMY** (3 rules, effective 2023-01-01):
- age BETWEEN [18, 65]
- annual_income ≤ 1,000,000 (₹10L)
- occupation_category NOT_IN ["agri_labour"]

**ALL rule_ids, policy_versions, document_ids, clauses, pages, verified_by, verified_on are literally `"<UNVERIFIED>"`.**

Policy-dependent results (T3, T4, T5, T10) are PROVISIONAL until Task 10b is complete.

### 11.6 Scheme Combination
`combine_schemes(states, mode="any")` → Kleene OR over JanSamarth + PMMY by default.

---

## 12. DECISION ENGINE — EXACT IMPLEMENTATION

**Source**: `src/decisions/gate.py`, `tau.py`, `review.py`

### 12.1 Gating Function (Exact Precedence)
```
gate(mode, PD, E, S, τ, τ_E):
1. PD ≥ τ                             → DECLINE  (PD_HIGH)
2. mode∈{D2,D4} AND S=="UNSATISFIED"  → DECLINE  (POLICY_INELIGIBLE)
3. mode∈{D2,D4} AND S=="UNRESOLVED"   → REVIEW   (POLICY_UNRESOLVED)
4. mode∈{D3,D4} AND E < τ_E          → REVIEW   (EVIDENCE_INSUFFICIENT)
5. otherwise                          → APPROVE
```

D1 = gate 1 only. D2 = gates 1+2+3. D3 = gates 1+4. D4 = all gates.

### 12.2 τ Selection
`select_tau(pd_val, target_approval=0.70)`: binary search over sorted unique PD values to find τ giving D1 approval rate closest to 70% on the validation set.

Matched-coverage comparison: re-tune τ for each system on validation to match D4's coverage, then compare test default rates.

### 12.3 Review Allocation (Experiment B)
Pool P = {PD < τ AND policy ≠ UNSATISFIED}
Mandatory M = {policy == UNRESOLVED} — consumed first
K = ⌊B × |P|⌋, B ∈ {0.20, 0.30}

Strategies R0 (random), R1 (entropy/highest-PD), R2 (lowest E), R3 (combined).

**R1 ≡ highest-PD-first**: within pool P where all PD < τ < 0.5, entropy H(p) is monotone in p.

Perfect-review oracle: referred applicant approved iff Y=0. Not a realistic human reviewer estimate.

---

## 13. EXPERIMENTS

| Experiment | Dataset | Model | Feature Set | Status | Result Location |
|---|---|---|---|---|---|
| T1 — Authentic baseline | Home Credit 307k | LR + XGBoost | HC-specific features | ✅ COMPLETE | `results/authentic/T1_results.json` |
| T2 — Ablation A/B/C | SynthGigCredit seeds 1–10 | LR + XGBoost | A, B, C | ⚠️ Code ready; no results | `results/ablation/` (empty) |
| T3 — Gating D1–D4 | SynthGigCredit seeds 1–10 | XGB-C | C | ⚠️ Code ready; no results | `results/gating/` (empty) |
| T4/T5 — Review R0–R3 | SynthGigCredit seeds 1–10 | XGB-C | C | ⚠️ Code ready; no results | `results/review/` (empty) |
| T6 — History H=1,3,6,12 | SynthGigCredit seeds 1–10 | XGB-C (no refit) | C | ⚠️ Code ready; no results | `results/history/` (empty) |
| T7 — DGP robustness | Both DGPs | All | C | ⚠️ Implicit in T2–T5; no separate runner | — |
| T8 — Calibration | Both DGPs | LR+XGB | C | ⚠️ Metrics implemented; no run | — |
| T9 — Fairness | Both DGPs | XGB-C | C + e_shram | ❌ NOT IMPLEMENTED | — |
| T10 — Policy correctness | SynthGigCredit | N/A | Policy attrs | ⚠️ Framework works; no dedicated runner | — |

---

## 14. VERIFIED RESULTS

### T1 — Home Credit (VERIFIED)

| Model | ROC-AUC | PR-AUC | Brier | ECE | Calib Slope |
|---|---|---|---|---|---|
| LR | 0.7383 | 0.2213 | 0.0689 | 0.0024 | 0.074 |
| XGBoost | 0.7568 | 0.2447 | 0.0678 | 0.0025 | 0.076 |

Prevalence: 8.07%. XGBoost outperforms LR on all metrics. ECE is near-zero (low ECE, but calibration slope ≈ 0.075 not ≈ 1.0 — systematic underprediction).

**Safe claim**: "On the Home Credit benchmark (307,511 applications, 8.1% default rate), XGBoost achieved ROC-AUC 0.757 and PR-AUC 0.245 — both substantially above the 8.1% prevalence baseline — validating the modelling and evaluation pipeline on authentic credit data."

**Safe claim**: "XGBoost outperforms Logistic Regression by 0.019 ROC-AUC and 0.023 PR-AUC, and is slightly better calibrated (Brier 0.0678 vs 0.0689)."

**Do NOT claim**: "The model works for Indian gig workers." Home Credit is Russian consumer loans.

### Test Suite (VERIFIED)
69/69 unit tests passing. All core math modules verified.

### T2–T6 Results
**NOT AVAILABLE**. Synthetic data seeds 1–10 not yet generated. All results are planned, not completed.

---

## 15. MATHEMATICAL FORMULATION (IMPLEMENTED)

All equations correspond to actual code:

**Probability of default**: `PD_i = P(Y_i=1 | X_i^risk)`, where `X_i^risk ∈ ℝ¹²` (set C)

**Logistic regression**: `PD_i = σ(β₀ + β^T X_i)`, fitted by minimising `−Σ[y·ln p + (1-y)·ln(1-p)] + (1/2C)||β||²`

**XGBoost**: `PD_i = σ(Σ_k f_k(X_i))`, gradient boosting with logistic loss

**Platt calibration**: `p_cal = σ(A·logit(p_raw) + B)`, A,B fitted on validation by MLE

**Liquidity recursion**: `L_t = L_{t-1} + I_t − E_t − D_t`

**Evidence score**: `E_i = 0.5·(H_i/12) + 0.25·AA_i + 0.25·ULI_i`

**Evidence status**: `E_i ≥ 0.5 → SUFFICIENT; else INSUFFICIENT`

**Policy state**: `S_i = h(W_i, R, t_dec) ∈ {SATISFIED, UNSATISFIED, UNRESOLVED}`

**Decision (D4)**: `D_i = f(PD_i, E_i, S_i; mode, τ, τ_E)` — exact precedence in §12.1

**Entropy (R1)**: `H(p) = −p·ln p − (1-p)·ln(1-p)`

**Review score (R3)**: `R3_i = 0.5·H(PD_i)/ln2 + 0.5·(1−E_i)`

**Coverage**: `#APPROVE / N_total`

**Risk**: `#(APPROVE ∧ Y=1) / #APPROVE` (default rate among approved)

**ECE**: `Σ_m (n_m/N)·|mean(y_m) − mean(p_m)|` (10 equal-frequency bins)

**Seed-level CI**: `Δ̄ ± t_{0.975,9} · s/√10` (t-distribution, df=9 over 10 seeds)

**Bonferroni α**: `0.05/3 ≈ 0.0167` (3 primary contrasts)

---

## 16. TEMPORAL LEAKAGE AUDIT

| Safeguard | Implemented? | Evidence | Risk |
|---|---|---|---|
| Features from months 1–12 only | ✅ YES | `build_features.py` restricts to `month <= obs_months` | Low |
| Default from months 13–24 only | ✅ YES | `_simulate_monthly()` computes default from `L_out` (outcome window) | Low |
| Separate RNG substreams | ✅ YES | `make_static_rng(seed*1000+1)` vs `make_outcome_rng(seed*1000+2)` | Low |
| Static attributes as-of-cutoff | ✅ YES | `platform_tenure`, `multi_platform` etc. taken from `applicants.parquet`, not re-derived | Low |
| `latent_params.parquet` write-only | ✅ YES | Feature code never reads latent_params; T-D4 test asserts this | Low |
| Platt fit on validation only | ✅ YES | `platt.py` explicitly fit on val; test contamination check in T1 code | Low |
| τ selected on validation | ✅ YES | `select_tau(pd_val)` in all experiment runners | Low |
| Test set touched once | ✅ YES (by convention) | Logged in run manifests | Medium (manual discipline) |
| Policy attributes independent of Y | ✅ YES (by DGP design) | G0 check 7: correlation < 0.05 | Low |
| No feature is deterministic function of Y | ✅ YES | Structural default via liquidity; features from income/expense | Low |

---

## 17. PROJECT STATUS SUMMARY

### Completed Work
- Full repo structure, configs, utilities
- DGP-1 and DGP-2 generator with all parameters, formulas, RNG separation
- Feature engineering (23 columns, 6 views, all formulas)
- Evidence engine (formula, threshold, states)
- Policy engine framework (Kleene, loader, versioning, rule_engine)
- Policy rule fixtures (UNVERIFIED)
- LR + XGBoost models with full preprocessing
- Platt calibration (custom implementation)
- Decision engine D1–D4 (exact precedence)
- τ selection and matched-coverage
- Review allocation R0–R3
- Evaluation metrics (PR-AUC, ROC-AUC, Brier, ECE, calibration, coverage/risk)
- Statistical tests (seed CI, paired bootstrap, Bonferroni)
- TreeSHAP explainability (XGBoost)
- Explanation JSON output
- Gate G0 validator (5 of 9 checks)
- Streamlit demo (heuristic PD)
- All experiment runners (T1–T6)
- Dataset 2 freeze record (FROZEN, CC BY 4.0)
- 69/69 unit tests passing
- **T1 results: LR ROC-AUC 0.738, XGB ROC-AUC 0.757 on Home Credit**

### Remaining Work
- Generate synthetic seeds 1–10 (after G0 PASS)
- Run T2 (ablation), T3 (gating), T4/T5 (review), T6 (history)
- Verify JanSamarth/PMMY rules (Task 10b) — required for non-provisional T3/T4/T5
- Add tests for calibration, models, metrics, SHAP, review allocation
- Complete G0 checks 1, 3, 6, 9
- Implement fairness experiment (T9)
- Connect trained model to Streamlit demo (replace heuristic PD)

---

## 18. LIMITATIONS

1. Synthetic default labels from structural liquidity mechanism
2. No public Indian gig-worker dataset with default labels
3. Home Credit population mismatch (Russian consumer loans vs Indian gig workers)
4. Synthetic policy variables — criteria are UNVERIFIED placeholders
5. DGP assumptions are methodological; income/volatility parameters are literature-informed and provisional
6. Simplified, manually transcribed policy rules (no NLP extraction)
7. Perfect-review oracle — not a realistic human reviewer
8. No production deployment; simulation only
9. No causal inference
10. AA/ULI completeness assumed independent of default — strong simplifying assumption
11. Evidence-score weights/threshold are designed assumptions, not empirically derived
12. Policy eligibility is independent of default by design — cannot show policy reduces default risk (by construction)
13. Calibration slope ≈ 0.075 on Home Credit (underprediction; bureau tables absent)
14. T2–T6 results not yet available

---

## 19. CLAIM AUDIT

| Claim | Status | Evidence | Safe Wording |
|---|---|---|---|
| "e-Shram registration predicts lower default" | ❌ DO NOT CLAIM | e_shram excluded from PD model | "e-Shram is a contextual subgroup variable for reporting only" |
| "XGBoost outperforms LR on authentic credit data" | ✅ SUPPORTED | T1: ROC-AUC 0.757 vs 0.738 | Exactly as stated |
| "Model improves real Indian gig-worker lending" | ❌ DO NOT CLAIM | Synthetic + Home Credit only | "Under simulation assumptions, the pipeline behaves as expected" |
| "Banks currently use exactly these features" | ⚠️ PARTIAL | Some documented (bureau, bank statements, AA); gig features are experimental | "Some conventional features reflect documented Indian lending practice; alternative gig features are experimental" |
| "AA completeness proves creditworthiness" | ❌ DO NOT CLAIM | E measures data confidence, not creditworthiness | "AA completeness measures data availability, not creditworthiness" |
| "Synthetic results prove real-world performance" | ❌ DO NOT CLAIM | Synthetic evidence only | "Under the stated simulation assumptions, ..." |
| "We invented alternative credit scoring" | ❌ DO NOT CLAIM | Prior art exists | "We adapt existing alternative credit-scoring approaches" |
| "Policy gating reduces default" | ❌ DO NOT CLAIM | P⟂Y by DGP design | "Policy gating changes compliance and coverage; default independence is by construction" |
| "The methodology validates for Indian gig workers" | ⚠️ CONDITIONAL | Valid only after real gig-worker data with labels | "The pipeline is designed for gig workers; its performance on real Indian gig-worker data cannot be claimed without real labels" |

---

**METHODOLOGY FROZEN — READY FOR IMPLEMENTATION**
**PROJECT IMPLEMENTATION STATUS: RESEARCH PROTOTYPE**
**PROJECT COMPLETION: 72%**
