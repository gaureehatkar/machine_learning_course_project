"""
Evidence-quality layer (TECH_DOC §13)

E_i = 0.5·(H_i/12) + 0.25·AA_i + 0.25·ULI_i,  threshold τ_E = 0.5

Weights and threshold are DESIGNED EXPERIMENTAL ASSUMPTIONS, not industry standards.

Interpretation: E measures CONFIDENCE IN THE DECISION, NOT creditworthiness.
  - At H=12, AA=ULI=0: E = 0.5 exactly (borderline sufficient).
  - Evidence gate only bites for thin-file applicants (H < 12).
  - Short history makes volatility/trend/seasonality unavailable → less reliable PD.

IMPORTANT SEPARATION:
  - Evidence variables (history_length, aa_completeness, uli_completeness) NEVER
    enter the PD model (set C only). They are evidence-layer inputs exclusively.
  - AA/ULI completeness are assumed independent of each other, of history, and of
    default (§22 limitation 11).

Module contract (IMPLEMENTATION_PLAN §4):
  compute_evidence(h, aa, uli, cfg) -> Series  ∈ [0, 1]
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def compute_evidence(
    h: np.ndarray | pd.Series,
    aa: np.ndarray | pd.Series,
    uli: np.ndarray | pd.Series,
    cfg: dict[str, Any],
) -> pd.Series:
    """
    Compute evidence scores for a batch of applicants.

    Parameters
    ----------
    h   : visible history length in months (integer, 1..12)
    aa  : AA completeness ∈ [0, 1]
    uli : ULI completeness ∈ [0, 1]
    cfg : experiment config (reads evidence.weights and evidence.tau_e)

    Returns
    -------
    pd.Series of evidence scores ∈ [0, 1]
    """
    weights = cfg["evidence"]["weights"]
    w_h = float(weights["history"])      # 0.5
    w_aa = float(weights["aa"])          # 0.25
    w_uli = float(weights["uli"])        # 0.25

    h = np.asarray(h, dtype=np.float64)
    aa = np.asarray(aa, dtype=np.float64)
    uli = np.asarray(uli, dtype=np.float64)

    # Handle missing AA / ULI: treat as 0 (most conservative — no evidence)
    aa_clean = np.where(np.isnan(aa), 0.0, aa)
    uli_clean = np.where(np.isnan(uli), 0.0, uli)

    # E_i = 0.5·(H_i/12) + 0.25·AA_i + 0.25·ULI_i
    scores = w_h * (h / 12.0) + w_aa * aa_clean + w_uli * uli_clean

    # Clamp to [0, 1] (defensive — formula should produce this by design)
    scores = np.clip(scores, 0.0, 1.0)

    return pd.Series(scores, name="evidence_score")


def evidence_status(
    scores: np.ndarray | pd.Series,
    cfg: dict[str, Any],
) -> pd.Series:
    """
    Return SUFFICIENT / INSUFFICIENT for each applicant.

    INSUFFICIENT (E < τ_E) → cannot auto-approve in D3/D4 modes.
    Analytic check (§8, Diagram 6): ≈29% of applicants are INSUFFICIENT.
    """
    tau_e = float(cfg["evidence"]["tau_e"])  # 0.5
    scores = np.asarray(scores, dtype=np.float64)
    status = np.where(scores >= tau_e, "SUFFICIENT", "INSUFFICIENT")
    return pd.Series(status, name="evidence_status")


def compute_evidence_full(
    features_df: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    """
    Compute evidence score and status for a feature table DataFrame.
    Adds columns: evidence_score, evidence_status.
    """
    scores = compute_evidence(
        features_df["history_length"],
        features_df["aa_completeness"],
        features_df["uli_completeness"],
        cfg,
    )
    status = evidence_status(scores, cfg)

    result = features_df.copy()
    result["evidence_score"] = scores.values
    result["evidence_status"] = status.values
    return result
