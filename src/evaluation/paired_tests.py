"""
Paired statistical tests for seed-level comparisons (Phase 8).

All tests operate on per-seed differences (n = n_seeds, df = n-1).

Provides:
  paired_ttest(a, b)         → PairedResult
  holm_correction(p_values)  → adjusted p-values
  bonferroni_correction(p_values, n_contrasts)
  cohen_d_z(diffs)           → effect size
  format_contrast_table(contrasts) → pd.DataFrame

Primary contrasts (pre-specified, Bonferroni α = 0.05/3 = 0.01667):
  1. A vs C, XGB ROC-AUC
  2. D1 vs D4 at matched coverage, default rate among approved
  3. R0 vs R3, bad-loan capture at 20% budget

Secondary / exploratory: labelled separately.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd
from scipy.stats import t as t_dist


BONFERRONI_N_PRIMARY = 3
ALPHA = 0.05
ALPHA_BONFERRONI = ALPHA / BONFERRONI_N_PRIMARY  # 0.01667


@dataclass
class PairedResult:
    n: int
    mean_a: float
    mean_b: float
    mean_diff: float      # b - a
    std_diff: float
    ci_lo: float
    ci_hi: float
    t_stat: float
    df: int
    p_value: float
    cohen_d_z: float

    def significant(self, alpha: float = ALPHA) -> bool:
        return self.p_value < alpha

    def __repr__(self) -> str:
        return (f"PairedResult(n={self.n}, Δ={self.mean_diff:+.4f} "
                f"[{self.ci_lo:+.4f}, {self.ci_hi:+.4f}], "
                f"p={self.p_value:.4f}, d_z={self.cohen_d_z:.3f})")


def paired_ttest(
    a: np.ndarray | Sequence,
    b: np.ndarray | Sequence,
) -> PairedResult:
    """
    Two-sided paired t-test on per-seed values a and b.

    diff = b - a
    t = mean(diff) / (std(diff) / sqrt(n))
    95% CI uses scipy.stats.t.ppf(0.975, df=n-1).
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    assert len(a) == len(b), "Arrays must have same length."
    n = len(a)
    diffs = b - a
    return _ttest_from_diffs(a, b, diffs, n)


def _ttest_from_diffs(a, b, diffs, n) -> PairedResult:
    mean_d = float(np.mean(diffs))
    std_d  = float(np.std(diffs, ddof=1)) if n > 1 else 0.0
    se     = std_d / np.sqrt(n) if n > 1 else 0.0
    t_crit = float(t_dist.ppf(0.975, n - 1)) if n > 1 else 0.0
    ci_lo  = mean_d - t_crit * se
    ci_hi  = mean_d + t_crit * se
    t_stat = mean_d / se if se > 0 else 0.0
    p_val  = float(2 * t_dist.sf(abs(t_stat), n - 1)) if n > 1 else 1.0
    d_z    = mean_d / std_d if std_d > 0 else 0.0
    return PairedResult(
        n=n,
        mean_a=float(np.mean(a)),
        mean_b=float(np.mean(b)),
        mean_diff=mean_d,
        std_diff=std_d,
        ci_lo=ci_lo,
        ci_hi=ci_hi,
        t_stat=t_stat,
        df=n - 1,
        p_value=p_val,
        cohen_d_z=d_z,
    )


def cohen_d_z(diffs: np.ndarray | Sequence) -> float:
    """Cohen's d_z = mean(diff) / std(diff)."""
    d = np.asarray(diffs, dtype=float)
    std = float(np.std(d, ddof=1))
    return float(np.mean(d)) / std if std > 0 else 0.0


def holm_correction(p_values: Sequence[float]) -> np.ndarray:
    """
    Holm-Bonferroni step-down correction.
    Returns adjusted p-values in the original order.
    """
    p = np.asarray(p_values, dtype=float)
    n = len(p)
    order = np.argsort(p)
    adjusted = np.zeros(n)
    prev = 0.0
    for rank, idx in enumerate(order):
        adj = p[idx] * (n - rank)
        adj = max(adj, prev)
        adj = min(adj, 1.0)
        adjusted[idx] = adj
        prev = adj
    return adjusted


def bonferroni_correction(
    p_values: Sequence[float],
    n_contrasts: int = BONFERRONI_N_PRIMARY,
) -> np.ndarray:
    """Simple Bonferroni: multiply by n_contrasts, clip to 1."""
    return np.minimum(np.asarray(p_values, dtype=float) * n_contrasts, 1.0)


def format_contrast_table(contrasts: list[dict]) -> pd.DataFrame:
    """
    Build a tidy DataFrame from a list of contrast dicts.

    Each dict must have keys:
      contrast, family, dgp, metric, a_label, b_label
      plus either (a_values, b_values) or a PairedResult in key 'result'.

    Optional keys: alpha (override), type ('primary'|'secondary'|'exploratory').
    """
    rows = []
    for c in contrasts:
        if "result" in c:
            r: PairedResult = c["result"]
        else:
            r = paired_ttest(c["a_values"], c["b_values"])

        alpha = c.get("alpha", ALPHA)
        adj_method = c.get("adj_method", "none")

        rows.append({
            "contrast":    c.get("contrast", ""),
            "family":      c.get("family", "primary"),
            "dgp":         c.get("dgp", ""),
            "metric":      c.get("metric", ""),
            "a_label":     c.get("a_label", "A"),
            "b_label":     c.get("b_label", "B"),
            "n":           r.n,
            "mean_a":      round(r.mean_a, 4),
            "mean_b":      round(r.mean_b, 4),
            "mean_diff":   round(r.mean_diff, 4),
            "ci_lo":       round(r.ci_lo, 4),
            "ci_hi":       round(r.ci_hi, 4),
            "t":           round(r.t_stat, 3),
            "df":          r.df,
            "p":           round(r.p_value, 4),
            "p_adjusted":  c.get("p_adjusted", round(r.p_value, 4)),
            "method":      adj_method,
            "significant": r.p_value < alpha,
            "cohen_d_z":   round(r.cohen_d_z, 3),
        })
    return pd.DataFrame(rows)
