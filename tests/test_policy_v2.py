"""
Tests for Policy Rules v2, Versioning, Occupation Mapping, and Ground Truth.
(Phase 2 Task 6)
"""
from datetime import date
from pathlib import Path
import pandas as pd
import pytest

from src.policy.kleene import (
    State, kleene_and, kleene_or, kleene_not, evaluate_atom
)
from src.policy.rule_loader import PolicyRule
from src.policy.rule_loader_v2 import (
    load_v2_policy_set,
    load_occupation_mapping,
    resolve_occupation_attrs,
    evaluate_policy_v2,
)
from src.policy.rule_engine import evaluate_policy
from src.policy.versioning import select_version


# ── Kleene truth tables ───────────────────────────────────────────────────────

class TestKleeneTruthTables:
    def test_and_satisfied_satisfied(self):
        assert kleene_and(State.SATISFIED, State.SATISFIED) == State.SATISFIED

    def test_and_satisfied_unsatisfied(self):
        assert kleene_and(State.SATISFIED, State.UNSATISFIED) == State.UNSATISFIED

    def test_and_satisfied_unresolved(self):
        assert kleene_and(State.SATISFIED, State.UNRESOLVED) == State.UNRESOLVED

    def test_and_unsatisfied_unresolved(self):
        assert kleene_and(State.UNSATISFIED, State.UNRESOLVED) == State.UNSATISFIED

    def test_or_unsatisfied_satisfied(self):
        assert kleene_or(State.UNSATISFIED, State.SATISFIED) == State.SATISFIED

    def test_or_unsatisfied_unsatisfied(self):
        assert kleene_or(State.UNSATISFIED, State.UNSATISFIED) == State.UNSATISFIED

    def test_or_unsatisfied_unresolved(self):
        assert kleene_or(State.UNSATISFIED, State.UNRESOLVED) == State.UNRESOLVED

    def test_or_satisfied_unresolved(self):
        assert kleene_or(State.SATISFIED, State.UNRESOLVED) == State.SATISFIED

    def test_not_satisfied(self):
        assert kleene_not(State.SATISFIED) == State.UNSATISFIED

    def test_not_unsatisfied(self):
        assert kleene_not(State.UNSATISFIED) == State.SATISFIED

    def test_not_unresolved(self):
        assert kleene_not(State.UNRESOLVED) == State.UNRESOLVED


# ── Date versioning boundary tests ─────────────────────────────────────────────

class TestDateVersioningBoundary:
    """
    On 2024-10-23, loan ceiling was 10L.
    On 2024-10-24, loan ceiling was raised to 20L.
    """
    @pytest.fixture(autouse=True)
    def setup(self):
        self.v2_dir = Path("configs/policy_rules/v2")
        self.policy_set = load_v2_policy_set(self.v2_dir)

    def test_date_boundary_before_revision(self):
        decision_date = date(2024, 10, 23)
        rules = select_version(self.policy_set, "pmmy_v2", decision_date)
        ceiling_rules = [r for r in rules if r.group == "loan_ceiling"]
        assert len(ceiling_rules) == 1
        assert ceiling_rules[0].condition["value"] == 1000000

        # 15L requested on 2024-10-23 -> UNSATISFIED
        attrs = {"pmmy_nonfarm_eligible": 1, "loan_amount_requested": 1500000}
        ev = evaluate_policy(rules, attrs)
        assert ev.state == State.UNSATISFIED

        # 10L requested on 2024-10-23 -> SATISFIED
        attrs_10 = {"pmmy_nonfarm_eligible": 1, "loan_amount_requested": 1000000}
        ev_10 = evaluate_policy(rules, attrs_10)
        assert ev_10.state == State.SATISFIED

    def test_date_boundary_on_revision(self):
        decision_date = date(2024, 10, 24)
        rules = select_version(self.policy_set, "pmmy_v2", decision_date)
        ceiling_rules = [r for r in rules if r.group == "loan_ceiling"]
        assert len(ceiling_rules) == 1
        assert ceiling_rules[0].condition["value"] == 2000000

        # 15L requested on 2024-10-24 -> SATISFIED
        attrs = {"pmmy_nonfarm_eligible": 1, "loan_amount_requested": 1500000}
        ev = evaluate_policy(rules, attrs)
        assert ev.state == State.SATISFIED

        # 25L requested on 2024-10-24 -> UNSATISFIED
        attrs_25 = {"pmmy_nonfarm_eligible": 1, "loan_amount_requested": 2500000}
        ev_25 = evaluate_policy(rules, attrs_25)
        assert ev_25.state == State.UNSATISFIED


