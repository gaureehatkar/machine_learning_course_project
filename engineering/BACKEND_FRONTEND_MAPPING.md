# Backend ↔ Frontend Mapping
**Date:** 2026-10-05  

Legend: **A** = working · **B** = partial · **C** = mock · **D** = UI-only/dead · **E** = was broken (now fixed)

---

## API Endpoints → Frontend Usage

| Backend Capability | API Endpoint | Frontend Feature | File | Status | Action taken |
|---|---|---|---|---|---|
| Credit decision (3-layer) | `POST /api/decide` | Assessment submit button | `useAssessmentStore.runAssessment()` → `assessmentApi.decide()` | **A** | Fixed: tau/tau_e schema, occupation normalisation, explain() args, mode forwarding |
| Explanation JSON | `POST /api/decide` (explain=true) | Decision result explanation panel | `DecisionResultPage.tsx` | **A** (was E) | Fixed: explain() TypeError resolved |
| Evidence gate result | `POST /api/decide` → `evidence_gate` | Evidence panel in result page | `adaptBackendResponse()` | **A** | No change needed |
| Policy gate result | `POST /api/decide` → `policy_gate` | Policy panel in result page | `adaptBackendResponse()` | **A** (was E) | Fixed: occupation_category mapping |
| Risk score / PD | `POST /api/decide` → `risk_score`, `risk_source` | Risk panel, credit score display | `adaptBackendResponse()` | **B** (was E) | Fixed: heuristic labelled; model loads from pkl if present |
| Tau / tau_e used | `POST /api/decide` → `tau_used`, `tau_e_used` | Settings page threshold display | `DecisionResultPage.tsx` | **A** (was E) | Fixed: fields now in schema, values reflected |
| Credit score display | `POST /api/decide` → `credit_score_display` | Credit score card | `DecisionResultPage.tsx` | **A** | No change |
| Standalone explanation | `POST /api/explain` | Not yet wired | — | **F** | New endpoint added; not yet used in frontend |
| Batch evaluation | `POST /api/evaluate_batch` | Not yet wired | — | **F** | New endpoint added; not yet used in frontend |
| Service health | `GET /api/health` | Not currently displayed | — | **F** | Could be added to dashboard header |
| Configuration / thresholds | `GET /api/config` | Not currently fetched | — | **F** | Settings page could pre-fill from this |
| T1 experiment results | `GET /api/results` | Dashboard ROC chart | Not yet fetched | **F** | New endpoint; dashboard uses hardcoded T1 values for now |
| Model status + T1 metrics | `GET /api/model_status` | Models page | Not yet fetched | **F** | New endpoint; Models page uses hardcoded T1 values for now |
| Decision history | `GET /api/history` | History page | `assessmentApi.getHistory()` | **C** | Always returns `[]`; client maintains session history |
| Model train | None | Models page Train button | `modelsApi.trainModel()` | **D** | Mock only; training is CLI. Button disabled in UI |
| Model deploy | None | Models page Deploy button | `modelsApi.deployModel()` | **D** | Mock only; no deploy endpoint. Button disabled in UI |
| Dataset list | None | Datasets page | `datasetsApi.getDatasets()` | **C** | Mock only; 3 real entries now shown |
| Dataset upload | None | Datasets page Upload button | `datasetsApi.uploadDataset()` | **D** | No backend upload endpoint; button is mock |
| Auth login/signup | None | LoginPage, SignupPage | `authApi.login/signup` | **C** | Mock only; no auth backend |

---

## Frontend Features with No Backend

| Frontend Feature | Component | Backend needed? | Decision |
|---|---|---|---|
| Login / Signup | `LoginPage.tsx`, `SignupPage.tsx` | No (research prototype) | Keep UI, mock stays; no real auth needed |
| Local decision fallback | `useAssessmentStore.computeDecision()` | No | Keep — offline fallback is useful |
| Live evidence score preview | `AssessmentPage.tsx` calculation | No (pure JS) | Keep — correct formula |
| Session history | `useAssessmentStore.history` | No | Keep — useful within session |
| Settings persistence | `useSettingsStore` | No | Keep — localStorage, correct |
| Dashboard session KPIs | `DashboardPage.tsx` | Partial | Keep — computed from session history |
| Monthly trend chart | `DashboardPage.tsx` | Yes (not available) | Zeroed out; labelled as placeholder |
| Gate pass rate chart | `DashboardPage.tsx` | Yes (not available) | Labelled as illustrative |
| Decision mode pie chart | `DashboardPage.tsx` | Yes (not available) | Labelled as illustrative |

---

## Backend Features with No Frontend

| Backend Capability | Where | Suggested frontend connection |
|---|---|---|
| `POST /api/explain` | `app/api/main.py` | Wire to "Re-explain" button on DecisionResultPage |
| `POST /api/evaluate_batch` | `app/api/main.py` | Could drive dashboard gate pass rates |
| `GET /api/results` | `app/api/main.py` | Dashboard ROC chart should fetch from here instead of hardcoding |
| `GET /api/model_status` | `app/api/main.py` | Models page should fetch from here for live artifact status |
| `GET /api/config` | `app/api/main.py` | Settings page could fetch defaults from here |
| `src/utils/model_io.save_model()` | Research pipeline | Called by `experiments/authentic/run.py` after training |
| `src/explainability/shap_values.py` | Research pipeline | SHAP requires trained model; not yet surfaced in API |

---

## Occupation Value Contract

The frontend dropdown and backend rule engine must agree on these values:

| Frontend sends | Backend normalises to | Rule engine key |
|---|---|---|
| `ride-hailing` | `ride_hailing` | `occupation_category` |
| `delivery` | `delivery` | `occupation_category` |
| `freelance` | `freelance_services` | `occupation_category` |
| `retail` | `retail_micro` | `occupation_category` |
| `agricultural` | `agri_labour` | `occupation_category` |
| `unknown` | `ride_hailing` (default) | `occupation_category` |

Normalisation is done in **both** `ApplicantFeatures.normalise_occupation()` (backend validator) and `normaliseOccupation()` (frontend `api.ts`).

---

## Tau / Tau_e Contract

| Layer | Before fix | After fix |
|---|---|---|
| Frontend sends | `{ ..., tau: 0.25, tau_e: 0.5 }` at top level of body | Same — correct |
| Backend schema | `DecisionRequest` had no `tau`/`tau_e` fields → silently dropped | Fixed: fields added to `DecisionRequest` |
| Backend uses | Hardcoded `CONFIG.get("decision.tau", 0.4)` | Uses request value if provided, config default otherwise |
| Response exposes | Nothing | `tau_used` and `tau_e_used` in `DecisionResponse` |
