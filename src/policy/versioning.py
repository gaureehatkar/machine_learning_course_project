"""
Policy version selector (ARCHITECTURE Diagram 5, TECH_DOC §14.3)

Version selection at decision time t:
  Candidates: rules with effective_from ≤ t < effective_to
  Selection:  highest priority, then latest effective_from
  Tie or none → PolicyVersionError (a configuration error, not UNRES)
"""
from __future__ import annotations

from datetime import date
from typing import Any

from src.policy.kleene import PolicyVersionError
from src.policy.rule_loader import PolicySet, PolicyRule


def select_version(
    policy_set: PolicySet,
    policy_id: str,
    t: date,
) -> list[PolicyRule]:
    """
    Return the active rules for a given policy_id at decision time t.

    Parameters
    ----------
    policy_set : loaded and validated PolicySet
    policy_id  : e.g. "jan_samarth" or "pmmy"
    t          : decision date

    Returns
    -------
    List of active PolicyRules (may be multiple rules in the same policy version)

    Raises
    ------
    PolicyVersionError if no active rules found for this policy at time t.
    """
    candidates = [
        r for r in policy_set.rules_for_policy(policy_id)
        if r.is_active_at(t)
    ]

    if not candidates:
        raise PolicyVersionError(
            f"No active rules for policy_id={policy_id!r} at t={t}. "
            "Check effective_from / effective_to dates in rule files."
        )

    # Group rules by their group name — each group contributes its active rule
    active: list[PolicyRule] = []
    groups = sorted(set(r.group for r in candidates))
    for grp in groups:
        grp_candidates = [r for r in candidates if r.group == grp]
        best_priority = max(r.priority for r in grp_candidates)
        top_priority = [r for r in grp_candidates if r.priority == best_priority]
        latest_from = max(r.effective_from for r in top_priority)
        active.extend([r for r in top_priority if r.effective_from == latest_from])

    return active
