# Integration Test Report
**Date:** 2026-10-05  
**Project:** SynthGigCredit-IN v1.2  

---

## Test Run Summary

| Suite | Tests | Passed | Failed |
|---|---|---|---|
| `test_api_decide.py` (new — engineering) | 38 | 38 | 0 |
| `test_decisions.py` | 12 | 12 | 0 |
| `test_evidence.py` | 6 | 6 | 0 |
| `test_policy.py` | 24 | 24 | 0 |
| `test_credit_score.py` | 14 | 14 | 0 |
| `test_features.py` | 15 | 15 | 0 |
| **TOTAL** | **113** | **113** | **0** |

`test_dgp.py` excluded — requires generated synthetic data files (`make generate`).

**Run command:**
```
python -m pytest tests/ --ignore=tests/test_dgp.py -v
```

---

## Bugs Fixed

| # | Severity | Bug | Fix |
|---|---|---|---|
| 1 | CRITICAL | `explain()` called with wrong kwargs in API → TypeError on every request | Rewrote call with correct positional args matching `explain()` signature |
| 2 | CRITICAL | No trained model loading in API — always used heuristic silently | Added lifespan loader: tries `results/authentic/xgb_c_model.pkl` then `lr_c_model.pkl`; falls back to heuristic with `risk_source="heuristic"` in response |
| 3 | HIGH | `tau`/`tau_e` from frontend silently dropped — `DecisionRequest` schema missing fields | Added `tau: float | None` and `tau_e: float | None` to `DecisionRequest`; values forwarded to `make_decision()`; `tau_used`/`tau_e_used` in response |
| 4 | HIGH | Policy engine called with key `occupation` — rules expect `occupation_category` | Added `_OCCUPATION_NORMALISE` map + Pydantic validator; policy attrs dict now uses `occupation_category` key |
| 5 | HIGH | Frontend occupation values (`ride-hailing`, `agricultural`, `freelance`) didn't match rule format | Added `normaliseOccupation()` in `api.ts`; also applied at backend validator level |
| 6 | HIGH | `decision_mode` from request hardcoded to `"D4"` in `make_decision()` call | Now forwards `req.decision_mode` (validated against `{"D1","D2","D3","D4"}`) |
| 7 | HIGH | Dashboard AUC badge showed `0.87` — actual T1 XGBoost AUC = `0.7568` | Badge updated to `0.7568`; T1 metrics panel added with source citation |
| 8 | MEDIUM | Monthly trend chart used `Math.random()` — fabricated on every render | Replaced with zeros + label "session history only; no historical backend data" |
| 9 | MEDIUM | Models page showed 6 fake models (Random Forest, Neural Net, SVM) with fabricated accuracy | Replaced with 6 real models (LR+XGBoost × sets A/B/C) with real T1 metrics where available |
| 10 | MEDIUM | Datasets page showed 6 fake datasets (DS-003..006 don't exist) | Reduced to 3 entries: DS-001 (Home Credit), DS-002 (Afsharinia survey), DS-003 (synthetic, pending generation) |
| 11 | LOW | `on_event("startup")` deprecated in newer FastAPI | Migrated to `lifespan` context manager |
| 12 | LOW | `@app.on_event` startup didn't run under `TestClient` | Fixed by using `TestClient` as context manager (`with TestClient(app)`) |

---

## New API Endpoints Added

| Endpoint | Purpose |
|---|---|
| `POST /api/explain` | Standalone explanation without re-running decision |
| `POST /api/evaluate_batch` | Batch decisions with summary statistics |
| `GET /api/model_status` | Model artifact availability + T1 metrics |
| `GET /api/results` | Raw T1 results JSON |

---

## New Tests Added (`tests/test_api_decide.py`)

38 tests covering:
- `/api/decide` schema validation (required fields, valid enums)
- Heuristic PD correctly labelled as `risk_source="heuristic"`
- `pd_xgb` / `pd_lr` overrides accepted and reflected
- `tau` override reflected in `tau_used`; affects decision outcome
- `tau_e` override reflected in `tau_e_used`; affects evidence gate
- Low evidence → REVIEW in D4 mode
- Occupation normalisation: `ride-hailing`→`ride_hailing`, `agricultural`→`agri_labour`, `freelance`→`freelance_services`
- `agri_labour` + `nonfarm_engaged=0` → policy UNSATISFIED → DECLINE in D2
- `explain()` no longer throws TypeError
- `/api/explain` standalone endpoint
- Batch evaluation: correct count, rates sum to 1, `tau_used` matches request
- Single vs batch consistency (same input → same outcome)
- Invalid input → 422: age out of range, invalid mode, missing field, tau > 1, empty batch
- All 4 decision modes forwarded correctly (D1 ignores policy+evidence, etc.)
- `/api/health`, `/api/config`, `/api/model_status` return correct schemas

---

## Frontend Changes Summary

| File | Change |
|---|---|
| `src/services/api.ts` | Added `normaliseOccupation()`; fixed occupation sent to backend; tau/tau_e now at correct top-level of body; `BackendDecisionResponse` updated with `risk_source`, `tau_used`, `tau_e_used` |
| `src/pages/DashboardPage.tsx` | AUC badge: `0.87` → `0.7568`; monthly trend: `Math.random()` → zeros + label; T1 metrics panel added; gate chart labelled illustrative |
| `src/pages/ModelsPage.tsx` | Replaced 6 fake models with 6 real LR+XGBoost models; real T1 metrics table; Train/Deploy buttons disabled with explanation; type/schema updated |
| `src/pages/DatasetsPage.tsx` | Reduced from 6 fake to 3 real/pending datasets |

---

## Remaining Work (Research-side Dependencies)

These items cannot be completed by engineering alone:

| Item | Dependency |
|---|---|
| Real model inference via `/api/decide` | Research teammate must train models and save with `src.utils.model_io.save_model()` to `results/authentic/xgb_c_model.pkl` |
| SHAP explanations in API response | Requires trained XGBoost model + `shap` package; `src/explainability/shap_values.py` is ready |
| Dashboard gate pass rate chart from real data | Requires running `/api/evaluate_batch` on a representative sample |
| Dashboard ROC curve from live data | `/api/results` endpoint now exists; frontend should fetch from it instead of hardcoded values |
| Ablation experiment metrics (sets A, B) | Research teammate must run `experiments/ablation/` |
| `test_dgp.py` | Requires `make generate` to produce synthetic data files |

---

## How to Run

**Backend:**
```bash
cd <project-root>
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd "ML Froent end/ml-frontend"
npm install
npm run dev
```

**Tests:**
```bash
python -m pytest tests/ --ignore=tests/test_dgp.py -v
```

**API docs (Swagger):**  
http://localhost:8000/docs

---

## Commands to verify fixes

```bash
# 1. Confirm explain() works — should return explanation JSON, no TypeError
curl -s -X POST http://localhost:8000/api/decide \
  -H "Content-Type: application/json" \
  -d '{"applicant":{"age":30,"platform_tenure":12,"e_shram_registered":1,"income_mean":25000,"income_volatility":0.25,"expense_mean":15000,"liquidity_current":50000,"history_length":9,"multi_platform":1,"emi_status":0,"aa_completeness":0.8,"uli_completeness":0.7,"age_policy":30,"income_policy":25000,"occupation":"ride-hailing","nonfarm_engaged":1,"e_shram_policy":1,"pd_xgb":null,"pd_lr":null,"applicant_id":"TEST-001","decision_date":"2026-01-01"},"decision_mode":"D4","explain":true,"tau":0.25,"tau_e":0.5}' \
  | python -m json.tool | grep -E '"outcome"|"tau_used"|"risk_source"|"decision"'

# 2. Confirm tau override reflected
# tau_used should be 0.15 in response

# 3. Run all tests
python -m pytest tests/ --ignore=tests/test_dgp.py -q
```
