#!/usr/bin/env python
"""
Generate ground-truth policy eligibility (policy_truth.parquet) for all datasets.

Computes true_policy_state using unmasked age and occupation directly from
the static RNG stream (reproducing the exact sequence before the 5% MCAR masking).
Evaluates ground-truth policy state under:
  - legacy: legacy rules (jan_samarth + pmmy)
  - v2_unknown: v2 pmmy rules with agri_scenario='unknown'
  - v2_ineligible: v2 pmmy rules with agri_scenario='ineligible'
  - v2_eligible: v2 pmmy rules with agri_scenario='eligible'

Saves:
  data/synthetic/dgp{dgp}/seed{seed}/policy_truth.parquet
"""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import date
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.config_loader import load_config, get_output_dir
from src.utils.seeding import make_static_rng
from src.data_generation.dgp import _draw_static_attributes
from src.policy.rule_loader import load_policy_set
from src.policy.rule_engine import evaluate_batch
from src.policy.rule_loader_v2 import (
    load_v2_policy_set,
    load_occupation_mapping,
    evaluate_policy_v2,
)

LEGACY_RULES_DIR = ROOT / "configs/policy_rules"
V2_RULES_DIR = ROOT / "configs/policy_rules/v2"


def generate_truth_for_seed(cfg: dict, dgp_id: int, seed: int):
    out_dir = get_output_dir(cfg, dgp_id, seed)
    n = cfg["data"]["n_applicants"]
    applicant_ids = [f"A{i:06d}" for i in range(n)]

    # 1. Reproduce unmasked attributes using static_rng
    static_rng = make_static_rng(seed)
    _ = _draw_static_attributes(static_rng, n, cfg)

    dgp_cfg = cfg["dgp"]
    missing_rate = dgp_cfg["attr_missing_rate"]

    # Raw age before masking
    age_raw = static_rng.normal(34, 11, size=n)
    age_unmasked = np.clip(age_raw, 18, 70).astype(np.float32)
    _missing_age_mask = static_rng.random(n) < missing_rate

    # Raw occupation before masking
    occ_keys = list(dgp_cfg["occupation_probs"].keys())
    occ_probs = list(dgp_cfg["occupation_probs"].values())
    occ_unmasked = static_rng.choice(occ_keys, size=n, p=occ_probs)
    _missing_occ_mask = static_rng.random(n) < missing_rate

    # Nonfarm business flag (0 iff agri_labour, else 1)
    nonfarm_unmasked = np.where(occ_unmasked == "agri_labour", 0, 1).astype(np.float32)

    # 2. Income from features_visible or monthly
    fvis_path = out_dir / "features_visible.parquet"
    if fvis_path.exists():
        fvis = pd.read_parquet(fvis_path)
        income_map = dict(zip(fvis["applicant_id"], fvis["income_mean"] * 12))
    else:
        monthly = pd.read_parquet(out_dir / "monthly.parquet")
        obs_m = monthly[monthly["month"] <= cfg["data"]["obs_months"]]
        mean_inc = obs_m.groupby("applicant_id")["income"].mean() * 12
        income_map = mean_inc.to_dict()

    annual_income = np.array([income_map.get(a, 25000.0 * 12) for a in applicant_ids])

    # 3. Evaluate under legacy rules
    legacy_pset = load_policy_set(LEGACY_RULES_DIR)
    ddate = date.fromisoformat(cfg["policy"]["decision_date"])

    df_legacy = pd.DataFrame({
        "applicant_id": applicant_ids,
        "age": age_unmasked,
        "annual_income": annual_income,
        "occupation_category": occ_unmasked,
        "nonfarm_business_flag": nonfarm_unmasked,
    })
    batch_legacy = evaluate_batch(df_legacy, legacy_pset, ddate, cfg["policy"]["scheme_mode"])
    true_legacy = [batch_legacy.get(a, {}).get("combined_state", "UNRESOLVED") for a in applicant_ids]

    # 4. Evaluate under v2 rules (unknown, ineligible, eligible)
    v2_pset = load_v2_policy_set(V2_RULES_DIR)
    occ_map = load_occupation_mapping(V2_RULES_DIR / "occupation_mapping.yaml")

    true_v2_unknown = []
    true_v2_ineligible = []
    true_v2_eligible = []

    for i in range(n):
        attrs = {
            "applicant_id": applicant_ids[i],
            "age": age_unmasked[i],
            "annual_income": annual_income[i],
            "occupation_category": occ_unmasked[i],
        }
        st_unk, _ = evaluate_policy_v2(attrs, v2_pset, ddate, scheme_mode="any", agri_scenario="unknown", mapping=occ_map)
        st_inel, _ = evaluate_policy_v2(attrs, v2_pset, ddate, scheme_mode="any", agri_scenario="ineligible", mapping=occ_map)
        st_elig, _ = evaluate_policy_v2(attrs, v2_pset, ddate, scheme_mode="any", agri_scenario="eligible", mapping=occ_map)

        true_v2_unknown.append(st_unk.value)
        true_v2_ineligible.append(st_inel.value)
        true_v2_eligible.append(st_elig.value)

    truth_df = pd.DataFrame({
        "applicant_id": applicant_ids,
        "age_unmasked": age_unmasked,
        "occupation_unmasked": occ_unmasked,
        "true_policy_legacy": true_legacy,
        "true_policy_v2_unknown": true_v2_unknown,
        "true_policy_v2_ineligible": true_v2_ineligible,
        "true_policy_v2_eligible": true_v2_eligible,
    })

    truth_path = out_dir / "policy_truth.parquet"
    truth_df.to_parquet(truth_path, index=False)
    return truth_df


def main():
    cfg = load_config(ROOT / "configs/experiment.yaml")
    print("Generating policy_truth.parquet for all seeds (0..10) x DGP (1..2)...")
    for dgp_id in [1, 2]:
        for seed in range(11):
            truth_df = generate_truth_for_seed(cfg, dgp_id, seed)
            # Consistency checks
            unres_legacy = (truth_df["true_policy_legacy"] == "UNRESOLVED").sum()
            unres_inel   = (truth_df["true_policy_v2_ineligible"] == "UNRESOLVED").sum()
            unres_elig   = (truth_df["true_policy_v2_eligible"] == "UNRESOLVED").sum()
            assert unres_legacy == 0, f"DGP{dgp_id} s{seed}: UNRESOLVED found in legacy truth: {unres_legacy}"
            assert unres_inel == 0,   f"DGP{dgp_id} s{seed}: UNRESOLVED found in v2 ineligible truth: {unres_inel}"
            assert unres_elig == 0,   f"DGP{dgp_id} s{seed}: UNRESOLVED found in v2 eligible truth: {unres_elig}"
            print(f"  DGP{dgp_id} s{seed}: OK (0 UNRESOLVED in legacy/ineligible/eligible)")

    print("All policy_truth.parquet files generated successfully.")


if __name__ == "__main__":
    main()
