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
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
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
    decision_mode: str = Field("D4", description="D1 | D2 | D3 | D4")
    explain: bool = Field(True, description="Include explanation JSON")
    tau: float | None = Field(None, ge=0, le=1, description="Optional PD threshold override")
    tau_e: float | None = Field(None, ge=0, le=1, description="Optional evidence threshold override")

    @field_validator("decision_mode", mode="before")
    @classmethod
    def normalize_decision_mode(cls, value: Any) -> str:
        # Keep the original UI labels usable while exposing the experiment modes.
        aliases = {"production": "D4", "diagnostic": "D4"}
        mode = aliases.get(str(value).lower(), str(value).upper())
        if mode not in {"D1", "D2", "D3", "D4"}:
            raise ValueError("decision_mode must be one of D1, D2, D3, or D4")
        return mode


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
    risk_source: str
    tau_used: float
    tau_e_used: float
    
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
    model_config = {"protected_namespaces": ()}

    status: str  # ok | degraded | error
    mode: str  # research
    version: str
    message: str
    model_loaded: bool


class ConfigResponse(BaseModel):
    """Configuration and thresholds."""
    approval_target: float
    evidence_threshold: float
    policy_schemes: list[str]
    risk_bins: list[float]
    decision_date: str
    default_tau: float


class ExplainRequest(BaseModel):
    applicant_id: str
    pd_calibrated: float = Field(ge=0, le=1)
    tau: float = Field(ge=0, le=1)
    decision: Literal["APPROVE", "REVIEW", "DECLINE"]
    reason_code: str | None = None
    evidence_score: float = Field(ge=0, le=1)
    evidence_status: Literal["SUFFICIENT", "INSUFFICIENT"]
    history_length: int = Field(ge=1, le=12)
    tau_e: float = Field(ge=0, le=1)
    mode: Literal["D1", "D2", "D3", "D4"] = "D4"
    policy_state: Literal["SATISFIED", "UNSATISFIED", "UNRESOLVED"] = "UNRESOLVED"


class BatchRequest(BaseModel):
    applicants: list[dict[str, Any]] = Field(min_length=1)
    decision_mode: Literal["D1", "D2", "D3", "D4"] = "D4"
    tau: float | None = Field(None, ge=0, le=1)
    tau_e: float | None = Field(None, ge=0, le=1)


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
        message="SynthGigCredit research prototype is operational; PD uses a heuristic unless supplied",
        model_loaded=False,
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
        policy_schemes=sorted({rule.policy_id for rule in POLICY_SET.rules}) if POLICY_SET else [],
        risk_bins=_risk_rank_bins(),
        decision_date=date.today().isoformat(),
        default_tau=_default_tau(),
    )


@app.get("/api/model_status")
async def model_status() -> dict[str, Any]:
    """Report model artifact availability and the saved T1 benchmark metrics."""
    result_paths = [
        ROOT / "results" / "benchmarks" / "T1_v2" / "T1_results_v2.json",
        ROOT / "results" / "authentic" / "T1_results_v2.json",
    ]
    t1_results = None
    for path in result_paths:
        if path.is_file():
            try:
                import json
                t1_results = json.loads(path.read_text(encoding="utf-8"))
                break
            except (OSError, ValueError):
                continue
    return {
        "xgb_available": False,
        "lr_available": False,
        "model_loaded": False,
        "risk_source": "heuristic",
        "t1_results": t1_results,
    }


# ── Decision Endpoint ──────────────────────────────────────────────────────────

@app.post("/api/decide", response_model=DecisionResponse)
async def decide(req: DecisionRequest) -> DecisionResponse:
    """
    Make a credit decision on an applicant.
    
    Accepts 26 applicant features, returns 3-layer decision + explanation.
    """
    if CONFIG is None or POLICY_SET is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return _decide_applicant(
        req.applicant,
        mode=req.decision_mode,
        include_explanation=req.explain,
        tau=req.tau,
        tau_e=req.tau_e,
    )


@app.post("/api/explain")
async def explain_standalone(req: ExplainRequest) -> dict[str, Any]:
    """Build an explanation from a previously computed decision and gate values."""
    decision_obj = Decision(req.decision, req.reason_code)
    result = explain(
        applicant_id=req.applicant_id,
        pd_calibrated=req.pd_calibrated,
        tau=req.tau,
        decision=decision_obj,
        evidence_score=req.evidence_score,
        evidence_status=req.evidence_status,
        history_length=req.history_length,
        tau_e=req.tau_e,
        policy_evaluation=None,
        mode=req.mode,
    )
    result["policy"]["state"] = req.policy_state
    return result


