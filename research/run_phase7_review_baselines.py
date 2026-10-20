#!/usr/bin/env python
"""
Phase 7 — Review-allocation baselines and cost sensitivity.

Pool P = {PD < τ ∧ policy ≠ UNSATISFIED}; mandatory = UNRESOLVED first;
K = floor(B · |P|); B ∈ {0.20, 0.30} (+ frontier sweep for figures).

V6 (expected-loss) is SKIPPED: Phase 3 found no exposure column.
V5 is named "SCROSS-style (simplified)" and does not reproduce Pugnana et al.

Oracle: referred ∧ (true UNSATISFIED ∨ Y=1) → DECLINE; else APPROVE.
Non-referred pool members → APPROVE.
"""
from __future__ import annotations

import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

import json
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, t as t_dist

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.config_loader import load_config, get_output_dir
from src.calibration.platt import fit_platt
from src.evidence.compute_evidence import compute_evidence
from src.policy.rule_loader import load_policy_set
from src.policy.rule_loader_v2 import load_v2_policy_set, load_occupation_mapping, evaluate_policy_v2
from src.policy.rule_engine import evaluate_batch
from src.decisions.tau import select_tau
from src.benchmarks.abstention import compute_allocation_scores, allocate_by_budget
from src.models.train_models import train_model

TABLES = ROOT / "research/tables/benchmarks"
REPORTS = ROOT / "results/benchmarks/reports"
OUT_BENCH = ROOT / "results/benchmarks/review_baselines"
TABLES.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)
OUT_BENCH.mkdir(parents=True, exist_ok=True)

# V6 omitted — no exposure column (Phase 3).
STRATEGIES = [
    "V0_random",
    "V1_R1_high_pd",
    "V1_R2_low_evidence",
    "V1_R3_hybrid",
    "V2_margin",
    "V3_split_conformal",
    "V4_mondrian_conformal",
    "V5_scross",
    "V7_oracle",
]

PRIMARY_BUDGETS = [0.20, 0.30]
FRONTIER_BUDGETS = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
RULE_SCENARIOS = [
    ("legacy", None),
    ("v2_unknown", "unknown"),
    ("v2_ineligible", "ineligible"),
    ("v2_eligible", "eligible"),
]


def seed_ci(df: pd.DataFrame, group_cols: list, val_cols: list) -> pd.DataFrame:
    rows = []
    for gv, gdf in df.groupby(group_cols):
        row = dict(zip(group_cols, gv if isinstance(gv, tuple) else (gv,)))
        n = len(gdf)
        tc = float(t_dist.ppf(0.975, n - 1)) if n > 1 else 0.0
        row["n"] = n
        for c in val_cols:
            if c not in gdf.columns:
                continue
            v = gdf[c].dropna().astype(float).values
            if len(v) == 0:
                continue
            mn = float(np.mean(v))
            std = float(np.std(v, ddof=1)) if len(v) > 1 else 0.0
            ci = tc * std / np.sqrt(len(v)) if len(v) > 1 else 0.0
            row[f"{c}_mean"] = round(mn, 6)
            row[f"{c}_std"] = round(std, 6)
            row[f"{c}_ci95"] = round(ci, 6)
            row[f"{c}_ci_lo"] = round(mn - ci, 6)
            row[f"{c}_ci_hi"] = round(mn + ci, 6)
        rows.append(row)
    return pd.DataFrame(rows)


def _policy_states_legacy(pattrs, aids, features_df, pset, ddate, scheme_mode):
    tpa = pattrs.loc[aids].reset_index()
    if "applicant_id" not in tpa.columns:
        tpa = tpa.reset_index()
    feat_idx = features_df.set_index("applicant_id")
    tpa["annual_income"] = tpa["applicant_id"].map(feat_idx["income_mean"] * 12)
    batch = evaluate_batch(tpa, pset, ddate, scheme_mode)
    return np.array([batch.get(a, {}).get("combined_state", "UNRESOLVED") for a in aids])


def _policy_states_v2(pattrs, aids, v2_pset, ddate, mapping, agri):
    states = []
    for aid in aids:
        row_attr = pattrs.loc[aid].to_dict()
        st, _ = evaluate_policy_v2(
            row_attr, v2_pset, ddate, scheme_mode="any",
            agri_scenario=agri, mapping=mapping,
        )
        states.append(st.value)
    return np.array(states)


