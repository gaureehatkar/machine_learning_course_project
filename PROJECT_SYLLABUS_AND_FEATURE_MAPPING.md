# PROJECT SYLLABUS AND FEATURE MAPPING
## Policy-Constrained Credit Decisioning with Evidence-Quality Gating for Thin-File Gig/Platform Workers
**Version 1.2 — Repository-Based (2026-09-22)**

A subject is listed ONLY if something in the project actually implements it.
Every feature is verified against `src/feature_engineering/build_features.py`.

---

## PART 1 — SYLLABUS MAPPING

### 1.1 Subject → Concept → Component → Module

| Subject | Concepts Applied | Project Component | File | Status | PPT-Ready? |
|---|---|---|---|---|---|
| **Probability & Statistics** | LogNormal/Normal/Uniform/Bernoulli distributions; probability of default; CV; bootstrap (paired applicant-level); seed-level t-CI (df=9); Bonferroni correction (α/3); effect sizes | DGP, risk model output, evaluation statistics | `src/data_generation/dgp.py`, `src/evaluation/statistical_tests.py` | ✅ Implemented | Yes |
| **Linear Algebra** | Feature vector X_i ∈ ℝ¹²; design matrices; logistic regression parameterisation β^T x; standardisation | LR model, feature tables | `src/models/train_models.py`, `src/feature_engineering/build_features.py` | ✅ Implemented | Yes |
| **Calculus / Optimisation** | Logistic loss minimisation; L2 regularisation; gradient boosting as functional gradient descent; Platt scaling by maximum likelihood (L-BFGS-B) | LR training, XGBoost, Platt calibration | `src/models/train_models.py`, `src/calibration/platt.py` | ✅ Implemented | Yes |
| **Machine Learning** | Supervised binary classification; Logistic Regression; XGBoost (gradient boosting); overfitting control (depth, subsample, regularisation); train/val/test discipline; Platt calibration; class imbalance handling via PR-AUC (no resampling) | Risk models, calibration | `src/models/`, `src/calibration/platt.py` | ✅ Implemented | Yes |
| **Data Mining** | Feature engineering; temporal aggregation over 12-month window; missing-value handling (NaN, median imputation, missing indicators); winsorisation; OLS trend and seasonal regression | Feature builder | `src/feature_engineering/build_features.py` | ✅ Implemented | Yes |
| **Software Engineering** | Modular architecture; YAML config-as-code; pytest unit and integration tests; reproducibility (seeds, manifests, pinned versions); CLI experiment commands; Makefile | Whole repository | `src/`, `tests/`, `configs/`, `Makefile` | ✅ Implemented | Yes |
| **Algorithms / Data Structures** | Decision trees (XGBoost); expression trees / AST for rule conditions; three-valued (Kleene) logic; version selection by effective-date intervals; top-K ranking for review | Rule engine, review allocation, evaluation | `src/policy/`, `src/decisions/review.py`, `src/evaluation/metrics.py` | ✅ Implemented | Yes |
| **Explainable AI** | TreeSHAP for XGBoost; reason codes (PD_HIGH, POLICY_INELIGIBLE, EVIDENCE_INSUFFICIENT); policy explanations with UNVERIFIED source clauses | Explanation output | `src/explainability/shap_values.py`, `src/decisions/gate.py` | ✅ Implemented (SHAP for XGB only; LR coefficients NOT implemented) | Yes (with caveat) |
| **Database Management** | Relational schemas (applicants, monthly, policy_attributes, features tables); keys (applicant_id); versioned rule tables with effective dates and provenance; Parquet columnar storage | Data layer, policy repository | `data/`, `configs/policy_rules/` | ✅ Partially (Parquet + YAML; no SQL DBMS) | Yes |
| **NLP** | **NOT IMPLEMENTED** — `src/policy/nlp_extract/` is empty; policy rules are manually transcribed | — | — | ❌ Not implemented | No — do NOT include |
| **Cloud / Distributed Systems** | **NOT IMPLEMENTED** — not in project scope | — | — | ❌ Not in scope | No |

### 1.2 Mathematical Concepts (Implemented)

