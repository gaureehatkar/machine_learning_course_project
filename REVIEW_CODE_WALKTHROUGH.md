# REVIEW CODE WALKTHROUGH
## Policy-Constrained Credit Decisioning — Faculty Review Preparation
**Generated from actual repository code — 2026-09-22**
**Do not modify this file. It reflects what is actually implemented.**

---

## 1. SYNTHETIC DATA GENERATION

### File paths
- `src/data_generation/dgp.py` — the math: distributions, monthly simulation, default rule
- `src/data_generation/generate_data.py` — the orchestrator: calls dgp.py, builds DataFrames, saves Parquet files
- `configs/experiment.yaml` — all parameters (income distributions, volatility, etc.)

### What this code does
Generates realistic but synthetic gig worker financial histories because real Indian gig worker loan repayment data is not publicly available. For each of 25,000 applicants it simulates 24 months of income, expenses, debt, and liquidity. It decides who defaults based on a mathematical rule — not based on policy or ML.

### Important functions

| Function | File | What it does |
|---|---|---|
| `_draw_static_attributes(rng, n, cfg)` | `dgp.py` line ~30 | Draws per-applicant constants: baseline income (LogNormal), volatility (Uniform), tenure, multi-platform flag, expense ratio, EMI, initial liquidity |
| `_draw_policy_attributes(rng, n, cfg)` | `dgp.py` line ~100 | Draws age (Normal 34±11), occupation type, nonfarm flag — for policy engine only |
| `_simulate_monthly(static, n, dgp_id, cfg, obs_rng, outcome_rng)` | `dgp.py` line ~130 | Simulates 24 months per applicant using the liquidity recursion formula |
| `generate_data(cfg, dgp_id, seed)` | `generate_data.py` line ~30 | Main function: calls the above three, builds applicants DataFrame, does 60/20/20 split |
| `save_data(...)` | `generate_data.py` line ~110 | Writes 4 Parquet files to `data/synthetic/dgp{id}/seed{n}/` |

### Key code to show (open `dgp.py`, scroll to line ~155)
The monthly simulation loop and the default rule:
```python
# Income formula
income = b * (1 + g)**t * (1 + amp*np.sin(2*pi*t/12 + phase)) * eps_t

# Liquidity recursion
L_curr = L_prev + income - expense - debt

# Default rule (DGP-1) — bottom of _simulate_monthly
consec = negative[:, :-1] & negative[:, 1:]   # two consecutive negative months
default_flag = consec.any(axis=1)
```

### Inputs and outputs
- **Input**: `configs/experiment.yaml` (n_applicants=25000, dgp_id, seed)
- **Output**: 4 Parquet files
  - `monthly.parquet` — 25,000 × 24 rows (income, expense, debt, liquidity per month)
  - `applicants.parquet` — 25,000 rows (static attributes + `default_flag` + `split`)
  - `policy_attributes.parquet` — 25,000 rows (age, occupation, nonfarm_flag)
  - `latent_params.parquet` — internal generator parameters (never read by ML code)

### Two DGP variants
- **DGP-1**: defaults when `L_t < 0 for 2 consecutive months` in months 13–24
- **DGP-2**: same OR `L_t < −₹10,000` in any single month — more severe

### RNG separation (important design point)
Two separate random number streams exist:
- `make_static_rng(seed)` → seeds `seed×1000+1` — used for months 1–12
- `make_outcome_rng(seed)` → seeds `seed×1000+2` — used for months 13–24

This guarantees that changing the default outcome does not change any feature value (no data leakage).

### What to say verbally
> "We couldn't get real Indian gig worker loan data, so we built a mathematical simulator. Each applicant gets a simulated income, expenses, and debt for 24 months. We track their bank balance — the liquidity. If the balance goes negative for two months in a row in the second year, they default. We separated the feature window (months 1–12) from the label window (months 13–24) to prevent any leakage."

### Dependencies
- `src/utils/seeding.py` (RNG functions)
- `src/utils/config_loader.py` (reads experiment.yaml)
- `sklearn.model_selection.StratifiedShuffleSplit` (60/20/20 split)

---

## 2. DATA PROCESSING / PREPROCESSING

### File path
- `src/feature_engineering/build_features.py`

### What this code does
Takes the raw monthly Parquet data and converts it into the 23-column feature table that the ML model needs. For each applicant it computes summary statistics (mean income, volatility, trend, etc.) over their visible history window. The output is a clean, structured table ready for model training.