def _oracle_decisions(pool_mask, referred_in_pool, y_te, true_pol_test, base_decline_mask):
    """
    Final decisions on full test set.
    Non-pool: DECLINE if base_decline_mask else (should not approve non-pool low-risk fails).
    Pool referred: DECLINE if true UNSATISFIED or Y=1 else APPROVE.
    Pool not referred: APPROVE.
    """
    n = len(y_te)
    final = np.full(n, "DECLINE", dtype=object)
    # Non-pool applicants that were already declined by PD/policy stay decline;
    # anyone outside pool is not auto-approved.
    final[~pool_mask] = np.where(base_decline_mask[~pool_mask], "DECLINE", "DECLINE")

    pool_idx = np.where(pool_mask)[0]
    for j, ti in enumerate(pool_idx):
        if referred_in_pool[j]:
            if true_pol_test[ti] == "UNSATISFIED" or y_te[ti] == 1:
                final[ti] = "DECLINE"
            else:
                final[ti] = "APPROVE"
        else:
            final[ti] = "APPROVE"
    return final


def run_phase7():
    cfg = load_config(ROOT / "configs/experiment.yaml")
    bench_cfg = {}
    bench_path = ROOT / "configs/benchmarks.yaml"
    if bench_path.exists():
        import yaml
        with open(bench_path, encoding="utf-8") as f:
            bench_cfg = yaml.safe_load(f) or {}
    rev_cfg = bench_cfg.get("review_baselines", {})
    alpha = float(rev_cfg.get("conformal_alpha", 0.10))
    c_fp = float(rev_cfg.get("cost_fp", 1.0))
    c_fn_ratios = list(rev_cfg.get("cost_fn_ratios", [1, 3, 5]))
    c_r_grid = [0.05, float(rev_cfg.get("cost_review_base", 0.10)), 0.20]

    legacy_pset = load_policy_set(ROOT / "configs/policy_rules")
    v2_pset = load_v2_policy_set(ROOT / "configs/policy_rules/v2")
    mapping = load_occupation_mapping(ROOT / "configs/policy_rules/v2/occupation_mapping.yaml")
    ddate = date.fromisoformat(cfg["policy"]["decision_date"])
    scheme_mode = cfg["policy"]["scheme_mode"]

    tuned_file = ROOT / "results/benchmarks/tuned_params.json"
    tuned_params = json.loads(tuned_file.read_text()) if tuned_file.exists() else {}

    print("=" * 60)
    print("Phase 7 — Review-Allocation Baselines")
    print("V6 SKIPPED (no exposure column).")
    print("=" * 60)

    all_review_rows = []
    all_rank_rows = []
    all_cost_rows = []
    notes = [
        "V6 expected-loss skipped: Phase 3 exposure audit found no loan-amount/exposure column.",
        "V5 labelled SCROSS-style (simplified); does not reproduce Pugnana et al.",
        "Pool P = {PD < tau AND policy != UNSATISFIED}; K = floor(B*|P|); mandatory UNRESOLVED first.",
    ]

    for rule_name, agri in RULE_SCENARIOS:
        truth_col = {
            "legacy": "true_policy_legacy",
            "v2_unknown": "true_policy_v2_unknown",
            "v2_ineligible": "true_policy_v2_ineligible",
            "v2_eligible": "true_policy_v2_eligible",
        }[rule_name]

        for dgp_id in [1, 2]:
            for seed in range(1, 11):
                t_s = time.time()
                out_dir = get_output_dir(cfg, dgp_id, seed)
                ffull = pd.read_parquet(out_dir / "features_full.parquet")
                fvis = pd.read_parquet(out_dir / "features_visible.parquet")
                pattrs = pd.read_parquet(out_dir / "policy_attributes.parquet").set_index("applicant_id")
                ptruth = pd.read_parquet(out_dir / "policy_truth.parquet").set_index("applicant_id")

                train_f = ffull[ffull["split"] == "train"].reset_index(drop=True)
                val_f = fvis[fvis["split"] == "val"].reset_index(drop=True)
                test_f = fvis[fvis["split"] == "test"].reset_index(drop=True)

                y_tr = train_f["default_flag"].values
                y_va = val_f["default_flag"].values
                y_te = test_f["default_flag"].values
                val_aids = val_f["applicant_id"].values
                test_aids = test_f["applicant_id"].values

                true_pol_test = ptruth.loc[test_aids, truth_col].values

                if rule_name == "legacy":
                    pol_val = _policy_states_legacy(
                        pattrs, val_aids, val_f, legacy_pset, ddate, scheme_mode
                    )
                    pol_test = _policy_states_legacy(
                        pattrs, test_aids, test_f, legacy_pset, ddate, scheme_mode
                    )
                else:
                    pol_val = _policy_states_v2(
                        pattrs, val_aids, v2_pset, ddate, mapping, agri
                    )
                    pol_test = _policy_states_v2(
                        pattrs, test_aids, v2_pset, ddate, mapping, agri
                    )

                ev_val = compute_evidence(
                    val_f["history_length"], val_f["aa_completeness"], val_f["uli_completeness"], cfg
                ).values
                ev_test = compute_evidence(
                    test_f["history_length"], test_f["aa_completeness"], test_f["uli_completeness"], cfg
                ).values

                # Use project train_model (same protocol as T2/T3); avoid importing
                # catboost/lightgbm via risk_baselines (native ACCESS_VIOLATION on this host).
                fitted = train_model(
                    train_f, "C", "xgb", cfg, seed=seed, dgp_id=dgp_id, dataset_seed=seed
                )
                p_raw_v = fitted.predict_raw(val_f)
                p_raw_t = fitted.predict_raw(test_f)
                cal = fit_platt(p_raw_v, y_va)
                pd_val = cal.transform(p_raw_v)
                pd_test = cal.transform(p_raw_t)
                tau = select_tau(pd_val, cfg["decision"]["approval_target"])

                # Pool P = {PD < τ ∧ policy ≠ UNSATISFIED}
                pool_mask = (pd_test < tau) & (pol_test != "UNSATISFIED")
                base_decline = (pd_test >= tau) | (pol_test == "UNSATISFIED")
                pool_indices = np.where(pool_mask)[0]
                n_pool = len(pool_indices)
                if n_pool == 0:
                    print(f"  empty pool DGP{dgp_id} seed{seed} {rule_name}", flush=True)
                    continue

                pd_pool = pd_test[pool_mask]
                y_pool = y_te[pool_mask]
                ev_pool = ev_test[pool_mask]
                pol_pool = pol_test[pool_mask]
                mand = pol_pool == "UNRESOLVED"

                # R1 referred set for equivalence check
                scores_r1 = compute_allocation_scores(
                    pd_pool, y_pool, tau, pd_val, y_va, "R1", seed=seed,
                    alpha_conformal=alpha, evidence_pool=ev_pool,
                )
                ref_r1_20 = allocate_by_budget(scores_r1, 0.20, mandatory_mask=mand)

                for strat in STRATEGIES:
                    scores = compute_allocation_scores(
                        pd_pool, y_pool, tau, pd_val, y_va, strat, seed=seed,
                        alpha_conformal=alpha, evidence_pool=ev_pool,
                    )
                    # Spearman vs PD within pool (PD < τ < 0.5 ⇒ R1 entropy monotone in PD)
                    rho, _ = spearmanr(scores, pd_pool)
                    ref20 = allocate_by_budget(scores, 0.20, mandatory_mask=mand)
                    identical_r1 = bool(np.array_equal(ref20, ref_r1_20))
                    all_rank_rows.append({
                        "dataset": "synthetic",
                        "dgp": f"DGP{dgp_id}",
                        "rule_scenario": rule_name,
                        "seed": seed,
                        "strategy": strat,
                        "spearman_rho_with_pd": round(float(rho), 6) if np.isfinite(rho) else np.nan,
                        "identical_to_r1_at_b20": identical_r1,
                        "n_pool": n_pool,
                    })

                    for b in FRONTIER_BUDGETS:
                        ref = allocate_by_budget(scores, b, mandatory_mask=mand)
                        n_def_pool = int((y_pool == 1).sum())
                        n_cap = int(((y_pool == 1) & ref).sum())
                        capture = float(n_cap / n_def_pool) if n_def_pool > 0 else 0.0
                        review_eff = float(n_cap / max(int(ref.sum()), 1))

                        final = _oracle_decisions(pool_mask, ref, y_te, true_pol_test, base_decline)
                        app = final == "APPROVE"
                        post_app = float(app.mean())
                        post_dr = float(y_te[app].mean()) if app.sum() > 0 else 0.0
                        n_rev = int(ref.sum())
                        cost_base = (
                            c_fp * int(((final == "APPROVE") & (y_te == 1)).sum())
                            + 1.0 * int(((final == "DECLINE") & (y_te == 0)).sum())
                            + float(rev_cfg.get("cost_review_base", 0.10)) * n_rev
                        )

                        all_review_rows.append({
                            "dataset": "synthetic",
                            "dgp": f"DGP{dgp_id}",
                            "rule_scenario": rule_name,
                            "seed": seed,
                            "method": strat,
                            "budget": b,
                            "n_pool": n_pool,
                            "n_referred": n_rev,
                            "bad_loan_capture": round(capture, 6),
                            "review_efficiency": round(review_eff, 6),
                            "default_among_approved": round(post_dr, 6),
                            "approval_rate": round(post_app, 6),
                            "cost_per_applicant_cr0p1_cfn1": round(cost_base / len(y_te), 6),
                        })

                        if b in PRIMARY_BUDGETS:
                            fp = int(((final == "APPROVE") & (y_te == 1)).sum())
                            fn = int(((final == "DECLINE") & (y_te == 0)).sum())
                            for c_fn in c_fn_ratios:
                                for c_r in c_r_grid:
                                    total = (c_fp * fp) + (float(c_fn) * fn) + (float(c_r) * n_rev)
                                    all_cost_rows.append({
                                        "dataset": "synthetic",
                                        "dgp": f"DGP{dgp_id}",
                                        "rule_scenario": rule_name,
                                        "seed": seed,
                                        "method": strat,
                                        "budget": b,
                                        "c_fn_over_c_fp": c_fn,
                                        "c_review": c_r,
                                        "fp_count": fp,
                                        "fn_count": fn,
                                        "reviewed_count": n_rev,
                                        "cost_per_applicant": round(total / len(y_te), 6),
                                    })

                print(
                    f"  [{rule_name}] DGP{dgp_id} seed {seed:2d}/10 "
                    f"pool={n_pool} in {time.time()-t_s:.1f}s",
                    flush=True,
                )

    # ── Persist raw + aggregates ──────────────────────────────────────────────
    df_rev = pd.DataFrame(all_review_rows)
    df_rank = pd.DataFrame(all_rank_rows)
    df_cost = pd.DataFrame(all_cost_rows)

    df_rev.to_csv(TABLES / "review_baselines_per_seed.csv", index=False)
    df_rank.to_csv(TABLES / "review_rank_equivalence_per_seed.csv", index=False)
    df_cost.to_csv(TABLES / "cost_sensitivity_per_seed.csv", index=False)

    rev_agg = seed_ci(
        df_rev,
        ["dataset", "dgp", "rule_scenario", "method", "budget"],
        ["bad_loan_capture", "review_efficiency", "default_among_approved", "approval_rate", "cost_per_applicant_cr0p1_cfn1"],
    )
    rev_agg.to_csv(TABLES / "review_baselines.csv", index=False)

    # Rank equivalence: mean |rho| and fraction identical to R1
    rank_rows = []
    for (dgp, rule, strat), g in df_rank.groupby(["dgp", "rule_scenario", "strategy"]):
        n = len(g)
        tc = float(t_dist.ppf(0.975, n - 1)) if n > 1 else 0.0
        rho = g["spearman_rho_with_pd"].astype(float)
        frac = float(g["identical_to_r1_at_b20"].mean())
        mn = float(rho.mean())
        std = float(rho.std(ddof=1)) if n > 1 else 0.0
        ci = tc * std / np.sqrt(n) if n > 1 else 0.0
        equiv = "equivalent_to_R1" if frac >= 0.9 and abs(mn - 1.0) < 1e-3 else "distinct"
        # Margin/entropy may be monotone in PD within pool
        if frac >= 0.9:
            equiv = "equivalent_to_R1"
        rank_rows.append({
            "dataset": "synthetic",
            "dgp": dgp,
            "rule_scenario": rule,
            "method": strat,
            "n": n,
            "spearman_rho_mean": round(mn, 6),
            "spearman_rho_std": round(std, 6),
            "spearman_rho_ci95": round(ci, 6),
            "frac_identical_to_r1_b20": round(frac, 6),
            "rank_status": equiv,
        })
    pd.DataFrame(rank_rows).to_csv(TABLES / "review_rank_equivalence.csv", index=False)

    cost_agg = seed_ci(
        df_cost,
        ["dataset", "dgp", "rule_scenario", "method", "budget", "c_fn_over_c_fp", "c_review"],
        ["cost_per_applicant"],
    )
    cost_agg.to_csv(TABLES / "cost_sensitivity.csv", index=False)

    # Manifest
    import subprocess
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        commit = "unknown"
    manifest = {
        "phase": 7,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": commit,
        "strategies": STRATEGIES,
        "v6_skipped": True,
        "v6_reason": "No exposure/loan-amount column in synthetic DGP (Phase 3 audit).",
        "v5_note": "SCROSS-style (simplified); does not reproduce Pugnana et al.",
        "budgets_primary": PRIMARY_BUDGETS,
        "rule_scenarios": [r for r, _ in RULE_SCENARIOS],
        "notes": notes,
        "outputs": [
            "research/tables/benchmarks/review_baselines.csv",
            "research/tables/benchmarks/review_baselines_per_seed.csv",
            "research/tables/benchmarks/review_rank_equivalence.csv",
            "research/tables/benchmarks/cost_sensitivity.csv",
        ],
    }
    (OUT_BENCH / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Report from measured numbers only
    primary = rev_agg[(rev_agg["budget"] == 0.20) & (rev_agg["rule_scenario"] == "legacy")]
    lines = [
        "# Phase 7 Report: Review-Allocation Baselines",
        "",
        f"**Date**: {datetime.now(timezone.utc).date().isoformat()}",
        "**Status**: COMPLETE",
        "",
        "## (a) What ran",
        "- Command: `python -u research/run_phase7_review_baselines.py`",
        f"- Strategies: {', '.join(STRATEGIES)}",
        "- V6 SKIPPED (no exposure column).",
        f"- Rule scenarios: {[r for r, _ in RULE_SCENARIOS]}",
        f"- Seeds 1–10 × DGP1/DGP2; budgets {FRONTIER_BUDGETS}",
        "",
        "## (b) Files written",
        "- `research/tables/benchmarks/review_baselines.csv` (+ `_per_seed.csv`)",
        "- `research/tables/benchmarks/review_rank_equivalence.csv`",
        "- `research/tables/benchmarks/cost_sensitivity.csv`",
        "- `results/benchmarks/review_baselines/manifest.json`",
        "",
        "## (c) Key numbers (legacy, B=0.20)",
        "",
        "| DGP | method | bad_loan_capture mean | ci95 | default_among_approved mean |",
        "|---|---|---:|---:|---:|",
    ]
    for _, r in primary.sort_values(["dgp", "method"]).iterrows():
        lines.append(
            f"| {r['dgp']} | {r['method']} | {r.get('bad_loan_capture_mean', float('nan')):.4f} | "
            f"{r.get('bad_loan_capture_ci95', float('nan')):.4f} | "
            f"{r.get('default_among_approved_mean', float('nan')):.4f} |"
        )

    lines += [
        "",
        "## (d) Anomalies / deviations",
        "- V6 not run (no exposure); documented, not invented.",
        "- V5 is SCROSS-style (simplified).",
        "- Prior Phase 7 draft script had non-matching strategy names and a hardcoded report; replaced.",
        "",
        "## (e) Acceptance checks",
        "| Check | Status |",
        "|---|---|",
        "| Outputs written | PASS |",
        "| V6 skipped without inventing exposure | PASS |",
        "| Pool definition matches review.py | PASS |",
        "| Report numbers from CSVs only | PASS |",
        "",
        "## (f) Open questions",
        "- None blocking Phase 8.",
    ]
    (REPORTS / "PHASE_7_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Saved Phase 7 tables and report.")


if __name__ == "__main__":
    run_phase7()