| Concept | Formula | Where Used | File |
|---|---|---|---|
| Probability of default | `PD_i = P(Y_i=1 \| X_i^risk)` | Risk model output | `src/models/train_models.py` |
| Logistic model | `σ(β₀ + β^T x)`, `σ(z) = 1/(1+e^{-z})` | Model A | `train_models.py` |
| Boosted model | `σ(Σ_k f_k(x))` | Model B | `train_models.py` |
| Log-loss + L2 | `−Σ[y·ln p + (1-y)·ln(1-p)] + (1/2C)||β||²` | LR training | `train_models.py` |
| Platt calibration | `p_cal = σ(A·logit(p_raw) + B)` | Calibration | `src/calibration/platt.py` |
| Liquidity recursion | `L_t = L_{t-1} + I_t − E_t − D_t` | DGP, features | `src/data_generation/dgp.py` |
| Income volatility | `CV_I = σ_I(ddof=1) / Ī` | Feature B | `build_features.py:_income_volatility()` |
| Income trend | `β₁/Ī` from OLS `I_t = β₀ + β₁t + ε` | Feature B | `build_features.py:_income_trend()` |
| Seasonality index | `√(a²+b²)/Ī` from harmonic OLS | Feature B | `build_features.py:_seasonality_index()` |
| Evidence score | `E = 0.5·H/12 + 0.25·AA + 0.25·ULI` | Evidence layer | `src/evidence/compute_evidence.py` |
| Policy state | `S = h(W, R, t_dec) ∈ {SATISFIED,UNSATISFIED,UNRESOLVED}` | Policy engine | `src/policy/rule_engine.py` |
| Kleene AND/OR/NOT | Three-valued logic tables | Policy engine | `src/policy/kleene.py` |
| Decision function | `D = f(PD, E, S; mode, τ, τ_E)` | Decision engine | `src/decisions/gate.py` |
| Predictive entropy | `H(p) = −p·ln p − (1-p)·ln(1-p)` | R1, R3 review strategies | `src/decisions/review.py` |
| Coverage / risk | `#APPROVE/N`; `#(APPROVE∧Y=1)/#APPROVE` | Evaluation metrics | `src/evaluation/metrics.py` |
| Brier score | `(1/N)Σ(PD_i − Y_i)²` | Metrics | `metrics.py:brier()` |
| ECE | `Σ_m (n_m/N)·\|mean(y_m) − mean(p_m)\|` over 10 quantile bins | Calibration metrics | `metrics.py:ece()` |
| Seed-level CI | `Δ̄ ± t_{0.975,9}·s/√10` | Statistical tests | `statistical_tests.py:seed_level_ci()` |
| Bonferroni α | `α/n_contrasts = 0.05/3 ≈ 0.0167` | Statistics | `statistical_tests.py:bonferroni_alpha()` |

---

## PART 2 — FEATURE DICTIONARY

Complete feature dictionary — every feature verified in `src/feature_engineering/build_features.py`.

### Set A — Conventional Financial Features (7) — All enter PD model

| Feature | Raw Source | Code Location | Real-World | Category | Formula | Unit | Window | In ML? | In Evidence? | In Policy? | In Decision? | Missing Treatment | Leakage Risk | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `income_mean` | Monthly income | `_income_mean()` | Industry-grounded (bank statement/AA) | Conventional | `(1/H)ΣI_t` | ₹/month | H visible months | ✅ Set C | No | No | No | Defined for H≥1 | Low | ✅ Implemented |
| `expense_mean` | Monthly expenses | `_expense_mean()` | Industry-grounded | Conventional | `(1/H)ΣE_t` | ₹/month | H visible months | ✅ Set C | No | No | No | Defined for H≥1 | Low | ✅ Implemented |
| `expense_ratio` | Income, expenses | `_expense_ratio()` | Industry-grounded (affordability) | Conventional | `Ē / Ī` | Dimensionless | H visible months | ✅ Set C | No | No | No | NaN if Ī=0 | Low | ✅ Implemented |
| `debt_mean` | Monthly debt/EMI | `_debt_mean()` | Industry-grounded (bureau obligations) | Conventional | `(1/H)ΣD_t` | ₹/month | H visible months | ✅ Set C | No | No | No | Defined for H≥1 | Low | ✅ Implemented |
| `has_emi` | Debt payments | `_has_emi()` | Industry-grounded | Conventional | `1 if any(D_t>0)` | Binary {0,1} | H visible months | ✅ Set C | No | No | No | Defined for H≥1 | Low | ✅ Implemented |
| `liquidity_mean` | Balance L_t | `_liquidity_mean()` | Industry-grounded (statement balances) | Conventional | `mean(L_t)` | ₹ | H visible months | ✅ Set C | No | No | No | Defined for H≥1 | Medium (cumulative; obs months only) | ✅ Implemented |
| `liquidity_min` | Balance L_t | `_liquidity_min()` | Industry-grounded (stress indicator) | Conventional | `min(L_t)` | ₹ | H visible months | ✅ Set C | No | No | No | Defined for H≥1 | Medium (test T-D4 asserts no outcome months) | ✅ Implemented |