@app.post("/api/evaluate_batch")
async def evaluate_batch_endpoint(req: BatchRequest) -> dict[str, Any]:
    """Evaluate a small batch with the same decision helper used by /api/decide."""
    if CONFIG is None or POLICY_SET is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    decisions: list[dict[str, Any]] = []
    for row in req.applicants:
        applicant = _applicant_from_batch(row)
        result = _decide_applicant(
            applicant,
            mode=req.decision_mode,
            include_explanation=False,
            tau=req.tau,
            tau_e=req.tau_e,
        ).model_dump()
        result["evidence_sufficient"] = result["evidence_gate"]["passed"] is True
        decisions.append(result)

    total = len(decisions)
    counts = {
        label.lower(): sum(row["outcome"] == label for row in decisions)
        for label in ("APPROVE", "REVIEW", "DECLINE")
    }
    summary = {
        "total": total,
        **counts,
        **{f"{name}_rate": count / total for name, count in counts.items()},
    }
    return {
        "decisions": decisions,
        "summary": summary,
        "tau_used": decisions[0]["tau_used"],
        "tau_e_used": decisions[0]["tau_e_used"],
        "mode": req.decision_mode,
    }


# ── Helper functions ───────────────────────────────────────────────────────────

def _default_tau() -> float:
    return float(CONFIG.get("decision", {}).get("tau", 0.4)) if CONFIG else 0.4


def _risk_rank_bins() -> list[float]:
    return [0.10, 0.30]


def _normalise_occupation(value: str) -> str:
    occupation = "_".join(value.strip().lower().replace("-", " ").split())
    aliases = {
        "agricultural": "agri_labour",
        "agriculture": "agri_labour",
        "freelance": "freelance_services",
    }
    return aliases.get(occupation, occupation)


