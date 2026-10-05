"""
Decision engine — gating function (TECH_DOC §15, ARCHITECTURE Diagram 7)

Gating function (Experiment A — D1 through D4):

  gate(mode, PD, E, S):
    PD ≥ τ                                   → DECLINE  (PD_HIGH)
    mode ∈ {D2,D4} and S = UNSATISFIED        → DECLINE  (POLICY_INELIGIBLE)
    mode ∈ {D2,D4} and S = UNRESOLVED         → REVIEW   (POLICY_UNRESOLVED)
    mode ∈ {D3,D4} and E < τ_E               → REVIEW   (EVIDENCE_INSUFFICIENT)
    otherwise                                 → APPROVE

Precedence: PD decline > policy-UNSAT decline > review triggers > approve.
Policy is a HARD CONSTRAINT (UNSAT → DECLINE) plus review trigger (UNRES → REVIEW).

D4 truth table (D1-D3 use subsets of the gates):
  PD < τ | Policy      | E ≥ τ_E | Decision | Reason
  -------|-------------|---------|----------|---------
  no     | any         | any     | DECLINE  | PD_HIGH
  yes    | UNSATISFIED | any     | DECLINE  | POLICY_INELIGIBLE
  yes    | UNRESOLVED  | any     | REVIEW   | POLICY_UNRESOLVED
  yes    | SATISFIED   | no      | REVIEW   | EVIDENCE_INSUFFICIENT
  yes    | SATISFIED   | yes     | APPROVE  | —

Module contract (IMPLEMENTATION_PLAN §4):
  make_decision(pd, evidence_score, policy_state, mode, tau, tau_e) -> Decision
"""
from __future__ import annotations

from dataclasses import dataclass

from src.policy.kleene import State

APPROVE = "APPROVE"
REVIEW = "REVIEW"
DECLINE = "DECLINE"

REASON_PD_HIGH = "PD_HIGH"
REASON_POLICY_INELIGIBLE = "POLICY_INELIGIBLE"
REASON_POLICY_UNRESOLVED = "POLICY_UNRESOLVED"
REASON_EVIDENCE_INSUFFICIENT = "EVIDENCE_INSUFFICIENT"

VALID_MODES = {"D1", "D2", "D3", "D4"}


@dataclass
class Decision:
    decision: str          # APPROVE | REVIEW | DECLINE
    reason_code: str | None

    def is_approve(self) -> bool:
        return self.decision == APPROVE

    def is_review(self) -> bool:
        return self.decision == REVIEW

    def is_decline(self) -> bool:
        return self.decision == DECLINE

    def __repr__(self) -> str:
        return f"Decision({self.decision!r}, reason={self.reason_code!r})"


def make_decision(
    pd: float,
    evidence_score: float,
    policy_state: str | State,
    mode: str,
    tau: float,
    tau_e: float,
) -> Decision:
    """
    Apply the gating function for a single applicant.

    Parameters
    ----------
    pd            : calibrated probability of default ∈ [0, 1]
    evidence_score: E_i ∈ [0, 1]
    policy_state  : "SATISFIED" | "UNSATISFIED" | "UNRESOLVED" (or State enum)
    mode          : "D1" | "D2" | "D3" | "D4"
    tau           : PD decision threshold (selected on validation for 70% D1 approval)
    tau_e         : evidence threshold (0.5 from config)

    Returns
    -------
    Decision with decision and reason_code
    """
    assert mode in VALID_MODES, f"Unknown mode: {mode!r}"

    if isinstance(policy_state, State):
        policy_state = policy_state.value

    # Gate 1: PD ≥ τ → DECLINE (highest precedence)
    if pd >= tau:
        return Decision(DECLINE, REASON_PD_HIGH)

    # Gate 2: Policy UNSATISFIED → DECLINE (D2, D4 only)
    if mode in {"D2", "D4"} and policy_state == "UNSATISFIED":
        return Decision(DECLINE, REASON_POLICY_INELIGIBLE)

    # Gate 3: Policy UNRESOLVED → REVIEW (D2, D4 only)
    if mode in {"D2", "D4"} and policy_state == "UNRESOLVED":
        return Decision(REVIEW, REASON_POLICY_UNRESOLVED)

    # Gate 4: Evidence insufficient → REVIEW (D3, D4 only)
    if mode in {"D3", "D4"} and evidence_score < tau_e:
        return Decision(REVIEW, REASON_EVIDENCE_INSUFFICIENT)

    # All gates passed → APPROVE
    return Decision(APPROVE, None)