### Set B — Alternative / Gig Features (5) — All enter PD model

| Feature | Raw Source | Code Location | Real-World | Category | Formula | Unit | Window | In ML? | In Evidence? | In Policy? | In Decision? | Missing Treatment | Leakage Risk | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `income_volatility` | Monthly income | `_income_volatility()` | Literature-grounded (gig instability) | Alternative | `σ_I(ddof=1) / Ī` | Dimensionless | H visible months | ✅ Set C | No | No | No | **NaN if H < 2**; XGB native; LR imputes train-median | Low | ✅ Implemented |
| `income_trend` | Monthly income | `_income_trend()` | Plausible experimental | Alternative | `β₁/Ī` from OLS | Dimensionless | H visible months | ✅ Set C | No | No | No | **NaN if H < 3** | Low | ✅ Implemented |
| `platform_tenure` | Platform records at cutoff | `app_row["platform_tenure"]` | Plausible experimental (single pilot) | Alternative | Integer months at cutoff; U{1..24}; STATIC | Months | As-of cutoff | ✅ Set C | No | No | No | Never (static; drawn at generation) | **Low — only because reference date is cutoff** | ✅ Implemented |
| `multi_platform` | Platform records at cutoff | `app_row["multi_platform"]` | Literature-grounded (weak) | Alternative | Binary {0,1}; STATIC | Binary | As-of cutoff | ✅ Set C | No | No | No | Never (static) | Low | ✅ Implemented |
| `seasonality_index` | Monthly income | `_seasonality_index()` | Literature-grounded (weak) | Alternative | `√(a²+b²)/Ī` from harmonic OLS | Dimensionless | H visible months | ✅ Set C | No | No | No | **NaN if H ≠ 12** (strict equality) | Low | ✅ Implemented |

### Evidence Features (3) — NEVER enter PD model

| Feature | Raw Source | Code Location | Real-World | Category | Formula | Unit | Window | In ML? | In Evidence? | In Policy? | In Decision? | Missing Treatment | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `history_length` | Available statement months | `app_row["history_length"]` | Industry-grounded (statement requirements) | Evidence | H_i ∈ {3,6,9,12}; drawn at generation | Months | As-of cutoff | ❌ NEVER | ✅ Evidence formula | No | Indirectly (via E) | Always present | ✅ Implemented |
| `aa_completeness` | AA data availability | `app_row["aa_completeness"]` | Industry-grounded framework; values synthetic | Evidence | U(0,1) synthetic | Fraction [0,1] | As-of cutoff | ❌ NEVER | ✅ Evidence formula | No | Indirectly (via E) | NaN → 0.0 (most conservative) | ✅ Implemented |
| `uli_completeness` | ULI data availability | `app_row["uli_completeness"]` | Plausible experimental (not deployed at scale) | Evidence | U(0,1) synthetic | Fraction [0,1] | As-of cutoff | ❌ NEVER | ✅ Evidence formula | No | Indirectly (via E) | NaN → 0.0 | ✅ Implemented |

### Policy Features (2) — NEVER enter PD model

