"""
Review / abstention baseline strategies (Phase 3).

Two baselines, using IDENTICAL pool logic to src.decisions.review:
  Pool P = {PD < tau AND policy != UNSATISFIED}
  Mandatory M = {policy == UNRESOLVED}  (consumed from budget first)
  K = floor(B × |P|)

Strategies:
  margin_to_threshold — refer applicants whose PD is closest to tau
  conformal_ambiguity — refer applicants with ambiguous split-conformal sets

Both return pd.Series of bool (True = referred), same contract as allocate_review().
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# ── Margin-to-threshold ───────────────────────────────────────────────────────

def margin_to_threshold(
    df: pd.DataFrame,
    strategy: str,
    budget: float,
    seed: int,
    tau: float,
) -> pd.Series:
    """
    Refer applicants whose |PD - tau| is smallest (most uncertain about approval).

    Parameters: same contract as allocate_review() in src.decisions.review.
    """
    assert 0 < budget <= 1.0
    referred = pd.Series(False, index=df.index)

    pool_mask = df.get("in_pool", pd.Series(True, index=df.index))
    pool_df   = df[pool_mask].copy()
    if len(pool_df) == 0:
        return referred

    mandatory_mask = pool_df["policy_state"] == "UNRESOLVED"
    M = pool_df[mandatory_mask]
    K = int(np.floor(budget * len(pool_df)))

    if len(M) > K:
        referred.loc[M.index] = True
        return referred

    referred.loc[M.index] = True
    remaining_K = K - len(M)
    non_mandatory = pool_df[~mandatory_mask].copy()
    if remaining_K <= 0 or len(non_mandatory) == 0:
        return referred

    pd_vals = non_mandatory["pd_calibrated"].values
    # Margin to threshold: smallest |PD - tau| → most uncertain
    scores = np.abs(pd_vals - tau)
    # Sort ascending (smallest margin = most uncertain = refer first)
    top_idx = non_mandatory.index[np.argsort(scores)[:remaining_K]]
    referred.loc[top_idx] = True
    return referred


# ── Split-conformal abstention ────────────────────────────────────────────────

class SplitConformalClassifier:
    """
    Inductive (split) conformal classifier.

    Calibrates nonconformity scores on a held-out calibration set,
    then produces prediction sets at coverage level (1 - alpha).
    A prediction set is {APPROVE} or {DECLINE} when unambiguous,
    or {APPROVE, DECLINE} when ambiguous.

    Nonconformity score: s_i = 1 - p_hat(y_i)  (probability of the true label)
    Threshold q_hat: (ceil((n_cal+1)*(1-alpha)) / n_cal) quantile of {s_i}

    Reference: Angelopoulos & Bates, "A Gentle Introduction to Conformal Prediction", 2022.
    """

    def __init__(self, alpha: float = 0.10):
        self.alpha = alpha
        self._q_hat: float | None = None

    def calibrate(self, p_cal: np.ndarray, y_cal: np.ndarray) -> "SplitConformalClassifier":
        """
        Compute nonconformity threshold from calibration predictions.
        p_cal: calibrated probabilities of default, shape (n,)
        y_cal: binary labels, shape (n,)
        """
        # Nonconformity score = 1 - p(true class)
        scores = np.where(y_cal == 1, 1 - p_cal, p_cal)
        n = len(scores)
        # Finite-sample valid quantile
        level = np.ceil((n + 1) * (1 - self.alpha)) / n
        level = min(level, 1.0)
        self._q_hat = float(np.quantile(scores, level))
        return self

    def ambiguity(self, p_test: np.ndarray) -> np.ndarray:
        """
        Ambiguity score: 1 if prediction set contains both classes, 0 otherwise.
        An applicant is in the prediction set for class c if 1 - p(c) <= q_hat.
        """
        if self._q_hat is None:
            raise RuntimeError("Call calibrate() first.")
        in_default = (1 - p_test) <= self._q_hat   # prediction set includes default
        in_good    = p_test        <= self._q_hat   # prediction set includes good
        ambiguous  = in_default & in_good
        return ambiguous.astype(float)


def conformal_ambiguity(
    df: pd.DataFrame,
    strategy: str,
    budget: float,
    seed: int,
    conformal_model: SplitConformalClassifier,
    tau: float,
) -> pd.Series:
    """
    Refer applicants by conformal ambiguity (both classes in prediction set),
    breaking ties by |PD - tau| (closest to threshold).

    Parameters: same contract as allocate_review().
    conformal_model: already calibrated SplitConformalClassifier.
    """
    assert 0 < budget <= 1.0
    referred = pd.Series(False, index=df.index)

    pool_mask = df.get("in_pool", pd.Series(True, index=df.index))
    pool_df   = df[pool_mask].copy()
    if len(pool_df) == 0:
        return referred

    mandatory_mask = pool_df["policy_state"] == "UNRESOLVED"
    M = pool_df[mandatory_mask]
    K = int(np.floor(budget * len(pool_df)))

    if len(M) > K:
        referred.loc[M.index] = True
        return referred

    referred.loc[M.index] = True
    remaining_K = K - len(M)
    non_mandatory = pool_df[~mandatory_mask].copy()
    if remaining_K <= 0 or len(non_mandatory) == 0:
        return referred

    pd_vals = non_mandatory["pd_calibrated"].values
    amb     = conformal_model.ambiguity(pd_vals)         # 1 = ambiguous
    margin  = np.abs(pd_vals - tau)                      # tiebreaker

    # Primary sort: ambiguous first (descending); secondary: smallest margin
    # Negate amb to sort ambiguous (1) before non-ambiguous (0) in ascending argsort
    sort_key = np.lexsort((margin, -amb))
    top_idx  = non_mandatory.index[sort_key[:remaining_K]]
    referred.loc[top_idx] = True
    return referred
