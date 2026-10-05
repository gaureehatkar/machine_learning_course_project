"""
History experiment — forced H ∈ {1,3,6,12} on test set, no refit (T6)
TECH_DOC §16.5
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

from src.utils.config_loader import load_config, get_output_dir
from src.models.train_models import train_model
from src.calibration.platt import fit_platt
from src.feature_engineering.build_features import build_features
from src.evaluation.metrics import compute_all_metrics


def run_history(cfg_path: str, dgp_id: int, seed: int):
    cfg = load_config(cfg_path)
    out_dir = get_output_dir(cfg, dgp_id, seed)

    monthly    = pd.read_parquet(out_dir / "monthly.parquet")
    applicants = pd.read_parquet(out_dir / "applicants.parquet")
    features_full = pd.read_parquet(out_dir / "features_full.parquet")

    train_f = features_full[features_full["split"] == "train"]
    val_visible = build_features(monthly, applicants, view="visible",
                                  obs_months=cfg["data"]["obs_months"])
    val_f = val_visible[val_visible["split"] == "val"]

    # Train on full 12-month view
    fitted = train_model(train_f, "C", "xgb", cfg, seed=seed)
    p_raw_val = fitted.predict_raw(val_f)
    cal = fit_platt(p_raw_val, val_f["default_flag"].values)

    results = {}
    for H in [1, 3, 6, 12]:
        test_H = build_features(monthly, applicants, view=f"H{H}",
                                 obs_months=cfg["data"]["obs_months"])
        test_H = test_H[test_H["split"] == "test"]
        p_raw  = fitted.predict_raw(test_H)
        p_cal  = cal.transform(p_raw)
        y_test = test_H["default_flag"].values
        metrics = compute_all_metrics(y_test, p_cal)
        results[f"H{H}"] = metrics
        print(f"  H={H:2d}: ROC-AUC={metrics['roc_auc']:.4f}  PR-AUC={metrics['pr_auc']:.4f}")

    res_dir = Path(f"results/history/dgp{dgp_id}/seed{seed}")
    res_dir.mkdir(parents=True, exist_ok=True)
    with (res_dir / "T6_results.json").open("w") as fh:
        json.dump(results, fh, indent=2)
    print(f"History results -> {res_dir}/T6_results.json")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiment.yaml")
    parser.add_argument("--dgp", type=int, default=1)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    run_history(args.config, args.dgp, args.seed)
