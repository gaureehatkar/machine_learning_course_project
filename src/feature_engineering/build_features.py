"""
Feature engineering — builds the 23-column feature table from monthly + applicants data.

Feature set layout (IMPLEMENTATION_PLAN.md §3, TECH_DOC §8):
  A (7 conventional):  income_mean, expense_mean, expense_ratio, debt_mean, has_emi,
                        liquidity_mean, liquidity_min
  B (5 alternative):   income_volatility, income_trend, platform_tenure, multi_platform,
                        seasonality_index
  C (12) = A ∪ B       ← ONLY these 12 enter the PD model
  Evidence (3):        history_length, aa_completeness, uli_completeness
  Policy (2):          jan_samarth_state, pmmy_state  (filled by policy engine later)
  Contextual (1):      e_shram_registered
  Metadata (4):        applicant_id, dgp_id, seed_id, split
  Target (1):          default_flag
  TOTAL = 23 columns

Views:
  full    — all 12 observation months (used for TRAINING)
  visible — most recent H_i months (used for VAL / TEST / decisions)
  H1/H3/H6/H12 — forced history windows (history experiment, §16.5)

CUTOFF INVARIANT (§10.5):
  Every feature is derived from months ≤ 12 only.
  Static attributes (platform_tenure, multi_platform, AA/ULI completeness,
  e_shram_registered, policy attributes) are as-of-cutoff values — never
  re-derived from forced-H views.

NaN rules (visible view, XGBoost handles natively; LR uses train-median imputation):
  income_volatility  → NaN if H < 2
  income_trend       → NaN if H < 3
  seasonality_index  → NaN if H < 12
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.utils.config_loader import load_config, get_output_dir


# ── Feature set definitions ────────────────────────────────────────────────────

FEATURE_SET_A = [
    "income_mean", "expense_mean", "expense_ratio",
    "debt_mean", "has_emi",
    "liquidity_mean", "liquidity_min",
]

FEATURE_SET_B = [
    "income_volatility", "income_trend",
    "platform_tenure", "multi_platform",
    "seasonality_index",
]

FEATURE_SET_C = FEATURE_SET_A + FEATURE_SET_B  # 12 features — only these enter PD model

EVIDENCE_COLS = ["history_length", "aa_completeness", "uli_completeness"]
POLICY_COLS = ["jan_samarth_state", "pmmy_state"]
CONTEXTUAL_COLS = ["e_shram_registered"]
METADATA_COLS = ["applicant_id", "dgp_id", "seed_id", "split"]
TARGET_COL = "default_flag"

ALL_COLUMNS_ORDERED = (
    METADATA_COLS + FEATURE_SET_C + EVIDENCE_COLS + POLICY_COLS + CONTEXTUAL_COLS + [TARGET_COL]
)  # 4 + 12 + 3 + 2 + 1 + 1 = 23


# ── Mathematics (spec §9.1) ────────────────────────────────────────────────────

def _income_mean(income: np.ndarray) -> float:
    """Ī = (1/H) Σ I_t"""
    return float(np.mean(income))


def _expense_mean(expense: np.ndarray) -> float:
    """Ē = (1/H) Σ E_t"""
    return float(np.mean(expense))


def _expense_ratio(expense: np.ndarray, income: np.ndarray) -> float:
    """Ē / Ī"""
    i_mean = np.mean(income)
    if i_mean == 0:
        return np.nan
    return float(np.mean(expense) / i_mean)


def _debt_mean(debt: np.ndarray) -> float:
    """mean(D_t) in ₹ per month"""
    return float(np.mean(debt))


def _has_emi(debt: np.ndarray) -> int:
    """1 if any D_t > 0"""
    return int(np.any(debt > 0))


def _liquidity_mean(liquidity: np.ndarray) -> float:
    """mean(L_t) over visible months"""
    return float(np.mean(liquidity))


def _liquidity_min(liquidity: np.ndarray) -> float:
    """min(L_t) over visible months — stress indicator"""
    return float(np.min(liquidity))


def _income_volatility(income: np.ndarray) -> float:
    """CV_I = σ_I / Ī, σ_I with ddof=1. NaN if H < 2."""
    if len(income) < 2:
        return np.nan
    i_mean = np.mean(income)
    if i_mean == 0:
        return np.nan
    return float(np.std(income, ddof=1) / i_mean)


def _income_trend(income: np.ndarray) -> float:
    """
    Trend = β₁ / Ī from OLS fit I_t = β₀ + β₁t + ε_t (scale-free).
    NaN if H < 3.
    """
    H = len(income)
    if H < 3:
        return np.nan
    i_mean = np.mean(income)
    if i_mean == 0:
        return np.nan
    t = np.arange(1, H + 1, dtype=np.float64)
    t_centered = t - t.mean()
    beta1 = np.dot(t_centered, income) / np.dot(t_centered, t_centered)
    return float(beta1 / i_mean)


def _seasonality_index(income: np.ndarray) -> float:
    """
    Fit I_t = β₀ + β₁t + a·sin(2πt/12) + b·cos(2πt/12) + ε_t via OLS.
    Index = √(a²+b²) / Ī  (scale-free). NaN unless H == 12.
    """
    H = len(income)
    if H != 12:
        return np.nan
    i_mean = np.mean(income)
    if i_mean == 0:
        return np.nan
    t = np.arange(1, 13, dtype=np.float64)
    # Design matrix: [1, t, sin, cos]
    X = np.column_stack([
        np.ones(12),
        t,
        np.sin(2 * np.pi * t / 12),
        np.cos(2 * np.pi * t / 12),
    ])
    try:
        coeffs, _, _, _ = np.linalg.lstsq(X, income, rcond=None)
    except np.linalg.LinAlgError:
        return np.nan
    a, b = coeffs[2], coeffs[3]
    return float(np.sqrt(a ** 2 + b ** 2) / i_mean)


# ── Window selection ───────────────────────────────────────────────────────────

def _get_visible_months(months: np.ndarray, H: int, obs_months: int = 12) -> np.ndarray:
    """
    Return the most-recent H months from the observation window.
    §16.5: visible view uses months (13 - H)..12  (most recent H months).
    """
    # months is an array of month numbers (1..12)
    cutoff_start = obs_months - H + 1  # e.g. H=6 → months 7..12
    mask = months >= cutoff_start
    return mask


# ── Per-applicant feature computation ─────────────────────────────────────────

def _compute_features_for_applicant(
    app_monthly: pd.DataFrame,
    H: int,
    obs_months: int = 12,
) -> dict:
    """
    Compute A+B features for a single applicant given their visible window.
    app_monthly: rows for this applicant from monthly.parquet, months 1..12 only.
    H: number of visible months to use.
    """
    # Select visible months: most recent H months
    all_months = app_monthly["month"].values
    mask = _get_visible_months(all_months, H, obs_months)
    visible = app_monthly[mask]

    income = visible["income"].values
    expense = visible["expense"].values
    debt = visible["debt_payment"].values
    liquidity = visible["liquidity"].values

    feats: dict = {}

    # Set A
    feats["income_mean"] = _income_mean(income)
    feats["expense_mean"] = _expense_mean(expense)
    feats["expense_ratio"] = _expense_ratio(expense, income)
    feats["debt_mean"] = _debt_mean(debt)
    feats["has_emi"] = _has_emi(debt)
    feats["liquidity_mean"] = _liquidity_mean(liquidity)
    feats["liquidity_min"] = _liquidity_min(liquidity)

    # Set B
    feats["income_volatility"] = _income_volatility(income)
    feats["income_trend"] = _income_trend(income)
    # platform_tenure and multi_platform: static as-of-cutoff, not recomputed from window
    # They are passed in from applicants_df — see build_features()
    feats["seasonality_index"] = _seasonality_index(income)

    return feats


# ── Main build_features function ───────────────────────────────────────────────

def build_features(
    monthly: pd.DataFrame,
    applicants: pd.DataFrame,
    policy_states: pd.DataFrame | None = None,
    view: str = "visible",
    obs_months: int = 12,
) -> pd.DataFrame:
    """
    Build the 23-column feature table.

    Parameters
    ----------
    monthly    : monthly.parquet (all 24 months; only months 1-12 used here)
    applicants : applicants.parquet (static attributes + split + default_flag)
    policy_states : optional DataFrame with applicant_id, jan_samarth_state, pmmy_state
                    (output of policy rule engine). If None, columns filled with None.
    view       : "full" | "visible" | "H1" | "H3" | "H6" | "H12"
    obs_months : 12 (from config)

    Returns
    -------
    DataFrame with ALL_COLUMNS_ORDERED (23 columns)
    """
    assert view in {"full", "visible", "H1", "H3", "H6", "H12"}, f"Unknown view: {view}"

    # Restrict to observation window only (months 1-12)
    monthly_obs = monthly[monthly["month"] <= obs_months].copy()

    # ── Determine H per applicant ─────────────────────────────────────────────
    h_map = {"full": obs_months, "H1": 1, "H3": 3, "H6": 6, "H12": 12}
    if view == "visible":
        h_series = applicants.set_index("applicant_id")["history_length"].astype(int)
    else:
        fixed_h = h_map[view]
        h_series = pd.Series(fixed_h, index=applicants["applicant_id"])

    # ── Select visible months per applicant ───────────────────────────────────
    # For each applicant: keep the most-recent H months (months obs_months-H+1 .. obs_months)
    # Since each H is in {1,3,6,12} and obs_months=12, visible = months >= (13 - H)
    # Join H onto monthly_obs and filter in one pass.
    monthly_obs = monthly_obs.join(
        h_series.rename("_H"), on="applicant_id"
    )
    monthly_obs = monthly_obs[
        monthly_obs["month"] >= (obs_months + 1 - monthly_obs["_H"])
    ]

    # ── Vectorized features via groupby ──────────────────────────────────────
    g = monthly_obs.groupby("applicant_id")

    income_mean   = g["income"].mean()
    expense_mean  = g["expense"].mean()
    debt_mean     = g["debt_payment"].mean()
    liquidity_mean= g["liquidity"].mean()
    liquidity_min = g["liquidity"].min()
    has_emi       = (g["debt_payment"].max() > 0).astype(int)

    # Income volatility: std / mean (ddof=1), NaN if H < 2
    income_std    = g["income"].std(ddof=1)          # NaN when count < 2
    income_vol    = income_std / income_mean.replace(0, np.nan)

    # Expense ratio: mean(expense) / mean(income)
    expense_ratio = expense_mean / income_mean.replace(0, np.nan)

    # Income trend and seasonality: require per-group OLS — use a fast NumPy path
    # Sort once so we can slice contiguous blocks instead of iterating groups
    monthly_sorted = monthly_obs.sort_values("applicant_id")
    grp_arrays = {}
    for aid, grp in monthly_sorted.groupby("applicant_id", sort=True):
        grp_arrays[aid] = grp["income"].values

    trend_vals = {}
    season_vals = {}
    t12 = np.arange(1, 13, dtype=np.float64)
    X12 = np.column_stack([
        np.ones(12), t12,
        np.sin(2 * np.pi * t12 / 12),
        np.cos(2 * np.pi * t12 / 12),
    ])
    XtX12_inv = np.linalg.inv(X12.T @ X12)

    for aid, inc in grp_arrays.items():
        H = len(inc)
        im = inc.mean()
        # trend
        if H < 3 or im == 0:
            trend_vals[aid] = np.nan
        else:
            t = np.arange(1, H + 1, dtype=np.float64)
            tc = t - t.mean()
            trend_vals[aid] = float(np.dot(tc, inc) / np.dot(tc, tc) / im)
        # seasonality
        if H != 12 or im == 0:
            season_vals[aid] = np.nan
        else:
            coeffs = XtX12_inv @ (X12.T @ inc)
            season_vals[aid] = float(np.sqrt(coeffs[2]**2 + coeffs[3]**2) / im)

    income_trend      = pd.Series(trend_vals, name="income_trend")
    seasonality_index = pd.Series(season_vals, name="seasonality_index")

    # ── Assemble feature frame ────────────────────────────────────────────────
    feats_agg = pd.DataFrame({
        "income_mean":       income_mean,
        "expense_mean":      expense_mean,
        "expense_ratio":     expense_ratio,
        "debt_mean":         debt_mean,
        "has_emi":           has_emi,
        "liquidity_mean":    liquidity_mean,
        "liquidity_min":     liquidity_min,
        "income_volatility": income_vol,
        "income_trend":      income_trend,
        "seasonality_index": seasonality_index,
    })

    # ── Merge with applicants (static attributes + metadata) ─────────────────
    app_indexed = applicants.set_index("applicant_id")
    feats_agg = feats_agg.join(app_indexed[[
        "platform_tenure", "multi_platform", "history_length",
        "aa_completeness", "uli_completeness", "e_shram_registered",
        "dgp_id", "seed_id", "split", "default_flag",
    ]])
    feats_agg.index.name = "applicant_id"
    features_df = feats_agg.reset_index()

    rows = None  # not used in vectorized path

    # Policy states (engine outputs — POL only, not in PD model)
    if policy_states is not None:
        features_df = features_df.merge(
            policy_states[["applicant_id", "jan_samarth_state", "pmmy_state"]],
            on="applicant_id",
            how="left",
        )
    else:
        features_df["jan_samarth_state"] = None
        features_df["pmmy_state"] = None

    # Enforce column order
    for col in ALL_COLUMNS_ORDERED:
        if col not in features_df.columns:
            features_df[col] = None
    features_df = features_df[ALL_COLUMNS_ORDERED]

    # Enforce types
    for col in FEATURE_SET_C + EVIDENCE_COLS:
        features_df[col] = pd.to_numeric(features_df[col], errors="coerce")

    return features_df


# ── CLI entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build feature tables")
    parser.add_argument("--config", default="configs/experiment.yaml")
    parser.add_argument("--dgp", type=int, required=True, choices=[1, 2])
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument(
        "--view", default="visible",
        choices=["full", "visible", "H1", "H3", "H6", "H12"],
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    out_dir = get_output_dir(cfg, args.dgp, args.seed)

    monthly = pd.read_parquet(out_dir / "monthly.parquet")
    applicants = pd.read_parquet(out_dir / "applicants.parquet")

    features = build_features(
        monthly, applicants,
        view=args.view,
        obs_months=cfg["data"]["obs_months"],
    )

    fname = f"features_{args.view}.parquet"
    out_path = out_dir / fname
    features.to_parquet(out_path, index=False)
    print(f"[build_features] view={args.view} -> {out_path}")
    print(f"  shape={features.shape}  NaN summary:")
    print(features[FEATURE_SET_C].isna().sum().to_string())
