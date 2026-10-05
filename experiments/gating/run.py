"""Gating experiment — D1-D4 (T3, Experiment A)."""
from __future__ import annotations
import argparse, json
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
from src.utils.config_loader import load_config, get_output_dir
from src.models.train_models import train_model
from src.calibration.platt import fit_platt
from src.evidence.compute_evidence import compute_evidence, evidence_status
from src.policy.rule_loader import load_policy_set
from src.policy.rule_engine import evaluate_batch, combine_schemes
from src.policy.kleene import State
from src.decisions.gate import make_decision
from src.decisions.tau import select_tau
from src.evaluation.metrics import (
    approval_rate, default_rate_among_approved,
    review_rate, policy_violation_rate, coverage_risk_curve
)


def run_gating(cfg_path: str, dgp_id: int, seed: int):
    cfg = load_config(cfg_path)
    out_dir = get_output_dir(cfg, dgp_id, seed)

    features_full    = pd.read_parquet(out_dir / "features_full.parquet")
    features_visible = pd.read_parquet(out_dir / "features_visible.parquet")
    policy_attrs     = pd.read_parquet(out_dir / "policy_attributes.parquet")

    train_f = features_full[features_full["split"] == "train"]
    val_f   = features_visible[features_visible["split"] == "val"]
    test_f  = features_visible[features_visible["split"] == "test"]

    # Train XGB-C
    fitted = train_model(train_f, "C", "xgb", cfg, seed=seed, dgp_id=dgp_id, dataset_seed=seed)
    p_raw_val  = fitted.predict_raw(val_f)
    p_raw_test = fitted.predict_raw(test_f)
    cal = fit_platt(p_raw_val, val_f["default_flag"].values)
    pd_val  = cal.transform(p_raw_val)
    pd_test = cal.transform(p_raw_test)

    # Select tau on validation (D1 approval = 70%)
    tau = select_tau(pd_val, cfg["decision"]["approval_target"])
    tau_e = cfg["evidence"]["tau_e"]
    print(f"  tau={tau:.4f}  (D1 approval target {cfg['decision']['approval_target']:.0%})")

    # Evidence on test set
    ev_scores = compute_evidence(
        test_f["history_length"], test_f["aa_completeness"], test_f["uli_completeness"], cfg
    ).values

    # Policy on test set
    policy_set = load_policy_set(cfg["policy"]["rules_dir"])
    decision_date = date.fromisoformat(cfg["policy"]["decision_date"])
    test_policy_attrs = policy_attrs[policy_attrs["applicant_id"].isin(test_f["applicant_id"])]
    # Add annual income from features
    income_map = test_f.set_index("applicant_id")["income_mean"] * 12
    test_policy_attrs = test_policy_attrs.copy()
    test_policy_attrs["annual_income"] = test_policy_attrs["applicant_id"].map(income_map)

    batch_results = evaluate_batch(
        test_policy_attrs, policy_set, decision_date,
        scheme_mode=cfg["policy"]["scheme_mode"]
    )
    combined_states = np.array([
        batch_results.get(aid, {}).get("combined_state", "UNRESOLVED")
        for aid in test_f["applicant_id"]
    ])

    y_test = test_f["default_flag"].values
    results = {}
    for mode in ["D1", "D2", "D3", "D4"]:
        decisions = np.array([
            make_decision(pd_test[i], ev_scores[i], combined_states[i], mode, tau, tau_e).decision
            for i in range(len(test_f))
        ])
        results[mode] = {
            "approval_rate": approval_rate(decisions),
            "default_rate_among_approved": default_rate_among_approved(decisions, y_test),
            "review_rate": review_rate(decisions),
            "policy_violation_rate": policy_violation_rate(decisions, combined_states) if mode == "D1" else 0.0,
        }
        print(f"  {mode}: approval={results[mode]['approval_rate']:.3f}  "
              f"default_rate={results[mode]['default_rate_among_approved']:.3f}  "
              f"review={results[mode]['review_rate']:.3f}")

    res_dir = Path(f"results/gating/dgp{dgp_id}/seed{seed}")
    res_dir.mkdir(parents=True, exist_ok=True)
    with (res_dir / "T3_results.json").open("w") as fh:
        json.dump(results, fh, indent=2)
    print(f"Gating results -> {res_dir}/T3_results.json")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiment.yaml")
    parser.add_argument("--dgp", type=int, default=1)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    run_gating(args.config, args.dgp, args.seed)