### Important constants (top of file, lines 35–55)
```python
FEATURE_SET_A = ["income_mean", "expense_mean", "expense_ratio",
                  "debt_mean", "has_emi", "liquidity_mean", "liquidity_min"]

FEATURE_SET_B = ["income_volatility", "income_trend",
                  "platform_tenure", "multi_platform", "seasonality_index"]

FEATURE_SET_C = FEATURE_SET_A + FEATURE_SET_B  # 12 features — ONLY these enter the ML model
```

### Important functions

| Function | Line | What it does |
|---|---|---|
| `_income_mean(income)` | ~60 | `mean(I_t)` over visible months |
| `_expense_ratio(expense, income)` | ~70 | `mean(E) / mean(I)` — affordability ratio |
| `_liquidity_min(liquidity)` | ~90 | `min(L_t)` — the lowest the bank balance ever went |
| `_income_volatility(income)` | ~100 | `std(I, ddof=1) / mean(I)` — how irregular income is. **NaN if fewer than 2 months** |
| `_income_trend(income)` | ~112 | OLS regression slope divided by mean income. **NaN if fewer than 3 months** |
| `_seasonality_index(income)` | ~130 | Fits a sine wave to income. **NaN if not exactly 12 months** |
| `build_features(monthly, applicants, policy_states, view, obs_months)` | ~175 | Main function — iterates over applicants, calls all the above, returns 23-column DataFrame |

### Views (show this in the review)
```python
# Training: always uses all 12 months
view = "full"    → H = 12

# Validation/test: uses only the applicant's actual history
view = "visible" → H = applicant's history_length (3, 6, 9, or 12)

# History experiment: forces a fixed window
view = "H1"      → H = 1
view = "H3"      → H = 3
view = "H6"      → H = 6
```

### Important design rule (point this out)
Static attributes like `platform_tenure` and `multi_platform` are **never recomputed from the window**. They are passed directly from `applicants.parquet`:
```python
feats["platform_tenure"] = int(app_row["platform_tenure"])   # from file, not recomputed
feats["multi_platform"]  = int(app_row["multi_platform"])    # from file, not recomputed
```

### Inputs and outputs
- **Input**: `monthly.parquet` + `applicants.parquet` (from step 1)
- **Output**: `features_full.parquet` or `features_visible.parquet` — 23 columns, one row per applicant

### What to say verbally
> "This is the preprocessing step. We take the monthly income and expense records and compute 12 financial features per applicant. For example, income volatility measures how irregular the income is — important for gig workers. Some features like seasonality require 12 months of data, so if an applicant only has 3 months of history those features become NaN, and the XGBoost model handles that natively."

### Dependencies
- `src/utils/config_loader.py`
- `numpy` for all math
- Output feeds directly into `src/models/train_models.py`

---

## 3. ML RISK MODEL

### File paths
- `src/models/train_models.py` — training: LR and XGBoost
- `src/calibration/platt.py` — Platt calibration
- `src/evaluation/metrics.py` — evaluation metrics
- `experiments/authentic/run.py` — the Home Credit experiment that produced real results
- `results/authentic/T1_results.json` — **actual verified results**

---

### 3a. Logistic Regression

**File**: `src/models/train_models.py`, class `WinsorisedScaler` + `train_model()` with `family="logreg"`

**Preprocessing pipeline** (lines ~65–90):
```python
class WinsorisedScaler:
    # Step 1: clip outliers at train 1st and 99th percentile
    # Step 2: fill NaN with column train-median
    # Step 3: StandardScaler (zero mean, unit variance)
```

**Model** (inside `train_model()`, lines ~155–165):
```python
model = LogisticRegression(
    C=1.0,           # inverse regularisation strength (L2)
    max_iter=1000,
    solver="lbfgs",
    penalty="l2",
)
model.fit(X_train, y_train)
```

**Why this preprocessing**: LR cannot handle NaN natively, so missing features (volatility when H<2, trend when H<3) are imputed with training-set medians. Winsorisation removes extreme outliers before scaling.

---

### 3b. XGBoost

**File**: `src/models/train_models.py`, `train_model()` with `family="xgb"`

