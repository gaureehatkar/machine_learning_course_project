#!/usr/bin/env python
"""
Fairness Analysis — T9: e-Shram Subgroup Analysis

Determines whether the 3-layer decision system produces different outcomes
for e-Shram registered vs unregistered workers.

IMPORTANT LIMITATIONS:
- All variables are SYNTHETIC, not real demographic data
- e-Shram is NOT a protected attribute under Indian law
- e-Shram is designed to be INDEPENDENT of default in the DGP
- Any differences are structural artifacts of the DGP, not real-world bias
- This is a METHODOLOGICAL DEMONSTRATION, not a fairness audit

Usage:
    python research/run_fairness.py
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from datetime import date
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.config_loader import load_config, get_output_dir
from src.models.train_models import train_model
from src.calibration.platt import fit_platt
from src.evidence.compute_evidence import compute_evidence
from src.policy.rule_loader import load_policy_set
from src.policy.rule_engine import evaluate_batch
from src.decisions.gate import make_decision
from src.decisions.tau import select_tau
from src.evaluation.metrics import roc_auc, approval_rate, default_rate_among_approved

RESULTS_DIR = ROOT / "research" / "results"
TABLES_DIR = ROOT / "research" / "tables"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
TABLES_DIR.mkdir(parents=True, exist_ok=True)


def run_fairness_analysis(cfg, dgp_id, seed):
    """Analyze e-Shram subgroup differences in decision outcomes."""
    out_dir = get_output_dir(cfg, dgp_id, seed)
    ffull = pd.read_parquet(out_dir / "features_full.parquet")
    fvis = pd.read_parquet(out_dir / "features_visible.parquet")
    pattrs = pd.read_parquet(out_dir / "policy_attributes.parquet")

    train_f = ffull[ffull["split"] == "train"].reset_index(drop=True)
    val_f = fvis[fvis["split"] == "val"].reset_index(drop=True)
    test_f = fvis[fvis["split"] == "test"].reset_index(drop=True)

    # Train XGB-C
    fitted = train_model(train_f, "C", "xgb", cfg, seed=seed, dgp_id=dgp_id, dataset_seed=seed)
    p_raw_v = fitted.predict_raw(val_f)
    p_raw_t = fitted.predict_raw(test_f)
    cal = fit_platt(p_raw_v, val_f["default_flag"].values)
    pd_val = cal.transform(p_raw_v)
    pd_test = cal.transform(p_raw_t)
    tau = select_tau(pd_val, cfg["decision"]["approval_target"])
    tau_e = cfg["evidence"]["tau_e"]

    # Evidence scores
    ev = compute_evidence(test_f["history_length"], test_f["aa_completeness"],
                          test_f["uli_completeness"], cfg).values

    # Policy evaluation
    pset = load_policy_set(cfg["policy"]["rules_dir"])
    ddate = date.fromisoformat(cfg["policy"]["decision_date"])
    tpa = pattrs[pattrs["applicant_id"].isin(test_f["applicant_id"])].copy()
    tpa["annual_income"] = tpa["applicant_id"].map(
        test_f.set_index("applicant_id")["income_mean"] * 12)
    batch = evaluate_batch(tpa, pset, ddate, cfg["policy"]["scheme_mode"])
    pol = np.array([batch.get(a, {}).get("combined_state", "UNRESOLVED")
                    for a in test_f["applicant_id"]])

    y = test_f["default_flag"].values
    esham = test_f["e_shram_registered"].values

    # D4 decisions
    dec = np.array([make_decision(pd_test[i], ev[i], pol[i], "D4", tau, tau_e).decision
                    for i in range(len(test_f))])

    # Split by e-Shram status
    esham_yes = esham == 1
    esham_no = esham == 0

    results = {
        "dgp": dgp_id,
        "seed": seed,
        "n_esham_yes": int(esham_yes.sum()),
        "n_esham_no": int(esham_no.sum()),
        # Overall
        "overall_approval_rate": float(approval_rate(dec)),
        "overall_default_rate": float(default_rate_among_approved(dec, y)),
        # e-Shram registered
        "esham_yes_approval_rate": float(approval_rate(dec[esham_yes])),
        "esham_yes_default_rate": float(default_rate_among_approved(dec[esham_yes], y[esham_yes])),
        "esham_yes_evidence_mean": float(ev[esham_yes].mean()),
        "esham_yes_pd_mean": float(pd_test[esham_yes].mean()),
        "esham_yes_auc": float(roc_auc(y[esham_yes], pd_test[esham_yes])) if y[esham_yes].sum() > 0 else None,
        # e-Shram not registered
        "esham_no_approval_rate": float(approval_rate(dec[esham_no])),
        "esham_no_default_rate": float(default_rate_among_approved(dec[esham_no], y[esham_no])),
        "esham_no_evidence_mean": float(ev[esham_no].mean()),
        "esham_no_pd_mean": float(pd_test[esham_no].mean()),
        "esham_no_auc": float(roc_auc(y[esham_no], pd_test[esham_no])) if y[esham_no].sum() > 1 else None,
        # Disparity
        "approval_rate_disparity": float(approval_rate(dec[esham_yes]) - approval_rate(dec[esham_no])),
        "evidence_score_disparity": float(ev[esham_yes].mean() - ev[esham_no].mean()),
        "pd_disparity": float(pd_test[esham_yes].mean() - pd_test[esham_no].mean()),
    }
    return results


def main():
    cfg = load_config("configs/experiment.yaml")
    seeds = list(range(1, 11))

    print("=" * 70)
    print("FAIRNESS ANALYSIS — e-Shram Subgroup (T9)")
    print("=" * 70)

    all_results = []
    for dgp_id in [1, 2]:
        for seed in seeds:
            print(f"  DGP{dgp_id} seed{seed}...", end=" ", flush=True)
            try:
                r = run_fairness_analysis(cfg, dgp_id, seed)
                all_results.append(r)
                print(f"OK  approval_disparity={r['approval_rate_disparity']:.4f}")
            except Exception as e:
                print(f"ERR {e}")

    # Save raw results
    df = pd.DataFrame(all_results)
    df.to_csv(TABLES_DIR / "T9_fairness_raw.csv", index=False)

    # Aggregate by DGP
    T_CRIT = 2.262
    agg_rows = []
    for dgp_id in [1, 2]:
        dgp_df = df[df["dgp"] == dgp_id]
        row = {"dgp": dgp_id}
        for col in ["approval_rate_disparity", "evidence_score_disparity", "pd_disparity",
                     "esham_yes_approval_rate", "esham_no_approval_rate",
                     "esham_yes_evidence_mean", "esham_no_evidence_mean",
                     "esham_yes_pd_mean", "esham_no_pd_mean"]:
            if col in dgp_df.columns:
                vals = dgp_df[col].dropna().values
                if len(vals) > 0:
                    row[f"{col}_mean"] = round(float(np.mean(vals)), 4)
                    row[f"{col}_std"] = round(float(np.std(vals, ddof=1)), 4) if len(vals) > 1 else 0
                    row[f"{col}_ci"] = round(T_CRIT * np.std(vals, ddof=1) / np.sqrt(len(vals)), 4) if len(vals) > 1 else 0
        agg_rows.append(row)

    agg_df = pd.DataFrame(agg_rows)
    agg_df.to_csv(TABLES_DIR / "T9_fairness_aggregated.csv", index=False)

    print(f"\nSaved: T9_fairness_raw.csv, T9_fairness_aggregated.csv")
    print(f"\n{'='*70}")
    print("FAIRNESS ANALYSIS COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
