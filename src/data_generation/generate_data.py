"""
generate_data(cfg, dgp_id, seed) -> (monthly_df, applicants_df, policy_attributes_df)

Implements the module contract from IMPLEMENTATION_PLAN.md §4.
Writes output parquet files to data/synthetic/dgp{dgp_id}/seed{seed}/.

Latent params (b, sigma_m, g, amp, phase, rho, ...) are written to
latent_params.parquet — write-only for the generator; never read by feature code.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit

from src.data_generation.dgp import (
    _draw_static_attributes,
    _draw_policy_attributes,
    _simulate_monthly,
)
from src.utils.config_loader import load_config, get_output_dir
from src.utils.seeding import make_static_rng, make_outcome_rng, split_seed


def generate_data(
    cfg: dict[str, Any],
    dgp_id: int,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Generate SynthGigCredit-IN-v1 for one (dgp_id, seed) pair.

    Returns
    -------
    monthly_df         : (n_applicants × 24) rows — applicant_id, month, income, ...
    applicants_df      : (n_applicants) rows — static attributes + default_flag + split
    policy_attributes_df : (n_applicants) rows — age, occupation_category, nonfarm_business_flag
    """
    n = cfg["data"]["n_applicants"]
    applicant_ids = [f"A{i:06d}" for i in range(n)]

    # ── RNG substreams — SEPARATE for static/obs vs outcome (T-D9) ────────────
    static_rng = make_static_rng(seed)
    outcome_rng = make_outcome_rng(seed)

    # ── 1. Draw static attributes (cutoff-dated) ──────────────────────────────
    static = _draw_static_attributes(static_rng, n, cfg)

    # ── 2. Draw policy attributes (separate table, cutoff-dated) ─────────────
    policy_attrs = _draw_policy_attributes(static_rng, n, cfg)
    # Note: policy attributes use the same static_rng since they are
    # observation-cutoff quantities (not outcome-window)

    # ── 3. Simulate 24 monthly records ───────────────────────────────────────
    monthly_df, default_flag = _simulate_monthly(
        static, n, dgp_id, cfg, static_rng, outcome_rng
    )

    # ── 4. Build applicants dataframe ─────────────────────────────────────────
    applicants_df = pd.DataFrame({
        "applicant_id": applicant_ids,
        "dgp_id": np.int8(dgp_id),
        "seed_id": np.int8(seed),
        "has_emi": static["has_emi"],
        # platform_tenure: AS OF the observation cutoff (end of month 12)
        # §10.5: static, no accrual during months 13-24
        "platform_tenure": static["tenure_cutoff"].astype(np.int8),
        # multi_platform: AS OF the cutoff — frozen
        "multi_platform": static["multi_platform"],
        "e_shram_registered": static["e_shram_registered"],
        "aa_completeness": static["aa_completeness"],
        "uli_completeness": static["uli_completeness"],
        "history_length": static["history_length"],
        "default_flag": default_flag,
    })

    # ── 5. Stratified train/val/test split 60/20/20 ───────────────────────────
    sss1 = StratifiedShuffleSplit(
        n_splits=1, test_size=0.20, random_state=split_seed(seed)
    )
    sss2 = StratifiedShuffleSplit(
        n_splits=1, test_size=0.25, random_state=split_seed(seed) + 1
        # 0.25 of 0.80 = 0.20 overall => 60/20/20
    )
    idx = np.arange(n)
    y = applicants_df["default_flag"].values

    train_val_idx, test_idx = next(sss1.split(idx, y))
    train_idx, val_idx = next(sss2.split(train_val_idx, y[train_val_idx]))
    train_idx = train_val_idx[train_idx]
    val_idx = train_val_idx[val_idx]

    split_col = np.full(n, "train", dtype=object)
    split_col[val_idx] = "val"
    split_col[test_idx] = "test"
    applicants_df["split"] = split_col

    # ── 6. Policy attributes dataframe ───────────────────────────────────────
    policy_attributes_df = pd.DataFrame({
        "applicant_id": applicant_ids,
        "dgp_id": np.int8(dgp_id),
        "seed_id": np.int8(seed),
        "age": policy_attrs["age"],
        "occupation_category": policy_attrs["occupation_category"],
        "nonfarm_business_flag": policy_attrs["nonfarm_business_flag"],
    })

    # ── 7. Latent params (write-only — never read by feature code) ────────────
    latent_params_df = pd.DataFrame({
        "applicant_id": applicant_ids,
        "b": static["b"],
        "sigma_m": static["sigma_m"],
        "g": static["g"],
        "amp": static["amp"],
        "phase": static["phase"],
        "rho": static["rho"],
    })

    return monthly_df, applicants_df, policy_attributes_df, latent_params_df


def save_data(
    cfg: dict[str, Any],
    dgp_id: int,
    seed: int,
    monthly_df: pd.DataFrame,
    applicants_df: pd.DataFrame,
    policy_attributes_df: pd.DataFrame,
    latent_params_df: pd.DataFrame,
) -> Path:
    """Write all parquet files and return output directory."""
    out_dir = get_output_dir(cfg, dgp_id, seed)
    out_dir.mkdir(parents=True, exist_ok=True)

    monthly_df.to_parquet(out_dir / "monthly.parquet", index=False)
    applicants_df.to_parquet(out_dir / "applicants.parquet", index=False)
    policy_attributes_df.to_parquet(out_dir / "policy_attributes.parquet", index=False)
    latent_params_df.to_parquet(out_dir / "latent_params.parquet", index=False)

    print(f"[generate_data] DGP={dgp_id} seed={seed} -> {out_dir}")
    n = len(applicants_df)
    prev = applicants_df["default_flag"].mean()
    print(f"  applicants={n:,}  default_rate={prev:.3f}")
    splits = applicants_df["split"].value_counts()
    print(f"  splits: {dict(splits)}")
    return out_dir


def load_data(
    cfg: dict[str, Any],
    dgp_id: int,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load previously generated parquet files."""
    out_dir = get_output_dir(cfg, dgp_id, seed)
    monthly_df = pd.read_parquet(out_dir / "monthly.parquet")
    applicants_df = pd.read_parquet(out_dir / "applicants.parquet")
    policy_attributes_df = pd.read_parquet(out_dir / "policy_attributes.parquet")
    return monthly_df, applicants_df, policy_attributes_df


# ── CLI entry point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate SynthGigCredit-IN-v1 dataset")
    parser.add_argument("--config", default="configs/experiment.yaml")
    parser.add_argument("--dgp", type=int, required=True, choices=[1, 2])
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()

    cfg = load_config(args.config)
    monthly, applicants, policy_attrs, latent = generate_data(cfg, args.dgp, args.seed)
    save_data(cfg, args.dgp, args.seed, monthly, applicants, policy_attrs, latent)
