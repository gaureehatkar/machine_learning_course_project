#!/usr/bin/env python
"""
Save per-seed test predictions as .npz for T2_v2 and T6_v2,
and update research/tables/benchmarks/calibration_old_vs_new.csv with T6 rows.
"""
from __future__ import annotations
import sys, time
from pathlib import Path
import numpy as np
import pandas as pd

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

T2_DIR = ROOT / "results/benchmarks/T2_v2"
T6_DIR = ROOT / "results/benchmarks/T6_v2"
TABLES = ROOT / "research/tables"
BENCH  = TABLES / "benchmarks"

T2_DIR.mkdir(parents=True, exist_ok=True)
T6_DIR.mkdir(parents=True, exist_ok=True)
BENCH.mkdir(parents=True, exist_ok=True)


def main():
    cfg = load_config(ROOT / "configs/experiment.yaml")

    # 1. Process T2 and save .npz
    print("--- Saving T2_v2 predictions ---")
    t2_raw = pd.read_csv(TABLES / "T2_ablation_raw.csv")
    for _, row in t2_raw.iterrows():
        dgp_id = int(row["dgp"])
        seed = int(row["seed"])
        config = str(row["config"])
        fs, fam = config.split("_", 1)

        npz_path = T2_DIR / f"predictions_dgp{dgp_id}_s{seed}_{config}.npz"
        if not npz_path.exists():
            out_dir = get_output_dir(cfg, dgp_id, seed)
            ffull = pd.read_parquet(out_dir / "features_full.parquet")
            fvis  = pd.read_parquet(out_dir / "features_visible.parquet")

            train_f = ffull[ffull["split"] == "train"].reset_index(drop=True)
            val_f   = fvis[fvis["split"] == "val"].reset_index(drop=True)
            test_f  = fvis[fvis["split"] == "test"].reset_index(drop=True)

            fitted = train_model(train_f, fs, fam, cfg, seed=seed, dgp_id=dgp_id, dataset_seed=seed)
            p_raw_v = fitted.predict_raw(val_f)
            p_raw_t = fitted.predict_raw(test_f)
            cal = fit_platt(p_raw_v, val_f["default_flag"].values)
            p_cal_v = cal.transform(p_raw_v)
            p_cal_t = cal.transform(p_raw_t)

            np.savez_compressed(
                npz_path,
                y_test=test_f["default_flag"].values.astype(np.float32),
                p_raw_test=p_raw_t.astype(np.float32),
                p_cal_test=p_cal_t.astype(np.float32),
                y_val=val_f["default_flag"].values.astype(np.float32),
                p_raw_val=p_raw_v.astype(np.float32),
                p_cal_val=p_cal_v.astype(np.float32),
            )
    print("Saved all T2_v2 .npz files.")

    # 2. Process T6 and save .npz
    print("--- Saving T6_v2 predictions ---")
    t6_raw = pd.read_csv(TABLES / "T6_history_raw.csv")
    for _, row in t6_raw.iterrows():
        dgp_id = int(row["dgp"])
        seed = int(row["seed"])
        H = str(row["H"])

        npz_path = T6_DIR / f"predictions_dgp{dgp_id}_s{seed}_{H}.npz"
        if not npz_path.exists():
            out_dir = get_output_dir(cfg, dgp_id, seed)
            ffull = pd.read_parquet(out_dir / "features_full.parquet")
            fvis  = pd.read_parquet(out_dir / "features_visible.parquet")

            train_f = ffull[ffull["split"] == "train"].reset_index(drop=True)
            val_f   = fvis[fvis["split"] == "val"].reset_index(drop=True)

            if H == "visible":
                test_f = fvis[fvis["split"] == "test"].reset_index(drop=True)
            else:
                monthly = pd.read_parquet(out_dir / "monthly.parquet")
                applicants = pd.read_parquet(out_dir / "applicants.parquet")
                test_all = build_features(monthly, applicants, view=H, obs_months=cfg["data"]["obs_months"])
                test_f = test_all[test_all["split"] == "test"].reset_index(drop=True)

            fitted = train_model(train_f, "C", "xgb", cfg, seed=seed, dgp_id=dgp_id, dataset_seed=seed)
            p_raw_v = fitted.predict_raw(val_f)
            p_raw_t = fitted.predict_raw(test_f)
            cal = fit_platt(p_raw_v, val_f["default_flag"].values)
            p_cal_v = cal.transform(p_raw_v)
            p_cal_t = cal.transform(p_raw_t)

            np.savez_compressed(
                npz_path,
                y_test=test_f["default_flag"].values.astype(np.float32),
                p_raw_test=p_raw_t.astype(np.float32),
                p_cal_test=p_cal_t.astype(np.float32),
                y_val=val_f["default_flag"].values.astype(np.float32),
                p_raw_val=p_raw_v.astype(np.float32),
                p_cal_val=p_cal_v.astype(np.float32),
            )
    print("Saved all T6_v2 .npz files.")

    # 3. Update calibration_old_vs_new.csv with T6 rows
    print("--- Updating calibration_old_vs_new.csv with T6 ---")
    cal_df = pd.read_csv(BENCH / "calibration_old_vs_new.csv")

    t6_old_agg = pd.read_csv(TABLES / "T6_history_agg.csv")
    t6_v2_agg  = pd.read_csv(TABLES / "T6_history_agg_v2.csv")

    # Remove any existing T6 rows to avoid duplicates
    cal_df = cal_df[cal_df["experiment"] != "T6"].copy()

    new_rows = []
    for _, r_old in t6_old_agg.iterrows():
        dgp_num = int(r_old["dgp"])
        h_val = str(r_old["H"])
        match_v2 = t6_v2_agg[(t6_v2_agg["dgp"] == dgp_num) & (t6_v2_agg["H"] == h_val)]
        if len(match_v2):
            r_v2 = match_v2.iloc[0]
            new_rows.append({
                "experiment": "T6",
                "dataset": "Synthetic",
                "dgp": f"DGP{dgp_num}",
                "config": f"C_xgb_{h_val}",
                "n_seeds": 10,
                "auc_old": float(r_old["roc_auc_mean"]),
                "auc_new": float(r_v2["roc_auc_mean"]),
                "brier_old": float(r_old["brier_mean"]),
                "brier_new": float(r_v2["brier_mean"]),
                "ece_old": float(r_old["ece_mean"]),
                "ece_new": float(r_v2["ece_mean"]),
                "slope_ols": float(r_old["calibration_slope_mean"]),
                "slope_logistic": float(r_v2["calibration_slope_mean"]),
                "intercept_logistic": float(r_v2["calibration_intercept_mean"]),
            })

    cal_df = pd.concat([cal_df, pd.DataFrame(new_rows)], ignore_index=True)
    cal_df.to_csv(BENCH / "calibration_old_vs_new.csv", index=False)
    print(f"calibration_old_vs_new.csv now has {len(cal_df)} rows.")


if __name__ == "__main__":
    main()