# ── Occupation mapping scenarios ──────────────────────────────────────────────

class TestOccupationMapping:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.mapping = load_occupation_mapping(Path("configs/policy_rules/v2/occupation_mapping.yaml"))
        self.policy_set = load_v2_policy_set(Path("configs/policy_rules/v2"))
        self.eval_date = date(2024, 1, 1)

    def test_agri_labour_unknown_scenario(self):
        # Scenario unknown -> UNRESOLVED
        state, _ = evaluate_policy_v2(
            {"occupation_category": "agri_labour"},
            self.policy_set,
            self.eval_date,
            agri_scenario="unknown",
            mapping=self.mapping,
        )
        assert state == State.UNRESOLVED

    def test_agri_labour_ineligible_scenario(self):
        # Scenario ineligible -> UNSATISFIED
        state, _ = evaluate_policy_v2(
            {"occupation_category": "agri_labour"},
            self.policy_set,
            self.eval_date,
            agri_scenario="ineligible",
            mapping=self.mapping,
        )
        assert state == State.UNSATISFIED

    def test_agri_labour_eligible_scenario(self):
        # Scenario eligible -> SATISFIED
        state, _ = evaluate_policy_v2(
            {"occupation_category": "agri_labour"},
            self.policy_set,
            self.eval_date,
            agri_scenario="eligible",
            mapping=self.mapping,
        )
        assert state == State.SATISFIED

    def test_nonfarm_occupations_always_satisfied(self):
        for occ in ["delivery", "ride_hailing", "freelance_services", "retail_micro"]:
            for scenario in ["unknown", "ineligible", "eligible"]:
                state, _ = evaluate_policy_v2(
                    {"occupation_category": occ},
                    self.policy_set,
                    self.eval_date,
                    agri_scenario=scenario,
                    mapping=self.mapping,
                )
                assert state == State.SATISFIED

    def test_unmapped_occupation_resolves_to_unknown(self):
        # Unknown/unmapped occupation -> falls back to unknown mapping entry -> UNRESOLVED
        state, _ = evaluate_policy_v2(
            {"occupation_category": "astronaut"},
            self.policy_set,
            self.eval_date,
            agri_scenario="unknown",
            mapping=self.mapping,
        )
        assert state == State.UNRESOLVED


# ── Ground-truth consistency ──────────────────────────────────────────────────

class TestGroundTruthConsistency:
    def test_zero_unresolved_in_ground_truth(self):
        truth_path = Path("data/synthetic/dgp1/seed1/policy_truth.parquet")
        assert truth_path.exists(), f"Ground truth file missing: {truth_path}"
        df = pd.read_parquet(truth_path)

        for col in [
            "true_policy_legacy",
            "true_policy_v2_ineligible",
            "true_policy_v2_eligible",
        ]:
            assert col in df.columns
            unresolved_count = (df[col] == "UNRESOLVED").sum()
            assert unresolved_count == 0, f"Found {unresolved_count} UNRESOLVED states in {col}"
            # States must only be SATISFIED or UNSATISFIED
            valid_states = {"SATISFIED", "UNSATISFIED"}
            actual_states = set(df[col].unique())
            assert actual_states.issubset(valid_states), f"Unexpected states in {col}: {actual_states}"