**Model** (lines ~170–185):
```python
model = XGBClassifier(
    n_estimators=100,      # 100 trees
    max_depth=4,           # tree depth (controls complexity)
    learning_rate=0.1,     # shrinkage — prevents overfitting
    subsample=0.8,         # 80% of rows per tree
    colsample_bytree=0.8,  # 80% of features per tree
    eval_metric="logloss",
)
model.fit(X_raw, y_train)  # NaN handled natively — no preprocessing needed
```

**No `scale_pos_weight`** — this is a deliberate choice noted in the code comment: "would distort calibration".

---

### 3c. Feature set assertion (important — show this)

Before training, the code asserts that forbidden columns NEVER enter the model:
```python
forbidden = [
    "history_length", "aa_completeness", "uli_completeness",  # evidence layer
    "jan_samarth_state", "pmmy_state",                         # policy layer
    "e_shram_registered",                                       # contextual
]
```
This enforces the core design principle: **Risk ≠ Evidence ≠ Policy**.

---

### 3d. Training code — `train_model()` function

**Signature**:
```python
def train_model(features_train, feature_set, family, cfg, seed, dgp_id, dataset_seed) -> FittedModel
```

- `feature_set`: `"A"` (7 conventional), `"B"` (5 alternative), or `"C"` (12 combined)
- `family`: `"logreg"` or `"xgb"`
- Returns a `FittedModel` object that wraps the trained model + metadata

---

### 3e. Probability of Default (PD)

**File**: `src/models/train_models.py`, `FittedModel.predict_raw()`:
```python
def predict_raw(self, features: pd.DataFrame) -> np.ndarray:
    X = features[self.feature_cols].values.astype(np.float64)
    if self.preprocessor is not None:
        X = self.preprocessor.transform(X)   # only for LR
    proba = self.model.predict_proba(X)
    return proba[:, 1]                        # probability of class 1 = default
```

This returns **raw PD** — a number between 0 and 1 representing the probability that the applicant will default.

---

### 3f. Platt Calibration

**File**: `src/calibration/platt.py`

**Why needed**: The raw probability from the model may not accurately reflect the true default rate. Platt calibration adjusts it.

**Formula**: `p_calibrated = σ(A × logit(p_raw) + B)`

**How it works** (lines ~55–80):
```python
class PlattCalibrator:
    def fit(self, p_raw, y):
        # Convert raw probabilities to log-odds (logit)
        logits = log(p / (1 - p))
        # Fit A and B by minimising log-loss using L-BFGS-B optimisation
        result = minimize(neg_log_likelihood, x0=[1.0, 0.0], method="L-BFGS-B")
        self.A, self.B = result.x

    def transform(self, p_raw):
        # Apply calibration: p_cal = sigmoid(A * logit(p_raw) + B)
        return sigmoid(self.A * logits + self.B)
```

**Fitted on validation set only** — never touches test data.

---

### 3g. Evaluation metrics

**File**: `src/evaluation/metrics.py`

| Function | What it measures |
|---|---|
| `roc_auc(y_true, y_score)` | Discrimination — how well model separates defaulters from non-defaulters |
| `pr_auc(y_true, y_score)` | Precision-recall — better for imbalanced data (8% default rate) |
| `brier(y_true, y_score)` | Probabilistic accuracy — lower is better |
| `ece(y_true, y_score)` | Calibration error — are predicted probabilities accurate? |

---

### 3h. Actual verified results (T1 — Home Credit)

**File**: `results/authentic/T1_results.json`

| Model | ROC-AUC | PR-AUC | Brier | ECE |
|---|---|---|---|---|
| Logistic Regression | **0.7383** | 0.2213 | 0.0689 | 0.0024 |
| XGBoost | **0.7568** | 0.2447 | 0.0678 | 0.0025 |

Dataset: 307,511 Home Credit loan applications, 8.07% default rate, stratified 60/20/20 split.

---

### What to say verbally
> "We train two models — Logistic Regression and XGBoost — on 12 financial features. For Logistic Regression we first winsorise the data to remove outliers and then scale it. XGBoost handles missing values natively. Both models output a probability of default between 0 and 1. We then apply Platt calibration on the validation set to make sure the probabilities are accurate. On the Home Credit dataset, XGBoost achieved ROC-AUC of 0.757."

### Dependencies
- `sklearn.linear_model.LogisticRegression`
- `xgboost.XGBClassifier`
- `scipy.optimize.minimize` (for Platt calibration)
- `src/feature_engineering/build_features.py` (feature set names)

---

## 4. EVIDENCE + POLICY + DECISION ENGINE

---

### 4a. Evidence Layer

