"""
Policy rule engine tests (IMPLEMENTATION_PLAN §6)
All fixtures are UNVERIFIED (not the real rule set).
"""
import pytest
from datetime import date

from src.policy.kleene import (
    State, kleene_and, kleene_or, kleene_not, evaluate_atom,
    AttributeValidationError, PolicyVersionError,
)
from src.policy.rule_loader import load_policy_set
from src.policy.versioning import select_version
from src.policy.rule_engine import evaluate_policy, combine_schemes, PolicyEvaluation


# ── Kleene truth tables ───────────────────────────────────────────────────────

class TestKleeneAnd:
    def test_all_satisfied(self):
        assert kleene_and(State.SATISFIED, State.SATISFIED) == State.SATISFIED

    def test_any_unsatisfied(self):
        assert kleene_and(State.SATISFIED, State.UNSATISFIED) == State.UNSATISFIED

    def test_unknown_without_false(self):
        assert kleene_and(State.SATISFIED, State.UNRESOLVED) == State.UNRESOLVED

    def test_false_dominates_unknown(self):
        assert kleene_and(State.UNSATISFIED, State.UNRESOLVED) == State.UNSATISFIED


class TestKleeneOr:
    def test_any_satisfied(self):
        assert kleene_or(State.UNSATISFIED, State.SATISFIED) == State.SATISFIED

    def test_all_unsatisfied(self):
        assert kleene_or(State.UNSATISFIED, State.UNSATISFIED) == State.UNSATISFIED

    def test_unknown_without_true(self):
        assert kleene_or(State.UNSATISFIED, State.UNRESOLVED) == State.UNRESOLVED

    def test_true_dominates_unknown(self):
        assert kleene_or(State.SATISFIED, State.UNRESOLVED) == State.SATISFIED


class TestKleeneNot:
    def test_not_satisfied(self):
        assert kleene_not(State.SATISFIED) == State.UNSATISFIED

    def test_not_unsatisfied(self):
        assert kleene_not(State.UNSATISFIED) == State.SATISFIED

    def test_not_unknown(self):
        assert kleene_not(State.UNRESOLVED) == State.UNRESOLVED


# ── Atom evaluation ───────────────────────────────────────────────────────────

def test_age_null_returns_unresolved():
    """NULL attribute → UNRESOLVED (on_missing = UNKNOWN)."""
    result = evaluate_atom(None, "BETWEEN", [18, 60])
    assert result == State.UNRESOLVED


def test_age_17_unsatisfied():
    result = evaluate_atom(17, "BETWEEN", [18, 60])
    assert result == State.UNSATISFIED


def test_age_18_satisfied():
    result = evaluate_atom(18, "BETWEEN", [18, 60])
    assert result == State.SATISFIED


def test_age_60_satisfied():
    result = evaluate_atom(60, "BETWEEN", [18, 60])
    assert result == State.SATISFIED


def test_age_61_unsatisfied():
    result = evaluate_atom(61, "BETWEEN", [18, 60])
    assert result == State.UNSATISFIED


def test_in_operator():
    result = evaluate_atom("ride_hailing", "IN", ["ride_hailing", "delivery"])
    assert result == State.SATISFIED


def test_not_in_operator():
    result = evaluate_atom("agri_labour", "NOT_IN", ["agri_labour"])
    assert result == State.UNSATISFIED


# ── Version selection ─────────────────────────────────────────────────────────

def test_no_active_version_raises():
    """No rules active at given date → PolicyVersionError."""
    policy_set = load_policy_set("configs/policy_rules")
    # Date before all rules
    with pytest.raises(PolicyVersionError):
        select_version(policy_set, "jan_samarth", date(2020, 1, 1))


def test_active_version_found():
    """Rules active at decision date are found."""
    policy_set = load_policy_set("configs/policy_rules")
    rules = select_version(policy_set, "jan_samarth", date(2026, 1, 1))
    assert len(rules) > 0


# ── Full engine evaluation ────────────────────────────────────────────────────

def test_eligible_applicant():
    """Age=30, income=500000, nonfarm=1 → SATISFIED (under UNVERIFIED fixtures)."""
    policy_set = load_policy_set("configs/policy_rules")
    rules = select_version(policy_set, "jan_samarth", date(2026, 1, 1))
    result = evaluate_policy(rules, {
        "age": 30.0,
        "annual_income": 500_000.0,
        "nonfarm_business_flag": 1,
        "occupation_category": "delivery",
    })
    assert result.state == State.SATISFIED


def test_too_young_unsatisfied():
    """Age=17 → UNSATISFIED."""
    policy_set = load_policy_set("configs/policy_rules")
    rules = select_version(policy_set, "jan_samarth", date(2026, 1, 1))
    result = evaluate_policy(rules, {
        "age": 17.0,
        "annual_income": 500_000.0,
        "nonfarm_business_flag": 1,
        "occupation_category": "delivery",
    })
    assert result.state == State.UNSATISFIED


def test_missing_age_unresolved():
    """Age=None → UNRESOLVED."""
    policy_set = load_policy_set("configs/policy_rules")
    rules = select_version(policy_set, "jan_samarth", date(2026, 1, 1))
    result = evaluate_policy(rules, {
        "age": None,
        "annual_income": 500_000.0,
        "nonfarm_business_flag": 1,
        "occupation_category": "delivery",
    })
    assert result.state == State.UNRESOLVED


def test_provenance_retained():
    """Provenance metadata is present in evaluation result."""
    policy_set = load_policy_set("configs/policy_rules")
    rules = select_version(policy_set, "jan_samarth", date(2026, 1, 1))
    result = evaluate_policy(rules, {
        "age": 30.0,
        "annual_income": 500_000.0,
        "nonfarm_business_flag": 1,
    })
    assert len(result.provenance) > 0
    for prov in result.provenance:
        assert "document_id" in prov
        assert "clause" in prov


# ── Scheme combination ────────────────────────────────────────────────────────

def test_combine_any_one_satisfied():
    """Any scheme SATISFIED → combined SATISFIED."""
    result = combine_schemes([State.SATISFIED, State.UNSATISFIED], mode="any")
    assert result == State.SATISFIED


def test_combine_all_must_be_satisfied():
    """All mode: one UNSATISFIED → UNSATISFIED."""
    result = combine_schemes([State.SATISFIED, State.UNSATISFIED], mode="all")
    assert result == State.UNSATISFIED
