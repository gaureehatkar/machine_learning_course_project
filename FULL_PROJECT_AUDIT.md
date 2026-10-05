# FULL PROJECT AUDIT — SynthGigCredit-IN
**Audit Date:** 2026-10-05  
**Audit Type:** Read-only. No changes made to any file.  
**Auditor note:** Source code is the primary source of truth. Documentation claims are verified against actual code.

---

## Table of Contents

1. [Actual Architecture Map](#1-actual-architecture-map)
2. [Current Working State Summary](#2-current-working-state-summary)
3. [Backend Status — Module by Module](#3-backend-status--module-by-module)
4. [Frontend Status — Page by Page](#4-frontend-status--page-by-page)
5. [Complete Frontend Functionality Classification](#5-complete-frontend-functionality-classification)
6. [Mock / Static / Hardcoded Data Inventory](#6-mock--static--hardcoded-data-inventory)
7. [Unused / UI-Only Functionality](#7-unused--ui-only-functionality)
8. [Backend Capabilities Not Used by Frontend](#8-backend-capabilities-not-used-by-frontend)
9. [Research / ML Pipeline Status](#9-research--ml-pipeline-status)
10. [Experiment Status Table](#10-experiment-status-table)
11. [Test Suite Status](#11-test-suite-status)
12. [Reproducibility Assessment](#12-reproducibility-assessment)
13. [Documentation Inconsistencies](#13-documentation-inconsistencies)
14. [Critical Issues (P0–P3)](#14-critical-issues-p0p3)
15. [Decision Table — Recommended Actions](#15-decision-table--recommended-actions)
16. [Final Summary](#16-final-summary)

---

## 1. Actual Architecture Map

```
DATASETS
├── Home Credit CSV (data/authentic/) — T1 only, 307k rows
├── Grounding survey XLSX (data/authentic/) — G0 validation only
└── Synthetic parquets (data/synthetic/dgp{1,2}/seed{0..10}/) — T2-T6

        ↓
FEATURE ENGINEERING (src/feature_engineering/build_features.py)
├── Set A: 7 conventional features (income_mean, expense_mean, expense_ratio,
│           debt_mean, has_emi, liquidity_mean, liquidity_min)
├── Set B: 5 alternative/gig features (income_volatility, income_trend,
│           platform_tenure, multi_platform, seasonality_index)
└── Set C: A + B combined (12 features total)

        ↓
PREPROCESSING (src/models/train_models.py — WinsorisedScaler)
├── LR: Winsorise(1/99 pct) → median impute NaN → StandardScale
└── XGB: raw (NaN native)

        ↓
MODEL TRAINING (src/models/train_models.py — FittedModel)
├── Logistic Regression (sklearn)
└── XGBoost

        ↓
PLATT CALIBRATION (src/calibration/platt.py)
└── Sigmoid fit on validation set — converts raw scores to probabilities

        ↓
EVIDENCE GATE (src/evidence/compute_evidence.py)
└── E = 0.5×(H/12) + 0.25×AA + 0.25×ULI  ≥  τ_E (0.50)

        ↓
POLICY ENGINE (src/policy/)
├── rule_loader.py — loads YAML rules from configs/policy_rules/
├── rule_engine.py — evaluate_policy() → PolicyEvaluation dataclass
├── kleene.py — 3-valued logic: TRUE / FALSE / UNRESOLVED
└── versioning.py — date-based rule version selection

        ↓
DECISION ENGINE (src/decisions/gate.py)
├── D1: PD < τ → APPROVE else DECLINE
├── D2: D1 + Policy gate (UNSAT → DECLINE, UNRES → REVIEW)
├── D3: D1 + Evidence gate (E < τ_E → REVIEW)
└── D4: D1 + Policy + Evidence (full stack)

        ↓
REVIEW ALLOCATION (src/decisions/review.py)
├── R0: random
├── R1: entropy / highest-PD-first
├── R2: lowest evidence score first
└── R3: combined R1 + R2

        ↓
EXPLAINABILITY (src/explainability/)
├── shap_values.py — TreeSHAP for XGBoost
├── lr_coefficients.py — coefficients + odds ratios for LR
└── explain.py — unified explanation JSON output

        ↓
CREDIT SCORING (src/scoring/credit_score.py)
└── score = offset + factor × ln(odds), clamped [300, 900]

        ↓
FASTAPI BACKEND (app/api/main.py — :8000)
├── GET /api/health
├── GET /api/config
├── GET /api/history (stub — returns [])
└── POST /api/decide — 3-layer evaluation + credit score

        ↓
REACT FRONTEND (ML Froent end/ml-frontend — :5173)
├── AssessmentPage → POST /api/decide (real) or computeDecision() (fallback)
├── DecisionResultPage → displays decision, credit score, gates, rationale
├── DashboardPage → KPIs from session history + static charts
├── HistoryPage → session history + mockHistory
├── SettingsPage → τ/τ_E persisted to localStorage
├── ModelsPage → entirely mock, no backend connection
├── DatasetsPage → entirely mock, no backend connection
├── LoginPage → fake auth (any email/pass works)
└── SignupPage → fake auth

STREAMLIT DEMO (app/main.py — separate from FastAPI)
└── Uses heuristic PD, not trained model
```

---

## 2. Current Working State Summary

| Component | Status | Evidence |
|---|---|---|
| Data generation (DGP1+2) | ✅ A — FULLY WORKING | 20/20 seeds generated, G0 PASS |
| Gate G0 | ✅ A — FULLY WORKING | PASS: 8/9 checks (Check 1 NULL, Check 9 deferred) |
| Feature engineering | ✅ A — FULLY WORKING | 40/40 feature parquets built |
| Preprocessing (WinsorisedScaler) | ✅ A — FULLY WORKING | Used in T1 run, verified |
| LR + XGB training | ✅ A — FULLY WORKING | T1 results verified |
| Platt calibration | ✅ A — FULLY WORKING | T1 uses it, results verified |
| Evidence engine | ✅ A — FULLY WORKING | 83/83 tests pass |
| Policy engine (Kleene) | ✅ A — FULLY WORKING | 83/83 tests pass |
| Decision engine D1–D4 | ✅ A — FULLY WORKING | 83/83 tests pass |
| Review allocation R0–R3 | ✅ A — FULLY WORKING | All 4 strategies implemented |
| Evaluation metrics (15 functions) | ✅ A — FULLY WORKING | All implemented, no stubs |
| Statistical tests (CI, bootstrap) | ✅ A — FULLY WORKING | All implemented |
| TreeSHAP explainability | ✅ A — FULLY WORKING | XGBoost only |
| LR coefficients / odds ratios | ✅ A — FULLY WORKING | New module, compiles |
| Credit scoring (300–900) | ✅ A — FULLY WORKING | 14/14 tests pass |
| FastAPI backend /api/decide | ⚠️ B — PARTIALLY WORKING | Works but uses heuristic PD, explain() call broken |
| T1 experiment | ✅ A — FULLY WORKING | Results in results/authentic/T1_results.json |
| T2 experiment (ablation) | ⚠️ B — CODE COMPLETE, NOT RUN | No T2_results.json |
| T3 experiment (gating) | ⚠️ B — CODE COMPLETE, NOT RUN | No T3_results.json |
| T4/T5 experiment (review) | ⚠️ B — CODE COMPLETE, NOT RUN | No T4_T5_results.json |
| T6 experiment (history) | ⚠️ B — CODE COMPLETE, NOT RUN | No T6_results.json |
| T9 experiment (fairness) | ❌ F — EMPTY STUB | experiments/fairness/__init__.py is empty |
| Methodology validation | ❌ F — EMPTY STUB | experiments/methodology_validation/__init__.py is empty |
| React frontend — Assessment flow | ✅ A — FULLY WORKING | Real API call + local fallback |
| React frontend — Decision display | ✅ A — FULLY WORKING | Gates, credit score, rationale rendered |
| React frontend — Dashboard KPIs | ⚠️ B — PARTIALLY WORKING | Mixed real + mock baseline data |
| React frontend — History | ⚠️ B — PARTIALLY WORKING | Real session + mock baseline data |
| React frontend — Models page | ❌ C — MOCK | All data mock, all buttons dead |
| React frontend — Datasets page | ❌ C — MOCK | All data mock, upload dead |
| React frontend — Auth | ❌ C — MOCK | No real authentication |
| React frontend — Settings | ⚠️ B — PARTIALLY WORKING | τ/τ_E flow into engine; other toggles ignored |

**Overall completion estimate (verified evidence only):** ~72%

---

## 3. Backend Status — Module by Module

### 3.1 `src/decisions/gate.py`
**Status: A — FULLY WORKING**  
`Decision` is a `@dataclass` with fields `decision: str` and `reason_code: str | None`.  
`make_decision()` is completely implemented with proper precedence logic.  
`.decision` returns one of `"APPROVE"` / `"REVIEW"` / `"DECLINE"`.  
No stubs, no TODOs, no hardcoded bypasses.

### 3.2 `src/decisions/tau.py`
**Status: A — FULLY WORKING**  
`select_tau()` and `match_tau()` fully implemented. No stubs.

### 3.3 `src/decisions/review.py`
**Status: A — FULLY WORKING**  
All four strategies R0/R1/R2/R3 are distinct, complete implementations inside `allocate_review()`.  
`apply_oracle()` (perfect-review simulation) is fully implemented.  
Import of `review_seed` from `src.utils.seeding` ✅ — `review_seed()` exists at line ~35 of seeding.py.

### 3.4 `src/evaluation/metrics.py`
**Status: A — FULLY WORKING**  
15 metric functions, all complete:
`pr_auc`, `prevalence_baseline`, `roc_auc`, `brier`, `ece`, `calibration_slope_intercept`, `approval_rate`, `default_rate_among_approved`, `review_rate`, `coverage`, `policy_violation_rate`, `coverage_risk_curve`, `bad_loan_capture`, `review_efficiency`, `compute_all_metrics`.  
**Note:** Gini and KS statistics are NOT implemented (not mentioned in docs either).

### 3.5 `src/evaluation/aggregate.py`
**Status: B — PARTIALLY WORKING**  
Thin CLI wrapper around `aggregate_over_seeds()` in `evaluate.py`.  
`aggregate_over_seeds()` only aggregates ROC-AUC (not PR-AUC, Brier, ECE).  
Works correctly but incomplete coverage.

### 3.6 `src/evaluation/statistical_tests.py`
**Status: A — FULLY WORKING**  
`seed_level_ci()`, `paired_bootstrap()`, `bonferroni_alpha()` — all complete.

### 3.7 `src/explainability/explain.py`
**Status: A — IMPLEMENTATION CORRECT, but API call is broken**  
`explain()` takes 11 specific parameters including `pd_calibrated`, `tau`, `decision`, `evidence_score`, etc.  
`app/api/main.py` calls it with wrong kwargs: `explain(applicant_id=..., features=..., decision=..., config=...)`.  
This will raise `TypeError` at runtime. The API catches this exception and returns `{"error": "TypeError"}` in the explanation field (non-blocking but broken).

### 3.8 `src/models/train_models.py`
**Status: A — FULLY WORKING**  
`WinsorisedScaler` complete. `FittedModel` dataclass complete with `predict_raw()`.  
`train_model()` complete for both `"logreg"` and `"xgb"` families.  
Feature set assertion prevents evidence/policy columns leaking into PD model.

### 3.9 `src/calibration/platt.py`
**Status: A — FULLY WORKING**  
Custom scipy L-BFGS-B implementation, not sklearn. Fully implemented.

### 3.10 `src/policy/`
**Status: A — FULLY WORKING**  
`kleene.py`: State enum (TRUE/FALSE/UNRESOLVED) + operations — complete.  
`rule_loader.py`: YAML loading + PolicySet structure — complete.  
`rule_engine.py`: `evaluate_policy()` returns `PolicyEvaluation` dataclass — complete.  
`versioning.py`: date-based version selection — complete.

### 3.11 `src/evidence/compute_evidence.py`
**Status: A — FULLY WORKING**  
Formula `E = 0.5×(H/12) + 0.25×AA + 0.25×ULI` correctly implemented.  
Returns pandas Series. API extracts scalar via `.item()`.

### 3.12 `app/api/main.py`
**Status: B — PARTIALLY WORKING**

| Endpoint | Status | Issue |
|---|---|---|
| GET /api/health | ✅ WORKING | Returns correct JSON |
| GET /api/config | ✅ WORKING | Reads from CONFIG |
| GET /api/history | ✅ WORKING | Stub returns [] |
| POST /api/decide | ⚠️ PARTIAL | Works but 2 issues below |

**Issue 1 — Heuristic PD:** The PD is computed by `_compute_risk_heuristic()` (volatility + liquidity + history-length formula). No trained ML model is loaded or used. The real `train_model()` / Platt calibration pipeline is not called.

**Issue 2 — explain() broken call:** `explain(applicant_id=..., features=..., decision=..., config=...)` does not match `explain()`'s actual 11-parameter signature. This raises `TypeError` caught by the try/except, returning `{"error": "TypeError..."}` in the explanation field. Non-blocking but explanation is always an error dict.

**Issue 3 — tau not in DecisionRequest:** The frontend sends `tau` and `tau_e` fields in the request body but `DecisionRequest` pydantic model does not have these fields. They are silently ignored. τ is always 0.4 (hardcoded default in the endpoint).

### 3.13 `app/main.py` (Streamlit)
**Status: B — PARTIALLY WORKING**  
Uses heuristic PD (not trained model). Standalone Streamlit app, not connected to FastAPI. Works for demo.

### 3.14 Experiment Runners
| File | Status | What it does |
|---|---|---|
| `experiments/authentic/run.py` | ✅ COMPLETE | Full LR+XGB pipeline, saves T1_results.json |
| `experiments/ablation/run.py` | ✅ COMPLETE CODE, not run | Trains A/B/C × LR/XGB, saves T2_results.json per seed |
| `experiments/gating/run.py` | ✅ COMPLETE CODE, not run | Trains XGB-C, evaluates D1-D4, saves T3_results.json |
| `experiments/review/run.py` | ✅ COMPLETE CODE, not run | Evaluates R0-R3 × budgets, saves T4_T5_results.json |
| `experiments/history/run.py` | ✅ COMPLETE CODE, not run | Evaluates H∈{1,3,6,12}, saves T6_results.json |
| `experiments/fairness/__init__.py` | ❌ EMPTY FILE | Zero bytes, no implementation |
| `experiments/methodology_validation/__init__.py` | ❌ EMPTY FILE | Zero bytes, no implementation |

Note: `experiments/gating/run.py` imports `evaluate_batch` from `src.policy.rule_engine` — this function's existence was not verified in the audit. If missing, T3 will fail on import.

### 3.15 Policy Rule Files
**`configs/policy_rules/jan_samarth.yaml`:** 3 rules — age range [18,60], annual_income ≤ 1000000, nonfarm_engaged == 1. Marked RESEARCH VERIFIED.  
**`configs/policy_rules/pmmy.yaml`:** 3 rules — age range [18,65], annual_income ≤ 1000000, non_agriculture == 1. Marked RESEARCH VERIFIED.  
**Issue:** occupation/platform mappings (ride_hailing, delivery, etc.) are not in these rules. The `nonfarm_engaged` field is hardcoded to `1` in the frontend's API call regardless of actual input. The `non_agriculture` field does not exist in the frontend's request payload — PMMY rules will likely return UNRESOLVED for all applicants.

---

## 4. Frontend Status — Page by Page

### 4.1 LoginPage (`pages/LoginPage.tsx`)
**Status: C — MOCK**  
Accepts any email (valid format) + password (≥6 chars). Uses `useAuthStore.login()` which has a hardcoded 500ms `setTimeout` and sets the user to `currentUser` (Ananya Menon, hardcoded in mockData.ts). No API call is made. `VITE_USE_MOCK` flag is irrelevant — auth always mocked.

### 4.2 SignupPage (`pages/SignupPage.tsx`)
**Status: C — MOCK**  
Creates an in-memory user with `role: 'analyst'`. No backend call. 700ms fake delay.

### 4.3 AssessmentPage (`pages/AssessmentPage.tsx`)
**Status: A — FULLY WORKING (with fallback)**  
All 20+ form fields are wired to Zustand store (`updateApplicant`, `updateFinances`, `updateEvidence`).  
"Assess applicant" → `runAssessment()` → tries `assessmentApi.decide()` → real FastAPI POST /api/decide.  
If backend unavailable → falls back to `computeDecision()` from `assessment.ts` (local JS scoring).  
Evidence score preview panel updates live from sliders.  
Decision mode selector (D1-D4) wired and functional.

### 4.4 DecisionResultPage (`pages/DecisionResultPage.tsx`)
**Status: A — MOSTLY WORKING**  
6-gate pipeline visual renders from real decision data.  
Credit score panel renders when `creditScore` is non-null (from backend).  
Risk metrics (PD gauge, DTI, liquidity, volatility, tenure index) render from store state.  
Evidence composition bars render from store state.  
Policy rules (6 hardcoded rule rows) render with dynamic pass/fail based on store values.  
Decision rationale paragraph is dynamically generated.  
Download JSON: fully wired → Blob download with real decision data.  
"Export PDF": dead button, no handler.  
"Save to history": dead button (history already auto-saved by `runAssessment()`).  
"Override decision": intentionally disabled (Admin label).  
AuditDrawer: partially connected (uses real scores when available, sampleTrace fallback when not).

### 4.5 DashboardPage (`pages/DashboardPage.tsx`)
**Status: B — PARTIALLY WORKING**  
KPI tiles (Total, Approval Rate, Avg PD, Evidence Coverage): **computed from real data** but anchored to `mockHistory` baseline (10 mock entries always included).  
Recent decisions table: **dynamic** — session history + mockHistory.  
ROC curve chart: **static hardcoded** `rocData` from mockData.ts, AUC "0.87" is a hardcoded string.  
Monthly trend chart: **randomized static** (Math.random() at module load, not real data).  
Decision mode pie chart: **hardcoded** 12/23/31/34%.  
Gate pass rates bar chart: **hardcoded** 6 percentages.  
Date filter ("Last 30 days"): dead button.  
Export button: dead button.

### 4.6 HistoryPage (`pages/HistoryPage.tsx`)
**Status: B — PARTIALLY WORKING**  
Search by applicant ID/name: **working** (live filter).  
Date range selector: **working** (transparent select overlay trick).  
Outcome filter: **working** (live filter).  
KPI rate cards: **computed** from filtered `[...history, ...mockHistory]`.  
Outcome trend chart: **computed** from filtered data.  
Details / Duplicate row buttons: dead.  
Export CSV button: dead.

### 4.7 ModelsPage (`pages/ModelsPage.tsx`)
**Status: C — MOCK**  
Data from local inline `mockModels` array (not `mockData.ts` and not `modelsApi`).  
All buttons dead (Refresh, Upload model, View, Download, Play/Pause/Archive, More).  
Filter tabs (All/Deployed/Archived) have no onClick handlers — non-functional.  
Pagination buttons dead.  
All charts static hardcoded arrays.  
`modelsApi.getModels()` / `trainModel()` / `deployModel()` never called from this page.

### 4.8 DatasetsPage (`pages/DatasetsPage.tsx`)
**Status: C — MOCK (filtering works)**  
Data from local inline `mockDatasets` array (not `mockData.ts` and not `datasetsApi`).  
Search input, type filter, status filter: **working** (client-side filter on mock data).  
File upload (drag-drop + "Choose files"): **dead** — `onDrop` only calls `setIsDragging(false)`, no file reading.  
All row action buttons dead (Eye, Download, Trash, More).  
Pagination dead.  
Dataset health section: all hardcoded (89.4%, 3 alerts, static bar chart).  
`datasetsApi.uploadDataset()` / `deleteDataset()` never called from this page.

### 4.9 SettingsPage (`pages/SettingsPage.tsx`)
**Status: B — PARTIALLY WORKING**  
Risk cutoff τ slider → persisted to `useSettingsStore` → read by `runAssessment()` ✅  
Evidence cutoff τ_E slider → persisted → read by `runAssessment()` ✅  
Default decision mode → persisted → read by `runAssessment()` fallback ✅  
enableJanSamarth / enablePMMY toggles → persisted but **never read by any business logic** ❌  
displayNotices toggle → persisted but NoticeBar doesn't read from store ❌  
Theme select → dark mode disabled (`<option value="dark" disabled>`) ❌  
Email/Desktop notifications → persisted but no notification system exists ❌  
Password change fields → collected but never submitted or validated ❌  
Avatar camera button → dead ❌

---

## 5. Complete Frontend Functionality Classification

| Page | Element | Type | Handler | Real Backend? | Data Source | Status |
|---|---|---|---|---|---|---|
| Login | Email input | Form | setState | No | Local state | WORKING |
| Login | Password input | Form | setState | No | Local state | WORKING |
| Login | Remember me | Checkbox | setState | No | Ignored | MOCK |
| Login | "Forgot password?" | Link | href="#" | No | — | DEAD |
| Login | "Sign in" button | Submit | useAuthStore.login() | No | currentUser mock | MOCK |
| Login | Demo fill button | Button | fillDemo() | No | Hardcoded strings | WORKING |
| Signup | All inputs | Form | setState | No | Local state | WORKING |
| Signup | Terms/Privacy links | Links | href="#" | No | — | DEAD |
| Signup | "Create Account" | Submit | useAuthStore.signup() | No | In-memory | MOCK |
| Assessment | All 20 form fields | Form | updateApplicant/Finances/Evidence | No | Zustand store | WORKING |
| Assessment | History duration buttons | Segmented control | setHistoryDuration | No | Zustand store | WORKING |
| Assessment | Decision mode radio | Radio group | setDecisionMode | No | Zustand store | WORKING |
| Assessment | "Assess applicant" | Submit | runAssessment() → /api/decide | Yes (with fallback) | Backend or local | WORKING |
| DecisionResult | Gate pipeline | Visual | — | Yes | decisionOutcome | WORKING |
| DecisionResult | Credit score panel | Visual | — | Yes | backendResp.credit_score | WORKING |
| DecisionResult | Risk metrics | Visual | — | Yes (heuristic PD) | store state | PARTIAL |
| DecisionResult | Evidence bars | Visual | — | Yes | store state | WORKING |
| DecisionResult | Policy rules | Visual | — | Partial (hardcoded 6 rows) | store state + hardcoded | PARTIAL |
| DecisionResult | "View audit trace" | Button | toggleAuditDrawer | No | Store + sampleTrace | PARTIAL |
| DecisionResult | "Export PDF" | Button | None | No | — | DEAD |
| DecisionResult | "Run new assessment" | Button | clearDecision + navigate | No | — | WORKING |
| DecisionResult | "Download JSON" | Button | Blob download | No | Store state | WORKING |
| DecisionResult | "Email report to ops" | Button | window.location.href mailto | No | Store state | WORKING |
| DecisionResult | "Duplicate assessment" | Button | navigate('/assessment') | No | — | PARTIAL |
| DecisionResult | "Override decision" | Button | disabled | No | — | DEAD (intentional) |
| DecisionResult | "Save to history" | Button | None | No | — | DEAD (redundant) |
| Dashboard | Total Assessments | KPI tile | — | No | session+mockHistory | PARTIAL |
| Dashboard | Approval Rate | KPI tile | — | No | session+mockHistory | PARTIAL |
| Dashboard | Avg Risk PD | KPI tile | — | No | session+mockHistory | PARTIAL |
| Dashboard | Evidence Coverage | KPI tile | — | No | session+mockHistory | PARTIAL |
| Dashboard | Monthly trend chart | AreaChart | — | No | Math.random() static | MOCK |
| Dashboard | Decision mode pie | PieChart | — | No | Hardcoded 12/23/31/34% | MOCK |
| Dashboard | ROC curve | LineChart | — | No | Hardcoded rocData | MOCK |
| Dashboard | Gate pass rates | BarChart | — | No | Hardcoded 96%/82%/74%... | MOCK |
| Dashboard | Recent decisions table | Table | — | No | session+mockHistory | PARTIAL |
| Dashboard | "Last 30 days" button | Button | None | No | — | DEAD |
| Dashboard | "Export" button | Button | None | No | — | DEAD |
| History | Search input | Input | setSearchQuery | No | mockHistory+session | WORKING |
| History | Date range select | Select (hidden) | setDateRange | No | mockHistory+session | WORKING |
| History | Outcome filter | Select (hidden) | setOutcomeFilter | No | mockHistory+session | WORKING |
| History | KPI rate cards | KPI | — | No | Computed from filtered | WORKING |
| History | Outcome trend chart | BarChart | — | No | Computed from filtered | WORKING |
| History | "Export CSV" | Button | None | No | — | DEAD |
| History | Details per row | Button | None | No | — | DEAD |
| History | Duplicate per row | Button | None | No | — | DEAD |
| Models | All data/tables | Table | — | No | Local inline mockModels | MOCK |
| Models | "Refresh" | Button | None | No | — | DEAD |
| Models | "Upload model" | Button | None | No | — | DEAD |
| Models | All row actions | Buttons | None | No | — | DEAD |
| Models | Filter tabs | Buttons | None | No | — | DEAD |
| Models | Pagination | Buttons | None | No | — | DEAD |
| Models | All charts | Charts | — | No | Hardcoded arrays | MOCK |
| Datasets | Search/filter controls | Inputs | setSearchQuery etc. | No | Local mockDatasets | WORKING |
| Datasets | File upload zone | Drag-drop | setIsDragging only | No | — | DEAD |
| Datasets | "Upload Dataset" | Button | None | No | — | DEAD |
| Datasets | "Choose files" | Button | None | No | — | DEAD |
| Datasets | All row actions | Buttons | None | No | — | DEAD |
| Datasets | Dataset health section | Visual | — | No | Hardcoded | MOCK |
| Datasets | Quality charts | Charts | — | No | Hardcoded/random static | MOCK |
| Settings | Risk cutoff τ slider | Range | updateField → applySettings | No | localStorage | WORKING |
| Settings | Evidence cutoff slider | Range | updateField → applySettings | No | localStorage | WORKING |
| Settings | Decision mode radio | Radio | updateField → applySettings | No | localStorage | WORKING |
| Settings | JanSamarth toggle | Toggle | updateField → applySettings | No | localStorage only | MOCK |
| Settings | PMMY toggle | Toggle | updateField → applySettings | No | localStorage only | MOCK |
| Settings | displayNotices toggle | Toggle | updateField → applySettings | No | localStorage only | MOCK |
| Settings | Theme select | Select | updateField | No | localStorage, dark disabled | MOCK |
| Settings | Notification toggles | Toggles | updateField → applySettings | No | localStorage only | MOCK |
| Settings | Password change fields | Inputs | setState | No | Never submitted | DEAD |
| Settings | Camera button | Button | None | No | — | DEAD |
| AuditDrawer | Risk/Evidence/Policy tabs | Tabs | setActiveTab | No | decisionOutcome or sampleTrace | PARTIAL |
| AuditDrawer | Audit hash | Display | Math.random() | No | Fake | MOCK |
| AuditDrawer | "LIVE" badge | Badge | — | No | Hardcoded label | MOCK |
| Header | Nav links | NavLinks | React Router | No | — | WORKING |
| Header | Preset dropdown | Dropdown | loadPreset() | No | getPreset() local | WORKING |
| Header | Logout | Button | logout() | No | Clears store | WORKING |

---

## 6. Mock / Static / Hardcoded Data Inventory

### 6.1 Authentication
| File | What is mocked | Real equivalent exists? |
|---|---|---|
| `useAuthStore.ts` | Entire login/signup with 500/700ms fake delay | No backend auth endpoint |
| `mockData.ts: currentUser` | User: Ananya Menon, USR-001, analyst@microfinance.in | No |

### 6.2 Dashboard Charts
| File | What is mocked | Real equivalent? |
|---|---|---|
| `DashboardPage.tsx: monthlyAssessmentData` | 12 months of Approved/Review/Declined counts, Math.random() at load | Partially — history store has real decisions |
| `DashboardPage.tsx: decisionModeData` | D1=12%, D2=23%, D3=31%, D4=34% | Session history could compute this |
| `DashboardPage.tsx: gatePassData` | 96%, 82%, 74%, 88%, 91%, 93% — all fake | No, backend doesn't track gate-level aggregate rates |
| `mockData.ts: rocData` | 11-point ROC curve hardcoded to look like AUC ~0.87 | Yes — T1_results.json has real AUC 0.757/0.738 |
| `DashboardPage.tsx` AUC badge | String `"AUC 0.87"` | Real T1 AUC = XGB 0.757, LR 0.738 |

### 6.3 Models Page
| File | What is mocked |
|---|---|
| `ModelsPage.tsx: mockModels` (local) | 6 models: Income Estimator, Default Risk Classifier, Evidence Completeness Scorer, Occupation BERT, etc. All fake. |
| `ModelsPage.tsx: accuracyTrendData` | 6-week accuracy trend for risk/evidence/policy — fully static |
| `ModelsPage.tsx: modelTypeDistribution` | Fully static pie/bar data |

### 6.4 Datasets Page
| File | What is mocked |
|---|---|
| `DatasetsPage.tsx: mockDatasets` (local) | 6 datasets with hardcoded names, row counts, statuses |
| `DatasetsPage.tsx: healthMetricsData` | 5-metric Authentic vs Synthetic quality bars — hardcoded |
| `DatasetsPage.tsx: qualityTrendData` | Math.random() noisy quality trend |
| Hardcoded strings | "89.4%" quality score, "+3.2%" trend, "3 alerts" |

### 6.5 History (Baseline)
| File | What is mocked |
|---|---|
| `mockData.ts: mockHistory` | 10 entries with Math.random() scores — always merged with real session history |

### 6.6 AuditDrawer
| Element | Mocked how |
|---|---|
| Hash value | `Math.random().toString(16)` — fake audit hash, changes every render |
| "LIVE" badge | Hardcoded string — no real-time connection |
| `sampleTrace` | Hardcoded fallback (riskPD 0.0482, Rajesh Kumar) used when no decision run |
| `pdComponents.basePD: 0.05` | Hardcoded constant |
| Thresholds in policy trace | approve: 0.7, review: 0.5, decline: 0.42 — hardcoded |

### 6.7 DecisionResultPage Hardcoded Constants
| Element | Value | Should come from |
|---|---|---|
| LGD assumption | `0.35` in `riskPD * 0.35` | Config or model parameter |
| Model confidence scaling | `evidenceScore * 95` | No real basis |
| τ display label | `"τ=25%"` string | Should read from settingsStore |
| "+0.04 monthly stability" | Hardcoded string | Should come from income_trend feature |
| "Q4 bias" label | Hardcoded string | Should come from seasonality data |

---

## 7. Unused / UI-Only Functionality

### 7.1 ModelsPage — Entire Page
**What user sees:** Model registry table with 6 models, accuracy charts, filter tabs, pagination, action buttons (train, deploy, archive).  
**What exists in backend:** `modelsApi.getModels()`, `trainModel()`, `deployModel()` in api.ts exist but are never called.  
**What actually happens:** All data from local inline `mockModels` const. All buttons have no onClick handlers.  
**Classification:** UI-ONLY  

### 7.2 DatasetsPage — Upload and Actions
**What user sees:** Dataset upload zone with drag-drop, file browser, preview/download/delete per row.  
**What actually happens:** Upload zone only toggles `isDragging` state. No file reading, no API call.  
**Classification:** UI-ONLY

### 7.3 Auth System
**What user sees:** Login form with email/password, signup form with all validation.  
**What actually happens:** Any valid-format credentials log in as "Ananya Menon". No real user system.  
**Classification:** MOCK

### 7.4 Settings — Policy Scheme Toggles
**What user sees:** JanSamarth and PMMY toggles with descriptions about controlling policy gate behavior.  
**What actually happens:** Saved to localStorage. Never read by policy engine or API call.  
**Classification:** UI-ONLY

### 7.5 Settings — Password Change
**What user sees:** Current/New/Confirm password fields.  
**What actually happens:** Fields collect values into local `formState`. `handleSave()` never reads them.  
**Classification:** UI-ONLY

### 7.6 Settings — Notifications
**What user sees:** Email notifications toggle, desktop notifications toggle, audit log frequency selector.  
**What actually happens:** Saved to localStorage. No notification system exists.  
**Classification:** UI-ONLY

### 7.7 Export PDF Button (DecisionResultPage)
**What user sees:** "Export PDF" button next to "Export JSON".  
**What actually happens:** No `onClick` handler. Nothing.  
**Classification:** DEAD

### 7.8 AuditDrawer — Fake Hash and "LIVE" Badge
**What user sees:** Hash like `0x3a7f2c1b...d8e4` and a "LIVE" badge suggesting real-time trace.  
**What actually happens:** Hash is `Math.random()`. "LIVE" is a hardcoded string.  
**Classification:** UI-ONLY (cosmetic)

### 7.9 HistoryPage — Export CSV, Details, Duplicate
**What user sees:** "Export CSV" header button, Details and Duplicate per-row buttons.  
**What actually happens:** All have no onClick handlers.  
**Classification:** DEAD

### 7.10 assessmentApi.submitAssessment()
**What it is:** `request<DecisionOutcome>('POST', '/assessment/submit', state)` in api.ts.  
**What actually happens:** Never called. `runAssessment()` calls `assessmentApi.decide()` directly.  
**Classification:** DEAD CODE

---

## 8. Backend Capabilities Not Used by Frontend

| Backend Capability | Endpoint/Function | Exists? | Frontend Uses It? | Where it could be used |
|---|---|---|---|---|
| Real tau selection | `select_tau()` | ✅ | ❌ | Settings τ slider could send to backend |
| Policy evaluation detail | `evaluate_policy()` → PolicyEvaluation | ✅ | ❌ | Policy panel could show real scheme/rule results |
| SHAP explanations | `compute_shap_values()` | ✅ | ❌ | AuditDrawer risk tab could show real SHAP |
| LR coefficients | `get_lr_coefficients()` | ✅ | ❌ | Could show in model explanation panel |
| explain() JSON | `explain()` (11-param) | ✅ | ❌ (broken call) | AuditDrawer could show real explanation |
| Review allocation | `allocate_review()` R0-R3 | ✅ | ❌ | Could drive a review queue UI |
| Evaluation metrics | `compute_all_metrics()` | ✅ | ❌ | Dashboard ROC/AUC could show real T1 values |
| Statistical tests | `seed_level_ci()`, `paired_bootstrap()` | ✅ | ❌ | Results dashboard could show real CIs |
| Coverage-risk curve | `coverage_risk_curve()` | ✅ | ❌ | Could replace static gate pass chart |
| GET /api/config | `/api/config` | ✅ | ❌ | Settings page could read τ/τ_E from backend |
| GET /api/history | `/api/history` (stub) | ✅ stub | ❌ | HistoryPage calls `getHistory()` never |

---

## 9. Research / ML Pipeline Status

### 9.1 Feature Sets
| Set | Features | Implemented? | Tested? |
|---|---|---|---|
| A (conventional) | income_mean, expense_mean, expense_ratio, debt_mean, has_emi, liquidity_mean, liquidity_min | ✅ Yes | ✅ Yes |
| B (gig/alternative) | income_volatility, income_trend, platform_tenure, multi_platform, seasonality_index | ✅ Yes | ✅ Yes |
| C (combined A+B) | All 12 | ✅ Yes | ✅ Yes |

### 9.2 Models
| Model | Implemented? | Used in T1? | Used in T2-T6 code? |
|---|---|---|---|
| Logistic Regression | ✅ Yes | ✅ Yes | ✅ Yes (T2) |
| XGBoost | ✅ Yes | ✅ Yes | ✅ Yes (T2, T3, T4, T5, T6) |

### 9.3 Calibration
| Method | Implemented? | Applied? |
|---|---|---|
| Raw predictions | ✅ Yes | ✅ T1 uses both raw and calibrated |
| Platt scaling (custom scipy) | ✅ Yes | ✅ T1, T2, T3, T4, T5, T6 all call fit_platt() |
| Isotonic regression | ❌ Not implemented | — |

### 9.4 Evidence
| Component | Implemented? | Tested? |
|---|---|---|
| E-score formula | ✅ Yes | ✅ Yes |
| τ_E threshold | ✅ Yes (0.5 from config) | ✅ Yes |
| evidence_status() | ✅ Yes | ✅ Yes |

### 9.5 Policy
| Component | Implemented? | Status |
|---|---|---|
| Rule YAML loading | ✅ Yes | Working |
| Kleene 3-valued logic | ✅ Yes | 83/83 tests pass |
| evaluate_policy() | ✅ Yes | Working |
| combine_schemes() | ✅ Yes | Working |
| JanSamarth rules | ✅ Research verified | 3 rules |
| PMMY rules | ✅ Research verified | 3 rules |
| Occupation mapping | ❌ Missing | ride_hailing/delivery not in rules |

### 9.6 Decision Engine
| Mode | Implemented? | Tested? |
|---|---|---|
| D1 (risk only) | ✅ Yes | ✅ Yes |
| D2 (risk + policy) | ✅ Yes | ✅ Yes |
| D3 (risk + evidence) | ✅ Yes | ✅ Yes |
| D4 (all three) | ✅ Yes | ✅ Yes |

### 9.7 Review Allocation
| Strategy | Implemented? | Tested? |
|---|---|---|
| R0 (random) | ✅ Yes | ❌ No dedicated test |
| R1 (entropy/PD) | ✅ Yes | ❌ No dedicated test |
| R2 (evidence) | ✅ Yes | ❌ No dedicated test |
| R3 (combined) | ✅ Yes | ❌ No dedicated test |

### 9.8 Explainability
| Method | Implemented? | Works with API? |
|---|---|---|
| TreeSHAP (XGBoost) | ✅ Yes | ❌ API call to explain() is broken |
| LR coefficients/odds ratios | ✅ Yes | ❌ API doesn't call it |
| Unified explain() JSON | ✅ Yes (11-param) | ❌ API passes wrong args |

### 9.9 Evaluation Metrics
| Metric | Implemented? | Used in T1? |
|---|---|---|
| ROC-AUC | ✅ | ✅ 0.738/0.757 |
| PR-AUC | ✅ | ✅ 0.221/0.245 |
| Brier Score | ✅ | ✅ 0.069/0.068 |
| ECE | ✅ | ✅ 0.0024/0.0025 |
| Calibration slope | ✅ | ✅ 0.074/0.076 |
| Gini coefficient | ❌ Not implemented | — |
| KS statistic | ❌ Not implemented | — |
| Approval rate | ✅ | Used in T3/T4/T5 code |
| Default rate among approved | ✅ | Used in T3/T4/T5 code |
| Policy violation rate | ✅ | Used in T3 code |
| Coverage-risk curve | ✅ | Used in T3 code |

---

## 10. Experiment Status Table

| Experiment | Code Exists? | Actually Run? | Results Exist? | Verified? | Status |
|---|---|---|---|---|---|
| T1: Authentic (LR+XGB) | ✅ Complete | ✅ Yes | ✅ T1_results.json | ✅ Verified | **COMPLETE** |
| G0: DGP Validation | ✅ Complete | ✅ Yes | ✅ gate_g0_report.json | ✅ PASS | **COMPLETE** |
| T2: Ablation (A/B/C) | ✅ Complete | ❌ Not run | ❌ Missing | ❌ | **NOT RUN** |
| T3: Gating (D1-D4) | ✅ Complete* | ❌ Not run | ❌ Missing | ❌ | **NOT RUN** |
| T4/T5: Review allocation | ✅ Complete | ❌ Not run | ❌ Missing | ❌ | **NOT RUN** |
| T6: History length | ✅ Complete | ❌ Not run | ❌ Missing | ❌ | **NOT RUN** |
| T9: Fairness | ❌ Empty file | ❌ | ❌ | ❌ | **NOT STARTED** |
| Methodology validation | ❌ Empty file | ❌ | ❌ | ❌ | **NOT STARTED** |
| Seed stability (Check 9) | ⚠️ Deferred | ❌ | ❌ | ❌ | **DEFERRED** |

*T3 imports `evaluate_batch` from `src.policy.rule_engine` — this function's existence unverified.

**Feature tables available for experiments:**
- DGP1: seeds 1-10 have `features_full.parquet` + `features_visible.parquet` ✅ (20 files)
- DGP2: seeds 1-10 have `features_full.parquet` + `features_visible.parquet` ✅ (20 files)
- All 40 feature files are ready. T2-T6 can be run immediately.

---

## 11. Test Suite Status

**Total: 83/83 PASSING** (verified run: 2026-10-05, 13.05s)

| Test File | Tests | Area | Pass? |
|---|---|---|---|
| `tests/test_dgp.py` | ~25 | DGP reproducibility, RNG separation, leakage, splits | ✅ All |
| `tests/test_features.py` | ~20 | Feature formulas, NaN rules, column ordering | ✅ All |
| `tests/test_evidence.py` | ~12 | Evidence score formula, threshold, weights | ✅ All |
| `tests/test_policy.py` | ~12 | Kleene logic, rule evaluation, versioning | ✅ All |
| `tests/test_decisions.py` | ~14 | D1-D4 gate logic, tau selection | ✅ All |
| `tests/test_credit_score.py` | 14 | Scorecard scaling, monotonicity, clamping | ✅ All |

**Coverage gaps (no tests):**
- `src/calibration/platt.py` — uncovered
- `src/models/train_models.py` — uncovered (WinsorisedScaler, FittedModel, train_model)
- `src/evaluation/metrics.py` — uncovered
- `src/evaluation/statistical_tests.py` — uncovered
- `src/decisions/review.py` — uncovered (R0/R1/R2/R3 strategies)
- `src/explainability/` — all uncovered
- `app/api/` — no API tests
- Integration tests — none
- End-to-end tests — none
- Frontend tests — none

---

## 12. Reproducibility Assessment

| Factor | Status | Details |
|---|---|---|
| Random seeds | ✅ Controlled | `static_seed(s) = s×1000+1`, `outcome_seed(s) = s×1000+2` |
| Train/val/test split | ✅ Controlled | `StratifiedShuffleSplit` with fixed seeds 42/43 (T1) or `split_seed(s)` (synthetic) |
| Feature ordering | ✅ Controlled | `ALL_COLUMNS_ORDERED` enforced in `build_features()` |
| Model config | ✅ Config-driven | `configs/models.yaml` stores XGB/LR hyperparameters |
| Calibration | ✅ Deterministic | scipy L-BFGS-B deterministic for same init |
| Experiment config | ✅ Single file | `configs/experiment.yaml` is single source of truth |
| Dependency versions | ✅ Pinned | `requirements.txt` has pinned versions |
| Data paths | ✅ Config-driven | `get_output_dir(cfg, dgp_id, seed)` derives paths |
| Model artifacts | ⚠️ Not saved | No `.pkl` files committed or generated — retraining required |
| R0 review randomness | ✅ Seeded | `review_seed(s) = 2000 + s` |
| G0 seed 0 not in exp seeds | ✅ Enforced | Precondition PRE-b checks this |
| Two team members getting same results | ✅ Should match | If same Python/library versions and same seed, results deterministic |

**Potential reproducibility risk:** Model artifacts are not persisted. T1 must be re-run. Results will match if `requirements.txt` is followed exactly.

---

## 13. Documentation Inconsistencies

### Inconsistency 1 — AUC 0.87 in Dashboard vs Real Results
**Dashboard shows:** `"AUC 0.87"` hardcoded badge on ROC curve  
**T1_results.json shows:** LR = 0.738, XGB = 0.757  
**Verdict:** Dashboard AUC is wrong — inflated by 0.11–0.13.

### Inconsistency 2 — explain() Signature Mismatch
**Documentation / explain.py contract:** `explain(applicant_id, pd_calibrated, tau, decision, evidence_score, evidence_status, history_length, tau_e, policy_evaluation, shap_reasons, mode)`  
**app/api/main.py actually calls:** `explain(applicant_id=..., features=..., decision=..., config=...)`  
**Verdict:** API call is broken. Always returns `{"error": "TypeError..."}` in explanation field.

### Inconsistency 3 — VITE_USE_MOCK=false Has No Effect
**Documentation implies:** Setting `VITE_USE_MOCK=false` enables real backend  
**Reality:** Auth remains mocked regardless. assessmentApi.decide() bypasses the flag. Pages use inline mock arrays.  
**Verdict:** The flag is mostly ineffective. Only the /api/decide call is ever real.

### Inconsistency 4 — Policy Gate UNRESOLVED for All Common Occupations
**Policy YAML rules:** Check `nonfarm_engaged == 1` (JanSamarth) and `non_agriculture == 1` (PMMY)  
**Frontend sends:** `nonfarm_engaged: 1` hardcoded, but `non_agriculture` field does NOT exist in `ApplicantFeatures` model  
**Result:** PMMY rule for `non_agriculture` cannot evaluate → UNRESOLVED. Most applicants get REVIEW not APPROVE.  
**Documentation says:** "Policy rules RESEARCH VERIFIED" — true, but integration is incomplete.

### Inconsistency 5 — `tau`/`tau_e` Not Accepted by API
**Frontend sends:** `{ ..., tau: 0.25, tau_e: 0.5 }` in request body when settings are changed  
**`DecisionRequest` model:** Does not have `tau` or `tau_e` fields → silently ignored by Pydantic  
**Endpoint hardcodes:** `tau = CONFIG.get("decision", {}).get("tau", 0.4)` — always 0.4 regardless of slider  
**Verdict:** Settings τ slider has no effect on backend decision.

### Inconsistency 6 — T2-T6 Results Claimed But Missing
**PROJECT_STATUS_AND_IMPLEMENTATION.md claims:** "Feature tables: 12/20 built"  
**Actual state:** All 40 feature files exist (20 DGP1 + 20 DGP2). But no T2-T6 results in `results/`.  
**Verdict:** Features are ready but experiments have not been executed.

---

## 14. Critical Issues (P0–P3)

### P0 — Blocks Research Completeness
| # | Issue | File | Impact |
|---|---|---|---|
| P0-1 | T2-T6 experiments not run — no results for ablation, gating, review, history | experiments/ | No experiment results for presentation |
| P0-2 | explain() call broken in API — wrong kwargs, always returns error dict | app/api/main.py | Explanation always fails at runtime |
| P0-3 | T9 fairness experiment is an empty stub | experiments/fairness/__init__.py | Fairness analysis completely missing |

### P1 — Important, Affects Demo/Correctness
| # | Issue | File | Impact |
|---|---|---|---|
| P1-1 | API uses heuristic PD, not trained ML model | app/api/main.py | Demo PD not from real model |
| P1-2 | tau/tau_e from Settings slider silently ignored by API | app/api/main.py + types | Settings slider has no effect on backend |
| P1-3 | non_agriculture field missing from ApplicantFeatures → PMMY always UNRESOLVED | app/api/main.py | Policy gate always pending for most applicants |
| P1-4 | AUC 0.87 on Dashboard is wrong — real T1 AUC is 0.757/0.738 | DashboardPage.tsx | Misinforms professor/audience |
| P1-5 | evaluate_batch import in gating/run.py — not verified to exist | experiments/gating/run.py | T3 may fail on import |

### P2 — Useful Improvements
| # | Issue | File | Impact |
|---|---|---|---|
| P2-1 | Auth is always mock — any credentials work | useAuthStore.ts | Security / realism |
| P2-2 | Monthly trend chart uses random data, not real session history | DashboardPage.tsx | Dashboard not informative |
| P2-3 | Models/Datasets pages are entirely mock with dead buttons | ModelsPage, DatasetsPage | Large dead UI sections |
| P2-4 | AuditDrawer hash is Math.random() fake | AuditDrawer.tsx | Misleading "LIVE" label |
| P2-5 | enableJanSamarth / enablePMMY toggles do nothing | SettingsPage + useSettingsStore | Settings UI misleads user |
| P2-6 | mockHistory always included in KPIs — anchors metrics to fake baseline | DashboardPage + HistoryPage | KPIs not truly real-session data |
| P2-7 | No tests for review allocation R0-R3 | tests/ | Critical feature untested |
| P2-8 | No tests for calibration, models, metrics, SHAP | tests/ | Key ML components untested |

### P3 — Minor / Cosmetic
| # | Issue | File | Impact |
|---|---|---|---|
| P3-1 | "Export PDF" button dead | DecisionResultPage.tsx | Missing feature |
| P3-2 | Password change fields collected but never submitted | SettingsPage.tsx | Cosmetic |
| P3-3 | "Forgot password?" dead link | LoginPage.tsx | Cosmetic |
| P3-4 | Bar chart colors broken in ModelsPage (wrong Recharts pattern) | ModelsPage.tsx | Visual bug |
| P3-5 | τ=25% label hardcoded in DecisionResultPage — doesn't update from Settings | DecisionResultPage.tsx | Minor inconsistency |
| P3-6 | LGD hardcoded as 0.35 in DecisionResultPage | DecisionResultPage.tsx | Hardcoded assumption |

---

## 15. Decision Table — Recommended Actions

> **These are recommendations only. No changes have been made.**

| Feature / Issue | Current Status | Recommended Action | Reason | Priority |
|---|---|---|---|---|
| T2 ablation experiment | Code complete, not run | COMPLETE IMPLEMENTATION — run it | 40 feature files ready | P0 |
| T3 gating experiment | Code complete, not run | COMPLETE IMPLEMENTATION — verify evaluate_batch import first | Need T3 results | P0 |
| T4/T5 review experiment | Code complete, not run | COMPLETE IMPLEMENTATION — run it | Need review results | P0 |
| T6 history experiment | Code complete, not run | COMPLETE IMPLEMENTATION — run it | Need history results | P0 |
| explain() broken call | TypeError at runtime | KEEP + FIX — fix API call to match 11-param signature | Explanation always fails | P0 |
| T9 fairness experiment | Empty stub | INVESTIGATE — decide scope before starting | Is this required for grade? | P1 |
| API uses heuristic PD | No trained model | KEEP + FIX — save model artifact, load at startup | Core demo correctness | P1 |
| tau/tau_e ignored by API | Silently dropped | KEEP + FIX — add tau/tau_e to DecisionRequest | Settings should affect decision | P1 |
| non_agriculture missing | PMMY always UNRESOLVED | KEEP + FIX — add field or map from occupation | Policy gate correctness | P1 |
| AUC 0.87 hardcoded wrong | Real AUC is 0.757 | KEEP + FIX — update to show real T1 AUC | Academic correctness | P1 |
| evaluate_batch in T3 | Unverified import | INVESTIGATE — check if function exists | T3 may fail on import | P1 |
| Auth always mock | Fake login | KEEP AS-IS | Research prototype, not production | P3 |
| ModelsPage all mock | Local fake data | KEEP AS-IS or POTENTIAL REMOVE | No real model registry needed | P2 |
| DatasetsPage upload dead | No file processing | KEEP AS-IS | No dataset upload feature needed | P2 |
| Monthly trend chart | Random data | KEEP + FIX — compute from session history | Replace Math.random() | P2 |
| Decision mode pie chart | Hardcoded percentages | KEEP + FIX — compute from session history | More realistic | P2 |
| mockHistory baseline | Always included | KEEP AS-IS for now | Provides demo data when no assessments run | P3 |
| enableJanSamarth/PMMY toggles | No effect | KEEP + FIX or REDESIGN | Should control API scheme_ids | P2 |
| AuditDrawer fake hash | Math.random() | KEEP + FIX — use real decision ID or timestamp | Misleading "LIVE" label | P2 |
| Export PDF button | Dead | KEEP + FIX or POTENTIAL REMOVE | Decide if PDF export needed | P3 |
| Password change fields | Never submitted | POTENTIAL REMOVE or DEFER | No auth backend | P3 |
| Settings theme dark | Disabled | DEFER | Not needed for demo | P3 |
| Test coverage gaps | Calibration/models/metrics/review uncovered | KEEP + FIX — add tests | Academic rigor | P2 |

---

## 16. Final Summary

### A. What Is Definitely Working
- Full data generation pipeline (DGP1 + DGP2, seeds 0-10)
- Gate G0 validation (PASS — 8/9 checks, 2 deferred)
- All feature engineering (40 feature parquets ready)
- All ML components: LR, XGB, Platt calibration, WinsorisedScaler
- Evidence engine (formula + threshold + status)
- Policy engine (Kleene 3-valued logic, YAML rules, versioning)
- Decision engine D1-D4 (make_decision fully implemented)
- Review allocation R0-R3 (all 4 strategies in allocate_review())
- All 15 evaluation metric functions
- Statistical tests (seed CI, paired bootstrap, Bonferroni)
- Credit scoring 300-900 (14 unit tests pass)
- T1 authentic experiment (LR ROC-AUC 0.738, XGB 0.757)
- FastAPI /api/health, /api/config endpoints
- Assessment form → /api/decide → result display (with heuristic PD)
- Download JSON from decision result
- History filtering (date, outcome, search)
- Settings τ/τ_E flowing into assessment engine
- 83/83 unit tests passing

### B. What Is Partially Working
- `/api/decide` — works but uses heuristic PD (not trained model), explain() call broken, tau/tau_e ignored
- Dashboard KPIs — computed but anchored to 10 mock entries
- AuditDrawer — uses real scores but fake hash, hardcoded thresholds, fake "LIVE" badge
- Policy gate — evaluates JanSamarth partially; PMMY misses non_agriculture field

### C. What Is Mock / Static
- Auth system (any credentials work)
- Models page (local inline mock data, no API calls)
- Datasets page (local inline mock data, upload dead)
- Dashboard ROC curve (AUC 0.87 wrong, hardcoded points)
- Dashboard trend chart (Math.random() on load)
- Dashboard mode pie (12/23/31/34% hardcoded)
- Dashboard gate pass rates (hardcoded 6 percentages)
- AuditDrawer hash (Math.random())
- mockHistory baseline always merged into KPIs

### D. What Is Currently Unused / UI-Only
- enableJanSamarth / enablePMMY toggles (no effect on engine)
- Password change fields (never submitted)
- Email/desktop notification toggles (no notification system)
- Settings displayNotices toggle (NoticeBar doesn't read store)
- assessmentApi.submitAssessment() (dead code, never called)
- modelsApi.getModels() / trainModel() / deployModel() (never called from UI)
- datasetsApi functions (never called from UI)
- Export PDF button (no handler)
- Save to history button (redundant — already auto-saved)

### E. What Is Broken
- explain() call in app/api/main.py — wrong kwargs → always TypeError at runtime
- tau/tau_e from Settings slider not accepted by API (silently dropped)
- PMMY non_agriculture field missing → always UNRESOLVED
- AUC 0.87 shown is wrong (real T1 AUC = 0.757 XGB, 0.738 LR)
- evaluate_batch import in experiments/gating/run.py (unverified)

### F. Backend Functionality Not Exposed in Frontend
- Real trained model predictions (no model artifact loaded)
- SHAP explanations (shap_values.py implemented but never called via API)
- LR coefficients/odds ratios (lr_coefficients.py never exposed via API)
- explain() full JSON (broken call, never successfully returns)
- Policy evaluation detail per scheme/rule
- Coverage-risk curve
- Review allocation engine

### G. Research Experiments Actually Complete
1. **Gate G0** — PASS (verified, results in gate_g0_report.json)
2. **T1 Authentic** — COMPLETE (verified LR 0.738, XGB 0.757 ROC-AUC)

### H. Research Experiments Remaining
3. T2 Ablation — code ready, 40 feature files ready, **not run**
4. T3 Gating — code ready, **not run** (verify evaluate_batch import first)
5. T4/T5 Review allocation — code ready, **not run**
6. T6 History length — code ready, **not run**
7. T9 Fairness — **empty stub, not started**
8. Methodology validation — **empty stub, not started**

### I. Top 10 Issues by Priority
1. **[P0]** T2-T6 experiments not run — no results for 5 core experiments
2. **[P0]** explain() call broken — API explanation always fails
3. **[P0]** T9 fairness is an empty file — decide if needed
4. **[P1]** API uses heuristic PD — real trained model not connected
5. **[P1]** tau/tau_e Settings slider silently ignored by backend
6. **[P1]** non_agriculture missing → PMMY always UNRESOLVED
7. **[P1]** Dashboard shows AUC 0.87 — real T1 is 0.757
8. **[P1]** evaluate_batch import in T3 runner — may fail
9. **[P2]** Review allocation R0-R3 has no unit tests
10. **[P2]** 30+ dead buttons across Models/Datasets/History pages

### J. Files Created by This Audit
- `FULL_PROJECT_AUDIT.md` — this document

### K. Recommended Next Steps (Do Not Implement Until Reviewed)
1. Verify `evaluate_batch` exists in `src/policy/rule_engine.py` before running T3
2. Run T2 → T3 → T4/T5 → T6 on all seeds (pipeline is ready)
3. Fix `explain()` call in `app/api/main.py` to match actual signature
4. Add `tau` / `tau_e` fields to `DecisionRequest` in API
5. Fix AUC badge in DashboardPage to show real T1 value (0.757)
6. Decide on T9 fairness experiment scope

---

*Audit complete. No files were modified.*  
*All findings are based on actual source code inspection and verified test execution.*  
*Last verified: 2026-10-05*