**File**: `src/evidence/compute_evidence.py`

**Evidence score formula** (line ~50):
```python
# E_i = 0.5·(H_i/12) + 0.25·AA_i + 0.25·ULI_i
scores = w_h * (h / 12.0) + w_aa * aa_clean + w_uli * uli_clean
```

**Three inputs**:
- `history_length` (H): how many months of financial data we have (3, 6, 9, or 12)
- `aa_completeness` (AA): how complete the Account Aggregator bank data is (0 to 1)
- `uli_completeness` (ULI): how complete the ULI platform data is (0 to 1)

**Threshold**: `τ_E = 0.5` (from `configs/experiment.yaml`, `evidence.tau_e`)

**Status** (`evidence_status()` function, line ~70):
```python
status = "SUFFICIENT"   if E >= 0.5
status = "INSUFFICIENT" if E <  0.5
```

**Example values**:
- H=12, AA=0, ULI=0 → E = 0.5 exactly (borderline)
- H=3,  AA=0, ULI=0 → E = 0.125 (clearly insufficient)
- H=12, AA=1, ULI=1 → E = 1.0 (maximum confidence)

**Important**: Missing AA or ULI is treated as 0 (most conservative).

**What to say verbally**:
> "The evidence score answers: do we have enough data to trust the ML model's output? It combines three signals — how many months of history we have, how complete the bank statement data is, and how complete the platform data is. If the score is below 0.5 we consider the evidence insufficient and send the application to human review instead of auto-deciding."

---

### 4b. Policy Layer

**File**: `src/policy/kleene.py` — three-valued logic
**File**: `src/policy/rule_engine.py` — evaluates rules
**File**: `src/policy/rule_loader.py` — loads and validates YAML rule files
**File**: `configs/policy_rules/jan_samarth.yaml` — JanSamarth rules
**File**: `configs/policy_rules/pmmy.yaml` — PMMY rules

#### Three-valued logic (`kleene.py`)

```python
class State(str, Enum):
    SATISFIED   = "SATISFIED"    # all conditions met
    UNSATISFIED = "UNSATISFIED"  # at least one condition failed
    UNRESOLVED  = "UNRESOLVED"   # data is missing — cannot determine
```

**Why three values?** Standard true/false breaks when data is missing. If an applicant's age is missing we cannot say they are ineligible — we say UNRESOLVED and send to review.

**Kleene AND** (`kleene_and()` function):
```python
# Any UNSATISFIED → UNSATISFIED  (definite failure)
# Any UNRESOLVED  → UNRESOLVED   (can't determine)
# All SATISFIED   → SATISFIED    (definite pass)
```

**`evaluate_atom()`** — evaluates a single rule condition:
```python
# Returns UNRESOLVED if attribute value is None or NaN (missing)
if attribute_value is None:
    return State.UNRESOLVED
# Otherwise evaluates: ==, !=, <, <=, >, >=, IN, NOT_IN, BETWEEN
```

#### Policy rule files (open `configs/policy_rules/jan_samarth.yaml`)

Three rules, currently UNVERIFIED placeholders:
- `age BETWEEN [18, 60]`
- `annual_income <= 1,000,000` (₹10 lakh)
- `nonfarm_business_flag == 1`

⚠️ **All rule content is labelled `<UNVERIFIED>` — these are test fixtures, not real verified JanSamarth criteria.**

#### Policy inputs
- `age` (from `policy_attributes.parquet`)
- `occupation_category`
- `nonfarm_business_flag`
- `annual_income` = `income_mean × 12` (derived at runtime)

**What to say verbally**:
> "The policy engine checks government scheme eligibility — JanSamarth and PMMY — independently of the ML model. We use three-valued logic: satisfied, unsatisfied, or unresolved. Unresolved happens when data like age is missing. If the applicant is unsatisfied — definitively ineligible — we decline. If unresolved we send to human review. This is a design choice to avoid incorrectly declining applicants just because their documents are incomplete."

---

### 4c. Decision Engine

**File**: `src/decisions/gate.py`

**Main function**: `make_decision(pd, evidence_score, policy_state, mode, tau, tau_e) → Decision`

