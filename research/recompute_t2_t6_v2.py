#!/usr/bin/env python
"""
Phase 1 (supplement) — Recompute T2 and T6 with logistic calibration slope.

Reads existing raw CSVs (NOT modified), retrains same models, adds:
  calibration_slope         (logistic — new)
  calibration_intercept     (logistic — new)
  calibration_slope_ols     (OLS — old, renamed for clarity)

Writes (new files, do not overwrite originals):
  research/tables/T2_ablation_raw_v2.csv
  research/tables/T2_ablation_agg_v2.csv
  research/tables/T6_history_raw_v2.csv
  research/tables/T6_history_agg_v2.csv  (with H_num column)
  research/tables/benchmarks/calibration_old_vs_new.csv (updated)
"""
from __future__ import annotations
import sys, time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as t_dist

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.config_loader import load_config, get_output_dir
from src.models.train_models import train_model
from src.calibration.platt import fit_platt
from src.evaluation.metrics import (
    compute_all_metrics,
    calibration_slope_intercept,
    calibration_slope_ols_deprecated,
)
from src.feature_engineering.build_features import build_features

TABLES = ROOT / "research" / "tables"
BENCH  = TABLES / "benchmarks"
BENCH.mkdir(parents=True, exist_ok=True)


def seed_ci(df: pd.DataFrame, group_cols: list, val_cols: list) -> pd.DataFrame:
    rows = []
    for gv, gdf in df.groupby(group_cols):
        row = dict(zip(group_cols, gv if isinstance(gv, tuple) else (gv,)))
        n = len(gdf)
        tc = float(t_dist.ppf(0.975, n - 1)) if n > 1 else 0.0
        for c in val_cols:
            if c in gdf.columns:
                v = gdf[c].dropna().values.astype(float)
                if len(v) > 0:
                    mn  = float(np.mean(v))
                    std = float(np.std(v, ddof=1)) if len(v) > 1 else 0.0
                    ci  = tc * std / np.sqrt(len(v)) if len(v) > 1 else 0.0
                    row[f"{c}_mean"] = round(mn, 4)
                    row[f"{c}_std"]  = round(std, 4)
                    row[f"{c}_ci"]   = round(ci, 4)
        rows.append(row)
    return pd.DataFrame(rows)


def compute_logistic_slope_for_row(cfg, dgp_id, seed, feature_set, family, h_view="visible"):
    """Retrain model and return logistic calibration slope on test."""
    out_dir = get_output_dir(cfg, dgp_id, seed)
    ffull = pd.read_parquet(out_dir / "features_full.parquet")
    fvis  = pd.read_parquet(out_dir / "features_visible.parquet")

    train_f = ffull[ffull["split"] == "train"].reset_index(drop=True)
    val_f   = fvis[fvis["split"] == "val"].reset_index(drop=True)

    if h_view == "visible":
        test_f = fvis[fvis["split"] == "test"].reset_index(drop=True)
    else:
        monthly    = pd.read_parquet(out_dir / "monthly.parquet")
        applicants = pd.read_parquet(out_dir / "applicants.parquet")
        test_all = build_features(monthly, applicants, view=h_view,
                                  obs_months=cfg["data"]["obs_months"])
        test_f = test_all[test_all["split"] == "test"].reset_index(drop=True)

    fitted   = train_model(train_f, feature_set, family, cfg,
                           seed=seed, dgp_id=dgp_id, dataset_seed=seed)
    p_raw_v  = fitted.predict_raw(val_f)
    p_raw_t  = fitted.predict_raw(test_f)
    cal      = fit_platt(p_raw_v, val_f["default_flag"].values)
    p_cal    = cal.transform(p_raw_t)
    y        = test_f["default_flag"].values

    slope_new, icept_new = calibration_slope_intercept(y, p_cal)
    slope_ols, icept_ols = calibration_slope_ols_deprecated(y, p_cal)
    return slope_new, icept_new, slope_ols, icept_ols


