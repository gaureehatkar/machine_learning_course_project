"""
Evaluation metrics (TECH_DOC §17, IMPLEMENTATION_PLAN §6)

Primary:
  PR-AUC (with prevalence baseline), Brier score

Secondary:
  ROC-AUC, ECE (10 equal-frequency bins), calibration slope/intercept

Decision:
  approval_rate, default_rate_among_approved, review_rate, coverage, coverage-risk curve

Review:
  pct_reviewed, bad_loan_capture, risk_reduction_vs_R0, review_efficiency

Fairness (supplementary):
  approval_rate_parity, subgroup_default_rates
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    roc_auc_score,
)


# ── Ranking / calibration metrics ────────────────────────────────────────────

def pr_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """PR-AUC (area under precision-recall curve). Report alongside prevalence."""
    return float(average_precision_score(y_true, y_score))


def prevalence_baseline(y_true: np.ndarray) -> float:
    """Prevalence baseline for PR-AUC (a no-skill classifier achieves this)."""
    return float(np.mean(y_true))


def roc_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    return float(roc_auc_score(y_true, y_score))


def brier(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Brier score — proper scoring rule for overall probabilistic accuracy."""
    return float(brier_score_loss(y_true, y_score))


def ece(
    y_true: np.ndarray,
    y_score: np.ndarray,
    n_bins: int = 10,
    strategy: str = "quantile",
) -> float:
    """
    Expected Calibration Error (10 equal-frequency / quantile bins).
    ECE = Σ_m (n_m/N) · |mean(y_m) - mean(p_m)|
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_score = np.asarray(y_score, dtype=np.float64)
    n = len(y_true)

    if strategy == "quantile":
        quantiles = np.linspace(0, 100, n_bins + 1)
        bin_edges = np.percentile(y_score, quantiles)
        bin_edges = np.unique(bin_edges)
    else:
        bin_edges = np.linspace(0.0, 1.0, n_bins + 1)

    ece_val = 0.0
    for i in range(len(bin_edges) - 1):
        lo, hi = bin_edges[i], bin_edges[i + 1]
        if i == len(bin_edges) - 2:
            mask = (y_score >= lo) & (y_score <= hi)
        else:
            mask = (y_score >= lo) & (y_score < hi)
        n_m = mask.sum()
        if n_m == 0:
            continue
        mean_y = y_true[mask].mean()
        mean_p = y_score[mask].mean()
        ece_val += (n_m / n) * abs(mean_y - mean_p)

    return float(ece_val)


def calibration_slope_intercept(
    y_true: np.ndarray,
    y_score: np.ndarray,
    clip_eps: float = 1e-6,
) -> tuple[float, float]:
    """
    Calibration slope and intercept: regress y on logit(p_cal).
    Ideal: slope = 1, intercept = 0.
    """
    from scipy.stats import linregress
    p = np.clip(np.asarray(y_score, dtype=np.float64), clip_eps, 1 - clip_eps)
    logits = np.log(p / (1 - p))
    y = np.asarray(y_true, dtype=np.float64)
    slope, intercept, _, _, _ = linregress(logits, y)
    return float(slope), float(intercept)


# ── Decision metrics ──────────────────────────────────────────────────────────

def approval_rate(decisions: np.ndarray) -> float:
    return float(np.mean(decisions == "APPROVE"))


def default_rate_among_approved(
    decisions: np.ndarray,
    y_true: np.ndarray,
) -> float:
    """Default rate among approved applicants (#(APPROVE ∧ Y=1) / #APPROVE)."""
    approved = decisions == "APPROVE"
    n_approved = approved.sum()
    if n_approved == 0:
        return float("nan")
    return float(y_true[approved].mean())


def review_rate(decisions: np.ndarray) -> float:
    return float(np.mean(decisions == "REVIEW"))


def coverage(decisions: np.ndarray, n_total: int | None = None) -> float:
    """Coverage = #APPROVE / N."""
    n = n_total if n_total is not None else len(decisions)
    return float(np.sum(decisions == "APPROVE") / n)


def policy_violation_rate(
    decisions: np.ndarray,
    policy_states: np.ndarray,
) -> float:
    """
    Policy-violation rate for D1 mode:
    Fraction of D1 approvals that are policy-UNSATISFIED.
    (D2/D4 violation rate is 0 by construction.)
    """
    approved = decisions == "APPROVE"
    n_approved = approved.sum()
    if n_approved == 0:
        return 0.0
    violations = (policy_states[approved] == "UNSATISFIED").sum()
    return float(violations / n_approved)


def coverage_risk_curve(
    pd_scores: np.ndarray,
    y_true: np.ndarray,
    tau_range: np.ndarray | None = None,
) -> pd.DataFrame:
    """Coverage-risk curve: {(coverage(τ), risk(τ))} over a τ sweep."""
    if tau_range is None:
        tau_range = np.linspace(
            pd_scores.min(), pd_scores.max(), 100
        )
    rows = []
    for tau in tau_range:
        decisions = np.where(pd_scores < tau, "APPROVE", "DECLINE")
        cov = coverage(decisions)
        dr = default_rate_among_approved(decisions, y_true)
        rows.append({"tau": tau, "coverage": cov, "default_rate": dr})
    return pd.DataFrame(rows)


# ── Review metrics ────────────────────────────────────────────────────────────

def bad_loan_capture(
    referred: np.ndarray,
    y_true: np.ndarray,
    pool_mask: np.ndarray,
) -> float:
    """Fraction of defaulters in the pool that are referred to review."""
    pool_defaults = (y_true[pool_mask] == 1).sum()
    if pool_defaults == 0:
        return float("nan")
    referred_defaults = ((referred[pool_mask]) & (y_true[pool_mask] == 1)).sum()
    return float(referred_defaults / pool_defaults)


def review_efficiency(
    referred: np.ndarray,
    y_true: np.ndarray,
) -> float:
    """Default rate among referred applicants (vs default rate among non-referred)."""
    if referred.sum() == 0:
        return float("nan")
    return float(y_true[referred].mean())


def gini(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Gini coefficient = 2*AUC - 1. Measures inequality of risk scores."""
    return 2.0 * roc_auc(y_true, y_score) - 1.0


def ks_statistic(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """
    Kolmogorov-Smirnov statistic: max_t |F_default(t) - F_nondefault(t)|.
    Maximum vertical distance between CDFs of default and non-default groups.
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_score = np.asarray(y_score, dtype=np.float64)
    
    default_scores = y_score[y_true == 1]
    nondefault_scores = y_score[y_true == 0]
    
    if len(default_scores) == 0 or len(nondefault_scores) == 0:
        return float("nan")
    
    # Compute empirical CDFs at all unique thresholds
    all_scores = np.sort(np.unique(np.concatenate([default_scores, nondefault_scores])))
    
    cdf_default = np.searchsorted(np.sort(default_scores), all_scores, side="right") / len(default_scores)
    cdf_nondefault = np.searchsorted(np.sort(nondefault_scores), all_scores, side="right") / len(nondefault_scores)
    
    return float(np.max(np.abs(cdf_default - cdf_nondefault)))


# ── All metrics in one call ───────────────────────────────────────────────────

def compute_all_metrics(
    y_true: np.ndarray,
    pd_calibrated: np.ndarray,
    pd_raw: np.ndarray | None = None,
) -> dict:
    """Compute all standard metrics for a model evaluation."""
    m = {
        "pr_auc": pr_auc(y_true, pd_calibrated),
        "prevalence_baseline": prevalence_baseline(y_true),
        "roc_auc": roc_auc(y_true, pd_calibrated),
        "brier": brier(y_true, pd_calibrated),
        "ece": ece(y_true, pd_calibrated),
    }
    slope, intercept = calibration_slope_intercept(y_true, pd_calibrated)
    m["calibration_slope"] = slope
    m["calibration_intercept"] = intercept
    m["gini"] = gini(y_true, pd_calibrated)
    m["ks"] = ks_statistic(y_true, pd_calibrated)
    return m
