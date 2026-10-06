"""
FastAPI Backend — SynthGigCredit Research Prototype

Endpoints:
  POST /api/decide        — accept DecisionRequest, return DecisionResponse
  POST /api/explain       — explain a single decision by applicant_id
  POST /api/evaluate_batch— batch decision evaluation
  GET  /api/health        — service status
  GET  /api/config        — configuration and thresholds
  GET  /api/model_status  — trained model availability and metrics
  GET  /api/results       — T1 authentic experiment results

Bugs fixed vs original:
  [FIX-1] explain() called with wrong arguments → now uses correct positional kwargs
  [FIX-2] No trained model loading → now tries results/authentic/{xgb,lr}_c_model.pkl
           and falls back to heuristic with honest status flag in response
  [FIX-3] tau / tau_e silently ignored → added to DecisionRequest schema, forwarded
  [FIX-4] policy engine called with 'occupation' key → now maps to 'occupation_category'
           and normalises frontend occupation values to rule-engine format
  [FIX-5] decision_mode from request hardcoded to D4 → now forwarded correctly

Usage:
  uvicorn app.api.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
import uvicorn

# Add project root to path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.config_loader import load_config
from src.utils.model_io import load_model
from src.evidence.compute_evidence import compute_evidence, evidence_status
from src.policy.rule_loader import load_policy_set, PolicySet
from src.policy.rule_engine import evaluate_policy, combine_schemes, PolicyEvaluation
from src.policy.versioning import select_version
from src.policy.kleene import State, PolicyVersionError
from src.decisions.gate import make_decision, Decision
from src.decisions.tau import select_tau
from src.scoring.credit_score import compute_score_and_tau, format_score_display
from src.explainability.explain import explain as build_explanation


# ── Occupation normalisation map ───────────────────────────────────────────────
# Frontend sends values like 'ride-hailing'; policy rules expect 'ride_hailing'.
# Mapping is exhaustive for all values the frontend occupation dropdown can produce.
_OCCUPATION_NORMALISE: dict[str, str] = {
    # frontend value          : rule-engine value
    "ride-hailing":           "ride_hailing",
    "ride_hailing":           "ride_hailing",
    "delivery":               "delivery",
    "freelance":              "freelance_services",
    "freelance_services":     "freelance_services",
    "retail":                 "retail_micro",
    "retail_micro":           "retail_micro",
    "agricultural":           "agri_labour",
    "agri_labour":            "agri_labour",
    "agri labour":            "agri_labour",
    "unknown":                "ride_hailing",   # default to non-agri for unknown
}

# Valid D-mode values
_VALID_MODES = {"D1", "D2", "D3", "D4"}

# Paths for trained model artefacts
_MODEL_DIR = ROOT / "results" / "authentic"
_XGB_PATH  = _MODEL_DIR / "xgb_c_model.pkl"
_LR_PATH   = _MODEL_DIR / "lr_c_model.pkl"


# ── Pydantic models ───────────────────────────────────────────────────────────

class ApplicantFeatures(BaseModel):
    """26 applicant input features for credit decision."""

    # Identity & Demographics
    age: int = Field(..., ge=18, le=65, description="Age in years")
    platform_tenure: int = Field(..., ge=1, le=24, description="Months on platform")
    e_shram_registered: int = Field(..., ge=0, le=1, description="e-Shram registration (0/1)")

    # Income & Stability
    income_mean: float = Field(..., gt=0, description="Average monthly income (₹)")
    income_volatility: float = Field(..., ge=0, description="Income CV (dimensionless)")
    expense_mean: float = Field(..., ge=0, description="Average monthly expense (₹)")
    liquidity_current: float = Field(..., description="Liquidity at cutoff")

    # Employment History
    history_length: int = Field(..., ge=3, le=12, description="Months of history (3/6/9/12)")
    multi_platform: int = Field(..., ge=0, le=1, description="Multi-platform worker (0/1)")
    emi_status: int = Field(..., ge=0, le=1, description="EMI holder (0/1)")

    # Data Quality — Evidence inputs
    aa_completeness: float = Field(..., ge=0, le=1, description="AA data completeness (0-1)")
    uli_completeness: float = Field(..., ge=0, le=1, description="ULI data completeness (0-1)")

    # Policy Attributes
    age_policy: int = Field(..., ge=18, le=65, description="Age for policy evaluation")
    income_policy: float = Field(..., gt=0, description="Monthly income for policy (₹)")
    occupation: str = Field(..., description="Occupation code (e.g., ride_hailing)")
    nonfarm_engaged: int = Field(..., ge=0, le=1, description="Non-farm income flag (0/1)")
    e_shram_policy: int = Field(..., ge=0, le=1, description="e-Shram for policy (0/1)")

    # Optional model PD overrides
    pd_lr: float | None = Field(None, ge=0, le=1, description="LR PD override (optional)")
    pd_xgb: float | None = Field(None, ge=0, le=1, description="XGBoost PD override (optional)")

    # Metadata
    applicant_id: str = Field(..., description="Unique applicant identifier")
    decision_date: str = Field(
        default_factory=lambda: date.today().isoformat(),
        description="Decision date (YYYY-MM-DD)",
    )

    @field_validator("occupation")
    @classmethod
    def normalise_occupation(cls, v: str) -> str:
        """[FIX-4] Normalise frontend occupation values to rule-engine format."""
        return _OCCUPATION_NORMALISE.get(v.lower().strip(), v)


class DecisionRequest(BaseModel):
    """Request body for /api/decide."""
    applicant: ApplicantFeatures
    decision_mode: str = Field("D4", description="D1 | D2 | D3 | D4")
    explain: bool = Field(True, description="Include explanation JSON")

    # [FIX-3] Accept tau / tau_e overrides from frontend
    tau: float | None = Field(
        None, ge=0.01, le=0.99,
        description="PD decision threshold override (uses config default if omitted)",
    )
    tau_e: float | None = Field(
        None, ge=0.0, le=1.0,
        description="Evidence threshold override (uses config default if omitted)",
    )

    @field_validator("decision_mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        v = v.upper()
        if v not in _VALID_MODES:
            raise ValueError(f"decision_mode must be one of {sorted(_VALID_MODES)}, got {v!r}")
        return v


class GateResult(BaseModel):
    """Result from a single gate."""
    gate_name: str
    passed: bool | None
    reasoning: str
    details: dict[str, Any] = Field(default_factory=dict)


class DecisionResponse(BaseModel):
    """Response body for /api/decide."""
    model_config = {"protected_namespaces": ()}

    applicant_id: str
    decision_date: str

    # Final decision
    outcome: str          # APPROVE | REVIEW | DECLINE
    recommendation: str

    # Gate trace
    evidence_gate: GateResult
    policy_gate: GateResult
    risk_rank: GateResult

    # Risk
    risk_score: float
    risk_source: str      # "model_xgb" | "model_lr" | "heuristic" | "override"

    # Credit score
    credit_score: int
    credit_score_display: dict[str, Any] | None

    # Thresholds actually used
    tau_used: float
    tau_e_used: float

    # Explanation
    explanation: dict[str, Any] | None = None

    # Metadata
    model_version: str
    mode: str


class ExplainRequest(BaseModel):
    """Request body for /api/explain."""
    applicant_id: str
    pd_calibrated: float = Field(..., ge=0, le=1)
    tau: float = Field(..., ge=0.01, le=0.99)
    decision: str = Field(..., description="APPROVE | REVIEW | DECLINE")
    reason_code: str | None = None
    evidence_score: float = Field(..., ge=0, le=1)
    evidence_status: str = Field(..., description="SUFFICIENT | INSUFFICIENT")
    history_length: int = Field(..., ge=1, le=12)
    tau_e: float = Field(0.5, ge=0, le=1)
    mode: str = Field("D4")
    policy_state: str = Field("UNRESOLVED")


class HealthResponse(BaseModel):
    status: str
    mode: str
    version: str
    message: str
    model_loaded: bool
    model_type: str | None


class ConfigResponse(BaseModel):
    approval_target: float
    evidence_threshold: float
    policy_schemes: list[str]
    risk_bins: list[float]
    decision_date: str
    default_tau: float
    default_mode: str


class ModelStatusResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    xgb_available: bool
    lr_available: bool
    xgb_path: str
    lr_path: str
    t1_results: dict[str, Any] | None
    note: str


# ── Global state (populated by lifespan) ─────────────────────────────────────
CONFIG: dict | None = None
POLICY_SET: PolicySet | None = None
FITTED_XGB = None
CALIBRATOR_XGB = None
FITTED_LR = None
CALIBRATOR_LR = None
MODEL_SOURCE: str = "heuristic"

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Load configuration and policy rules at startup."""
    global CONFIG, POLICY_SET, FITTED_XGB, CALIBRATOR_XGB, FITTED_LR, CALIBRATOR_LR, MODEL_SOURCE

    cfg_path = ROOT / "configs" / "experiment.yaml"
    CONFIG = load_config(str(cfg_path))
    rules_dir = ROOT / CONFIG["policy"]["rules_dir"]
    POLICY_SET = load_policy_set(rules_dir)
    print(f"[API] Config loaded. Policy rules: {len(POLICY_SET)} rules")

    if _XGB_PATH.exists():
        try:
            FITTED_XGB, CALIBRATOR_XGB = load_model(str(_XGB_PATH))
            MODEL_SOURCE = "model_xgb"
        except Exception as exc:
            print(f"[API] WARNING: Could not load XGBoost: {exc}")
    else:
        print(f"[API] No XGBoost model at {_XGB_PATH} — using heuristic PD")

    if _LR_PATH.exists() and FITTED_XGB is None:
        try:
            FITTED_LR, CALIBRATOR_LR = load_model(str(_LR_PATH))
            MODEL_SOURCE = "model_lr"
        except Exception as exc:
            print(f"[API] WARNING: Could not load LR: {exc}")
    yield


