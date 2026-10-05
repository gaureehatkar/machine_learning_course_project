"""
Review allocation experiment — R0-R3 at 20%/30% budgets (T4, T5, Experiment B)
TECH_DOC §16.4, ARCHITECTURE Diagram 8
"""
from __future__ import annotations
import argparse, json
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd

from src.utils.config_loader import load_config, get_output_dir
from src.models.train_models import train_model
from src.calibration.platt import fit_platt
from src.evidence.compute_evidence import compute_evidence
from src.policy.rule_loader import load_policy_set
from src.policy.rule_engine import evaluate_batch
from src.policy.kleene import State
from src.decisions.gate import make_decision
from src.decisions.tau import select_tau
from src.decisions.review import allocate_review, apply_oracle
from src.evaluation.metrics import approval_rate, default_rate_among_approved


def run_review(cfg_path: str, dgp_id: int, seed: int):
    cfg = load_config(cfg_path)
    out_dir = get_output_dir(cfg, dgp_id, seed)

    features_full    = pd.read_parquet(out_dir / "features_full.parquet")
    features_visible = pd.read_parquet(out_dir / "features_visible.parquet")
    policy_attrs     = pd.read_parquet(out_dir / "policy_attributes.parquet")

    train_f = features_full[features_full["split"] == "train"]
    val_f   = features_visible[features_visible["split"] == "val"]
    test_f  = features_visible[features_visible["split"] == "test"].copy()

    # Train XGB-C, calibrate
    fitted = train_model(train_f, "C", "xgb", cfg, seed=seed)
    p_raw_val  = fitted.predict_raw(val_f)
    p_raw_test = fitted.predict_raw(test_f)
    cal = fit_platt(p_raw_val, val_f["default_flag"].values)
    pd_val  = cal.transform(p_raw_val)
    pd_test = cal.transform(p_raw_test)
    tau = select_tau(pd_val, cfg["decision"]["approval_target"])
    tau_e = cfg["evidence"]["tau_e"]

    # Evidence and policy
    ev_scores = compute_evidence(
        test_f["history_length"], test_f["aa_completeness"], test_f["uli_completeness"], cfg
    ).values

    policy_set = load_policy_set(cfg["policy"]["rules_dir"])
    decision_date = date.fromisoformat(cfg["policy"]["decision_date"])
    test_pa = policy_attrs[policy_attrs["applicant_id"].isin(test_f["applicant_id"])].copy()
    income_map = test_f.set_index("applicant_id")["income_mean"] * 12
    test_pa["annual_income"] = test_pa["applicant_id"].map(income_map)
    batch = evaluate_batch(test_pa, policy_set, decision_date, cfg["policy"]["scheme_mode"])
    pol_states = np.array([batch.get(a, {}).get("combined_state", "UNRESOLVED")
                           for a in test_f["applicant_id"]])

    # Build pool P: PD < tau AND policy != UNSATISFIED
    pool_mask = (pd_test < tau) & (pol_states != "UNSATISFIED")
    test_f["pd_calibrated"] = pd_test
    test_f["evidence_score"] = ev_scores
    test_f["policy_state"]   = pol_states
    test_f["in_pool"]        = pool_mask

    y_test = test_f["default_flag"].values
    results = {}

    for budget in cfg["decision"]["review_budgets"]:
        for strategy in cfg["decision"]["review_strategies"]:
            key = f"B{int(budget*100)}_{strategy}"
            referred = allocate_review(test_f, strategy, budget, seed)
            # Oracle simulation
            final_decisions = np.where(pool_mask, "APPROVE", "DECLINE")  # non-pool → DECLINE
            ref_idx = referred[referred].index
            pool_ref = ref_idx.intersection(test_f[pool_mask].index)
            final_decisions[pool_ref] = np.where(
                test_f.loc[pool_ref, "default_flag"].values == 0, "APPROVE", "DECLINE"
            )
            n_referred = int(referred.sum())
            n_pool = int(pool_mask.sum())
            pct_reviewed = n_referred / n_pool if n_pool > 0 else 0
            defaults_in_pool = int((y_test[pool_mask] == 1).sum())
            referred_defaults = int((referred.values[pool_mask] & (y_test[pool_mask] == 1)).sum())
            bad_loan_capture = referred_defaults / defaults_in_pool if defaults_in_pool > 0 else float("nan")
            approved_mask = final_decisions == "APPROVE"
            dr_approved = float(y_test[approved_mask].mean()) if approved_mask.sum() > 0 else float("nan")
            results[key] = {
                "budget": budget, "strategy": strategy,
                "n_pool": n_pool, "n_referred": n_referred,
                "pct_reviewed": round(pct_reviewed, 4),
                "bad_loan_capture": round(bad_loan_capture, 4) if not np.isnan(bad_loan_capture) else None,
                "default_rate_among_approved": round(dr_approved, 4) if not np.isnan(dr_approved) else None,
            }
            print(f"  {key}: reviewed={pct_reviewed:.1%}  bad_loan_capture={bad_loan_capture:.3f}  dr_approved={dr_approved:.3f}")

    res_dir = Path(f"results/review/dgp{dgp_id}/seed{seed}")
    res_dir.mkdir(parents=True, exist_ok=True)
    with (res_dir / "T4_T5_results.json").open("w") as fh:
        json.dump(results, fh, indent=2)
    print(f"Review results -> {res_dir}/T4_T5_results.json")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiment.yaml")
    parser.add_argument("--dgp", type=int, default=1)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    run_review(args.config, args.dgp, args.seed)
