"""
FastAPI Backend — SynthGigCredit Research Prototype

Endpoints:
  POST /api/decide — accept DecisionRequest (26 fields), return DecisionResponse
  GET /api/health — service status
  GET /api/config — configuration endpoints and thresholds

Usage:
  uvicorn app.api.main:app --host 0.0.0.0 --port 8000
  
Design:
  - Accepts 26 applicant features (income, history_length, evidence scores, etc.)
  - Returns 3-layer decision (evidence gate → policy gate → risk rank)
  - Includes explanation JSON (feature importance, policy rule matches, risk factors)
  - Research prototype only; no production deployment
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import uvicorn

# Add project root to path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.config_loader import load_config, get_output_dir
from src.evidence.compute_evidence import compute_evidence, evidence_status
from src.policy.rule_loader import load_policy_set, PolicySet
from src.policy.rule_engine import evaluate_policy, combine_schemes
from src.policy.versioning import select_version
from src.policy.kleene import State, PolicyVersionError
from src.decisions.gate import make_decision, Decision
from src.decisions.tau import select_tau
from src.scoring.credit_score import compute_score_and_tau, format_score_display
from src.explainability.explain import explain


# ── Pydantic models ───────────────────────────────────────────────────────────

class ApplicantFeatures(BaseModel):
    """26 applicant input features for credit decision."""
    
    # Identity & Demographics (3)
    age: int = Field(..., ge=18, le=65, description="Age in years")
    platform_tenure: int = Field(..., ge=1, le=24, description="Months on platform")
    e_shram_registered: int = Field(..., ge=0, le=1, description="e-Shram registration (0/1)")
    
    # Income & Stability (4)
    income_mean: float = Field(..., gt=0, description="Average monthly income (₹)")
    income_volatility: float = Field(..., ge=0, description="Income CV (dimensionless)")
    expense_mean: float = Field(..., ge=0, description="Average monthly expense (₹)")
    liquidity_current: float = Field(..., description="Liquidity L_t at cutoff (arbitrary units)")
    
    # Employment History (3)
    history_length: int = Field(..., ge=3, le=12, description="Months of history (3/6/9/12)")
    multi_platform: int = Field(..., ge=0, le=1, description="Multi-platform worker (0/1)")
    emi_status: int = Field(..., ge=0, le=1, description="EMI holder (0/1)")
    
    # Data Quality (Completeness) — Evidence inputs (2)
    aa_completeness: float = Field(..., ge=0, le=1, description="AA data completeness (0-1)")
    uli_completeness: float = Field(..., ge=0, le=1, description="ULI data completeness (0-1)")
    
    # Policy Attributes (5) — for policy gate evaluation
    age_policy: int = Field(..., ge=18, le=65, description="Age for policy (same as age)")
    income_policy: float = Field(..., gt=0, description="Income for policy (same as income_mean)")
    occupation: str = Field(..., description="Occupation code (e.g., ride_hailing)")
    nonfarm_engaged: int = Field(..., ge=0, le=1, description="Non-farm income (0/1)")
    e_shram_policy: int = Field(..., ge=0, le=1, description="e-Shram for policy (0/1)")
    
    # Model Predictions (2) — placeholder; will be computed from features
    # (The backend will call trained model; these are for manual override if needed)
    pd_lr: float | None = Field(None, ge=0, le=1, description="LR PD estimate (optional)")
    pd_xgb: float | None = Field(None, ge=0, le=1, description="XGBoost PD estimate (optional)")
    
    # Metadata (2)
    applicant_id: str = Field(..., description="Unique applicant identifier")
    decision_date: str = Field(default_factory=lambda: date.today().isoformat(), 
                               description="Decision date (YYYY-MM-DD)")


class DecisionRequest(BaseModel):
    """Request body for credit decision endpoint."""
    applicant: ApplicantFeatures
    decision_mode: str = Field("production", description="production | diagnostic")
    explain: bool = Field(True, description="Include explanation JSON")


class GateResult(BaseModel):
    """Result from a single gate (evidence, policy, or risk)."""
    gate_name: str
    passed: bool | None  # None if gate is skipped or uncertain
    reasoning: str
    details: dict[str, Any] = Field(default_factory=dict)


class DecisionResponse(BaseModel):
    """Response body for credit decision endpoint."""
    model_config = {"protected_namespaces": ()}

    applicant_id: str
    decision_date: str
    
    # 3-layer decision
    outcome: str  # APPROVE | REVIEW | DECLINE
    recommendation: str  # Why this outcome?
    
    # Gates trace
    evidence_gate: GateResult
    policy_gate: GateResult
    risk_rank: GateResult
    
    # Risk score (PD 0-1)
    risk_score: float
    
    # Credit score (derived, for display only)
    credit_score: int
    credit_score_display: dict[str, Any]  # Formatted for UI
    
    # Explanation (optional)
    explanation: dict[str, Any] | None = None
    
    # Metadata
    model_version: str
    mode: str  # production | diagnostic


class HealthResponse(BaseModel):
    """Health check response."""
    status: str  # ok | degraded | error
    mode: str  # research
    version: str
    message: str


class ConfigResponse(BaseModel):
    """Configuration and thresholds."""
    approval_target: float
    evidence_threshold: float
    policy_schemes: list[str]
    risk_bins: list[float]
    decision_date: str


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="SynthGigCredit Decision API",
    description="Research prototype for policy-constrained credit decisioning",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load config once at startup
CONFIG = None
POLICY_SET = None


@app.on_event("startup")
async def startup_event():
    """Load configuration and policy rules at startup."""
    global CONFIG, POLICY_SET
    cfg_path = ROOT / "configs" / "experiment.yaml"
    CONFIG = load_config(str(cfg_path))
    rules_dir = ROOT / CONFIG["policy"]["rules_dir"]
    POLICY_SET = load_policy_set(rules_dir)
    print(f"[API] Loaded config from {cfg_path}")
    print(f"[API] Loaded {len(POLICY_SET)} policy rules")


# ── Health & Config Endpoints ──────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Service health check."""
    return HealthResponse(
        status="ok",
        mode="research",
        version="0.1.0",
        message="SynthGigCredit research prototype is operational"
    )


