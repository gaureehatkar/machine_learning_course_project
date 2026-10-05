"""
Decision engine tests — all D4 truth-table rows (IMPLEMENTATION_PLAN §6)
"""
import pytest

from src.decisions.gate import make_decision, APPROVE, REVIEW, DECLINE
from src.decisions.tau import select_tau
import numpy as np


TAU = 0.30
TAU_E = 0.5


class TestD4TruthTable:
    """All 5 rows of the D4 truth table (TECH_DOC §15, ARCHITECTURE Diagram 9)."""

    def test_pd_high_decline(self):
        """PD >= τ → DECLINE PD_HIGH regardless of policy/evidence."""
        d = make_decision(pd=0.35, evidence_score=0.9, policy_state="SATISFIED",
                          mode="D4", tau=TAU, tau_e=TAU_E)
        assert d.decision == DECLINE
        assert d.reason_code == "PD_HIGH"

    def test_pd_high_overrides_policy_unsat(self):
        """PD HIGH has precedence over POLICY_INELIGIBLE."""
        d = make_decision(pd=0.35, evidence_score=0.9, policy_state="UNSATISFIED",
                          mode="D4", tau=TAU, tau_e=TAU_E)
        assert d.reason_code == "PD_HIGH"

    def test_policy_unsat_decline(self):
        """PD < τ, UNSATISFIED → DECLINE POLICY_INELIGIBLE."""
        d = make_decision(pd=0.10, evidence_score=0.9, policy_state="UNSATISFIED",
                          mode="D4", tau=TAU, tau_e=TAU_E)
        assert d.decision == DECLINE
        assert d.reason_code == "POLICY_INELIGIBLE"

    def test_policy_unres_review(self):
        """PD < τ, UNRESOLVED → REVIEW POLICY_UNRESOLVED."""
        d = make_decision(pd=0.10, evidence_score=0.9, policy_state="UNRESOLVED",
                          mode="D4", tau=TAU, tau_e=TAU_E)
        assert d.decision == REVIEW
        assert d.reason_code == "POLICY_UNRESOLVED"

    def test_evidence_insufficient_review(self):
        """PD < τ, SAT, E < τ_E → REVIEW EVIDENCE_INSUFFICIENT."""
        d = make_decision(pd=0.10, evidence_score=0.3, policy_state="SATISFIED",
                          mode="D4", tau=TAU, tau_e=TAU_E)
        assert d.decision == REVIEW
        assert d.reason_code == "EVIDENCE_INSUFFICIENT"

    def test_all_clear_approve(self):
        """PD < τ, SAT, E >= τ_E → APPROVE."""
        d = make_decision(pd=0.10, evidence_score=0.8, policy_state="SATISFIED",
                          mode="D4", tau=TAU, tau_e=TAU_E)
        assert d.decision == APPROVE
        assert d.reason_code is None


class TestD1Mode:
    """D1: only PD gate (no policy, no evidence)."""

    def test_d1_approve_when_pd_low(self):
        d = make_decision(pd=0.10, evidence_score=0.0, policy_state="UNSATISFIED",
                          mode="D1", tau=TAU, tau_e=TAU_E)
        assert d.decision == APPROVE

    def test_d1_decline_when_pd_high(self):
        d = make_decision(pd=0.35, evidence_score=0.0, policy_state="SATISFIED",
                          mode="D1", tau=TAU, tau_e=TAU_E)
        assert d.decision == DECLINE


class TestD2Mode:
    """D2: PD + policy gates only."""

    def test_d2_ignores_evidence(self):
        """D2 does not gate on evidence."""
        d = make_decision(pd=0.10, evidence_score=0.0, policy_state="SATISFIED",
                          mode="D2", tau=TAU, tau_e=TAU_E)
        assert d.decision == APPROVE

    def test_d2_declines_policy_unsat(self):
        d = make_decision(pd=0.10, evidence_score=0.0, policy_state="UNSATISFIED",
                          mode="D2", tau=TAU, tau_e=TAU_E)
        assert d.decision == DECLINE


class TestD3Mode:
    """D3: PD + evidence gates only."""

    def test_d3_ignores_policy(self):
        """D3 does not gate on policy."""
        d = make_decision(pd=0.10, evidence_score=0.8, policy_state="UNSATISFIED",
                          mode="D3", tau=TAU, tau_e=TAU_E)
        assert d.decision == APPROVE

    def test_d3_reviews_low_evidence(self):
        d = make_decision(pd=0.10, evidence_score=0.3, policy_state="SATISFIED",
                          mode="D3", tau=TAU, tau_e=TAU_E)
        assert d.decision == REVIEW


class TestTauSelection:
    def test_tau_gives_target_approval_rate(self):
        """τ selection should give D1 approval ≈ 70%."""
        rng = np.random.default_rng(42)
        pd_val = rng.beta(2, 8, size=1000)  # ~20% default, mostly low PD
        tau = select_tau(pd_val, target_approval=0.70)
        approval_rate = float(np.mean(pd_val < tau))
        # Allow ±5% tolerance
        assert abs(approval_rate - 0.70) < 0.05, (
            f"Expected ~70% approval, got {approval_rate:.3f} at τ={tau:.4f}"
        )
