"""
Per-seed evaluation runner — computes all metrics for one (dgp_id, seed) pair.
Writes results to results/<experiment>/dgp{d}/seed{s}/.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd

from src.utils.config_loader import load_config, get_output_dir
from src.evaluation.metrics import compute_all_metrics


def evaluate_seed(cfg: dict, dgp_id: int, seed: int) -> dict:
    out_dir = get_output_dir(cfg, dgp_id, seed)
    results_dir = Path(f"results/ablation/dgp{dgp_id}/seed{seed}")

    summary = {"dgp_id": dgp_id, "seed_id": seed, "models": {}}

    # Load ablation results if available
    ablation_path = results_dir / "T2_results.json"
    if ablation_path.exists():
        with ablation_path.open() as fh:
            summary["models"] = json.load(fh)

    return summary


def aggregate_over_seeds(cfg: dict) -> dict:
    """Aggregate per-seed results into mean ± CI tables."""
    from src.evaluation.statistical_tests import seed_level_ci

    all_results: dict[str, dict] = {}
    for dgp_id in cfg["data"]["dgps"]:
        dgp_key = f"dgp{dgp_id}"
        all_results[dgp_key] = {}
        seed_data: dict[str, list] = {}

        for seed in cfg["data"]["seeds"]:
            res_path = Path(f"results/ablation/dgp{dgp_id}/seed{seed}/T2_results.json")
            if not res_path.exists():
                continue
            with res_path.open() as fh:
                seed_res = json.load(fh)
            for key, metrics in seed_res.items():
                if isinstance(metrics, dict) and "roc_auc" in metrics:
                    if key not in seed_data:
                        seed_data[key] = []
                    seed_data[key].append(metrics["roc_auc"])

        for model_key, roc_list in seed_data.items():
            if len(roc_list) >= 2:
                mean, lo, hi = seed_level_ci(roc_list)
                all_results[dgp_key][model_key] = {
                    "roc_auc_mean": round(mean, 4),
                    "roc_auc_ci_lo": round(lo, 4),
                    "roc_auc_ci_hi": round(hi, 4),
                    "n_seeds": len(roc_list),
                }

    return all_results
