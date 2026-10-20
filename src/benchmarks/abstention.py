"""
Review-allocation and abstention baselines (Phase 7).

Strategies:
  V0 / R0 — random
  V1 / R1 — highest PD (entropy-monotone within pool PD < τ < 0.5)
  V1 / R2 — lowest evidence (matches src.decisions.review)
  V1 / R3 — 0.5·H(PD)/ln2 + 0.5·(1 − E) (matches src.decisions.review)
  V2 — margin-to-threshold (|PD − τ| smallest first)
  V3 — split conformal reject (ambiguity of prediction set)
  V4 — Mondrian (class-conditional) conformal reject
  V5 — SCROSS-style (simplified): confidence-quantile ranking
  V6 — expected-loss (PD × exposure) — NOT implemented without exposure column
  V7 — perfect ranking upper bound (true defaulters first)
"""
from __future__ import annotations

import numpy as np

_LN2 = np.log(2)


def _normalize_strategy(strategy: str) -> str:
    s = strategy.upper().replace("-", "_")
    aliases = {
        "V0": "V0",
        "V0_RANDOM": "V0",
        "RANDOM": "V0",
        "R0": "V0",
        "V1_R1": "R1",
        "V1_R1_HIGH_PD": "R1",
        "R1": "R1",
        "HIGH_PD": "R1",
        "V1_R2": "R2",
        "V1_R2_LOW_EVIDENCE": "R2",
        "R2": "R2",
        "LOW_EVIDENCE": "R2",
        "V1_R3": "R3",
        "V1_R3_HYBRID": "R3",
        "R3": "R3",
        "V2": "V2",
        "V2_MARGIN": "V2",
        "MARGIN": "V2",
        "V3": "V3",
        "V3_SPLIT_CONFORMAL": "V3",
        "SPLIT_CONFORMAL": "V3",
        "V4": "V4",
        "V4_MONDRIAN_CONFORMAL": "V4",
        "MONDRIAN_CONFORMAL": "V4",
        "V5": "V5",
        "V5_SCROSS": "V5",
        "SCROSS": "V5",
        "V6": "V6",
        "V6_EXPECTED_LOSS": "V6",
        "EXPECTED_LOSS": "V6",
        "V7": "V7",
        "V7_ORACLE": "V7",
        "ORACLE": "V7",
    }
    if s not in aliases:
        raise ValueError(f"Unknown review allocation strategy: {strategy}")
    return aliases[s]


def _entropy(p: np.ndarray) -> np.ndarray:
    eps = 1e-12
    p = np.clip(p, eps, 1 - eps)
    return -(p * np.log(p) + (1 - p) * np.log(1 - p))


def compute_allocation_scores(
    pd_pool: np.ndarray,
    y_pool: np.ndarray | None,
    tau: float,
    pd_val: np.ndarray,
    y_val: np.ndarray,
    strategy: str,
    seed: int = 42,
    alpha_conformal: float = 0.10,
    evidence_pool: np.ndarray | None = None,
    exposure_pool: np.ndarray | None = None,
) -> np.ndarray:
    """
    Priority scores for applicants in pool P. Higher = refer first.
    """
    n_pool = len(pd_pool)
    strat = _normalize_strategy(strategy)
    ev = (
        np.asarray(evidence_pool, dtype=float)
        if evidence_pool is not None
        else np.ones(n_pool, dtype=float)
    )

    if strat == "V0":
        rng = np.random.RandomState(seed)
        return rng.uniform(0.0, 1.0, size=n_pool)

    if strat == "R1":
        return _entropy(pd_pool)

    if strat == "R2":
        return 1.0 - ev

    if strat == "R3":
        return 0.5 * (_entropy(pd_pool) / _LN2) + 0.5 * (1.0 - ev)

    if strat == "V2":
        return -np.abs(pd_pool - tau)

    if strat == "V3":
        cal_scores = np.where(y_val == 1, 1.0 - pd_val, pd_val)
        n_val = len(y_val)
        q_level = np.ceil((n_val + 1) * (1.0 - alpha_conformal)) / max(n_val, 1)
        q_hat = np.quantile(cal_scores, min(1.0, q_level))
        in_c1 = (1.0 - pd_pool) <= q_hat
        in_c0 = pd_pool <= q_hat
        both = in_c1 & in_c0
        # Ambiguity first; ties broken by PD (higher risk first)
        return both.astype(float) * 2.0 + pd_pool

    if strat == "V4":
        val_0 = pd_val[y_val == 0]
        val_1 = 1.0 - pd_val[y_val == 1]
        n0, n1 = len(val_0), len(val_1)
        q0 = (
            np.quantile(val_0, min(1.0, np.ceil((n0 + 1) * (1.0 - alpha_conformal)) / n0))
            if n0 > 0
            else 0.5
        )
        q1 = (
            np.quantile(val_1, min(1.0, np.ceil((n1 + 1) * (1.0 - alpha_conformal)) / n1))
            if n1 > 0
            else 0.5
        )
        in_c0 = pd_pool <= q0
        in_c1 = (1.0 - pd_pool) <= q1
        both = in_c1 & in_c0
        return both.astype(float) * 2.0 + pd_pool

    if strat == "V5":
        # SCROSS-style (simplified): does NOT reproduce Pugnana et al.
        # Cross-fitted confidence ≈ proximity tightness × risk mass.
        # Lowest confidence first → high score for low confidence.
        confidence = 1.0 - np.abs(pd_pool - 0.5) * 2.0  # in [0,1], peak at 0.5
        return 1.0 - confidence  # refer lowest confidence first

    if strat == "V6":
        if exposure_pool is None:
            raise ValueError(
                "V6 expected-loss requires an exposure column; none available. Skip V6."
            )
        return pd_pool * np.asarray(exposure_pool, dtype=float)

    if strat == "V7":
        if y_pool is None:
            raise ValueError("V7 Oracle requires true labels y_pool")
        return y_pool.astype(float) * 10.0 + pd_pool

    raise ValueError(f"Unknown review allocation strategy: {strategy}")


def allocate_by_budget(
    scores: np.ndarray,
    budget: float,
    mandatory_mask: np.ndarray | None = None,
) -> np.ndarray:
    """
    Flag top K = floor(B · |P|) for review.
    Mandatory set (e.g. UNRESOLVED) is consumed first, matching src.decisions.review.
    """
    n = len(scores)
    k = int(np.floor(budget * n))
    k = max(0, min(n, k))
    referred = np.zeros(n, dtype=bool)
    if k == 0:
        return referred

    if mandatory_mask is None:
        mandatory_mask = np.zeros(n, dtype=bool)
    else:
        mandatory_mask = np.asarray(mandatory_mask, dtype=bool)

    mand_idx = np.where(mandatory_mask)[0]
    if len(mand_idx) >= k:
        # Budget infeasible for all mandatory — refer first k mandatory by score
        order = mand_idx[np.argsort(scores[mand_idx])[::-1][:k]]
        referred[order] = True
        return referred

    referred[mand_idx] = True
    remaining = k - len(mand_idx)
    non_mand = np.where(~mandatory_mask)[0]
    if remaining <= 0 or len(non_mand) == 0:
        return referred

    order = non_mand[np.argsort(scores[non_mand])[::-1][:remaining]]
    referred[order] = True
    return referred
