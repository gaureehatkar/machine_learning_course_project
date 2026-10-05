"""
Explanation output module (ARCHITECTURE Diagram 10)

Produces the explanation JSON interface:
{
  "applicant_id": "...",
  "mode": "D4",
  "pd": 0.13,
  "tau": 0.21,
  "decision": "REVIEW",
  "reason_codes": ["EVIDENCE_INSUFFICIENT"],
  "risk_reasons": [{"feature": "liquidity_min", "shap": 0.04}],
  "evidence": {"score": 0.41, "threshold": 0.5, "status": "INSUFFICIENT", "history_length": 6},
  "policy": {"state": "SATISFIED", "version": "<UNVERIFIED>", "rule_results": [], "sources": []}
}

Module contract:
  explain(applicant_id, ...) -> dict (explanation JSON)
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.decisions.gate import Decision
from src.policy.rule_engine import PolicyEvaluation


def explain(
    applicant_id: str,
    pd_calibrated: float,
    tau: float,
    decision: Decision,
    evidence_score: float,
    evidence_status: str,
    history_length: int,
    tau_e: float,
    policy_evaluation: PolicyEvaluation | None,
    shap_reasons: list[dict] | None = None,
    mode: str = "D4",
) -> dict[str, Any]:
    """
    Build the explanation JSON for one applicant.

    Parameters
    ----------
    applicant_id       : applicant identifier
    pd_calibrated      : calibrated probability of default
    tau                : PD decision threshold
    decision           : Decision object from gate.py
    evidence_score     : E_i ∈ [0, 1]
    evidence_status    : "SUFFICIENT" | "INSUFFICIENT"
    history_length     : H_i in months
    tau_e              : evidence threshold (0.5)
    policy_evaluation  : PolicyEvaluation from rule_engine.py (or None)
    shap_reasons       : list of {feature, shap, value} from explain.py
    mode               : D1 | D2 | D3 | D4

    Returns
    -------
    dict — explanation JSON (interface spec from ARCHITECTURE §12, Diagram 10)
    """
    result: dict[str, Any] = {
        "applicant_id": applicant_id,
        "mode": mode,
        "pd": round(float(pd_calibrated), 4),
        "tau": round(float(tau), 4),
        "decision": decision.decision,
        "reason_codes": [decision.reason_code] if decision.reason_code else [],
        "risk_reasons": shap_reasons or [],
        "evidence": {
            "score": round(float(evidence_score), 4),
            "threshold": float(tau_e),
            "status": evidence_status,
            "history_length": int(history_length),
        },
        "policy": _format_policy(policy_evaluation),
    }
    return result


def _format_policy(pe: PolicyEvaluation | None) -> dict:
    if pe is None:
        return {
            "state": "UNRESOLVED",
            "version": "N/A",
            "rule_results": [],
            "sources": [],
        }
    return {
        "state": pe.state.value,
        # UNVERIFIED until Task 10b
        "version": f"{pe.policy_version} (UNVERIFIED until Task 10b)",
        "effective_from": pe.effective_from,
        "effective_to": pe.effective_to,
        "rule_results": [
            {
                "rule_id": rr.rule_id,
                "group": rr.group,
                "state": rr.state.value,
                "reason_code": rr.reason_code,
            }
            for rr in pe.rule_results
        ],
        "sources": pe.provenance,
    }
