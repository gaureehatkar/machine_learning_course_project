#!/usr/bin/env python
"""Regenerate all synthetic datasets and feature views.

Recreates data/synthetic/dgp{1,2}/seed{0..10}/ with:
  - monthly.parquet, applicants.parquet, policy_attributes.parquet, latent_params.parquet
  - features_full.parquet, features_visible.parquet
  - features_H1/H3/H6/H12.parquet (forced-history views for the T6 experiment)

Seed 0 is the Gate-G0 / hyperparameter-tuning seed; seeds 1-10 are the
experimental seeds. This script is the tracked replacement for the gitignored
`generate_all_seeds.py` convenience wrapper.

Usage:
    python -m scripts.regenerate_synthetic_data
    python -u scripts/regenerate_synthetic_data.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.config_loader import load_config, get_output_dir
from src.data_generation.generate_data import generate_data, save_data
from src.feature_engineering.build_features import build_features

# full + visible are the main train/score views; H1/H3/H6/H12 are the forced-history
# views scored (without refit) in the T6 history-sensitivity experiment.
VIEWS = ["full", "visible", "H1", "H3", "H6", "H12"]
DGPS = [1, 2]
SEEDS = list(range(0, 11))  # 0 = G0/tuning seed, 1-10 = experimental seeds


def main() -> None:
    cfg = load_config(ROOT / "configs/experiment.yaml")
    obs_months = cfg["data"]["obs_months"]
    t0 = time.time()

    print("=" * 64)
    print("Regenerating synthetic data: 2 DGPs x 11 seeds x 6 feature views")
    print("=" * 64)

    # ── 1. Generate raw datasets ──────────────────────────────────────────────
    for dgp in DGPS:
        for seed in SEEDS:
            t_s = time.time()
            monthly, applicants, policy_attrs, latent = generate_data(cfg, dgp, seed)
            save_data(cfg, dgp, seed, monthly, applicants, policy_attrs, latent)
            print(f"  [gen] DGP{dgp} seed{seed:2d} done in {time.time()-t_s:.1f}s", flush=True)

    # ── 2. Build feature views ────────────────────────────────────────────────
    for dgp in DGPS:
        for seed in SEEDS:
            out_dir = get_output_dir(cfg, dgp, seed)
            monthly = __import__("pandas").read_parquet(out_dir / "monthly.parquet")
            applicants = __import__("pandas").read_parquet(out_dir / "applicants.parquet")
            for view in VIEWS:
                features = build_features(
                    monthly, applicants, view=view, obs_months=obs_months
                )
                out_path = out_dir / f"features_{view}.parquet"
                features.to_parquet(out_path, index=False)
            print(f"  [feat] DGP{dgp} seed{seed:2d} all views built", flush=True)

    print("=" * 64)
    print(f"Done in {time.time()-t0:.1f}s")
    print(f"  {len(DGPS)} DGPs x {len(SEEDS)} seeds x {len(VIEWS)} views = "
          f"{len(DGPS)*len(SEEDS)*len(VIEWS)} feature files")


if __name__ == "__main__":
    main()