**Exact gate logic** (lines ~70–90):
```python
# Gate 1 — always active in all modes
if pd >= tau:
    return Decision("DECLINE", "PD_HIGH")

# Gate 2 — only in D2 and D4
if mode in {"D2", "D4"} and policy_state == "UNSATISFIED":
    return Decision("DECLINE", "POLICY_INELIGIBLE")

# Gate 3 — only in D2 and D4
if mode in {"D2", "D4"} and policy_state == "UNRESOLVED":
    return Decision("REVIEW", "POLICY_UNRESOLVED")

# Gate 4 — only in D3 and D4
if mode in {"D3", "D4"} and evidence_score < tau_e:
    return Decision("REVIEW", "EVIDENCE_INSUFFICIENT")

# All gates passed
return Decision("APPROVE", None)
```

**Four modes**:
| Mode | Active gates | What it tests |
|---|---|---|
| D1 | Gate 1 only | ML alone — baseline |
| D2 | Gates 1, 2, 3 | ML + Policy |
| D3 | Gates 1, 4 | ML + Evidence |
| D4 | All 4 gates | Full system — ML + Policy + Evidence |

**Decision reason codes**:
- `PD_HIGH` — ML model says too risky
- `POLICY_INELIGIBLE` — scheme rules say ineligible
- `POLICY_UNRESOLVED` — missing policy attributes
- `EVIDENCE_INSUFFICIENT` — not enough data history

**What to say verbally**:
> "The decision engine combines all three layers in strict priority order. First we check if the ML model says the risk is too high. Then we check policy eligibility. Then we check evidence sufficiency. This precedence order is deliberate — a high-risk applicant is declined regardless of their policy status. The D1 through D4 modes let us compare what happens when we add each layer, which is the core research question."

### Dependencies
- `src/policy/kleene.py` (State enum)
- Inputs: PD from models, E from evidence, S from policy engine

---

## 5. STREAMLIT UI

### File path
`app/main.py` — single file, contains everything

### How to run
```powershell
cd c:\Users\DELL\Desktop\ml-project
python -m streamlit run app/main.py
```
Then open `http://localhost:8501`

### User inputs (editable fields in the "Edit Applicant Attributes" section)
| Input | Type | Range |
|---|---|---|
| Monthly Income (₹) | Number | 5,000–1,00,000 |
| Expense Ratio | Slider | 0.1–1.0 |
| Has EMI | Checkbox | Yes/No |
| History Length (months) | Dropdown | 3, 6, 9, 12 |
| AA Completeness | Slider | 0.0–1.0 |
| ULI Completeness | Slider | 0.0–1.0 |
| Age | Slider | 18–70 |
| Occupation | Dropdown | ride_hailing, delivery, freelance_services, retail_micro, agri_labour |

There is also a **"Generate Random Applicant"** button that creates a random applicant using the same distributions as the DGP.

### How inputs flow through the system

```
User input / Random applicant
        ↓
_naive_pd_estimate(applicant)         ← Risk layer [HEURISTIC — see limitation]
        ↓
compute_evidence(H, AA, ULI, cfg)     ← Evidence layer [REAL formula]
        ↓
evaluate_policy(rules, attributes)    ← Policy layer [REAL engine, UNVERIFIED rules]
        ↓
make_decision(pd, ev_score, policy,   ← Decision engine [REAL gate logic]
              mode, tau, tau_e)
        ↓
Display: APPROVE / REVIEW / DECLINE
```

### Risk output (left panel — "📊 Risk Layer")
- Displays estimated PD as a percentage
- Shows the threshold τ (adjustable in sidebar)
- Shows whether the PD gate passes or fails
- Lists top 3 risk factors: expense_ratio, income_volatility, liquidity_min
- ⚠️ Note shown in UI: "Heuristic PD — no trained model loaded"

### Evidence output (middle panel — "🔍 Evidence Layer")
- Displays E score (0–1)
- Shows contribution breakdown: history + AA + ULI
- Shows SUFFICIENT or INSUFFICIENT status
- Shows whether the evidence gate is active (depends on mode)

### Policy output (right panel — "📋 Policy Layer")
- Shows JanSamarth: ✅ SATISFIED / ❌ UNSATISFIED / ❓ UNRESOLVED
- Shows PMMY: same three states
- Shows each rule group's evaluation (e.g., `[age_eligibility] → SATISFIED`)
- Shows combined state (Kleene OR over both schemes)
- Shows warning: "⚠️ UNVERIFIED — policy rules are placeholders"

### Final decision
- Large coloured banner at the top: 🟢 APPROVE / 🟡 REVIEW / 🔴 DECLINE
- Shows which mode (D1–D4) produced the decision
- Shows reason code if declined or sent to review

