"""
Policy rule loader v2 — loads configs/policy_rules/v2/ rules
and resolves occupation → pmmy_nonfarm_eligible via occupation_mapping.yaml.

Implements three agri_scenario modes: unknown (default), ineligible, eligible.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import yaml

from src.policy.kleene import State
from src.policy.rule_loader import load_policy_set, PolicySet
from src.policy.rule_engine import evaluate_policy, combine_schemes, PolicyEvaluation
from src.policy.versioning import select_version
from src.policy.kleene import PolicyVersionError


# ── Occupation mapping ────────────────────────────────────────────────────────

def load_occupation_mapping(mapping_path: Path) -> dict:
    with open(mapping_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data


def resolve_occupation_attrs(
    occupation_category: str | None,
    mapping: dict,
    agri_scenario: str | None = None,
) -> dict[str, Any]:
    """
    Given an occupation_category string, return the policy attribute dict
    with pmmy_nonfarm_eligible resolved.

    agri_scenario overrides the mapping file's default if provided.
    """
    occ = (occupation_category or "unknown").lower().replace("-", "_").replace(" ", "_")
    cfg_scenario = mapping.get("agri_scenario", "unknown")
    scenario = agri_scenario or cfg_scenario

    mappings = mapping.get("mappings", {})
    entry = mappings.get(occ, mappings.get("unknown", {}))
    flag = entry.get("pmmy_nonfarm_eligible")

    # Apply scenario for null values
    if flag is None:
        if scenario == "ineligible":
            flag = 0
        elif scenario == "eligible":
            flag = 1
        else:
            flag = None  # UNKNOWN → UNRESOLVED in Kleene

    return {"pmmy_nonfarm_eligible": flag}


# ── V2 policy evaluation ──────────────────────────────────────────────────────

def evaluate_policy_v2(
    attributes: dict[str, Any],
    policy_set: PolicySet,
    decision_date: date,
    scheme_mode: str = "any",
    agri_scenario: str | None = None,
    mapping: dict | None = None,
) -> tuple[State, dict[str, str]]:
    """
    Evaluate v2 policy rules for a single applicant.

    Returns (combined_state, per_scheme_states_dict).
    """
    # Resolve occupation if mapping is provided
    if mapping is not None:
        occ_attrs = resolve_occupation_attrs(
            attributes.get("occupation_category"),
            mapping,
            agri_scenario=agri_scenario,
        )
        attrs = {**attributes, **occ_attrs}
    else:
        attrs = attributes

    # For now only pmmy_v2 is defined
    scheme_ids = ["pmmy_v2"]
    scheme_results: list[State] = []
    scheme_states: dict[str, str] = {}

    for scheme_id in scheme_ids:
        try:
            rules = select_version(policy_set, scheme_id, decision_date)
            ev: PolicyEvaluation = evaluate_policy(rules, attrs)
            scheme_results.append(ev.state)
            scheme_states[scheme_id] = ev.state.value
        except PolicyVersionError:
            scheme_results.append(State.UNRESOLVED)
            scheme_states[scheme_id] = "UNRESOLVED"

    combined = combine_schemes(scheme_results, mode=scheme_mode)
    return combined, scheme_states


def load_v2_policy_set(v2_dir: Path) -> PolicySet:
    """Load all .yaml rule files from configs/policy_rules/v2/ (skip README)."""
    return load_policy_set(v2_dir)
