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

**Response:**
```json
{
  "applicant_id": "APP001",
  "decision_date": "2026-09-29",
  "outcome": "APPROVE",
  "recommendation": "Applicant passed evidence and policy gates with acceptable risk.",
  "evidence_gate": {
    "gate_name": "evidence",
    "passed": true,
    "reasoning": "Evidence score 0.725 ≥ threshold 0.5",
    "details": {
      "score": 0.725,
      "threshold": 0.5,
      "history_length": 12,
      "aa_completeness": 0.95,
      "uli_completeness": 0.8
    }
  },
  "policy_gate": {
    "gate_name": "policy",
    "passed": true,
    "reasoning": "Policy state: SATISFIED",
    "details": {
      "schemes_evaluated": {
        "jan_samarth": "SATISFIED",
        "pmmy": "SATISFIED"
      },
      "age": 35,
      "income": 25000.0,
      "occupation": "ride_hailing"
    }
  },
  "risk_rank": {
    "gate_name": "risk_rank",
    "passed": true,
    "reasoning": "Risk rank: low (PD 0.156)",
    "details": {
      "pd_estimate": 0.156,
      "risk_rank": "low",
      "bins": [3, 5, 10]
    }
  },
  "risk_score": 0.156,
  "explanation": {
    "model": "xgb",
    "applicant_id": "APP001",
    "predicted_pd": 0.156,
    "top_shap_features": [
      {
        "feature": "income_mean",
        "shap": 0.082,
        "value": 25000
      }
    ]
  },
  "model_version": "0.1.0",
  "mode": "production"
}
```

### `GET /api/health`

Service health check.

**Response:**
```json
{
  "status": "ok",
  "mode": "research",
  "version": "0.1.0",
  "message": "SynthGigCredit research prototype is operational"
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
  "risk_bins": [3, 5, 10],
  "decision_date": "2026-09-29"
}
```

## 3-Layer Decision Logic

1. **Evidence Gate**: Evaluates data quality (history_length, AA/ULI completeness)
   - Passes if evidence_score ≥ τ_e (0.5)
   - **Outcome**: PASS or FAIL

2. **Policy Gate**: Evaluates eligibility against government policies (JanSamarth, PMMY)
   - Evaluates age, income, occupation rules
   - Combines policies using Kleene OR (any satisfied = pass)
   - **Outcome**: SATISFIED, UNRESOLVED, or UNSATISFIED

3. **Risk Rank**: Estimates probability of default (PD)
   - Uses trained XGBoost-C or Logistic Regression model
   - Falls back to heuristic if models not available
   - Maps PD to risk rank (low/medium/high)
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

## Integration with Trained Models

Once trained models are available:

1. Place XGBoost model artifact at: `results/authentic/xgb_c_model.pkl`
2. Place Logistic Regression artifact at: `results/authentic/lr_c_model.pkl`

The API will automatically load and use these models in `/api/decide` endpoint.

To use heuristic PD instead (for testing without trained models):
```json
{
  "applicant": {
    ...
    "pd_xgb": null,
    "pd_lr": null,
    ...
  }
}
```

## Explanation Types

### XGBoost Explanation
Uses TreeSHAP (Shapley Additive exPlanations) for feature importance ranking.

### Logistic Regression Explanation
Uses coefficient-based interpretation:
- **Coefficients**: Log-odds per unit feature change
- **Odds Ratios**: Multiplicative change in odds
- **Feature Contributions**: Per-applicant contribution to log-odds

## Error Handling

- **503 Service Unavailable**: Config/policy rules not loaded (startup incomplete)
- **500 Internal Server Error**: Processing error (invalid features, model error)
- **422 Unprocessable Entity**: Invalid request schema

## Mode Flags

- `decision_mode: "production"` — Full 3-layer decision (D4)
- `decision_mode: "diagnostic"` — Same as production (for future testing modes)

- `explain: true` — Include explanation JSON in response
- `explain: false` — Return decision only (faster)

## Performance Notes

- **Average decision time**: 10-50ms (without model inference)
- **With trained model inference**: 50-200ms
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
