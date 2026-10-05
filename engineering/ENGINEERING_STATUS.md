# Engineering Status — SynthGigCredit-IN
**Audit date:** 2026-10-05  
**Auditor:** Engineering agent  
**Baseline tests:** 75 passed, 0 failed (test_dgp.py excluded — requires generated data)

---

## Classification Key

| Code | Meaning |
|------|---------|
| A | Fully working — logic correct, tested |
| B | Partially working — core logic ok, edge cases or integration gaps |
| C | Mock / static — returns hard-coded or randomly generated data |
| D | UI-only / dead — frontend feature with no backend support |
| E | Broken — will throw an error or produce wrong output at runtime |
| F | Backend-only — implemented in backend, no frontend usage |
| G | Duplicate / redundant |

---

## Backend Features

| Feature | File | Status | Notes |
|---------|------|--------|-------|
| Evidence computation `compute_evidence()` | `src/evidence/compute_evidence.py` | **A** | Formula correct, all tests pass |
| Decision gate `make_decision()` D1–D4 | `src/decisions/gate.py` | **A** | All truth-table rows correct, all tests pass |
| Tau selection `select_tau()` | `src/decisions/tau.py` | **A** | Correct binary-search algorithm, tested |
| Policy Kleene engine | `src/policy/kleene.py` | **A** | Three-valued logic correct, all tests pass |
| Policy rule engine `evaluate_policy()` | `src/policy/rule_engine.py` | **A** | Full provenance, conflict detection, tested |
| Policy rule loader `load_policy_set()` | `src/policy/rule_loader.py` | **A** | Schema validation, correct |
| Policy versioning `select_version()` | `src/policy/versioning.py` | **A** | Date-range filtering correct |
| Credit score computation | `src/scoring/credit_score.py` | **A** | Scorecard formula correct, tested |
| Platt calibration `PlattCalibrator` | `src/calibration/platt.py` | **A** | MLE fitting correct |
| Model training `train_model()` | `src/models/train_models.py` | **A** | LR + XGBoost pipelines correct |
| Model IO `save_model()` / `load_model()` | `src/utils/model_io.py` | **F** | Implemented but **never called from API** |
| Feature engineering `build_features()` | `src/feature_engineering/build_features.py` | **A** | Vectorised, correct NaN rules |
| SHAP explanation `compute_shap_values()` | `src/explainability/shap_values.py` | **F** | Implemented, never called from API; requires `shap` package |
| LR coefficient explanation | `src/explainability/lr_coefficients.py` | **F** | Implemented, never called from API |
| Explanation wrapper `explain()` | `src/explainability/explain.py` | **B** | Signature correct; **caller in API uses wrong arguments — broken at API layer** |
| Batch policy evaluation `evaluate_batch()` | `src/policy/rule_engine.py` | **B** | Logic correct but `annual_income` derivation incomplete for API use |
| Config loader | `src/utils/config_loader.py` | **A** | YAML loading + assertions correct |
| Data generation `generate_data` | `src/data_generation/` | **F** | Research code, not part of API |

### API — `app/api/main.py`

| Endpoint / Feature | Status | Bug |
|-------------------|--------|-----|
| `GET /api/health` | **A** | None |
| `GET /api/config` | **A** | None |
| `GET /api/history` | **C** | Always returns `[]`; client is told to maintain own history |
| `POST /api/decide` — evidence gate | **A** | Evidence layer correct |
| `POST /api/decide` — policy gate | **E** | Passes `app_data.__dict__` to policy engine with key `occupation` but rules expect `occupation_category` → PMMY enterprise rule always UNRESOLVED |
| `POST /api/decide` — risk/PD | **E** | Uses `_compute_risk_heuristic()` always; **no trained model loaded**; no attempt to load `.pkl` |
| `POST /api/decide` — tau / tau_e override | **E** | `DecisionRequest` schema has no `tau`/`tau_e` fields; frontend values silently dropped |
| `POST /api/decide` — decision logic | **A** | `make_decision()` call is correct once PD + policy are fixed |
| `POST /api/decide` — explain call | **E** | Calls `explain(applicant_id, features=..., decision=..., config=...)` but `explain()` signature is `explain(applicant_id, pd_calibrated, tau, decision, ...)` → **TypeError on every request** |
| `POST /api/decide` — mode passthrough | **B** | `decision_mode` accepted but not forwarded as `mode` to `make_decision()` (hardcoded `"D4"`) |
| Credit score in response | **A** | Scorecard computation correct |
| CORS headers | **A** | Configured for localhost:5173 and :3000 |

---

## Frontend Features

### Assessment / Decision Workflow