### Sidebar controls
- **Decision mode**: D1 / D2 / D3 / D4 — switch and watch decision change live
- **PD threshold τ**: slider 0.05–0.60

### Explanation JSON (expandable at bottom)
Shows full structured output including pd, tau, decision, reason_codes, evidence breakdown, policy clause references.

### What to demonstrate during review
1. Click "Generate Random Applicant" → show the three panels
2. **Sidebar: change mode from D1 to D4** — watch how the decision can change
3. **Edit applicant: set Age to 17** → Policy goes UNSATISFIED → in D2/D4 decision becomes DECLINE (POLICY_INELIGIBLE)
4. **Edit applicant: set History Length to 3** → Evidence score drops to ~0.2 → in D3/D4 decision becomes REVIEW (EVIDENCE_INSUFFICIENT)
5. **Expand "Full Explanation JSON"** — show the structured audit output

---

## 6. IMPORTANT LIMITATIONS TO BE UPFRONT ABOUT

### 6a. Streamlit uses heuristic PD — NOT the trained XGBoost model [PARTIAL]
**Where**: `app/main.py`, function `_naive_pd_estimate()` (line ~100)

```python
def _naive_pd_estimate(applicant: dict) -> float:
    # THIS IS NOT A TRAINED MODEL
    # Simple formula for demo purposes only
    score = 0.05 + 0.3 * max(0, er - 0.5) + 0.2 * vol + 0.1 * max(0, -lr)
    return float(np.clip(score, 0.01, 0.95))
```

The real trained XGBoost model exists in `experiments/authentic/run.py` and was validated on Home Credit (ROC-AUC 0.757). The demo hasn't been connected to it yet because synthetic experiment results are still pending. The UI explicitly labels this with a warning caption.

**What to say**: *"The demo uses a heuristic formula for the probability of default to illustrate the three-layer architecture. The actual XGBoost model has been trained and evaluated — results are in `results/authentic/T1_results.json`. Connecting the trained model to the demo is the next step."*

### 6b. Policy rules are UNVERIFIED placeholders [PARTIAL]
**Where**: `configs/policy_rules/jan_samarth.yaml` and `pmmy.yaml`

Every `rule_id`, `policy_version`, `page`, `clause`, `verified_by` field is literally `"<UNVERIFIED>"`. The engine framework works correctly — the Kleene logic, rule loading, and versioning are all tested. The rule *content* (actual JanSamarth/PMMY criteria) has not yet been verified against official government documents.

**What to say**: *"The policy rule engine framework is fully implemented and tested. The rules themselves are placeholder fixtures — we haven't yet verified the exact criteria from the official JanSamarth and PMMY documents. That verification is the next task."*

### 6c. Synthetic experiment results (T2–T6) not yet generated [PLANNED]
Code for all experiments is written and tested:
- `experiments/ablation/run.py` (T2 — feature set comparison)
- `experiments/gating/run.py` (T3 — D1 vs D4)
- `experiments/review/run.py` (T4/T5 — review allocation)
- `experiments/history/run.py` (T6 — history length effect)

But the 20 synthetic datasets (2 DGPs × 10 seeds) have not been generated yet. This requires Gate G0 to pass first, then running the generation pipeline (~15 minutes).

**Only T1 (Home Credit authentic) has verified results** in `results/authentic/T1_results.json`.

### 6d. Fairness experiment not implemented [NOT IMPLEMENTED]
`experiments/fairness/` contains only an empty `__init__.py`. No run.py exists. This is listed in the architecture as planned but not built.

---

## FACULTY QUESTIONS I SHOULD BE READY FOR

---

**Q: Where is the synthetic data generated?**
> `src/data_generation/generate_data.py` — function `generate_data()`. It calls `dgp.py` internally. The parameters come from `configs/experiment.yaml`.

---

**Q: How is the default label created? How do you know who defaults?**
> In `src/data_generation/dgp.py`, at the bottom of `_simulate_monthly()`. The label is structural — if bank balance `L_t < 0` for two consecutive months in months 13–24, the person defaults. It has nothing to do with the ML model or policy rules.

---

**Q: How is the data processed / what preprocessing do you do?**
> `src/feature_engineering/build_features.py`. The monthly income/expense records are aggregated into 12 summary features per applicant — mean income, volatility, trend, etc. For LR, outliers are clipped and NaNs are imputed. For XGBoost, NaNs are left as-is (XGBoost handles them natively).

