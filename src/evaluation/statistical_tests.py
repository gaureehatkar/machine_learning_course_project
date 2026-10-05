"""
Statistical tests (TECH_DOC §18)

Design:
  Independent units = seeds (10 per DGP)
  Model/decision contrasts: paired (same test set per seed)
  Within-seed: paired applicant-level bootstrap (1,000 resamples)
  DGP robustness: per-DGP analysis (pooled numbers are descriptive only)

Multiplicity:
  3 primary contrasts (A vs B, B vs C, A vs C; D2-D1, D3-D1, D4-D1)
  Bonferroni α = 0.05/3 ≈ 0.0167

All else exploratory and labelled as such.
"""
from __future__ import annotations

import numpy as np
import scipy.stats as stats


def seed_level_ci(
    deltas: list[float] | np.ndarray,
) -> tuple[float, float, float]:
    """
    Seed-level confidence interval over 10 seeds (t-distribution, df=9).
    Returns (mean_delta, lower_95, upper_95).

    Parameters
    ----------
    deltas : list of per-seed metric differences Δ_s = m_X - m_Y, length 10
    """
    deltas = np.asarray(deltas, dtype=np.float64)
    n = len(deltas)
    mean_d = float(np.mean(deltas))
    se = float(np.std(deltas, ddof=1) / np.sqrt(n))
    t_crit = float(stats.t.ppf(0.975, df=n - 1))
    return mean_d, mean_d - t_crit * se, mean_d + t_crit * se


def paired_bootstrap(
    df: "pd.DataFrame",
    metric_fn,
    sys_x_col: str,
    sys_y_col: str,
    y_col: str = "default_flag",
    n: int = 1000,
    seed: int = 0,
) -> dict:
    """
    Paired applicant-level bootstrap CI (descriptive, within-seed).

    Resamples applicants jointly across two systems to estimate the
    distribution of Δ = metric(sys_x) - metric(sys_y).

    Parameters
    ----------
    df        : DataFrame with applicant-level scores and labels
    metric_fn : callable(y_true, y_score) -> float
    sys_x_col : column name for system X scores
    sys_y_col : column name for system Y scores
    y_col     : target column
    n         : number of bootstrap resamples
    seed      : random seed

    Returns
    -------
    dict with keys: mean, lower, upper, n_resamples
    """
    import pandas as pd
    rng = np.random.default_rng(seed)
    N = len(df)
    y = df[y_col].values
    sx = df[sys_x_col].values
    sy = df[sys_y_col].values

    deltas = np.empty(n)
    for i in range(n):
        idx = rng.integers(0, N, size=N)
        deltas[i] = metric_fn(y[idx], sx[idx]) - metric_fn(y[idx], sy[idx])

    return {
        "mean": float(np.mean(deltas)),
        "lower": float(np.percentile(deltas, 2.5)),
        "upper": float(np.percentile(deltas, 97.5)),
        "n_resamples": n,
    }


def bonferroni_alpha(alpha: float = 0.05, n_contrasts: int = 3) -> float:
    """Bonferroni-corrected alpha for multiple comparisons."""
    return alpha / n_contrasts