| Feature | Component | Status | Notes |
|---------|-----------|--------|-------|
| Applicant input form | `AssessmentPage.tsx` | **A** | All fields present, correct |
| Finance inputs | `AssessmentPage.tsx` | **A** | Income, expenses, debt, liquidity, volatility |
| Evidence sliders (AA, ULI, history) | `AssessmentPage.tsx` | **A** | Live evidence score preview correct |
| Decision mode selector (D1–D4) | `AssessmentPage.tsx` | **A** | Sent to backend correctly |
| Tau/tau_e threshold from settings | `useSettingsStore.ts` → `api.ts` | **E** | Values sent at wrong level of request body; backend schema rejects/ignores them |
| `POST /api/decide` call | `api.ts assessmentApi.decide()` | **B** | Calls real backend; occupation values use wrong format (`ride-hailing` vs `ride_hailing`) |
| Fallback to local computation | `useAssessmentStore.ts` | **A** | Falls back to `computeDecision()` when backend offline |
| Decision result display | `DecisionResultPage.tsx` | **B** | Displays gates correctly; adapts backend response |
| SHAP/explanation display | `DecisionResultPage.tsx` | **B** | Shows explanation JSON; blocked by explain() bug on backend |

### Dashboard

| Feature | Status | Notes |
|---------|--------|-------|
| Total assessments KPI | **B** | Session history + mock baseline; not from backend |
| Approval rate KPI | **B** | Computed from session history; reasonable |
| Average risk PD KPI | **B** | Computed from session history; reasonable |
| Evidence coverage KPI | **B** | Computed from session history; reasonable |
| Monthly assessment trend chart | **C** | `Math.random()` — **fabricated every render** |
| Decision mode pie chart | **C** | Static hardcoded percentages |
| ROC curve chart | **C** | `rocData` from `mockData.ts`; **AUC badge shows 0.87 — WRONG** (actual T1 XGBoost = 0.7568) |
| Gate pass rate bar chart | **C** | Static hardcoded percentages |
| Recent decisions table | **B** | Real session history + mock history rows |

### Models Page

| Feature | Status | Notes |
|---------|--------|-------|
| Model registry table | **C** | 6 fake models (Random Forest, Neural Net, SVM — none exist in project) |
| Model accuracy values | **C** | Fabricated (0.892, 0.784, etc.) |
| Accuracy trend chart | **C** | Fabricated weekly trend |
| Model type distribution | **C** | Fabricated |
| Train button | **D** | Calls mock route only; no backend train endpoint |
| Deploy button | **D** | Calls mock route only; no backend deploy endpoint |
| Archive button | **D** | Calls mock route only; no backend archive endpoint |
| Download button | **D** | No download endpoint |

### Datasets Page

| Feature | Status | Notes |
|---------|--------|-------|
| Dataset list | **C** | 6 fake datasets (DS-003/004/005/006 don't exist) |
| Upload button | **D** | Mock only; no backend upload endpoint |
| Delete button | **D** | Mock only; no backend delete endpoint |
| DS-001 Home Credit | **B** | Exists in `data/authentic/`; row/column counts approximate |
| DS-002 SynthGigCredit-IN-v1 | **B** | Generated if `make generate` run; approximate row count |

### Settings Page

| Feature | Status | Notes |
|---------|--------|-------|
| Risk cutoff % | **E** | Persisted but tau not reaching backend |
| Evidence cutoff | **E** | Persisted but tau_e not reaching backend |
| Default decision mode | **A** | Used in local fallback |
| Policy toggles (JanSamarth/PMMY) | **D** | Stored but not sent to backend or used in decision |

---

## Confirmed Bugs (Prioritised)

| # | Severity | Location | Description |
|---|----------|----------|-------------|
| 1 | **CRITICAL** | `app/api/main.py` | `explain()` called with wrong arguments → TypeError on every `/api/decide` with `explain=true` |
| 2 | **CRITICAL** | `app/api/main.py` | No trained model loading; always uses heuristic PD |
| 3 | **HIGH** | `app/api/main.py` | `tau` and `tau_e` from frontend silently ignored — `DecisionRequest` schema missing these fields |
| 4 | **HIGH** | `app/api/main.py` | Policy engine called with `occupation` key; rules expect `occupation_category` → PMMY enterprise rule always UNRESOLVED |
| 5 | **HIGH** | `ML Froent end/ml-frontend/src/services/api.ts` | Occupation values use frontend format (`ride-hailing`) vs rule format (`ride_hailing`) |
| 6 | **HIGH** | `DashboardPage.tsx` | AUC badge shows 0.87 — actual T1 XGBoost AUC is 0.7568 |
| 7 | **MEDIUM** | `app/api/main.py` | `decision_mode` from request hardcoded to `"D4"` in `make_decision()` call |
| 8 | **MEDIUM** | `DashboardPage.tsx` | Monthly trend chart uses `Math.random()` — fabricated on every render |
| 9 | **LOW** | `ModelsPage.tsx` | All 6 models are fake; misleading model metrics displayed |
| 10 | **LOW** | `DatasetsPage.tsx` | 4 of 6 datasets are fabricated |

---

## Baseline Test Results (pre-fix)

```
75 passed, 0 failed
(test_dgp.py skipped — requires generated synthetic data files)
```
