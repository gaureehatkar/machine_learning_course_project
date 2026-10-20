#!/usr/bin/env python
"""
Phase 2 — Re-run T3, T4/T5, and T9 under legacy and v2 rules.

Rule scenarios:
  1. legacy: legacy rules (jan_samarth + pmmy)
  2. v2_unknown: v2 pmmy with agri_scenario='unknown' (default)
  3. v2_ineligible: v2 pmmy with agri_scenario='ineligible'
  4. v2_eligible: v2 pmmy with agri_scenario='eligible'

Uses true_policy_state from data/synthetic/dgp{dgp}/seed{seed}/policy_truth.parquet
to compute true policy violation rates:
  violation_rate = #(APPROVE & true_policy == UNSATISFIED) / #APPROVE

Writes:
  results/benchmarks/policy_v2/manifest.json
  research/tables/benchmarks/policy_v2_vs_legacy.csv
  research/tables/benchmarks/policy_v2_vs_legacy_per_seed.csv
  results/benchmarks/reports/PHASE_2_REPORT.md
"""
from __future__ import annotations
import json, sys, time, subprocess
from pathlib import Path
from datetime import date
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
from src.policy.rule_loader_v2 import (
    load_v2_policy_set,
    load_occupation_mapping,
    evaluate_policy_v2,
)
from src.decisions.gate import make_decision
from src.decisions.tau import select_tau
from src.decisions.review import allocate_review
from src.evaluation.metrics import (
    approval_rate,
    default_rate_among_approved,
    review_rate,
    bad_loan_capture,
)

OUT_DIR = ROOT / "results/benchmarks/policy_v2"
TABLES_DIR = ROOT / "research/tables/benchmarks"
OUT_DIR.mkdir(parents=True, exist_ok=True)
TABLES_DIR.mkdir(parents=True, exist_ok=True)


def seed_ci(df: pd.DataFrame, group_cols: list, val_cols: list) -> pd.DataFrame:
    rows = []
    for gv, gdf in df.groupby(group_cols):
        row = dict(zip(group_cols, gv if isinstance(gv, tuple) else (gv,)))
        n = len(gdf)
        tc = float(t_dist.ppf(0.975, n - 1)) if n > 1 else 0.0
        row["n"] = n
        for c in val_cols:
            if c in gdf.columns:
                v = gdf[c].dropna().values.astype(float)
                if len(v) > 0:
                    mn = float(np.mean(v))
                    std = float(np.std(v, ddof=1)) if len(v) > 1 else 0.0
                    ci = tc * std / np.sqrt(len(v)) if len(v) > 1 else 0.0
                    row[f"{c}_mean"] = round(mn, 4)
                    row[f"{c}_std"] = round(std, 4)
                    row[f"{c}_ci"] = round(ci, 4)
                    row[f"{c}_ci_lo"] = round(mn - ci, 4)
                    row[f"{c}_ci_hi"] = round(mn + ci, 4)
        rows.append(row)
    return pd.DataFrame(rows)


