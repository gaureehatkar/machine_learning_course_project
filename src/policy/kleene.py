"""
Kleene three-valued logic for the policy rule engine (TECH_DOC §14.2)

State ∈ {SATISFIED, UNSATISFIED, UNRESOLVED}
  Canonical names stored as full strings.
  SAT / UNSAT / UNRES are shorthand used in tables/diagrams only.

Kleene strong logic:
  AND  — any FALSE → FALSE, else any UNKNOWN → UNKNOWN, else TRUE
  OR   — any TRUE  → TRUE,  else any UNKNOWN → UNKNOWN, else FALSE
  NOT  — NOT TRUE = FALSE, NOT FALSE = TRUE, NOT UNKNOWN = UNKNOWN
"""
from __future__ import annotations

from enum import Enum


class State(str, Enum):
    """Policy evaluation state — canonical names (§14.2, fix #5)."""
    SATISFIED = "SATISFIED"
    UNSATISFIED = "UNSATISFIED"
    UNRESOLVED = "UNRESOLVED"

    # Convenience alias for UNKNOWN in rule evaluation
    UNKNOWN = "UNRESOLVED"

    @classmethod
    def from_bool(cls, value: bool | None) -> "State":
        """Convert a Python bool or None to a State."""
        if value is None:
            return cls.UNRESOLVED
        return cls.SATISFIED if value else cls.UNSATISFIED

    def is_true(self) -> bool:
        return self == State.SATISFIED

    def is_false(self) -> bool:
        return self == State.UNSATISFIED

    def is_unknown(self) -> bool:
        return self == State.UNRESOLVED

    def __repr__(self) -> str:
        return self.value


# ── Kleene operations ──────────────────────────────────────────────────────────

def kleene_and(*states: State) -> State:
    """
    Kleene AND over arbitrary number of states.
    Any UNSATISFIED → UNSATISFIED
    Else any UNRESOLVED → UNRESOLVED
    Else SATISFIED
    """
    if any(s.is_false() for s in states):
        return State.UNSATISFIED
    if any(s.is_unknown() for s in states):
        return State.UNRESOLVED
    return State.SATISFIED


def kleene_or(*states: State) -> State:
    """
    Kleene OR over arbitrary number of states.
    Any SATISFIED → SATISFIED
    Else any UNRESOLVED → UNRESOLVED
    Else UNSATISFIED
    """
    if any(s.is_true() for s in states):
        return State.SATISFIED
    if any(s.is_unknown() for s in states):
        return State.UNRESOLVED
    return State.UNSATISFIED


def kleene_not(state: State) -> State:
    """
    Kleene NOT.
    NOT SATISFIED = UNSATISFIED
    NOT UNSATISFIED = SATISFIED
    NOT UNRESOLVED = UNRESOLVED
    """
    if state.is_true():
        return State.UNSATISFIED
    if state.is_false():
        return State.SATISFIED
    return State.UNRESOLVED


def evaluate_atom(attribute_value, operator: str, value) -> State:
    """
    Evaluate a single condition atom.
    Returns UNRESOLVED if attribute_value is None / NaN (missing data).
    Raises AttributeValidationError for out-of-range values.

    Supported operators: == != < <= > >= IN NOT_IN BETWEEN
    """
    import math

    # Missing attribute → UNKNOWN (on_missing = "UNKNOWN" per spec)
    if attribute_value is None:
        return State.UNRESOLVED
    try:
        if isinstance(attribute_value, float) and math.isnan(attribute_value):
            return State.UNRESOLVED
    except (TypeError, ValueError):
        pass

    op = operator.upper()

    try:
        if op == "==":
            result = attribute_value == value
        elif op == "!=":
            result = attribute_value != value
        elif op == "<":
            result = attribute_value < value
        elif op == "<=":
            result = attribute_value <= value
        elif op == ">":
            result = attribute_value > value
        elif op == ">=":
            result = attribute_value >= value
        elif op == "IN":
            result = attribute_value in value
        elif op == "NOT_IN":
            result = attribute_value not in value
        elif op == "BETWEEN":
            lo, hi = value
            inclusive = True  # spec default
            result = lo <= attribute_value <= hi if inclusive else lo < attribute_value < hi
        else:
            raise ValueError(f"Unknown operator: {operator}")
    except TypeError as exc:
        raise AttributeValidationError(
            f"Cannot compare {attribute_value!r} with operator {operator!r}: {exc}"
        ) from exc

    return State.from_bool(result)


class AttributeValidationError(Exception):
    """Raised when an attribute value is out of range or incompatible with the operator."""


class PolicyVersionError(Exception):
    """Raised when no active policy version is found at the decision date (config error)."""


class RuleConflictError(Exception):
    """Raised internally when rules in the same group conflict at equal priority."""