@app.get("/api/history")
async def get_history() -> list:
    """Return empty decision history (client maintains its own session history)."""
    return []


@app.get("/api/config", response_model=ConfigResponse)
async def get_config() -> ConfigResponse:
    """Return current configuration."""
    if CONFIG is None:
        raise HTTPException(status_code=503, detail="Config not loaded")
    
    return ConfigResponse(
        approval_target=CONFIG["decision"]["approval_target"],
        evidence_threshold=CONFIG["evidence"]["tau_e"],
        policy_schemes=list(POLICY_SET.keys()) if POLICY_SET else [],
        risk_bins=CONFIG["cost"]["L"],
        decision_date=date.today().isoformat()
    )


# ── Decision Endpoint ──────────────────────────────────────────────────────────

@app.post("/api/decide", response_model=DecisionResponse)
async def decide(req: DecisionRequest) -> DecisionResponse:
    """
    Make a credit decision on an applicant.
    
    Accepts 26 applicant features, returns 3-layer decision + explanation.
    """
    if CONFIG is None or POLICY_SET is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    app_data = req.applicant
    
    try:
        # ── Layer 1: Evidence Gate ─────────────────────────────────────────
        e_score = float(compute_evidence(
            app_data.history_length,
            app_data.aa_completeness,
            app_data.uli_completeness,
            CONFIG,
        ).item())
        tau_e = CONFIG["evidence"]["tau_e"]
        evidence_pass = e_score >= tau_e
        
        evidence_gate = GateResult(
            gate_name="evidence",
            passed=evidence_pass,
            reasoning=f"Evidence score {e_score:.3f} {'≥' if evidence_pass else '<'} threshold {tau_e}",
            details={
                "score": round(e_score, 3),
                "threshold": tau_e,
                "history_length": app_data.history_length,
                "aa_completeness": app_data.aa_completeness,
                "uli_completeness": app_data.uli_completeness,
            }
        )
        
        # ── Layer 2: Policy Gate ───────────────────────────────────────────
        policy_pass = None
        policy_matches = {}
        policy_state = "UNRESOLVED"  # default

        if evidence_pass:
            try:
                decision_date_obj = date.fromisoformat(app_data.decision_date)
                # Evaluate each policy scheme by ID
                scheme_ids = ["jan_samarth", "pmmy"]
                scheme_results: list[State] = []
                for scheme_id in scheme_ids:
                    try:
                        active_rules = select_version(POLICY_SET, scheme_id, decision_date_obj)
                        eval_result = evaluate_policy(active_rules, app_data.__dict__)
                        scheme_results.append(eval_result.state)
                        policy_matches[scheme_id] = eval_result.state.value
                    except PolicyVersionError:
                        # No active rules for this scheme on this date → UNRESOLVED
                        scheme_results.append(State.UNRESOLVED)
                        policy_matches[scheme_id] = "UNRESOLVED"

                # Combine with Kleene OR (qualify under any scheme)
                combined = combine_schemes(scheme_results, mode=CONFIG["policy"]["scheme_mode"])
                policy_state = combined.value
                policy_pass = (combined == State.TRUE)
            except Exception as e:
                policy_state = "UNRESOLVED"
                policy_pass = None
                policy_matches["error"] = str(e)
        
        policy_gate = GateResult(
            gate_name="policy",
            passed=policy_pass,
            reasoning="Policy gate skipped (evidence failed)" if not evidence_pass else 
                     f"Policy state: {policy_state}",
            details={
                "schemes_evaluated": policy_matches,
                "age": app_data.age_policy,
                "income": round(app_data.income_policy, 2),
                "occupation": app_data.occupation,
            }
        )
        
        # ── Risk Score (PD estimate) ───────────────────────────────────────
        # Use provided PD if available, otherwise compute heuristic
        if app_data.pd_xgb is not None and 0 <= app_data.pd_xgb <= 1:
            risk_score = app_data.pd_xgb
        elif app_data.pd_lr is not None and 0 <= app_data.pd_lr <= 1:
            risk_score = app_data.pd_lr
        else:
            risk_score = _compute_risk_heuristic(app_data, CONFIG)
        
        # Map risk score to rank
        risk_bins = CONFIG["cost"]["L"]
        risk_rank = None
        if len(risk_bins) >= 3:
            if risk_score <= risk_bins[0]:
                risk_rank = "low"
            elif risk_score <= risk_bins[1]:
                risk_rank = "medium"
            else:
                risk_rank = "high"
        
        risk_gate = GateResult(
            gate_name="risk_rank",
            passed=risk_rank is not None,
            reasoning=f"Risk rank: {risk_rank} (PD {risk_score:.3f})",
            details={
                "pd_estimate": round(risk_score, 3),
                "risk_rank": risk_rank,
                "bins": risk_bins,
            }
        )
        
        # ── Final Decision using gating function ────────────────────────────
        # Use D4 mode (all gates enabled)
        # Threshold tau is set to match 70% approval target on validation set
        # For now use a conservative default tau = 0.4
        tau = CONFIG.get("decision", {}).get("tau", 0.4)
        
        decision_obj = make_decision(
            pd=risk_score,
            evidence_score=e_score,
            policy_state=policy_state,
            mode="D4",  # All gates enabled
            tau=tau,
            tau_e=tau_e,
        )
        
        # ── Credit Score (display only; does NOT affect decision logic) ────────
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
            model_name="heuristic" if app_data.pd_xgb is None and app_data.pd_lr is None else "model",
        )
        
        # ── Explanation ────────────────────────────────────────────────────
        explanation_dict = None
        if req.explain:
            try:
                explanation_dict = explain(
                    applicant_id=app_data.applicant_id,
                    features=app_data.dict(),
                    decision=decision_obj,
                    config=CONFIG,
                )
            except Exception as e:
                # Explanation failure should not block decision
                explanation_dict = {"error": str(e)}
        
        return DecisionResponse(
            applicant_id=app_data.applicant_id,
            decision_date=app_data.decision_date,
            outcome=decision_obj.decision,
            recommendation=_decision_rationale(decision_obj),
            evidence_gate=evidence_gate,
            policy_gate=policy_gate,
            risk_rank=risk_gate,
            risk_score=round(risk_score, 3),
            credit_score=int(round(score)),
            credit_score_display=score_display,
            explanation=explanation_dict,
            model_version="0.1.0",
            mode=req.decision_mode,
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decision error: {str(e)}")


# ── Helper functions ───────────────────────────────────────────────────────────

def _compute_risk_heuristic(app: ApplicantFeatures, cfg: dict) -> float:
    """
    Compute risk score using heuristic (before trained model is available).
    
    Returns: risk score in [0, 1]
    """
    # Simple heuristic: combine volatility, liquidity, history
    volatility_component = min(app.income_volatility / 0.5, 1.0)  # normalize by 50%
    liquidity_component = max(-app.liquidity_current / 100, 0.0)  # negative liquidity → risk
    history_component = (12 - app.history_length) / 9  # shorter history → higher risk
    
    # Average the components
    risk_score = (volatility_component * 0.4 + 
                  liquidity_component * 0.3 + 
                  history_component * 0.3)
    
    return max(0, min(risk_score, 1.0))


def _decision_rationale(decision: Decision) -> str:
    """Generate plain-English rationale for the decision."""
    rationale_map = {
        "APPROVE": "Applicant passed evidence and policy gates with acceptable risk.",
        "REVIEW": "Applicant requires human review (policy uncertain or medium risk).",
        "DECLINE": "Applicant failed evidence gate or has high risk profile.",
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