def main():
    cfg = load_config(ROOT / "configs/experiment.yaml")

    # ── T2 ────────────────────────────────────────────────────────────────────
    print("="*60)
    print("T2: recomputing calibration slopes (logistic)")
    print("="*60)
    t2_raw = pd.read_csv(TABLES / "T2_ablation_raw.csv")
    rows = []
    for _, row in t2_raw.iterrows():
        dgp_id = int(row["dgp"]); seed = int(row["seed"]); config = str(row["config"])
        fs, fam = config.split("_", 1)
        print(f"  DGP{dgp_id} s{seed} {config}...", end=" ", flush=True)
        t0 = time.time()
        try:
            sn, in_, so, io = compute_logistic_slope_for_row(cfg, dgp_id, seed, fs, fam)
            r = row.to_dict()
            r["calibration_slope"]         = sn
            r["calibration_intercept"]     = in_
            r["calibration_slope_ols"]     = so
            r["calibration_intercept_ols"] = io
            rows.append(r)
            print(f"logistic={sn:.4f} ols={so:.4f} ({time.time()-t0:.1f}s)")
        except Exception as e:
            print(f"ERR {e}")
            rows.append(row.to_dict())

    t2_v2 = pd.DataFrame(rows)
    t2_v2.to_csv(TABLES / "T2_ablation_raw_v2.csv", index=False)

    mc = ["roc_auc","pr_auc","brier","ece","calibration_slope","calibration_intercept",
          "calibration_slope_ols","gini","ks"]
    seed_ci(t2_v2, ["dgp","config"], mc).to_csv(TABLES / "T2_ablation_agg_v2.csv", index=False)
    print("Saved T2_ablation_raw_v2.csv + T2_ablation_agg_v2.csv")

    # ── T6 ────────────────────────────────────────────────────────────────────
    print()
    print("="*60)
    print("T6: recomputing calibration slopes (logistic)")
    print("="*60)
    t6_raw = pd.read_csv(TABLES / "T6_history_raw.csv")
    rows6 = []
    for _, row in t6_raw.iterrows():
        dgp_id = int(row["dgp"]); seed = int(row["seed"]); H = str(row["H"])
        print(f"  DGP{dgp_id} s{seed} {H}...", end=" ", flush=True)
        t0 = time.time()
        try:
            sn, in_, so, io = compute_logistic_slope_for_row(
                cfg, dgp_id, seed, "C", "xgb", h_view=H)
            r = row.to_dict()
            r["calibration_slope"]         = sn
            r["calibration_intercept"]     = in_
            r["calibration_slope_ols"]     = so
            r["calibration_intercept_ols"] = io
            r["H_num"] = int(H.replace("H",""))
            rows6.append(r)
            print(f"logistic={sn:.4f} ({time.time()-t0:.1f}s)")
        except Exception as e:
            print(f"ERR {e}")
            r = row.to_dict(); r["H_num"] = int(H.replace("H",""))
            rows6.append(r)

    t6_v2 = pd.DataFrame(rows6)
    t6_v2.to_csv(TABLES / "T6_history_raw_v2.csv", index=False)
    mc6 = mc + ["evidence_mean","evidence_fail_rate"]
    t6_agg = seed_ci(t6_v2, ["dgp","H"], mc6)
    t6_agg["H_num"] = t6_agg["H"].str.replace("H","").astype(int)
    t6_agg.to_csv(TABLES / "T6_history_agg_v2.csv", index=False)
    print("Saved T6_history_raw_v2.csv + T6_history_agg_v2.csv")

    # ── Update calibration comparison table ───────────────────────────────────
    print()
    base = pd.read_csv(BENCH / "calibration_old_vs_new.csv")
    t2_agg_v2 = pd.read_csv(TABLES / "T2_ablation_agg_v2.csv")
    for idx, row in base.iterrows():
        if row["experiment"] == "T2":
            dgp_val = int(str(row["dgp"]).replace("DGP",""))
            match = t2_agg_v2[
                (t2_agg_v2["dgp"] == dgp_val) &
                (t2_agg_v2["config"] == row["config"])
            ]
            if len(match):
                base.at[idx, "auc_new"]           = match["roc_auc_mean"].iloc[0]
                base.at[idx, "brier_new"]          = match["brier_mean"].iloc[0]
                base.at[idx, "ece_new"]            = match["ece_mean"].iloc[0]
                base.at[idx, "slope_logistic"]     = match["calibration_slope_mean"].iloc[0]
                base.at[idx, "intercept_logistic"] = match["calibration_intercept_mean"].iloc[0]
    base.to_csv(BENCH / "calibration_old_vs_new.csv", index=False)
    print("Updated calibration_old_vs_new.csv with T2 logistic slopes")

    print("\nAll done.")


if __name__ == "__main__":
    main()
