# FastAPI Backend — SynthGigCredit Decision API

Research prototype for policy-constrained credit decisioning with evidence-quality gating.

## Quick Start

### Installation

```bash
# FastAPI and Uvicorn are already installed in the project environment
# If not, install:
pip install fastapi uvicorn pydantic
```

### Running the Server

```bash
cd <project-root>
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: **http://localhost:8000**

### API Documentation

Interactive documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints

### `POST /api/decide`

Make a credit decision on an applicant.

**Request:**
```json
{
  "applicant": {
    "age": 35,
    "platform_tenure": 12,
    "e_shram_registered": 1,
    "income_mean": 25000,
    "income_volatility": 0.2,
    "expense_mean": 18000,
    "liquidity_current": 50,
    "history_length": 12,
    "multi_platform": 1,
    "emi_status": 0,
    "aa_completeness": 0.95,
    "uli_completeness": 0.80,
    "age_policy": 35,
    "income_policy": 25000,
    "occupation": "ride_hailing",
    "nonfarm_engaged": 1,
    "e_shram_policy": 1,
    "pd_lr": null,
    "pd_xgb": null,
    "applicant_id": "APP001",
    "decision_date": "2026-09-29"
  },
  "decision_mode": "production",
  "explain": true
}
```

**Response fields:** `outcome` (`APPROVE`, `REVIEW`, `DECLINE`), the three gate objects, `risk_score`, `risk_source`, `tau_used`, `tau_e_used`, `credit_score`, `explanation`, and the normalized `mode` (`D1`–`D4`). Risk source is `override_xgb`, `override_lr`, or `heuristic`. The score is illustrative and does not affect the decision.

### `GET /api/health`

Service health check.

**Response:**
```json
{
  "status": "ok",
  "mode": "research",
  "version": "0.1.0",
  "message": "SynthGigCredit research prototype is operational; PD uses a heuristic unless supplied",
  "model_loaded": false
}
```

### `GET /api/config`

Get current configuration and thresholds.

**Response:**
```json
{
  "approval_target": 0.7,
  "evidence_threshold": 0.5,
  "policy_schemes": ["jan_samarth", "pmmy"],
  "risk_bins": [0.1, 0.3],
  "decision_date": "2026-10-23",
  "default_tau": 0.4
}
```

### `GET /api/model_status`

Reports whether inference model artifacts are loaded and returns saved T1 benchmark metrics when available. In the current prototype, no trained inference artifact is loaded, so decisions use the request PD override or the heuristic.

### `POST /api/explain`

Builds explanation JSON from a prior decision's PD, thresholds, outcome, evidence status, and policy state. It does not compute SHAP values.

### `POST /api/evaluate_batch`

Accepts `{"applicants": [...], "decision_mode": "D4", "tau": 0.3, "tau_e": 0.5}`. Batch applicant records use `age`, `income_monthly`, `history_length`, `aa_completeness`, `uli_completeness`, `occupation`, `nonfarm_engaged`, and optional `pd_xgb` or `pd_lr`. Empty batches and out-of-range thresholds are rejected with HTTP 422. Each result uses the same decision code as `/api/decide`.

## 3-Layer Decision Logic

1. **Evidence Gate**: Evaluates data quality (history_length, AA/ULI completeness)
   - Passes if evidence_score ≥ τ_e (0.5)
   - **Outcome**: PASS or FAIL

2. **Policy Gate**: Evaluates the configured JanSamarth and PMMY research rules
   - Combines rule states using the configured three-valued logic
   - Rule provenance is UNVERIFIED; results are not an eligibility determination

3. **Risk Rank**: Uses a supplied PD override when present, otherwise the documented heuristic
   - Maps PD to low (<0.10), medium (0.10–<0.30), or high (≥0.30)
   - **Outcome**: PD score and rank

## Final Decision Tree (D4 Mode)

```
PD >= τ (0.4)          → DECLINE (high risk)
    ↓
Policy = UNSATISFIED   → DECLINE (ineligible)
    ↓
Policy = UNRESOLVED    → REVIEW (uncertain policy)
    ↓
Evidence < τ_e (0.5)   → REVIEW (insufficient data)
    ↓
                          → APPROVE (all gates pass)
```

## PD source and explanations

No trained inference model is currently loaded by this API. If `pd_xgb` is provided, it takes precedence over `pd_lr`; if neither is supplied, the heuristic is used. `/api/model_status` distinguishes benchmark metrics from an inference model artifact. Explanation output contains decision, evidence, and policy details; it does not contain SHAP explanations.

## Error Handling

- **503 Service Unavailable**: Config/policy rules not loaded (startup incomplete)
- **500 Internal Server Error**: Processing error (invalid features, model error)
- **422 Unprocessable Entity**: Invalid request schema

## Decision modes

- `D1`: PD gate only
- `D2`: PD and policy gates
- `D3`: PD and evidence gates
- `D4`: all three gates
- Legacy request labels `production` and `diagnostic` map to `D4`.

- `explain: true` — Include explanation JSON in response
- `explain: false` — Return decision only (faster)

## Performance Notes

- **Average decision time**: 10-50ms (without model inference)
- **Max batch size recommended**: 1000 applicants/request

## Development Notes

- Research prototype only; no production deployment features
- No authentication/authorization
- No rate limiting
- No caching
- Single-threaded (use Gunicorn + workers for production)

## References

- **Architecture**: `FINAL_PROJECT_ARCHITECTURE.md` (Diagram 7 — Decision Engine)
- **Technical Spec**: `FINAL_PROJECT_TECHNICAL_DOCUMENTATION.md` (§12 — Backend)
- **Frontend Requirements**: `FRONTEND_REQUIREMENTS.md` (API specification)
