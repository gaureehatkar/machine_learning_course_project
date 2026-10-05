"""
Threshold selection (TECH_DOC §15, IMPLEMENTATION_PLAN §4)

τ selection protocol:
  - Select τ on the VALIDATION set so that D1 approvals = 70% (approval_target).
  - The same τ is reused for D2-D4 (differences come from the gates, not from τ).
  - Matched-coverage comparison: re-tune τ for D1-D3 so their auto-approval
    coverage equals D4's.

Module contract:
  select_tau(pd_val, target_approval=0.70) -> float
  match_tau(pd_val, gate_fn, target_coverage) -> float
"""
from __future__ import annotations

import numpy as np


def select_tau(
    pd_val: np.ndarray,
    target_approval: float = 0.70,
) -> float:
    """
    Select τ so that D1 approval rate = target_approval on the validation set.

    D1 mode approves whenever PD < τ, so:
      approval_rate(τ) = mean(PD < τ)

    We find the τ that gives the closest approval rate to target_approval.
    Uses the sorted PD values as candidate thresholds.

    Parameters
    ----------
    pd_val          : calibrated PD scores on the validation set
    target_approval : desired D1 approval rate (default 0.70)

    Returns
    -------
    float τ
    """
    pd_val = np.asarray(pd_val, dtype=np.float64)
    # Candidate τ values: unique sorted PD values + small increments
    candidates = np.sort(np.unique(pd_val))

    best_tau = candidates[0]
    best_diff = float("inf")

    for tau in candidates:
        rate = float(np.mean(pd_val < tau))
        diff = abs(rate - target_approval)
        if diff < best_diff:
            best_diff = diff
            best_tau = tau

    # Also check just above max to allow 100% approval edge case
    tau_max = float(candidates[-1]) + 1e-9
    rate = float(np.mean(pd_val < tau_max))
    if abs(rate - target_approval) < best_diff:
        best_tau = tau_max

    return float(best_tau)


def match_tau(
    pd_val: np.ndarray,
    gate_fn,
    target_coverage: float,
) -> float:
    """
    Find τ such that the gate function produces auto-approval coverage = target_coverage
    on the validation set.

    gate_fn(pd_val_single, tau) -> bool (True = auto-approve)

    Used for matched-coverage comparison (D1-D3 tuned to match D4's coverage).
    """
    pd_val = np.asarray(pd_val, dtype=np.float64)
    candidates = np.sort(np.unique(pd_val))

    best_tau = candidates[0]
    best_diff = float("inf")

    for tau in candidates:
        approved = np.array([gate_fn(p, tau) for p in pd_val])
        coverage = float(np.mean(approved))
        diff = abs(coverage - target_coverage)
        if diff < best_diff:
            best_diff = diff
            best_tau = tau

    return float(best_tau)