| Feature | Raw Source | Code Location | Real-World | Category | Source | Unit | Window | In ML? | In Evidence? | In Policy? | In Decision? | Missing Treatment | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `jan_samarth_state` | Rule engine output | `rule_engine.py` | UNVERIFIED (Task 10b incomplete) | Policy | Kleene eval over policy_attrs | {SATISFIED,UNSATISFIED,UNRESOLVED} | As-of cutoff | ❌ NEVER | No | ✅ Engine output | ✅ D2/D4 gating | NULL attr → UNRESOLVED | ✅ Framework implemented; content UNVERIFIED |
| `pmmy_state` | Rule engine output | `rule_engine.py` | UNVERIFIED (Task 10b incomplete) | Policy | Kleene eval over policy_attrs | {SATISFIED,UNSATISFIED,UNRESOLVED} | As-of cutoff | ❌ NEVER | No | ✅ Engine output | ✅ D2/D4 gating | NULL attr → UNRESOLVED | ✅ Framework implemented; content UNVERIFIED |

### Contextual Variable (1) — Reporting only

| Feature | Raw Source | Code Location | Real-World | Category | Formula | Unit | Window | In ML? | In Evidence? | In Policy? | In Decision? | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `e_shram_registered` | e-Shram registration | `app_row["e_shram_registered"]` | Registration exists; prevalence 0.64 is methodological | Contextual | Bernoulli(0.64) synthetic | Binary {0,1} | As-of cutoff | ❌ NEVER | No | No | ❌ NEVER | ✅ Implemented (subgroup reporting only) |

### Raw Policy Attributes (separate table: `policy_attributes.parquet`)

| Attribute | Generation | Used By | Status |
|---|---|---|---|
| `age` | Normal(34,11) clipped [18,70]; 5% MCAR NaN; PROVISIONAL | Policy engine | ✅ Implemented; PROVISIONAL |
| `occupation_category` | Categorical 5 types, 5% MCAR; PROVISIONAL | Policy engine | ✅ Implemented; PROVISIONAL |
| `nonfarm_business_flag` | 0 iff agri_labour; NaN if occupation is NaN | Policy engine | ✅ Implemented; PROVISIONAL |
| `annual_income` (derived) | 12 × visible-window `income_mean`; computed in experiment runners | Policy engine | ✅ Derived at runtime; not stored |

### Metadata and Target

| Column | Role | Status |
|---|---|---|
| `applicant_id` | String identifier; format `A{i:06d}` | ✅ Implemented |
| `dgp_id` | DGP identifier {1,2} | ✅ Implemented |
| `seed_id` | Dataset seed {0..10} | ✅ Implemented |
| `split` | {train, val, test} — stratified 60/20/20 | ✅ Implemented |
| `default_flag` | Target: 1 if structural default in months 13–24 | ✅ Implemented |

**Total: 4 metadata + 12 model features + 3 evidence + 2 policy + 1 contextual + 1 target = 23 columns** ✅

---

## PART 3 — SOURCE → TRANSFORMATION → DESTINATION

| Source | Transformation | Output Feature | Destination | Implemented? |
|---|---|---|---|---|
| Monthly income (months 1..H) | mean | `income_mean` | PD model (set C) | ✅ |
| Monthly income (months 1..H) | σ(ddof=1)/mean | `income_volatility` | PD model (set C) | ✅ |
| Monthly income (months 1..H) | OLS β₁/mean | `income_trend` | PD model (set C) | ✅ |
| Monthly income (H=12 only) | Harmonic OLS amplitude/mean | `seasonality_index` | PD model (set C) | ✅ |
| Monthly expense (months 1..H) | mean | `expense_mean` | PD model (set C) | ✅ |
| Monthly expense / income | mean(E)/mean(I) | `expense_ratio` | PD model (set C) | ✅ |
| Monthly debt (months 1..H) | mean | `debt_mean` | PD model (set C) | ✅ |
| Monthly debt (months 1..H) | any > 0 | `has_emi` | PD model (set C) | ✅ |
| Liquidity L_t (months 1..H) | mean | `liquidity_mean` | PD model (set C) | ✅ |
| Liquidity L_t (months 1..H) | min | `liquidity_min` | PD model (set C) | ✅ |
| Platform records (at cutoff) | integer count (static) | `platform_tenure` | PD model (set C) | ✅ |
| Platform records (at cutoff) | binary ≥2 (static) | `multi_platform` | PD model (set C) | ✅ |
| Visible history count | H_i from draw | `history_length` | Evidence engine | ✅ |
| AA data availability | fraction (synthetic) | `aa_completeness` | Evidence engine | ✅ |
| ULI data availability | fraction (synthetic) | `uli_completeness` | Evidence engine | ✅ |
| age, occupation, nonfarm, annual_income + rule files | Kleene rule evaluation | `jan_samarth_state`, `pmmy_state` | Decision engine | ✅ (UNVERIFIED content) |
| e-Shram registration | binary (synthetic) | `e_shram_registered` | Subgroup reporting | ✅ |
| Liquidity L_t (months 13–24 ONLY) | structural default rule | `default_flag` | Training target / evaluation | ✅ |