---

**Q: Where is XGBoost trained?**
> `src/models/train_models.py`, function `train_model()` with `family="xgb"`. The actual training on Home Credit data is in `experiments/authentic/run.py`.

---

**Q: How is the probability of default (PD) calculated?**
> `src/models/train_models.py`, `FittedModel.predict_raw()` — calls `model.predict_proba(X)[:, 1]`. Then Platt calibration is applied in `src/calibration/platt.py` to adjust the probabilities.

---

**Q: What is Platt calibration and why did you use it?**
> `src/calibration/platt.py`. It adjusts the raw model probabilities so they accurately reflect real default rates. Formula: `p_calibrated = sigmoid(A × logit(p_raw) + B)`. We fit A and B on the validation set only, never the test set. We chose Platt over isotonic regression because with only 5,000 validation samples isotonic could overfit.

---

**Q: How is the evidence score calculated?**
> `src/evidence/compute_evidence.py`, function `compute_evidence()`. Formula: `E = 0.5 × (H/12) + 0.25 × AA + 0.25 × ULI`. If E < 0.5, the evidence is insufficient and in D3/D4 mode the application goes to review instead of being auto-approved.

---

**Q: Where is the policy logic?**
> `src/policy/kleene.py` has the three-valued logic. `src/policy/rule_engine.py` has `evaluate_policy()` which evaluates rule conditions. Rules are in `configs/policy_rules/jan_samarth.yaml` and `pmmy.yaml`.

---

**Q: What is SATISFIED / UNSATISFIED / UNRESOLVED?**
> These are the three states from Kleene logic in `src/policy/kleene.py`. SATISFIED means all eligibility conditions are met. UNSATISFIED means at least one condition is definitely false. UNRESOLVED means data is missing so we cannot determine — for example age is None. This prevents incorrectly declining applicants with incomplete documents.

---

**Q: How does the decision engine work?**
> `src/decisions/gate.py`, function `make_decision()`. Four sequential checks in order: (1) is PD too high? (2) is policy UNSATISFIED? (3) is policy UNRESOLVED? (4) is evidence insufficient? First check that fails determines the outcome. D1 only does check 1; D4 does all four.

---

**Q: What is D1, D2, D3, D4?**
> Four experimental modes in `src/decisions/gate.py`. D1 = ML only. D2 = ML + Policy. D3 = ML + Evidence. D4 = all three. The research question is whether D4 gives better outcomes than D1 at fixed human-review budgets.

---

**Q: Where is the Streamlit UI implemented?**
> Single file: `app/main.py`. Run with `python -m streamlit run app/main.py`.

---

**Q: Is the Streamlit UI using the trained XGBoost model?**
> No. Currently the UI uses a heuristic formula in `_naive_pd_estimate()` in `app/main.py` (line ~100). The trained XGBoost model exists and has been evaluated — ROC-AUC 0.757 on Home Credit (`results/authentic/T1_results.json`) — but it has not yet been connected to the demo. The evidence layer, policy engine, and decision engine in the demo are all using real implemented code.

---

**Q: What are your actual results?**
> Only T1 (Home Credit authentic experiment) has verified results, in `results/authentic/T1_results.json`: XGBoost ROC-AUC 0.757, LR 0.738, on 307,511 real loan applications with 8.07% default rate. Synthetic experiment results (T2–T6) require the full data generation pipeline to run first.

---

**Q: What parts are currently incomplete?**
> Three things: (1) The Streamlit demo shows heuristic PD instead of the trained model. (2) The JanSamarth/PMMY policy rules are UNVERIFIED placeholders — the engine works but rule content needs checking against official documents. (3) Synthetic experiments T2–T6 have no results yet — the code is written but the pipeline hasn't been run at scale.

---

**Q: Did you test your code?**
> Yes. Run `pytest tests/ -v` — 69 unit tests, all passing. Tests cover the DGP formulas, all feature engineering functions, the evidence formula, the Kleene truth tables, the policy engine, and all five D1–D4 truth-table rows.

---

**Q: Why no database?**
> Deliberate design choice for a research pipeline. We use Parquet files for tabular data (fast for ML workloads), YAML for configuration and policy rules, and JSON for results. The design follows relational principles — `applicant_id` links all tables, policy rules have effective-date versioning — but without the overhead of a SQL engine. A production lending system would add a database for audit logs and applicant records.
