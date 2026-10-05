"""
Credit scoring — Scorecard scaling transformation (RESEARCH PROTOTYPE ONLY)

Transforms default probability (PD) into a displayed credit score using
standard scorecard methodology:
  score = offset + factor * ln(odds)
  where odds = (1-PD) / PD
  factor = PDO / ln(2)
  offset = base_score - factor * ln(base_odds)

DISCLAIMER: Illustrative score derived from default probability. 
NOT comparable to bureau scores. For research prototype only.

References:
  - Naeem Siddiqi. Credit Risk Scorecards: Developing and Implementing 
    Intelligent Credit Scoring. John Wiley & Sons, 2006.
"""
from __future__ import annotations

import numpy as np


def compute_credit_score(
    pd: float,
    base_score: float = 600,
    base_odds: float = 0.05,
    pdo: float = 50,
    score_min: float = 300,
    score_max: float = 900,
) -> float:
    """
    Compute credit score from probability of default.

    Parameters
    ----------
    pd : float
        Probability of default ∈ (0, 1), e.g., 0.15 for 15%
    base_score : float
        Score at base_odds (default: 600)
    base_odds : float
        Odds at base_score (default: 0.05, i.e., 1 in 20)
    pdo : float
        Points-to-Double-Odds — score change for 2x odds change (default: 50)
    score_min, score_max : float
        Clamp range for displayed score (default: 300–900)

    Returns
    -------
    score : float
        Credit score, clamped to [score_min, score_max]

    Formula
    -------
    odds = (1 - PD) / PD
    factor = PDO / ln(2)
    offset = base_score - factor * ln(base_odds)
    score = offset + factor * ln(odds)
    """
    # Clamp PD to avoid log(0) or log(∞)
    pd = max(min(pd, 0.9999), 0.0001)

    # Compute odds
    odds = (1.0 - pd) / pd

    # Compute factor and offset
    factor = pdo / np.log(2.0)
    offset = base_score - factor * np.log(base_odds)

    # Compute score
    score = offset + factor * np.log(odds)

    # Clamp to range
    score = max(min(score, score_max), score_min)

    return float(score)


def compute_score_and_tau(
    pd: float,
    tau: float,
    base_score: float = 600,
    base_odds: float = 0.05,
    pdo: float = 50,
    score_min: float = 300,
    score_max: float = 900,
) -> tuple[float, float]:
    """
    Compute both credit score and score equivalent of tau threshold.

    Returns
    -------
    score : float
        Credit score for applicant's PD
    tau_score : float
        Credit score equivalent of tau threshold
    """
    score = compute_credit_score(pd, base_score, base_odds, pdo, score_min, score_max)
    tau_score = compute_credit_score(tau, base_score, base_odds, pdo, score_min, score_max)
    return score, tau_score


def format_score_display(
    score: float,
    pd: float,
    tau: float,
    tau_score: float,
    phase: str = "1",
    model_name: str = "heuristic",
) -> dict:
    """
    Format credit score for display in API response and UI.

    Parameters
    ----------
    score : float
        Applicant's credit score
    pd : float
        Applicant's probability of default
    tau : float
        PD decision threshold
    tau_score : float
        Score equivalent of tau
    phase : str
        Development phase (e.g., "1" for Phase 1)
    model_name : str
        Model name (e.g., "heuristic", "xgboost", "logreg")

    Returns
    -------
    display_dict : dict
        Formatted display object with score, PD, threshold info, and label
    """
    return {
        "score": int(round(score)),
        "pd_percent": round(pd * 100, 1),
        "threshold_score": int(round(tau_score)),
        "threshold_pd_percent": round(tau * 100, 1),
        "phase": f"Phase {phase} {model_name} (demo)",
        "disclaimer": (
            "Illustrative score derived from default probability. "
            "Not comparable to bureau scores."
        ),
    }