---

## PART 4 — FEATURE SET AUDIT

Verified by `tests/test_features.py` and assertion in `src/models/train_models.py:_assert_feature_set()`:

- ✅ Set A has exactly 7 columns
- ✅ Set B has exactly 5 columns
- ✅ Set C = A∪B has exactly 12 columns
- ✅ `ALL_COLUMNS_ORDERED` has exactly 23 entries
- ✅ No evidence columns (`history_length`, `aa_completeness`, `uli_completeness`) appear in set C
- ✅ No policy columns (`jan_samarth_state`, `pmmy_state`) appear in set C
- ✅ No contextual column (`e_shram_registered`) appears in set C
- ✅ Static attributes (`platform_tenure`, `multi_platform`) are cutoff values — T-D8 passes
- ✅ Cutoff invariant: perturbing months 13–24 leaves features bit-identical — T-D9 passes

---

## PART 5 — PPT-READINESS TABLE

| PPT Section | Evidence Available | Status | Safe to Present? |
|---|---|---|---|
| Problem: thin-file gig workers lack credit history | Literature, project framing | ✅ | Yes |
| Architecture: three-layer system (Risk ≠ Evidence ≠ Policy) | `src/decisions/gate.py`, feature separation | ✅ | Yes |
| Dataset: Home Credit 307k rows, 8.07% default | `T1_results.json` | ✅ Verified | Yes — label as Russian consumer loans |
| Dataset: Afsharinia & Gurtoo gig workers, Bangalore, CC BY 4.0 | `docs/dataset2_freeze.md` | ✅ Verified | Yes — label as grounding only, no default labels |
| Synthetic dataset: SynthGigCredit-IN-v1 design | `src/data_generation/` | ✅ Code verified | Yes — label as simulation under stated assumptions |
| Feature engineering: 12 features, A/B/C sets, 6 views | `build_features.py`, tests | ✅ | Yes |
| Evidence formula: E = 0.5·H/12 + 0.25·AA + 0.25·ULI | `compute_evidence.py` | ✅ | Yes — label as designed assumption, not industry standard |
| Policy engine: Kleene 3-valued, JanSamarth/PMMY | `src/policy/` | ✅ Framework | Yes — clearly label rules as UNVERIFIED placeholders |
| Decision engine: D1–D4, APPROVE/REVIEW/DECLINE | `gate.py`, all 5 D4 rows tested | ✅ | Yes |
| T1 results: XGB ROC-AUC 0.757, LR 0.738 | `results/authentic/T1_results.json` | ✅ Verified | Yes — label as Home Credit validation of pipeline |
| T2–T6 results | No result files | ❌ Not available | No — do not present as results |
| Streamlit demo | `app/main.py` working with heuristic PD | ✅ (with caveat) | Yes — label PD as heuristic, note no trained model loaded |
| Test suite: 69/69 passing | pytest output | ✅ | Yes |
| Contributions | FINAL_PROJECT_TECHNICAL_DOCUMENTATION §3 | ✅ | Yes |
| Limitations | FINAL_PROJECT_TECHNICAL_DOCUMENTATION §18 | ✅ | Yes — be upfront |