def run_experiment(cfg: dict):
    legacy_pset = load_policy_set(ROOT / "configs/policy_rules")
    v2_pset = load_v2_policy_set(ROOT / "configs/policy_rules/v2")
    occ_map = load_occupation_mapping(ROOT / "configs/policy_rules/v2/occupation_mapping.yaml")
    ddate = date.fromisoformat(cfg["policy"]["decision_date"])
    tau_e = cfg["evidence"]["tau_e"]

    scenarios = ["legacy", "v2_unknown", "v2_ineligible", "v2_eligible"]

    per_seed_rows = []

    print("Running Phase 2 policy experiments across 10 seeds x 2 DGPs x 4 rule scenarios...")
    t0 = time.time()

    for dgp_id in [1, 2]:
        for seed in range(1, 11):
            t_seed = time.time()
            out_dir = get_output_dir(cfg, dgp_id, seed)
            ffull = pd.read_parquet(out_dir / "features_full.parquet")
            fvis = pd.read_parquet(out_dir / "features_visible.parquet")
            pattrs = pd.read_parquet(out_dir / "policy_attributes.parquet")
            ptruth = pd.read_parquet(out_dir / "policy_truth.parquet")

            train_f = ffull[ffull["split"] == "train"].reset_index(drop=True)
            val_f = fvis[fvis["split"] == "val"].reset_index(drop=True)
            test_f = fvis[fvis["split"] == "test"].copy().reset_index(drop=True)

            # Fit XGB on Feature Set C
            fitted = train_model(train_f, "C", "xgb", cfg, seed=seed, dgp_id=dgp_id, dataset_seed=seed)
            p_raw_v = fitted.predict_raw(val_f)
            p_raw_t = fitted.predict_raw(test_f)
            cal = fit_platt(p_raw_v, val_f["default_flag"].values)
            pd_val = cal.transform(p_raw_v)
            pd_test = cal.transform(p_raw_t)

            tau = select_tau(pd_val, cfg["decision"]["approval_target"])

            ev_test = compute_evidence(
                test_f["history_length"],
                test_f["aa_completeness"],
                test_f["uli_completeness"],
                cfg,
            ).values

            y_test = test_f["default_flag"].values
            test_aids = test_f["applicant_id"].values

            # Pre-index test applicant attributes for O(1) lookups
            pattrs_indexed = pattrs.set_index("applicant_id")
            test_attr_dict = {aid: pattrs_indexed.loc[aid].to_dict() for aid in test_aids}

            # Map test applicant truth
            truth_map = ptruth.set_index("applicant_id")

            # Evaluate each scenario
            for scen in scenarios:
                if scen == "legacy":
                    tpa = pattrs_indexed.loc[test_aids].reset_index()
                    tpa["annual_income"] = tpa["applicant_id"].map(
                        test_f.set_index("applicant_id")["income_mean"] * 12
                    )
                    batch = evaluate_batch(tpa, legacy_pset, ddate, cfg["policy"]["scheme_mode"])
                    pol_test = np.array([batch.get(a, {}).get("combined_state", "UNRESOLVED") for a in test_aids])
                    true_pol = truth_map.loc[test_aids, "true_policy_legacy"].values
                else:
                    agri_mode = scen.replace("v2_", "")
                    pol_states = []
                    for aid in test_aids:
                        row_attr = test_attr_dict[aid]
                        st, _ = evaluate_policy_v2(
                            row_attr,
                            v2_pset,
                            ddate,
                            scheme_mode="any",
                            agri_scenario=agri_mode,
                            mapping=occ_map,
                        )
                        pol_states.append(st.value)
                    pol_test = np.array(pol_states)
                    true_pol = truth_map.loc[test_aids, f"true_policy_{scen}"].values

                # D4 Gate Decisions
                dec_d4 = np.array([
                    make_decision(pd_test[i], ev_test[i], pol_test[i], "D4", tau, tau_e).decision
                    for i in range(len(test_f))
                ])

                # D1 Gate Decisions (for comparison / violation benchmark)
                dec_d1 = np.array([
                    make_decision(pd_test[i], ev_test[i], pol_test[i], "D1", tau, tau_e).decision
                    for i in range(len(test_f))
                ])

                d4_app = approval_rate(dec_d4)
                d4_rev = review_rate(dec_d4)
                d4_dr = default_rate_among_approved(dec_d4, y_test)

                # True violation rate: share of approved who are truly UNSATISFIED
                # In D4:
                d4_approved_mask = dec_d4 == "APPROVE"
                if d4_approved_mask.sum() > 0:
                    d4_viol = float((true_pol[d4_approved_mask] == "UNSATISFIED").sum() / d4_approved_mask.sum())
                else:
                    d4_viol = 0.0

                # In D1:
                d1_approved_mask = dec_d1 == "APPROVE"
                if d1_approved_mask.sum() > 0:
                    d1_viol = float((true_pol[d1_approved_mask] == "UNSATISFIED").sum() / d1_approved_mask.sum())
                else:
                    d1_viol = 0.0

                # Review allocation (R1 at 20% budget on pool)
                pool = (pd_test < tau) & (pol_test != "UNSATISFIED")
                test_f_copy = test_f.copy()
                test_f_copy["pd_calibrated"] = pd_test
                test_f_copy["evidence_score"] = ev_test
                test_f_copy["policy_state"] = pol_test
                test_f_copy["in_pool"] = pool

                ref_r1 = allocate_review(test_f_copy, "R1", 0.20, seed)
                capture_r1 = bad_loan_capture(ref_r1.values, y_test, pool)

                # Post-review approval and default rate after perfect oracle review
                final_dec = np.where(pool, "APPROVE", "DECLINE")
                # Oracle review logic:
                # Referred applicants:
                # If truly UNSATISFIED -> DECLINE
                # Else if defaulter (Y=1) -> DECLINE
                # Else -> APPROVE
                ref_mask = ref_r1.values & pool
                final_dec[ref_mask] = np.where(
                    (true_pol[ref_mask] == "UNSATISFIED") | (y_test[ref_mask] == 1),
                    "DECLINE",
                    "APPROVE",
                )

                post_app = float(np.mean(final_dec == "APPROVE"))
                post_dr = default_rate_among_approved(final_dec, y_test)

                # e-Shram fairness metric (T9 on D4)
                esham = test_f["e_shram_registered"].values
                esham_yes = esham == 1
                esham_no = esham == 0
                app_eshram_yes = float(approval_rate(dec_d4[esham_yes]))
                app_eshram_no = float(approval_rate(dec_d4[esham_no]))
                eshram_parity_diff = app_eshram_yes - app_eshram_no

                per_seed_rows.append({
                    "dgp": f"DGP{dgp_id}",
                    "seed": seed,
                    "scenario": scen,
                    "tau": round(float(tau), 4),
                    "d4_approval_rate": round(d4_app, 4),
                    "d4_review_rate": round(d4_rev, 4),
                    "d4_default_rate": round(d4_dr, 4),
                    "d4_violation_rate": round(d4_viol, 4),
                    "d1_violation_rate": round(d1_viol, 4),
                    "bad_loan_capture_r1_b20": round(capture_r1, 4),
                    "post_review_approval_rate": round(post_app, 4),
                    "post_review_default_rate": round(post_dr, 4),
                    "eshram_parity_diff": round(eshram_parity_diff, 4),
                })
            print(f"  [DGP{dgp_id} seed {seed:2d}/10] completed in {time.time()-t_seed:.1f}s", flush=True)

    df_seed = pd.DataFrame(per_seed_rows)
    df_seed.to_csv(TABLES_DIR / "policy_v2_vs_legacy_per_seed.csv", index=False)

    # Aggregated table
    metrics_to_agg = [
        "d4_approval_rate",
        "d4_review_rate",
        "d4_default_rate",
        "d4_violation_rate",
        "d1_violation_rate",
        "bad_loan_capture_r1_b20",
        "post_review_approval_rate",
        "post_review_default_rate",
        "eshram_parity_diff",
    ]
    df_agg = seed_ci(df_seed, ["dgp", "scenario"], metrics_to_agg)
    df_agg.to_csv(TABLES_DIR / "policy_v2_vs_legacy.csv", index=False)

    # Write manifest
    try:
        git_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        git_hash = "unknown"

    manifest = {
        "git_commit": git_hash,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scenarios": scenarios,
        "n_seeds": 10,
        "dgps": ["DGP1", "DGP2"],
        "elapsed_seconds": round(time.time() - t0, 2),
    }
    with open(OUT_DIR / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Phase 2 complete in {manifest['elapsed_seconds']}s.")
    print(f"Saved: {TABLES_DIR / 'policy_v2_vs_legacy.csv'}")
    return df_agg


if __name__ == "__main__":
    cfg = load_config(ROOT / "configs/experiment.yaml")
    run_experiment(cfg)