def _decide_applicant(
    app_data: ApplicantFeatures,
    *,
    mode: str,
    include_explanation: bool,
    tau: float | None,
    tau_e: float | None,
) -> DecisionResponse:
    """Apply the shared evidence, policy, and PD gates for one applicant."""
    if CONFIG is None or POLICY_SET is None:
        raise HTTPException(status_code=503, detail="Service not ready")

    try:
        e_score = float(compute_evidence(
            [app_data.history_length],
            [app_data.aa_completeness],
            [app_data.uli_completeness],
            CONFIG,
        ).iloc[0])
        tau_e_used = float(tau_e if tau_e is not None else CONFIG["evidence"]["tau_e"])
        tau_used = float(tau if tau is not None else _default_tau())
        evidence_pass = e_score >= tau_e_used

        evidence_active = mode in {"D3", "D4"}
        evidence_gate = GateResult(
            gate_name="evidence",
            passed=evidence_pass if evidence_active else None,
            reasoning=(
                f"Evidence score {e_score:.3f} {'≥' if evidence_pass else '<'} threshold {tau_e_used:.3f}"
                if evidence_active else f"Evidence gate skipped in {mode} mode"
            ),
            details={
                "score": round(e_score, 3),
                "threshold": tau_e_used,
                "history_length": app_data.history_length,
                "aa_completeness": app_data.aa_completeness,
                "uli_completeness": app_data.uli_completeness,
            },
        )

        occupation_normalised = _normalise_occupation(app_data.occupation)
        policy_attributes = {
            "age": app_data.age_policy,
            "annual_income": app_data.income_policy * 12,
            "occupation_category": occupation_normalised,
            "nonfarm_business_flag": app_data.nonfarm_engaged,
        }
        policy_matches: dict[str, str] = {}
        policy_evaluations = {}
        policy_states: list[State] = []
        decision_date_obj = date.fromisoformat(app_data.decision_date)
        scheme_ids = sorted({rule.policy_id for rule in POLICY_SET.rules})
        for scheme_id in scheme_ids:
            try:
                active_rules = select_version(POLICY_SET, scheme_id, decision_date_obj)
                evaluation = evaluate_policy(active_rules, policy_attributes)
                policy_evaluations[scheme_id] = evaluation
                policy_states.append(evaluation.state)
                policy_matches[scheme_id] = evaluation.state.value
            except PolicyVersionError:
                policy_states.append(State.UNRESOLVED)
                policy_matches[scheme_id] = State.UNRESOLVED.value

        combined = combine_schemes(
            policy_states,
            mode=str(CONFIG.get("policy", {}).get("scheme_mode", "any")),
        )
        policy_state = combined.value
        policy_active = mode in {"D2", "D4"}
        policy_pass = combined == State.SATISFIED
        policy_gate = GateResult(
            gate_name="policy",
            passed=policy_pass if policy_active else None,
            reasoning=(
                f"Policy state: {policy_state} (rules UNVERIFIED)"
                if policy_active else f"Policy gate skipped in {mode} mode"
            ),
            details={
                "schemes_evaluated": policy_matches,
                "policy_state": policy_state,
                "policy_rules_status": "UNVERIFIED",
                "age": app_data.age_policy,
                "income": round(app_data.income_policy, 2),
                "occupation": app_data.occupation,
                "occupation_normalised": occupation_normalised,
            },
        )

        if app_data.pd_xgb is not None:
            risk_score = float(app_data.pd_xgb)
            risk_source = "override_xgb"
        elif app_data.pd_lr is not None:
            risk_score = float(app_data.pd_lr)
            risk_source = "override_lr"
        else:
            risk_score = _compute_risk_heuristic(app_data, CONFIG)
            risk_source = "heuristic"

        rank_bins = _risk_rank_bins()
        risk_rank = "low" if risk_score < rank_bins[0] else "medium" if risk_score < rank_bins[1] else "high"
        risk_gate = GateResult(
            gate_name="risk_rank",
            passed=True,
            reasoning=f"Risk rank: {risk_rank} (PD {risk_score:.3f})",
            details={
                "pd_estimate": round(risk_score, 3),
                "risk_rank": risk_rank,
                "bins": rank_bins,
                "source": risk_source,
            },
        )

        decision_obj = make_decision(
            pd=risk_score,
            evidence_score=e_score,
            policy_state=policy_state,
            mode=mode,
            tau=tau_used,
            tau_e=tau_e_used,
        )

        scoring_cfg = CONFIG.get("scoring", {})
        score, tau_score = compute_score_and_tau(
            pd=risk_score,
            tau=tau_used,
            base_score=scoring_cfg.get("base_score", 600),
            base_odds=scoring_cfg.get("base_odds", 0.05),
            pdo=scoring_cfg.get("pdo", 50),
            score_min=scoring_cfg.get("score_min", 300),
            score_max=scoring_cfg.get("score_max", 900),
        )
        score_display = format_score_display(
            score=score,
            pd=risk_score,
            tau=tau_used,
            tau_score=tau_score,
            phase="1",
            model_name=risk_source,
        )

        explanation_dict = None
        if include_explanation:
            representative_evaluation = policy_evaluations.get("jan_samarth") or next(
                iter(policy_evaluations.values()), None
            )
            explanation_dict = explain(
                applicant_id=app_data.applicant_id,
                pd_calibrated=risk_score,
                tau=tau_used,
                decision=decision_obj,
                evidence_score=e_score,
                evidence_status="SUFFICIENT" if evidence_pass else "INSUFFICIENT",
                history_length=app_data.history_length,
                tau_e=tau_e_used,
                policy_evaluation=representative_evaluation,
                mode=mode,
            )

        return DecisionResponse(
            applicant_id=app_data.applicant_id,
            decision_date=app_data.decision_date,
            outcome=decision_obj.decision,
            recommendation=_decision_rationale(decision_obj),
            evidence_gate=evidence_gate,
            policy_gate=policy_gate,
            risk_rank=risk_gate,
            risk_score=round(risk_score, 3),
            risk_source=risk_source,
            tau_used=tau_used,
            tau_e_used=tau_e_used,
            credit_score=int(round(score)),
            credit_score_display=score_display,
            explanation=explanation_dict,
            model_version="0.1.0",
            mode=mode,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Decision error: {exc}") from exc


def _applicant_from_batch(row: dict[str, Any]) -> ApplicantFeatures:
    """Expand the compact batch schema to the full single-applicant request."""
    age = int(row.get("age", 30))
    income = float(row.get("income_monthly", row.get("income_mean", 20000)))
    history = int(row.get("history_length", 12))
    return ApplicantFeatures(
        age=age,
        platform_tenure=max(1, min(24, history)),
        e_shram_registered=int(row.get("e_shram_registered", 0)),
        income_mean=income,
        income_volatility=float(row.get("income_volatility", 0.0)),
        expense_mean=float(row.get("expense_mean", 0.0)),
        liquidity_current=float(row.get("liquidity_current", 0.0)),
        history_length=history,
        multi_platform=int(row.get("multi_platform", 0)),
        emi_status=int(row.get("emi_status", 0)),
        aa_completeness=float(row.get("aa_completeness", 0.0)),
        uli_completeness=float(row.get("uli_completeness", 0.0)),
        age_policy=int(row.get("age_policy", age)),
        income_policy=float(row.get("income_policy", income)),
        occupation=str(row.get("occupation", "unknown")),
        nonfarm_engaged=int(row.get("nonfarm_engaged", 0)),
        e_shram_policy=int(row.get("e_shram_policy", row.get("e_shram_registered", 0))),
        pd_lr=row.get("pd_lr"),
        pd_xgb=row.get("pd_xgb"),
        applicant_id=str(row.get("applicant_id", "BATCH")),
        decision_date=str(row.get("decision_date", CONFIG["policy"].get("decision_date", date.today().isoformat()))),
    )

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
