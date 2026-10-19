#!/usr/bin/env python
"""
Phase 0 — Recompute T2 and T6 calibration slopes with the fixed logistic method.

Reads the existing raw CSVs (not modified), replaces calibration_slope and
calibration_intercept columns, and writes *_v2 files with:
  - calibration_slope         (new logistic)
  - calibration_intercept     (new logistic)
  - calibration_slope_ols     (old OLS, kept for comparison)
  - calibration_intercept_ols (old OLS, kept for comparison)

Writes:
  research/tables/T2_ablation_raw_v2.csv
  research/tables/T2_ablation_agg_v2.csv
  research/tables/T6_history_raw_v2.csv
  research/tables/T6_history_agg_v2.csv

Does NOT overwrite or modify the originals.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as t_dist

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.evaluation.metrics import (
    calibration_slope_intercept,
    calibration_slope_ols_deprecated,
)
from src.utils.config_loader import load_config, get_output_dir
from src.models.train_models import train_model
from src.calibration.platt import fit_platt

TABLES = ROOT / "research" / "tables"


def recompute_slopes(df_raw: pd.DataFrame, feature_set_col: str, cfg) -> pd.DataFrame:
    """
    Re-derive calibration slope for every (dgp, seed, config) row by
    re-training the model and recomputing the slope on the saved predictions.

    To avoid re-running the full pipeline, we use the saved per-seed
    features parquets and re-run only the calibration slope calculation
    with the new function.
    """
    rows = []
    for _, row in df_raw.iterrows():
        dgp_id = int(row["dgp"])
        seed   = int(row["seed"])
        config = str(row[feature_set_col])  # e.g. "A_logreg" or "H1"

        out_dir = get_output_dir(cfg, dgp_id, seed)

        # Parse feature_set and family
        if "_" in config and config[1] == "_":
            # T2 format: "A_logreg", "B_xgb", etc.
            fs, fam = config.split("_", 1)
            h_view = "visible"
        else:
            # T6 format: "H1", "H3", "H6", "H12"
            fs = "C"
            fam = "xgb"
            h_view = config  # "H1", "H3", etc.

        try:
            ffull = pd.read_parquet(out_dir / "features_full.parquet")
            fvis  = pd.read_parquet(out_dir / "features_visible.parquet")

            train_f = ffull[ffull["split"] == "train"].reset_index(drop=True)
            val_f   = fvis[fvis["split"] == "val"].reset_index(drop=True)

            if h_view == "visible":
                test_f = fvis[fvis["split"] == "test"].reset_index(drop=True)
            else:
                # T6: rebuild forced-H test set
                monthly    = pd.read_parquet(out_dir / "monthly.parquet")
                applicants = pd.read_parquet(out_dir / "applicants.parquet")
                from src.feature_engineering.build_features import build_features
                test_all = build_features(monthly, applicants, view=h_view,
                                          obs_months=cfg["data"]["obs_months"])
                test_f = test_all[test_all["split"] == "test"].reset_index(drop=True)

            fitted   = train_model(train_f, fs, fam, cfg, seed=seed, dgp_id=dgp_id, dataset_seed=seed)
            p_raw_v  = fitted.predict_raw(val_f)
            p_raw_t  = fitted.predict_raw(test_f)
            cal      = fit_platt(p_raw_v, val_f["default_flag"].values)
            p_cal    = cal.transform(p_raw_t)
            y        = test_f["default_flag"].values

            slope_new,  icept_new  = calibration_slope_intercept(y, p_cal)
            slope_ols,  icept_ols  = calibration_slope_ols_deprecated(y, p_cal)

            new_row = row.to_dict()
            new_row["calibration_slope"]         = slope_new
            new_row["calibration_intercept"]     = icept_new
            new_row["calibration_slope_ols"]     = slope_ols
            new_row["calibration_intercept_ols"] = icept_ols
            rows.append(new_row)
            print(f"  DGP{dgp_id} s{seed} {config}: new={slope_new:.4f}  ols={slope_ols:.4f}")
        except Exception as e:
            print(f"  DGP{dgp_id} s{seed} {config}: ERROR {e}")
            rows.append(row.to_dict())

    return pd.DataFrame(rows)


def seed_ci_agg(df: pd.DataFrame, group_cols: list, val_cols: list) -> pd.DataFrame:
    """Aggregate with mean ± 95% CI using dynamic t-crit from scipy."""
    rows = []
    for gv, gdf in df.groupby(group_cols):
        row = dict(zip(group_cols, gv if isinstance(gv, tuple) else (gv,)))
        n_seeds = len(gdf)
        t_crit = float(t_dist.ppf(0.975, n_seeds - 1)) if n_seeds > 1 else 0.0
        for col in val_cols:
            if col in gdf.columns:
                vals = gdf[col].dropna().values.astype(float)
                if len(vals) > 0:
                    mn  = float(np.mean(vals))
                    std = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
                    ci  = t_crit * std / np.sqrt(len(vals)) if len(vals) > 1 else 0.0
                    row[f"{col}_mean"] = round(mn, 4)
                    row[f"{col}_std"]  = round(std, 4)
                    row[f"{col}_ci"]   = round(ci, 4)
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    cfg = load_config(ROOT / "configs/experiment.yaml")
    TABLES.mkdir(parents=True, exist_ok=True)

    # ── T2 ─────────────────────────────────────────────────────────────────
    print("=" * 60)
    print("T2: recomputing calibration slopes")
    print("=" * 60)
    t2_raw = pd.read_csv(TABLES / "T2_ablation_raw.csv")
    t2_raw_v2 = recompute_slopes(t2_raw, "config", cfg)
    t2_raw_v2.to_csv(TABLES / "T2_ablation_raw_v2.csv", index=False)

    metric_cols = ["roc_auc", "pr_auc", "brier", "ece",
                   "calibration_slope", "calibration_intercept",
                   "calibration_slope_ols", "calibration_intercept_ols",
                   "gini", "ks"]
    t2_agg_v2 = seed_ci_agg(t2_raw_v2, ["dgp", "config"], metric_cols)
    t2_agg_v2.to_csv(TABLES / "T2_ablation_agg_v2.csv", index=False)
    print(f"Saved T2_ablation_raw_v2.csv + T2_ablation_agg_v2.csv")

    # ── T6 ─────────────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("T6: recomputing calibration slopes")
    print("=" * 60)
    t6_raw = pd.read_csv(TABLES / "T6_history_raw.csv")
    t6_raw_v2 = recompute_slopes(t6_raw, "H", cfg)
    # Add numeric H column (Phase 4 fix bundled here)
    t6_raw_v2["H_num"] = t6_raw_v2["H"].str.replace("H", "").astype(int)
    t6_raw_v2.to_csv(TABLES / "T6_history_raw_v2.csv", index=False)

    metric_cols_t6 = metric_cols + ["evidence_mean", "evidence_fail_rate"]
    t6_agg_v2 = seed_ci_agg(t6_raw_v2, ["dgp", "H"], metric_cols_t6)
    t6_agg_v2["H_num"] = t6_agg_v2["H"].str.replace("H", "").astype(int)
    t6_agg_v2.to_csv(TABLES / "T6_history_agg_v2.csv", index=False)
    print(f"Saved T6_history_raw_v2.csv + T6_history_agg_v2.csv")

    # ── Side-by-side comparison ─────────────────────────────────────────────
    print()
    print("=== Calibration slope comparison: OLD (OLS) vs NEW (logistic) ===")
    print("T2 — DGP1:")
    comp = t2_agg_v2[t2_agg_v2["dgp"] == 1][
        ["config", "calibration_slope_ols_mean", "calibration_slope_mean"]
    ].rename(columns={"calibration_slope_ols_mean": "slope_ols",
                      "calibration_slope_mean": "slope_logistic"})
    print(comp.to_string(index=False))

    print("\nT6 — DGP1:")
    comp6 = t6_agg_v2[t6_agg_v2["dgp"] == 1].sort_values("H_num")[
        ["H", "calibration_slope_ols_mean", "calibration_slope_mean"]
    ].rename(columns={"calibration_slope_ols_mean": "slope_ols",
                      "calibration_slope_mean": "slope_logistic"})
    print(comp6.to_string(index=False))


if __name__ == "__main__":
    main()
