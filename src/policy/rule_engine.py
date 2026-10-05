"""
Policy rule engine (ARCHITECTURE Diagram 5, TECH_DOC §14)

Evaluates versioned JanSamarth/PMMY rules using Kleene three-valued logic.
Returns PolicyEvaluation with state, rule_results, reason_codes, provenance.

Design properties:
  - Deterministic: no randomness, no ML
  - Three-valued: SATISFIED / UNSATISFIED / UNRESOLVED
  - Clause-level provenance retained for every evaluation
  - Policy state is INDEPENDENT of default_flag by design (§10.2)

ALL rule content is UNVERIFIED until Task 10b.
The engine framework is unblocked (§2.1 gate table).

Module contract (IMPLEMENTATION_PLAN §4):
  evaluate_policy(version_rules, attributes) -> PolicyEvaluation
  combine_schemes(states, mode) -> State
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from src.policy.kleene import (
    State, kleene_and, kleene_or, kleene_not, evaluate_atom,
    AttributeValidationError, PolicyVersionError,
)
from src.policy.rule_loader import PolicyRule, PolicySet
from src.policy.versioning import select_version


# ── Result data classes ────────────────────────────────────────────────────────

@dataclass
class RuleResult:
    rule_id: str
    group: str
    state: State
    reason_code: str | None = None
    provenance: dict = field(default_factory=dict)


@dataclass
class PolicyEvaluation:
    """
    Full policy evaluation result for one applicant / one scheme.
    policy_id, version, state, rule_results, reason_codes, provenance.
    """
    policy_id: str
    policy_version: str
    effective_from: str
    effective_to: str | None
    state: State
    rule_results: list[RuleResult] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)
    provenance: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "effective_from": self.effective_from,
            "effective_to": self.effective_to,
            "state": self.state.value,
            "reason_codes": self.reason_codes,
            "provenance": self.provenance,
        }


# ── Condition evaluation ───────────────────────────────────────────────────────

def _eval_condition(condition: dict, attributes: dict[str, Any]) -> State:
    """
    Recursively evaluate a condition tree.

    condition grammar:
      expr := { "attribute": str, "operator": str, "value": any }
             | { "all_of": [expr, ...] }
             | { "any_of": [expr, ...] }
             | { "not": expr }
    """
    cond = condition

    if "all_of" in cond:
        sub_states = [_eval_condition(c, attributes) for c in cond["all_of"]]
        return kleene_and(*sub_states)

    if "any_of" in cond:
        sub_states = [_eval_condition(c, attributes) for c in cond["any_of"]]
        return kleene_or(*sub_states)

    if "not" in cond:
        sub_state = _eval_condition(cond["not"], attributes)
        return kleene_not(sub_state)

    if "attribute" in cond:
        attr_name = cond["attribute"]
        operator = cond["operator"]
        value = cond["value"]
        attr_value = attributes.get(attr_name)
        return evaluate_atom(attr_value, operator, value)

    raise ValueError(f"Unrecognised condition structure: {cond}")


# ── Main evaluate function ─────────────────────────────────────────────────────

def evaluate_policy(
    version_rules: list[PolicyRule],
    attributes: dict[str, Any],
) -> PolicyEvaluation:
    """
    Evaluate a set of active rules (from select_version) against applicant attributes.

    Parameters
    ----------
    version_rules : list of active PolicyRules from select_version()
    attributes    : dict of attribute name → value (None = missing)

    Returns
    -------
    PolicyEvaluation with Kleene-evaluated state and full provenance.
    """
    if not version_rules:
        raise PolicyVersionError("No rules provided to evaluate_policy.")

    # Use metadata from the first rule (all should share policy_id/version)
    first = version_rules[0]
    policy_id = first.policy_id
    policy_version = first.policy_version
    effective_from = str(first.effective_from)
    effective_to = str(first.effective_to) if first.effective_to else None

    rule_results: list[RuleResult] = []
    groups_seen: dict[str, list[State]] = {}

    for rule in version_rules:
        try:
            atom_state = _eval_condition(rule.condition, attributes)
        except AttributeValidationError as exc:
            atom_state = State.UNRESOLVED
            reason_code = f"ATTR_VALIDATION_ERROR:{exc}"
        else:
            reason_code = None

        rr = RuleResult(
            rule_id=rule.rule_id,
            group=rule.group,
            state=atom_state,
            reason_code=reason_code,
            provenance={
                "document_id": rule.source.get("document_id"),
                "page": rule.source.get("page"),
                "clause": rule.source.get("clause"),
                "text": rule.source.get("text"),
                "verified_by": rule.source.get("verified_by"),
                "verified_on": rule.source.get("verified_on"),
            },
        )
        rule_results.append(rr)

        if rule.group not in groups_seen:
            groups_seen[rule.group] = []
        groups_seen[rule.group].append(atom_state)

    # Combine rules within each group (AND within group by default)
    group_states: list[State] = []
    for group, states in groups_seen.items():
        group_state = kleene_and(*states)
        group_states.append(group_state)

    # Conflict detection: if any group has conflicting rules at same priority
    # (both SAT and UNSAT present) → RULE_CONFLICT → UNRESOLVED
    # For simplicity: detect by AND result being inconsistent
    # Full conflict detection: same group, same priority, opposite results
    _detect_conflicts(version_rules, rule_results)

    # Final policy state: AND over all group states
    final_state = kleene_and(*group_states) if group_states else State.UNRESOLVED

    reason_codes = [
        rr.reason_code for rr in rule_results if rr.reason_code
    ]
    provenance = [rr.provenance for rr in rule_results]

    return PolicyEvaluation(
        policy_id=policy_id,
        policy_version=policy_version,
        effective_from=effective_from,
        effective_to=effective_to,
        state=final_state,
        rule_results=rule_results,
        reason_codes=reason_codes,
        provenance=provenance,
    )


def _detect_conflicts(
    rules: list[PolicyRule],
    results: list[RuleResult],
) -> None:
    """
    Detect conflicting rules in the same group at the same priority level.
    Sets reason_code = RULE_CONFLICT on affected results and sets state to UNRESOLVED.
    """
    # Group by (group, priority)
    from collections import defaultdict
    gp_results: dict = defaultdict(list)
    for rule, result in zip(rules, results):
        gp_results[(rule.group, rule.priority)].append(result)

    for (group, priority), res_list in gp_results.items():
        states = {r.state for r in res_list}
        if State.SATISFIED in states and State.UNSATISFIED in states:
            for r in res_list:
                r.state = State.UNRESOLVED
                r.reason_code = "RULE_CONFLICT"


# ── Scheme combination ─────────────────────────────────────────────────────────

def combine_schemes(states: list[State], mode: str = "any") -> State:
    """
    Combine multiple scheme states into a single state.

    mode="any"  → Kleene OR  (applicant qualifies under any scheme)
    mode="all"  → Kleene AND (applicant must qualify under all schemes)
    mode="jan_samarth" → return only JanSamarth state (index 0)
    mode="pmmy"        → return only PMMY state (index 1)
    """
    if not states:
        return State.UNRESOLVED
    if mode == "any":
        return kleene_or(*states)
    if mode == "all":
        return kleene_and(*states)
    if mode == "jan_samarth":
        return states[0] if states else State.UNRESOLVED
    if mode == "pmmy":
        return states[1] if len(states) > 1 else State.UNRESOLVED
    raise ValueError(f"Unknown scheme mode: {mode!r}")


# ── Batch evaluation helper ────────────────────────────────────────────────────

def evaluate_batch(
    policy_attributes_df,
    policy_set: PolicySet,
    decision_date: date,
    scheme_mode: str = "any",
    policy_ids: list[str] | None = None,
) -> dict[str, dict]:
    """
    Evaluate all applicants in a DataFrame.

    Returns dict: applicant_id → {
        "jan_samarth_state": str,
        "pmmy_state": str,
        "combined_state": str,
        "evaluations": [PolicyEvaluation.to_dict(), ...]
    }
    """
    if policy_ids is None:
        policy_ids = ["jan_samarth", "pmmy"]

    results = {}
    for _, row in policy_attributes_df.iterrows():
        aid = row["applicant_id"]
        # Build attribute dict — annual_income derived from feature table if available
        attrs = {
            "age": row.get("age"),
            "occupation_category": row.get("occupation_category"),
            "nonfarm_business_flag": row.get("nonfarm_business_flag"),
        }
        # annual_income may be passed in if available
        if "annual_income" in row.index:
            attrs["annual_income"] = row["annual_income"]

        evals = []
        eval_states = []
        scheme_states = {}

        for pid in policy_ids:
            try:
                version_rules = select_version(policy_set, pid, decision_date)
                eval_result = evaluate_policy(version_rules, attrs)
            except PolicyVersionError:
                eval_result = PolicyEvaluation(
                    policy_id=pid,
                    policy_version="UNKNOWN",
                    effective_from="N/A",
                    effective_to=None,
                    state=State.UNRESOLVED,
                    reason_codes=["NO_ACTIVE_VERSION"],
                )
            evals.append(eval_result.to_dict())
            eval_states.append(eval_result.state)
            scheme_states[pid] = eval_result.state.value

        combined = combine_schemes(eval_states, scheme_mode)
        results[aid] = {
            **scheme_states,
            "combined_state": combined.value,
            "evaluations": evals,
        }

    return results