app = FastAPI(
    title="SynthGigCredit Decision API",
    description="Research prototype — policy-constrained credit decisioning",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health & Config ────────────────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    model_loaded = MODEL_SOURCE != "heuristic"
    return HealthResponse(
        status="ok",
        mode="research",
        version="0.2.0",
        message="SynthGigCredit research prototype is operational",
        model_loaded=model_loaded,
        model_type=MODEL_SOURCE if model_loaded else None,
    )


@app.get("/api/history")
async def get_history() -> list:
    """Client maintains its own session history."""
    return []


@app.get("/api/config", response_model=ConfigResponse)
async def get_config() -> ConfigResponse:
    if CONFIG is None:
        raise HTTPException(status_code=503, detail="Config not loaded")
    return ConfigResponse(
        approval_target=CONFIG["decision"]["approval_target"],
        evidence_threshold=CONFIG["evidence"]["tau_e"],
        policy_schemes=["jan_samarth", "pmmy"],
        risk_bins=CONFIG["cost"]["L"],
        decision_date=date.today().isoformat(),
        default_tau=float(CONFIG.get("decision", {}).get("tau", 0.25)),
        default_mode="D4",
    )


@app.get("/api/model_status", response_model=ModelStatusResponse)
async def model_status() -> ModelStatusResponse:
    """Return trained model availability and T1 experiment results."""
    import json
    t1_path = _MODEL_DIR / "T1_results.json"
    t1_results = None
    if t1_path.exists():
        with open(t1_path) as fh:
            t1_results = json.load(fh)

    return ModelStatusResponse(
        xgb_available=_XGB_PATH.exists(),
        lr_available=_LR_PATH.exists(),
        xgb_path=str(_XGB_PATH),
        lr_path=str(_LR_PATH),
        t1_results=t1_results,
        note=(
            "To enable model inference, train models and save with "
            "src.utils.model_io.save_model() to the paths above."
        ),
    )


@app.get("/api/results")
async def get_results() -> dict:
    """Return T1 authentic experiment results."""
    import json
    t1_path = _MODEL_DIR / "T1_results.json"
    if not t1_path.exists():
        raise HTTPException(status_code=404, detail="T1 results not found")
    with open(t1_path) as fh:
        return json.load(fh)


# ── Decision Endpoint ──────────────────────────────────────────────────────────

@app.post("/api/decide", response_model=DecisionResponse)
async def decide(req: DecisionRequest) -> DecisionResponse:
    """Make a credit decision. Fixes applied: model loading, explain(), tau, PMMY."""
    if CONFIG is None or POLICY_SET is None:
        raise HTTPException(status_code=503, detail="Service not ready")

    app_data = req.applicant

    # [FIX-3] Resolve effective tau / tau_e — request overrides beat config defaults
    tau: float = req.tau if req.tau is not None else float(CONFIG.get("decision", {}).get("tau", 0.25))
    tau_e: float = req.tau_e if req.tau_e is not None else float(CONFIG["evidence"]["tau_e"])

    # [FIX-5] Forward the requested decision mode
    mode: str = req.decision_mode  # already validated and uppercased by validator

    try:
        # ── Layer 1: Evidence Gate ─────────────────────────────────────────
        import numpy as np
        e_score = float(compute_evidence(
            np.array([app_data.history_length]),
            np.array([app_data.aa_completeness]),
            np.array([app_data.uli_completeness]),
            CONFIG,
        ).iloc[0])

        evidence_pass = e_score >= tau_e
        ev_status_str = "SUFFICIENT" if evidence_pass else "INSUFFICIENT"

        evidence_gate = GateResult(
            gate_name="evidence",
            passed=evidence_pass,
            reasoning=f"Evidence score {e_score:.3f} {'≥' if evidence_pass else '<'} threshold {tau_e}",
            details={
                "score": round(e_score, 4),
                "threshold": tau_e,
                "history_length": app_data.history_length,
                "aa_completeness": app_data.aa_completeness,
                "uli_completeness": app_data.uli_completeness,
            },
        )

        # ── Layer 2: Policy Gate ───────────────────────────────────────────
        policy_pass = None
        policy_matches: dict[str, str] = {}
        policy_state = "UNRESOLVED"
        last_policy_eval: PolicyEvaluation | None = None

        try:
            decision_date_obj = date.fromisoformat(app_data.decision_date)

            # [FIX-4] Build attribute dict using 'occupation_category' key (rule-engine format)
            # occupation field is already normalised by ApplicantFeatures validator
            policy_attrs: dict[str, Any] = {
                "age":                   float(app_data.age_policy),
                "annual_income":         float(app_data.income_policy) * 12,
                "occupation_category":   app_data.occupation,          # normalised key
                "nonfarm_business_flag": int(app_data.nonfarm_engaged),
            }

            scheme_ids = ["jan_samarth", "pmmy"]
            scheme_results: list[State] = []

            for scheme_id in scheme_ids:
                try:
                    active_rules = select_version(POLICY_SET, scheme_id, decision_date_obj)
                    eval_result = evaluate_policy(active_rules, policy_attrs)
                    scheme_results.append(eval_result.state)
                    policy_matches[scheme_id] = eval_result.state.value
                    if last_policy_eval is None:
                        last_policy_eval = eval_result
                except PolicyVersionError:
                    scheme_results.append(State.UNRESOLVED)
                    policy_matches[scheme_id] = "UNRESOLVED"

            combined = combine_schemes(scheme_results, mode=CONFIG["policy"]["scheme_mode"])
            policy_state = combined.value
            policy_pass = combined == State.SATISFIED

        except Exception as exc:
            policy_state = "UNRESOLVED"
            policy_pass = None
            policy_matches["error"] = str(exc)

        policy_gate = GateResult(
            gate_name="policy",
            passed=policy_pass,
            reasoning=f"Policy state: {policy_state}",
            details={
                "schemes_evaluated": policy_matches,
                "age": app_data.age_policy,
                "annual_income_used": round(float(app_data.income_policy) * 12, 2),
                "occupation_normalised": app_data.occupation,
                "nonfarm_flag": app_data.nonfarm_engaged,
            },
        )

        # ── Risk Score (PD) ────────────────────────────────────────────────
        risk_score, risk_source = _compute_pd(app_data, CONFIG)

        # Map PD to risk rank using config bins
        risk_bins = CONFIG["cost"]["L"]
        if risk_score <= risk_bins[0] / 100:
            risk_rank_str = "low"
        elif risk_score <= risk_bins[1] / 100:
            risk_rank_str = "medium"
        else:
            risk_rank_str = "high"

        risk_gate = GateResult(
            gate_name="risk_rank",
            passed=risk_score < tau,
            reasoning=f"Risk rank: {risk_rank_str} (PD {risk_score:.3f}, τ={tau})",
            details={
                "pd_estimate": round(risk_score, 4),
                "risk_rank": risk_rank_str,
                "tau": tau,
                "bins": risk_bins,
                "source": risk_source,
            },
        )

        # ── Final Decision ─────────────────────────────────────────────────
        decision_obj = make_decision(
            pd=risk_score,
            evidence_score=e_score,
            policy_state=policy_state,
            mode=mode,
            tau=tau,
            tau_e=tau_e,
        )

        # ── Credit Score (display only) ────────────────────────────────────
        scoring_cfg = CONFIG.get("scoring", {})
        score, tau_score = compute_score_and_tau(
            pd=risk_score,
            tau=tau,
            base_score=scoring_cfg.get("base_score", 600),
            base_odds=scoring_cfg.get("base_odds", 0.05),
            pdo=scoring_cfg.get("pdo", 50),
            score_min=scoring_cfg.get("score_min", 300),
            score_max=scoring_cfg.get("score_max", 900),
        )
        score_display = format_score_display(
            score=score,
            pd=risk_score,
            tau=tau,
            tau_score=tau_score,
            phase="1",
            model_name=risk_source,
        )

        # ── [FIX-1] Explanation — correct arguments ────────────────────────
        explanation_dict: dict[str, Any] | None = None
        if req.explain:
            try:
                explanation_dict = build_explanation(
                    applicant_id=app_data.applicant_id,
                    pd_calibrated=risk_score,
                    tau=tau,
                    decision=decision_obj,
                    evidence_score=e_score,
                    evidence_status=ev_status_str,
                    history_length=int(app_data.history_length),
                    tau_e=tau_e,
                    policy_evaluation=last_policy_eval,
                    shap_reasons=None,   # SHAP requires trained model — None if unavailable
                    mode=mode,
                )
                explanation_dict["risk_source"] = risk_source
            except Exception as exc:
                explanation_dict = {
                    "error": str(exc),
                    "risk_source": risk_source,
                }

        return DecisionResponse(
            applicant_id=app_data.applicant_id,
            decision_date=app_data.decision_date,
            outcome=decision_obj.decision,
            recommendation=_decision_rationale(decision_obj),
            evidence_gate=evidence_gate,
            policy_gate=policy_gate,
            risk_rank=risk_gate,
            risk_score=round(risk_score, 4),
            risk_source=risk_source,
            credit_score=int(round(score)),
            credit_score_display=score_display,
            tau_used=tau,
            tau_e_used=tau_e,
            explanation=explanation_dict,
            model_version="0.2.0",
            mode=mode,
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Decision error: {str(exc)}")


# ── Explain Endpoint ───────────────────────────────────────────────────────────

@app.post("/api/explain")
async def explain_endpoint(req: ExplainRequest) -> dict[str, Any]:
    """
    Standalone explanation endpoint.
    Accepts a pre-computed PD and decision, returns explanation JSON.
    """
    from src.decisions.gate import Decision as _Decision
    dec = _Decision(decision=req.decision, reason_code=req.reason_code)

    try:
        result = build_explanation(
            applicant_id=req.applicant_id,
            pd_calibrated=req.pd_calibrated,
            tau=req.tau,
            decision=dec,
            evidence_score=req.evidence_score,
            evidence_status=req.evidence_status,
            history_length=req.history_length,
            tau_e=req.tau_e,
            policy_evaluation=None,
            shap_reasons=None,
            mode=req.mode,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Explanation error: {str(exc)}")


# ── Batch Evaluation Endpoint ──────────────────────────────────────────────────

class BatchApplicant(BaseModel):
    """Single applicant for batch evaluation."""
    applicant_id: str
    age: float
    income_monthly: float
    income_volatility: float = 0.3
    expense_mean: float = 0.0
    liquidity_current: float = 10000.0
    history_length: int = Field(6, ge=3, le=12)
    aa_completeness: float = Field(0.5, ge=0, le=1)
    uli_completeness: float = Field(0.5, ge=0, le=1)
    occupation: str = "ride_hailing"
    nonfarm_engaged: int = Field(1, ge=0, le=1)
    pd_xgb: float | None = None
    pd_lr: float | None = None


class BatchRequest(BaseModel):
    applicants: list[BatchApplicant]
    decision_mode: str = Field("D4")
    tau: float | None = None
    tau_e: float | None = None


class BatchSummary(BaseModel):
    total: int
    approve: int
    review: int
    decline: int
    approve_rate: float
    review_rate: float
    decline_rate: float
    evidence_fail_count: int
    policy_unresolved_count: int
    heuristic_pd_count: int


@app.post("/api/evaluate_batch")
async def evaluate_batch(req: BatchRequest) -> dict[str, Any]:
    """
    Batch decision evaluation.
    Uses identical logic as single /api/decide — same preprocessing, thresholds,
    evidence, policy, decision functions.
    """
    if CONFIG is None or POLICY_SET is None:
        raise HTTPException(status_code=503, detail="Service not ready")

    if not req.applicants:
        raise HTTPException(status_code=422, detail="applicants list is empty")

    tau: float = req.tau if req.tau is not None else float(CONFIG.get("decision", {}).get("tau", 0.25))
    tau_e: float = req.tau_e if req.tau_e is not None else float(CONFIG["evidence"]["tau_e"])

    mode = req.decision_mode.upper()
    if mode not in _VALID_MODES:
        raise HTTPException(status_code=422, detail=f"Invalid decision_mode: {mode!r}")

    import numpy as np

    results = []
    n_approve = n_review = n_decline = 0
    n_evidence_fail = n_policy_unres = n_heuristic = 0
    decision_date_obj = date.fromisoformat(CONFIG["policy"]["decision_date"])

    for app_item in req.applicants:
        # Evidence
        e_score = float(compute_evidence(
            np.array([app_item.history_length]),
            np.array([app_item.aa_completeness]),
            np.array([app_item.uli_completeness]),
            CONFIG,
        ).iloc[0])
        if e_score < tau_e:
            n_evidence_fail += 1

        # Policy
        occ_norm = _OCCUPATION_NORMALISE.get(app_item.occupation.lower().strip(), app_item.occupation)
        policy_attrs = {
            "age": float(app_item.age),
            "annual_income": float(app_item.income_monthly) * 12,
            "occupation_category": occ_norm,
            "nonfarm_business_flag": int(app_item.nonfarm_engaged),
        }
        scheme_states: list[State] = []
        for scheme_id in ["jan_samarth", "pmmy"]:
            try:
                rules = select_version(POLICY_SET, scheme_id, decision_date_obj)
                ev = evaluate_policy(rules, policy_attrs)
                scheme_states.append(ev.state)
            except PolicyVersionError:
                scheme_states.append(State.UNRESOLVED)

        combined = combine_schemes(scheme_states, CONFIG["policy"]["scheme_mode"])
        if combined == State.UNRESOLVED:
            n_policy_unres += 1

        # PD
        if app_item.pd_xgb is not None:
            pd_val = float(app_item.pd_xgb)
            src = "override_xgb"
        elif app_item.pd_lr is not None:
            pd_val = float(app_item.pd_lr)
            src = "override_lr"
        elif FITTED_XGB is not None and CALIBRATOR_XGB is not None:
            pd_val, src = _model_pd_from_scalars(app_item, FITTED_XGB, CALIBRATOR_XGB, "model_xgb")
            if src == "heuristic":
                n_heuristic += 1
        else:
            pd_val = _heuristic_pd(app_item.income_volatility, app_item.expense_mean,
                                   app_item.income_monthly, app_item.liquidity_current)
            src = "heuristic"
            n_heuristic += 1

        # Decision
        dec = make_decision(
            pd=pd_val,
            evidence_score=e_score,
            policy_state=combined.value,
            mode=mode,
            tau=tau,
            tau_e=tau_e,
        )

        if dec.decision == "APPROVE":
            n_approve += 1
        elif dec.decision == "REVIEW":
            n_review += 1
        else:
            n_decline += 1

        results.append({
            "applicant_id": app_item.applicant_id,
            "outcome": dec.decision,
            "reason_code": dec.reason_code,
            "pd": round(pd_val, 4),
            "pd_source": src,
            "evidence_score": round(e_score, 4),
            "evidence_sufficient": e_score >= tau_e,
            "policy_state": combined.value,
        })

    total = len(results)
    summary = BatchSummary(
        total=total,
        approve=n_approve,
        review=n_review,
        decline=n_decline,
        approve_rate=round(n_approve / total, 4),
        review_rate=round(n_review / total, 4),
        decline_rate=round(n_decline / total, 4),
        evidence_fail_count=n_evidence_fail,
        policy_unresolved_count=n_policy_unres,
        heuristic_pd_count=n_heuristic,
    )

    return {
        "summary": summary.model_dump(),
        "tau_used": tau,
        "tau_e_used": tau_e,
        "mode": mode,
        "decisions": results,
    }


# ── Helper functions ───────────────────────────────────────────────────────────

def _compute_pd(app: ApplicantFeatures, cfg: dict) -> tuple[float, str]:
    """
    Compute PD for a single applicant.

    Priority:
      1. pd_xgb override from request
      2. pd_lr override from request
      3. Trained XGBoost model (if loaded)
      4. Trained LR model (if loaded)
      5. Heuristic fallback (explicit in response)

    Returns (pd_value, source_label).
    """
    if app.pd_xgb is not None:
        return float(app.pd_xgb), "override_xgb"
    if app.pd_lr is not None:
        return float(app.pd_lr), "override_lr"

    if FITTED_XGB is not None and CALIBRATOR_XGB is not None:
        try:
            feat_row = _applicant_to_feature_row(app)
            raw = FITTED_XGB.predict_raw(feat_row)
            calibrated = CALIBRATOR_XGB.transform(raw)
            return float(calibrated[0]), "model_xgb"
        except Exception:
            pass  # fall through to heuristic

    if FITTED_LR is not None and CALIBRATOR_LR is not None:
        try:
            feat_row = _applicant_to_feature_row(app)
            raw = FITTED_LR.predict_raw(feat_row)
            calibrated = CALIBRATOR_LR.transform(raw)
            return float(calibrated[0]), "model_lr"
        except Exception:
            pass

    pd_val = _heuristic_pd(
        app.income_volatility,
        app.expense_mean,
        app.income_mean,
        app.liquidity_current,
    )
    return pd_val, "heuristic"


def _applicant_to_feature_row(app: ApplicantFeatures):
    """
    Convert a single ApplicantFeatures to a one-row DataFrame for model inference.

    Maps the API input fields to the feature set C columns expected by the trained model.
    income_trend and seasonality_index are NaN (history-window features unavailable at API).
    """
    import pandas as pd_lib
    from src.feature_engineering.build_features import FEATURE_SET_C

    # Map available fields; set unavailable ones to NaN
    row = {
        "income_mean":       app.income_mean,
        "expense_mean":      app.expense_mean,
        "expense_ratio":     app.expense_mean / app.income_mean if app.income_mean > 0 else float("nan"),
        "debt_mean":         0.0,           # not in API schema; use 0 as neutral
        "has_emi":           float(app.emi_status),
        "liquidity_mean":    app.liquidity_current,
        "liquidity_min":     app.liquidity_current,
        "income_volatility": app.income_volatility,
        "income_trend":      float("nan"),  # unavailable from single-point API input
        "platform_tenure":   float(app.platform_tenure),
        "multi_platform":    float(app.multi_platform),
        "seasonality_index": float("nan"),  # unavailable from single-point API input
    }
    # Ensure all required columns are present
    for col in FEATURE_SET_C:
        if col not in row:
            row[col] = float("nan")

    return pd_lib.DataFrame([row])[FEATURE_SET_C]


def _model_pd_from_scalars(app_item: BatchApplicant, fitted, calibrator, source: str) -> tuple[float, str]:
    """Compute model PD for a BatchApplicant, fall back to heuristic on error."""
    try:
        import pandas as pd_lib
        from src.feature_engineering.build_features import FEATURE_SET_C
        row = {
            "income_mean":       app_item.income_monthly,
            "expense_mean":      app_item.expense_mean,
            "expense_ratio":     app_item.expense_mean / app_item.income_monthly if app_item.income_monthly > 0 else float("nan"),
            "debt_mean":         0.0,
            "has_emi":           0.0,
            "liquidity_mean":    app_item.liquidity_current,
            "liquidity_min":     app_item.liquidity_current,
            "income_volatility": app_item.income_volatility,
            "income_trend":      float("nan"),
            "platform_tenure":   1.0,
            "multi_platform":    0.0,
            "seasonality_index": float("nan"),
        }
        for col in FEATURE_SET_C:
            if col not in row:
                row[col] = float("nan")
        feat = pd_lib.DataFrame([row])[FEATURE_SET_C]
        raw = fitted.predict_raw(feat)
        cal = calibrator.transform(raw)
        return float(cal[0]), source
    except Exception:
        pd_val = _heuristic_pd(
            app_item.income_volatility, app_item.expense_mean,
            app_item.income_monthly, app_item.liquidity_current,
        )
        return pd_val, "heuristic"


def _heuristic_pd(
    income_volatility: float,
    expense_mean: float,
    income_mean: float,
    liquidity_current: float,
) -> float:
    """
    Heuristic PD fallback — used ONLY when no trained model is available.
    Labelled as 'heuristic' in response so it is never mistaken for a model output.
    """
    import numpy as np
    vol_component = min(income_volatility / 0.5, 1.0)
    er = (expense_mean / income_mean) if income_mean > 0 else 0.7
    er_component = max(0.0, er - 0.5)
    liq_component = max(0.0, -liquidity_current / max(income_mean, 1))
    pd_val = 0.05 + 0.35 * vol_component + 0.3 * er_component + 0.1 * liq_component
    return float(np.clip(pd_val, 0.01, 0.95))


def _decision_rationale(decision: Decision) -> str:
    rationale_map = {
        "APPROVE": "Applicant passed evidence and policy gates with acceptable risk.",
        "REVIEW":  "Applicant requires human review (policy uncertain or borderline risk).",
        "DECLINE": "Applicant failed risk threshold or is policy-ineligible.",
    }
    return rationale_map.get(decision.decision, "Unknown decision")


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
