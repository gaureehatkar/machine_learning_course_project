#!/usr/bin/env python
"""
Phase 4 — Matched-coverage comparison.

For each seed/DGP, for each Dx in {D2, D3, D4}:
  1. Compute Dx approval rate on VALIDATION set.
  2. Tune D1's tau on VALIDATION to hit the same approval rate.
  3. Evaluate both D1 and Dx on TEST set.
  4. Report realized coverage, default rate among approved.

Paired t-test over 10 seeds (df=9), 95% CI of difference.

Outputs:
  results/benchmarks/matched_coverage/matched_coverage_raw.csv
  research/tables/benchmarks/matched_coverage.csv
  results/benchmarks/matched_coverage/manifest.json
"""
from __future__ import annotations
import json, sys, time, subprocess
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from scipy.stats import t as t_dist

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
from src.evaluation.metrics import default_rate_among_approved, approval_rate
from src.evaluation.paired_tests import paired_ttest, format_contrast_table

OUT = ROOT / "results/benchmarks/matched_coverage"
TABLES = ROOT / "research/tables/benchmarks"
OUT.mkdir(parents=True, exist_ok=True)
TABLES.mkdir(parents=True, exist_ok=True)


def tune_tau_for_coverage(pd_val: np.ndarray, target_coverage: float) -> float:
    """
    Find tau on VALIDATION to achieve target approval rate (D1 mode: approve if PD < tau).
    Uses a coarse-to-fine sweep — never touches test set.
    """
    candidates = np.linspace(pd_val.min(), pd_val.max(), 500)
    best_tau = float(candidates[0])
    best_diff = float("inf")
    for tau in candidates:
        rate = float((pd_val < tau).mean())
        diff = abs(rate - target_coverage)
        if diff < best_diff:
            best_diff = diff
            best_tau = float(tau)
    return best_tau


def run_seed(cfg, dgp_id: int, seed: int, policy_set, modes=("D2","D3","D4")):
    out_dir = get_output_dir(cfg, dgp_id, seed)
    ffull = pd.read_parquet(out_dir / "features_full.parquet")
    fvis  = pd.read_parquet(out_dir / "features_visible.parquet")
    pattrs = pd.read_parquet(out_dir / "policy_attributes.parquet")

    train_f = ffull[ffull["split"]=="train"].reset_index(drop=True)
    val_f   = fvis[fvis["split"]=="val"].reset_index(drop=True)
    test_f  = fvis[fvis["split"]=="test"].reset_index(drop=True)

    fitted = train_model(train_f, "C", "xgb", cfg, seed=seed, dgp_id=dgp_id, dataset_seed=seed)
    p_raw_v = fitted.predict_raw(val_f)
    p_raw_t = fitted.predict_raw(test_f)
    cal = fit_platt(p_raw_v, val_f["default_flag"].values)
    pd_val  = cal.transform(p_raw_v)
    pd_test = cal.transform(p_raw_t)

    # Evidence and policy on both val and test
    from datetime import date
    ev_val  = compute_evidence(val_f["history_length"],  val_f["aa_completeness"],  val_f["uli_completeness"],  cfg).values
    ev_test = compute_evidence(test_f["history_length"], test_f["aa_completeness"], test_f["uli_completeness"], cfg).values

    tau_e = cfg["evidence"]["tau_e"]
    ddate = date.fromisoformat(cfg["policy"]["decision_date"])

    def get_pol(features_df):
        pa = pattrs[pattrs["applicant_id"].isin(features_df["applicant_id"])].copy()
        pa["annual_income"] = pa["applicant_id"].map(features_df.set_index("applicant_id")["income_mean"] * 12)
        batch = evaluate_batch(pa, policy_set, ddate, cfg["policy"]["scheme_mode"])
        return np.array([batch.get(a,{}).get("combined_state","UNRESOLVED") for a in features_df["applicant_id"]])

    pol_val  = get_pol(val_f)
    pol_test = get_pol(test_f)
    y_test   = test_f["default_flag"].values

    # D1 baseline tau from config (70% approval target on validation)
    tau_d1_base = select_tau(pd_val, cfg["decision"]["approval_target"])

    results = []
    for mode in modes:
        # Dx approval rate on VALIDATION
        dx_decisions_val = np.array([
            make_decision(pd_val[i], ev_val[i], pol_val[i], mode, tau_d1_base, tau_e).decision
            for i in range(len(val_f))
        ])
        dx_coverage_val = float(approval_rate(dx_decisions_val))

        # Tune D1 tau on VALIDATION to match Dx coverage
        tau_d1_matched = tune_tau_for_coverage(pd_val, dx_coverage_val)

        # Evaluate D1 (matched tau) on TEST
        d1_decisions_test = np.array([
            make_decision(pd_test[i], ev_test[i], pol_test[i], "D1", tau_d1_matched, tau_e).decision
            for i in range(len(test_f))
        ])
        d1_coverage_test = float(approval_rate(d1_decisions_test))
        d1_dr = float(default_rate_among_approved(d1_decisions_test, y_test))

        # Evaluate Dx on TEST
        dx_decisions_test = np.array([
            make_decision(pd_test[i], ev_test[i], pol_test[i], mode, tau_d1_base, tau_e).decision
            for i in range(len(test_f))
        ])
        dx_coverage_test = float(approval_rate(dx_decisions_test))
        dx_dr = float(default_rate_among_approved(dx_decisions_test, y_test))

        results.append({
            "dgp": dgp_id, "seed": seed, "comparison": f"D1_vs_{mode}",
            "target_coverage_val": round(dx_coverage_val, 4),
            "tau_d1_matched": round(tau_d1_matched, 4),
            "d1_coverage_test": round(d1_coverage_test, 4),
            "dx_coverage_test": round(dx_coverage_test, 4),
            "d1_dr_approved": round(d1_dr, 4) if not np.isnan(d1_dr) else None,
            "dx_dr_approved": round(dx_dr, 4) if not np.isnan(dx_dr) else None,
            "diff_dr": round(d1_dr - dx_dr, 4) if not np.isnan(d1_dr) and not np.isnan(dx_dr) else None,
        })
    return results


