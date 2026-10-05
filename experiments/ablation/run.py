"""Ablation experiment — A/B/C feature sets × LR/XGB (T2)."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
from src.utils.config_loader import load_config, get_output_dir
from src.models.train_models import train_model
from src.calibration.platt import fit_platt
from src.evaluation.metrics import compute_all_metrics


def run_ablation(cfg_path: str, dgp_id: int, seed: int):
    cfg = load_config(cfg_path)
    out_dir = get_output_dir(cfg, dgp_id, seed)
    features_full    = pd.read_parquet(out_dir / "features_full.parquet")
    features_visible = pd.read_parquet(out_dir / "features_visible.parquet")

    results = {}
    for feature_set in ["A", "B", "C"]:
        for family in ["logreg", "xgb"]:
            key = f"{feature_set}_{family}"
            print(f"  Training dgp={dgp_id} seed={seed} set={feature_set} family={family}")
            train_f = features_full[features_full["split"] == "train"]
            val_f   = features_visible[features_visible["split"] == "val"]
            test_f  = features_visible[features_visible["split"] == "test"]

            try:
                fitted = train_model(train_f, feature_set, family, cfg,
                                     seed=seed, dgp_id=dgp_id, dataset_seed=seed)
                p_raw_val  = fitted.predict_raw(val_f)
                p_raw_test = fitted.predict_raw(test_f)
                cal = fit_platt(p_raw_val, val_f["default_flag"].values)
                p_cal_test = cal.transform(p_raw_test)
                metrics = compute_all_metrics(test_f["default_flag"].values, p_cal_test)
                results[key] = metrics
                print(f"    ROC-AUC={metrics['roc_auc']:.4f}  PR-AUC={metrics['pr_auc']:.4f}")
            except Exception as e:
                print(f"    ERROR: {e}")
                results[key] = {"error": str(e)}

    res_dir = Path(f"results/ablation/dgp{dgp_id}/seed{seed}")
    res_dir.mkdir(parents=True, exist_ok=True)
    with (res_dir / "T2_results.json").open("w") as fh:
        json.dump(results, fh, indent=2)
    print(f"Ablation results -> {res_dir}/T2_results.json")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiment.yaml")
    parser.add_argument("--dgp", type=int, default=1)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    run_ablation(args.config, args.dgp, args.seed)
