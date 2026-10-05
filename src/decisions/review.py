"""
Human-review allocation — Experiment B (TECH_DOC §16.4, ARCHITECTURE Diagram 8)

Pool P = { PD < τ  and  S ≠ UNSATISFIED }
Mandatory set M = { S = UNRESOLVED }  (consumes budget first)
K = floor(B × card(P)),  B ∈ {0.20, 0.30}

Ranking strategies:
  R0  — random (control)
  R1  — entropy H(PD) = -p ln p - (1-p) ln(1-p)  ≡ highest-PD-first within P
          (because every member of P has PD < τ < 0.5, entropy is monotone in PD)
  R2  — lowest E (evidence score)  → 1 - E
  R3  — 0.5·H(PD)/ln2 + 0.5·(1 - E)

Perfect-review oracle simulation:
  Referred applicant approved iff Y = 0 (defaulters always declined in review).
  Non-referred members of P: auto-approved.

Module contract:
  allocate_review(df, strategy, budget, seed) -> Series (boolean: True = referred)
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.utils.seeding import review_seed


_LN2 = np.log(2)


def _entropy(p: np.ndarray) -> np.ndarray:
    """Predictive entropy H(p) = -p ln p - (1-p) ln(1-p)."""
    eps = 1e-12
    p = np.clip(p, eps, 1 - eps)
    return -(p * np.log(p) + (1 - p) * np.log(1 - p))


def allocate_review(
    df: pd.DataFrame,
    strategy: str,
    budget: float,
    seed: int,
) -> pd.Series:
    """
    Allocate human-review budget.

    Parameters
    ----------
    df       : DataFrame with columns: applicant_id, pd_calibrated, evidence_score,
               policy_state (combined), default_flag, tau (applied as filter)
    strategy : "R0" | "R1" | "R2" | "R3"
    budget   : B ∈ {0.20, 0.30}  (fraction of pool P)
    seed     : dataset seed (for R0 reproducibility)

    Returns
    -------
    pd.Series of bool, index=df.index, True = referred to human review.
    """
    strategy = strategy.upper()
    assert strategy in {"R0", "R1", "R2", "R3"}, f"Unknown strategy: {strategy!r}"
    assert 0 < budget <= 1.0, f"Budget must be in (0, 1]: {budget}"

    referred = pd.Series(False, index=df.index)

    # Pool P: applicants already passed PD gate AND not POLICY_INELIGIBLE
    # (i.e., PD < τ and policy_state != UNSATISFIED)
    # In practice, df passed here is already the eligible pool
    pool_mask = df.get("in_pool", pd.Series(True, index=df.index))
    pool_df = df[pool_mask].copy()

    if len(pool_df) == 0:
        return referred

    # Mandatory set M: policy UNRESOLVED (consumed first)
    mandatory_mask = pool_df["policy_state"] == "UNRESOLVED"
    M = pool_df[mandatory_mask]

    # Budget K
    K = int(np.floor(budget * len(pool_df)))

    if len(M) > K:
        # Budget infeasible — cannot cover all mandatory UNRESOLVED
        # Report this case; refer all mandatory
        print(
            f"[review] WARNING: Mandatory set |M|={len(M)} > K={K} "
            f"(budget infeasible at B={budget:.0%}). Referring all mandatory."
        )
        referred.loc[M.index] = True
        return referred

    # Mark mandatory as referred
    referred.loc[M.index] = True
    remaining_K = K - len(M)

    # Non-mandatory pool
    non_mandatory = pool_df[~mandatory_mask].copy()

    if remaining_K <= 0 or len(non_mandatory) == 0:
        return referred

    # Compute ranking scores
    pd_vals = non_mandatory["pd_calibrated"].values
    e_vals = non_mandatory["evidence_score"].values if "evidence_score" in non_mandatory.columns else np.ones(len(non_mandatory))

    rng = np.random.default_rng(review_seed(seed))

    if strategy == "R0":
        # Random control — shuffle non-mandatory
        scores = rng.random(len(non_mandatory))
    elif strategy == "R1":
        # Entropy = monotone in PD within pool (R1 ≡ highest-PD-first, per spec note)
        scores = _entropy(pd_vals)
    elif strategy == "R2":
        # Lowest evidence first
        scores = 1.0 - e_vals
    elif strategy == "R3":
        # Combined: 0.5·H(PD)/ln2 + 0.5·(1 - E)
        scores = 0.5 * (_entropy(pd_vals) / _LN2) + 0.5 * (1.0 - e_vals)

    # Top K - |M| by score (descending)
    top_indices = non_mandatory.index[np.argsort(scores)[::-1][:remaining_K]]
    referred.loc[top_indices] = True

    return referred


def apply_oracle(
    df: pd.DataFrame,
    referred: pd.Series,
) -> pd.Series:
    """
    Perfect-review oracle simulation (§16.4):
      Referred applicant approved iff Y = 0 (defaulter always declined).
      Non-referred members of pool P: auto-approved.

    Returns pd.Series of final decisions: "APPROVE" | "DECLINE"
    """
    decisions = pd.Series("APPROVE", index=df.index)

    # Non-pool applicants keep their gate decision (DECLINE from PD/policy)
    # This function only concerns pool P members
    pool_mask = df.get("in_pool", pd.Series(True, index=df.index))

    # Referred: approve only if Y=0
    referred_idx = referred[referred].index
    referred_pool = referred_idx.intersection(df[pool_mask].index)
    decisions.loc[referred_pool] = np.where(
        df.loc[referred_pool, "default_flag"].values == 0,
        "APPROVE",
        "DECLINE",
    )

    return decisions
