"""
Policy rule loader and validator (TECH_DOC §14.3, ARCHITECTURE Diagram 5)

Loads structured rule files (YAML/JSON) from configs/policy_rules/.
Each file contains one or more versioned rules with:
  rule_id, policy_id, policy_version, effective_from, effective_to,
  priority, group, condition, on_missing, source (provenance)

ALL rule content is marked UNVERIFIED until Task 10b is complete.
The framework itself (loader, validator, Kleene eval, versioning) is unblocked.

Schema validation:
  - Required fields present
  - Operator whitelist enforced
  - No duplicate rule_ids within a file
  - Effective date sanity (effective_from < effective_to if to is not null)
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from src.policy.kleene import AttributeValidationError


# ── Whitelist ──────────────────────────────────────────────────────────────────
ALLOWED_OPERATORS = {"==", "!=", "<", "<=", ">", ">=", "IN", "NOT_IN", "BETWEEN"}

REQUIRED_RULE_FIELDS = {
    "rule_id", "policy_id", "policy_version",
    "effective_from", "group", "condition", "on_missing", "source",
}

REQUIRED_SOURCE_FIELDS = {
    "document_id", "page", "clause", "text", "verified_by", "verified_on",
}


# ── Data classes ───────────────────────────────────────────────────────────────

class PolicyRule:
    """A single versioned policy rule."""
    def __init__(self, data: dict[str, Any]):
        self.rule_id: str = data["rule_id"]
        self.policy_id: str = data["policy_id"]
        self.policy_version: str = data["policy_version"]
        self.effective_from: date = _parse_date(data["effective_from"])
        self.effective_to: date | None = _parse_date(data.get("effective_to")) if data.get("effective_to") else None
        self.priority: int = int(data.get("priority", 100))
        self.group: str = data["group"]
        self.condition: dict = data["condition"]
        self.on_missing: str = data.get("on_missing", "UNKNOWN")
        self.source: dict = data["source"]
        self._raw = data

    def is_active_at(self, t: date) -> bool:
        """True if effective_from ≤ t < effective_to (or to is None)."""
        if t < self.effective_from:
            return False
        if self.effective_to is not None and t >= self.effective_to:
            return False
        return True

    def __repr__(self) -> str:
        return f"PolicyRule(id={self.rule_id!r}, policy={self.policy_id!r}, v={self.policy_version!r})"


class PolicySet:
    """A validated collection of PolicyRules, loaded from one or more files."""
    def __init__(self, rules: list[PolicyRule]):
        self.rules = rules

    def __len__(self) -> int:
        return len(self.rules)

    def rules_for_policy(self, policy_id: str) -> list[PolicyRule]:
        return [r for r in self.rules if r.policy_id == policy_id]


# ── Loader ─────────────────────────────────────────────────────────────────────

def load_policy_set(path: str | Path) -> PolicySet:
    """
    Load all rule files from a directory (or a single file).
    Validates schema and returns a PolicySet.
    """
    path = Path(path)
    if path.is_dir():
        files = sorted(path.glob("*.yaml")) + sorted(path.glob("*.json"))
    elif path.is_file():
        files = [path]
    else:
        raise FileNotFoundError(f"Policy rules path not found: {path}")

    all_rules: list[PolicyRule] = []
    seen_ids: set[str] = set()

    for f in files:
        raw = _load_file(f)
        # Support single-rule dict or list of rules
        if isinstance(raw, dict):
            rule_dicts = raw.get("rules", [raw])
        elif isinstance(raw, list):
            rule_dicts = raw
        else:
            raise ValueError(f"Unexpected structure in {f}: {type(raw)}")

        for rd in rule_dicts:
            _validate_rule_dict(rd, f)
            if rd["rule_id"] in seen_ids:
                raise ValueError(f"Duplicate rule_id {rd['rule_id']!r} in {f}")
            seen_ids.add(rd["rule_id"])
            all_rules.append(PolicyRule(rd))

    return PolicySet(all_rules)


def _load_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        if path.suffix == ".json":
            return json.load(fh)
        return yaml.safe_load(fh)


def _validate_rule_dict(rd: dict, source_file: Path) -> None:
    """Validate a rule dict against the schema."""
    missing = REQUIRED_RULE_FIELDS - set(rd.keys())
    if missing:
        raise ValueError(f"Rule {rd.get('rule_id', '?')} in {source_file} missing fields: {missing}")

    # Validate source provenance fields
    src = rd.get("source", {})
    missing_src = REQUIRED_SOURCE_FIELDS - set(src.keys())
    if missing_src:
        raise ValueError(
            f"Rule {rd['rule_id']!r} source provenance missing fields: {missing_src}"
        )

    # Validate condition operators (recursively)
    _validate_condition(rd["condition"], rd["rule_id"])

    # Date sanity
    eff_from = _parse_date(rd["effective_from"])
    eff_to = rd.get("effective_to")
    if eff_to:
        eff_to_d = _parse_date(eff_to)
        if eff_from >= eff_to_d:
            raise ValueError(
                f"Rule {rd['rule_id']!r}: effective_from {eff_from} >= effective_to {eff_to_d}"
            )


def _validate_condition(cond: dict | list, rule_id: str) -> None:
    """Recursively validate condition tree operators."""
    if isinstance(cond, dict):
        if "operator" in cond:
            op = cond["operator"].upper()
            if op not in ALLOWED_OPERATORS:
                raise ValueError(
                    f"Rule {rule_id!r}: operator {op!r} not in whitelist {ALLOWED_OPERATORS}"
                )
        for key in ("all_of", "any_of"):
            if key in cond:
                for sub in cond[key]:
                    _validate_condition(sub, rule_id)
        if "not" in cond:
            _validate_condition(cond["not"], rule_id)


def _parse_date(d: Any) -> date:
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        return date.fromisoformat(d)
    raise ValueError(f"Cannot parse date: {d!r}")