def main():
    cfg = load_config(ROOT / "configs/experiment.yaml")
    policy_set = load_policy_set(cfg["policy"]["rules_dir"])
    seeds = cfg["data"]["seeds"]  # 1-10

    print("="*60)
    print("Phase 4 — Matched-Coverage Comparison")
    print("="*60)

    all_rows = []
    for dgp_id in cfg["data"]["dgps"]:
        for seed in seeds:
            print(f"  DGP{dgp_id} seed{seed}...", end=" ", flush=True)
            t0 = time.time()
            try:
                rows = run_seed(cfg, dgp_id, seed, policy_set)
                all_rows.extend(rows)
                print(f"OK {time.time()-t0:.1f}s")
            except Exception as e:
                print(f"ERR {e}")

    raw_df = pd.DataFrame(all_rows)
    raw_df.to_csv(OUT / "matched_coverage_raw.csv", index=False)

    # Aggregate with paired t-tests
    t_crit = lambda n: float(t_dist.ppf(0.975, n-1)) if n > 1 else 0.0
    agg_rows = []
    contrasts_for_table = []

    for dgp_id in cfg["data"]["dgps"]:
        for comp in ["D1_vs_D2","D1_vs_D3","D1_vs_D4"]:
            sub = raw_df[(raw_df["dgp"]==dgp_id)&(raw_df["comparison"]==comp)].dropna(subset=["diff_dr"])
            if len(sub) == 0:
                continue
            diffs = sub["diff_dr"].values  # D1 - Dx
            d1_dr = sub["d1_dr_approved"].values
            dx_dr = sub["dx_dr_approved"].values
            n = len(diffs)
            tc = t_crit(n)
            mean_diff = float(np.mean(diffs))
            std_diff  = float(np.std(diffs, ddof=1)) if n > 1 else 0.0
            ci        = tc * std_diff / np.sqrt(n) if n > 1 else 0.0
            se        = std_diff / np.sqrt(n) if n > 1 else 0.0
            from scipy.stats import t as t_dist2
            t_stat = mean_diff / se if se > 0 else 0.0
            p_val  = float(2 * t_dist2.sf(abs(t_stat), n-1)) if n > 1 else 1.0

            agg_rows.append({
                "dgp": f"DGP{dgp_id}", "comparison": comp, "n_seeds": n,
                "mean_d1_dr": round(float(np.mean(d1_dr)), 4),
                "mean_dx_dr": round(float(np.mean(dx_dr)), 4),
                "mean_diff_dr": round(mean_diff, 4),
                "ci_lo": round(mean_diff - ci, 4),
                "ci_hi": round(mean_diff + ci, 4),
                "t_stat": round(t_stat, 3),
                "df": n-1,
                "p_value": round(p_val, 4),
                "significant_05": p_val < 0.05,
                "significant_bonferroni": p_val < (0.05/3),
            })

    agg_df = pd.DataFrame(agg_rows)
    agg_df.to_csv(TABLES / "matched_coverage.csv", index=False)

    print("\n=== Matched-Coverage Results ===")
    print(agg_df.to_string(index=False))

    # Manifest
    try:
        git_hash = subprocess.check_output(["git","rev-parse","HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        git_hash = "unknown"
    with open(OUT / "manifest.json", "w") as f:
        json.dump({"git_commit": git_hash, "phase": 4,
                   "timestamp": datetime.now(timezone.utc).isoformat()}, f, indent=2)

    print(f"\nSaved: matched_coverage.csv ({len(agg_df)} rows)")
    print(f"Saved: matched_coverage_raw.csv ({len(raw_df)} rows)")


if __name__ == "__main__":
    main()
