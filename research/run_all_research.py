#!/usr/bin/env python
"""
Comprehensive Research Runner — SynthGigCredit-IN

Runs T2 (ablation), T3 (gating + tau_E sensitivity), T4/T5 (review), T6 (history)
across 10 seeds x 2 DGPs. Aggregates with seed-level CIs. Saves all results.

Usage:
    python research/run_all_research.py
    python research/run_all_research.py --max-seed 3 --dgp 1 --experiment t2
"""
from __future__ import annotations
import argparse, json, sys, time
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
from src.policy.kleene import State
from src.decisions.gate import make_decision
from src.decisions.tau import select_tau
from src.decisions.review import allocate_review
from src.evaluation.metrics import (
    compute_all_metrics, gini, ks_statistic,
    approval_rate, default_rate_among_approved, review_rate,
    policy_violation_rate,
)
from src.feature_engineering.build_features import build_features

RESULTS_DIR = ROOT / "research" / "results"
TABLES_DIR = ROOT / "research" / "tables"
for d in [RESULTS_DIR, TABLES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

T_CRIT = 2.262  # t(0.975, 9) for 10 seeds


def run_t2(cfg, dgp_id, seed):
    """T2: A/B/C feature sets x LR/XGB."""
    out_dir = get_output_dir(cfg, dgp_id, seed)
    ffull = pd.read_parquet(out_dir / "features_full.parquet")
    fvis = pd.read_parquet(out_dir / "features_visible.parquet")
    train_f = ffull[ffull["split"] == "train"].reset_index(drop=True)
    val_f = fvis[fvis["split"] == "val"].reset_index(drop=True)
    test_f = fvis[fvis["split"] == "test"].reset_index(drop=True)
    results = {}
    for fs in ["A", "B", "C"]:
        for fam in ["logreg", "xgb"]:
            key = f"{fs}_{fam}"
            try:
                fitted = train_model(train_f, fs, fam, cfg, seed=seed, dgp_id=dgp_id, dataset_seed=seed)
                p_raw_v = fitted.predict_raw(val_f)
                p_raw_t = fitted.predict_raw(test_f)
                cal = fit_platt(p_raw_v, val_f["default_flag"].values)
                p_cal = cal.transform(p_raw_t)
                m = compute_all_metrics(test_f["default_flag"].values, p_cal)
                results[key] = m
            except Exception as e:
                results[key] = {"error": str(e)}
    return results


def run_t3(cfg, dgp_id, seed):
    """T3: D1-D4 gating + tau_E sensitivity."""
    out_dir = get_output_dir(cfg, dgp_id, seed)
    ffull = pd.read_parquet(out_dir / "features_full.parquet")
    fvis = pd.read_parquet(out_dir / "features_visible.parquet")
    pattrs = pd.read_parquet(out_dir / "policy_attributes.parquet")
    train_f = ffull[ffull["split"] == "train"].reset_index(drop=True)
    val_f = fvis[fvis["split"] == "val"].reset_index(drop=True)
    test_f = fvis[fvis["split"] == "test"].reset_index(drop=True)

    fitted = train_model(train_f, "C", "xgb", cfg, seed=seed, dgp_id=dgp_id, dataset_seed=seed)
    p_raw_v = fitted.predict_raw(val_f)
    p_raw_t = fitted.predict_raw(test_f)
    cal = fit_platt(p_raw_v, val_f["default_flag"].values)
    pd_val = cal.transform(p_raw_v)
    pd_test = cal.transform(p_raw_t)
    tau = select_tau(pd_val, cfg["decision"]["approval_target"])
    tau_e = cfg["evidence"]["tau_e"]

    ev = compute_evidence(test_f["history_length"], test_f["aa_completeness"],
                          test_f["uli_completeness"], cfg).values
    pset = load_policy_set(cfg["policy"]["rules_dir"])
    ddate = date.fromisoformat(cfg["policy"]["decision_date"])
    tpa = pattrs[pattrs["applicant_id"].isin(test_f["applicant_id"])].copy()
    tpa["annual_income"] = tpa["applicant_id"].map(
        test_f.set_index("applicant_id")["income_mean"] * 12)
    batch = evaluate_batch(tpa, pset, ddate, cfg["policy"]["scheme_mode"])
    pol = np.array([batch.get(a, {}).get("combined_state", "UNRESOLVED")
                    for a in test_f["applicant_id"]])
    y = test_f["default_flag"].values
    res = {"tau": float(tau), "tau_e": float(tau_e)}

    for mode in ["D1", "D2", "D3", "D4"]:
        dec = np.array([make_decision(pd_test[i], ev[i], pol[i], mode, tau, tau_e).decision
                        for i in range(len(test_f))])
        res[mode] = {
            "approval_rate": float(approval_rate(dec)),
            "default_rate_among_approved": float(default_rate_among_approved(dec, y)),
            "review_rate": float(review_rate(dec)),
            "policy_violation_rate": float(policy_violation_rate(dec, pol)) if mode == "D1" else 0.0,
        }

    # tau_E sensitivity
    res["tau_e_sensitivity"] = {}
    for te in [0.30, 0.40, 0.50, 0.60, 0.70]:
        dec4 = np.array([make_decision(pd_test[i], ev[i], pol[i], "D4", tau, te).decision
                         for i in range(len(test_f))])
        res["tau_e_sensitivity"][str(te)] = {
            "approval_rate": float(approval_rate(dec4)),
            "default_rate_among_approved": float(default_rate_among_approved(dec4, y)),
            "review_rate": float(review_rate(dec4)),
            "evidence_fail_rate": float((ev < te).mean()),
        }
    return res


def run_t4t5(cfg, dgp_id, seed):
    """T4/T5: R0-R3 x budgets with cost analysis."""
    out_dir = get_output_dir(cfg, dgp_id, seed)
    ffull = pd.read_parquet(out_dir / "features_full.parquet")
    fvis = pd.read_parquet(out_dir / "features_visible.parquet")
    pattrs = pd.read_parquet(out_dir / "policy_attributes.parquet")
    train_f = ffull[ffull["split"] == "train"].reset_index(drop=True)
    val_f = fvis[fvis["split"] == "val"].reset_index(drop=True)
    test_f = fvis[fvis["split"] == "test"].copy().reset_index(drop=True)

    fitted = train_model(train_f, "C", "xgb", cfg, seed=seed, dgp_id=dgp_id, dataset_seed=seed)
    p_raw_v = fitted.predict_raw(val_f)
    p_raw_t = fitted.predict_raw(test_f)
    cal = fit_platt(p_raw_v, val_f["default_flag"].values)
    pd_val = cal.transform(p_raw_v)
    pd_test = cal.transform(p_raw_t)
    tau = select_tau(pd_val, cfg["decision"]["approval_target"])
    tau_e = cfg["evidence"]["tau_e"]

    ev = compute_evidence(test_f["history_length"], test_f["aa_completeness"],
                          test_f["uli_completeness"], cfg).values
    pset = load_policy_set(cfg["policy"]["rules_dir"])
    ddate = date.fromisoformat(cfg["policy"]["decision_date"])
    tpa = pattrs[pattrs["applicant_id"].isin(test_f["applicant_id"])].copy()
    tpa["annual_income"] = tpa["applicant_id"].map(
        test_f.set_index("applicant_id")["income_mean"] * 12)
    batch = evaluate_batch(tpa, pset, ddate, cfg["policy"]["scheme_mode"])
    pol = np.array([batch.get(a, {}).get("combined_state", "UNRESOLVED")
                    for a in test_f["applicant_id"]])
    y = test_f["default_flag"].values

    pool = (pd_test < tau) & (pol != "UNSATISFIED")
    test_f["pd_calibrated"] = pd_test
    test_f["evidence_score"] = ev
    test_f["policy_state"] = pol
    test_f["in_pool"] = pool

    res = {}
    c_fn = cfg["cost"]["m"]
    c_fp = cfg["cost"]["m"]
    c_revs = cfg["cost"]["c_rev"]

    for bi, budget in enumerate(cfg["decision"]["review_budgets"]):
        for strat in cfg["decision"]["review_strategies"]:
            key = f"B{int(budget*100)}_{strat}"
            ref = allocate_review(test_f, strat, budget, seed)
            final = np.where(pool, "APPROVE", "DECLINE")
            ref_idx = ref[ref].index
            pool_ref = ref_idx.intersection(test_f[pool].index)
            final[pool_ref] = np.where(
                test_f.loc[pool_ref, "default_flag"].values == 0, "APPROVE", "DECLINE")

            n_ref = int(ref.sum())
            n_pool = int(pool.sum())
            pct = n_ref / n_pool if n_pool > 0 else 0
            d_pool = int((y[pool] == 1).sum())
            ref_d = int((ref.values & pool & (y == 1)).sum())
            capture = ref_d / d_pool if d_pool > 0 else float("nan")
            app_mask = final == "APPROVE"
            dr_app = float(y[app_mask].mean()) if app_mask.sum() > 0 else float("nan")

            n_app_def = int(((final == "APPROVE") & (y == 1)).sum())
            n_dec_good = int(((final == "DECLINE") & (y == 0)).sum())
            cost = c_fn * n_app_def + c_fp * n_dec_good + c_revs[bi] * n_ref
            cost_pa = cost / len(y)

            res[key] = {
                "budget": budget, "strategy": strat,
                "n_pool": n_pool, "n_referred": n_ref,
                "pct_reviewed": round(pct, 4),
                "bad_loan_capture": round(capture, 4) if not np.isnan(capture) else None,
                "default_rate_among_approved": round(dr_app, 4) if not np.isnan(dr_app) else None,
                "n_approved_default": n_app_def,
                "n_declined_good": n_dec_good,
                "total_cost": round(cost, 2),
                "cost_per_applicant": round(cost_pa, 4),
            }
    return res


def run_t6(cfg, dgp_id, seed):
    """T6: H=1,3,6,12 forced views."""
    out_dir = get_output_dir(cfg, dgp_id, seed)
    monthly = pd.read_parquet(out_dir / "monthly.parquet")
    applicants = pd.read_parquet(out_dir / "applicants.parquet")
    ffull = pd.read_parquet(out_dir / "features_full.parquet")
    train_f = ffull[ffull["split"] == "train"].reset_index(drop=True)
    val_vis = build_features(monthly, applicants, view="visible",
                             obs_months=cfg["data"]["obs_months"])
    val_f = val_vis[val_vis["split"] == "val"].reset_index(drop=True)

    fitted = train_model(train_f, "C", "xgb", cfg, seed=seed)
    p_raw_v = fitted.predict_raw(val_f)
    cal = fit_platt(p_raw_v, val_f["default_flag"].values)

    res = {}
    for H in [1, 3, 6, 12]:
        test_H = build_features(monthly, applicants, view=f"H{H}",
                                obs_months=cfg["data"]["obs_months"])
        test_H = test_H[test_H["split"] == "test"].reset_index(drop=True)
        p_raw = fitted.predict_raw(test_H)
        p_cal = cal.transform(p_raw)
        y = test_H["default_flag"].values
        m = compute_all_metrics(y, p_cal)
        ev = compute_evidence(test_H["history_length"], test_H["aa_completeness"],
                              test_H["uli_completeness"], cfg).values
        res[f"H{H}"] = {
            **m,
            "evidence_mean": float(ev.mean()),
            "evidence_fail_rate": float((ev < cfg["evidence"]["tau_e"]).mean()),
        }
    return res


def seed_ci(df, group_cols, val_cols):
    """Compute mean +/- 95% CI across seeds."""
    rows = []
    for gv, gdf in df.groupby(group_cols):
        row = dict(zip(group_cols, gv if isinstance(gv, tuple) else (gv,)))
        for c in val_cols:
            if c in gdf.columns:
                v = gdf[c].dropna().values
                if len(v) > 0:
                    row[f"{c}_mean"] = round(float(np.mean(v)), 4)
                    row[f"{c}_std"] = round(float(np.std(v, ddof=1)), 4) if len(v) > 1 else 0
                    row[f"{c}_ci"] = round(T_CRIT * np.std(v, ddof=1) / np.sqrt(len(v)), 4) if len(v) > 1 else 0
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/experiment.yaml")
    ap.add_argument("--max-seed", type=int, default=10)
    ap.add_argument("--dgp", type=int, nargs="+", default=[1, 2])
    ap.add_argument("--experiment", choices=["t2","t3","t4t5","t6","all"], default="all")
    args = ap.parse_args()
    cfg = load_config(args.config)
    seeds = list(range(1, args.max_seed + 1))
    print("="*70)
    print(f"RESEARCH RUNNER: seeds={seeds}, dgps={args.dgp}, exp={args.experiment}")
    print("="*70)

    # T2
    if args.experiment in ["t2","all"]:
        print("\n[T2] Ablation")
        t2 = {}
        for d in args.dgp:
            for s in seeds:
                print(f"  DGP{d} s{s}...", end=" ", flush=True)
                t0=time.time()
                try:
                    t2[(d,s)] = run_t2(cfg,d,s)
                    print(f"OK {time.time()-t0:.1f}s")
                except Exception as e:
                    print(f"ERR {e}")
                    t2[(d,s)] = {"error":str(e)}
        json.dump({f"{k[0]}_{k[1]}":v for k,v in t2.items()},
                  open(RESULTS_DIR/"T2_raw.json","w"), indent=2)
        rows=[]
        for (d,s),r in t2.items():
            if isinstance(r, str) or (isinstance(r, dict) and "error" in r):
                continue
            for ck,m in r.items():
                if isinstance(m, dict) and "error" in m: continue
                if not isinstance(m, dict): continue
                row={"dgp":d,"seed":s,"config":ck, **m}
                rows.append(row)
        t2df=pd.DataFrame(rows)
        t2df.to_csv(TABLES_DIR/"T2_ablation_raw.csv", index=False)
        mc=["roc_auc","pr_auc","brier","ece","calibration_slope","gini","ks"]
        seed_ci(t2df,["dgp","config"],mc).to_csv(TABLES_DIR/"T2_ablation_agg.csv", index=False)
        print(f"  Saved T2_ablation_agg.csv")

    # T3
    if args.experiment in ["t3","all"]:
        print("\n[T3] Gating")
        t3 = {}
        for d in args.dgp:
            for s in seeds:
                print(f"  DGP{d} s{s}...", end=" ", flush=True)
                t0=time.time()
                try:
                    t3[(d,s)] = run_t3(cfg,d,s)
                    print(f"OK {time.time()-t0:.1f}s")
                except Exception as e:
                    print(f"ERR {e}")
                    t3[(d,s)] = {"error":str(e)}
        json.dump({f"{k[0]}_{k[1]}":v for k,v in t3.items()},
                  open(RESULTS_DIR/"T3_raw.json","w"), indent=2)
        rows=[]
        for (d,s),r in t3.items():
            if isinstance(r, str) or (isinstance(r, dict) and "error" in r): continue
            for mode in ["D1","D2","D3","D4"]:
                if mode in r and isinstance(r[mode], dict):
                    rows.append({"dgp":d,"seed":s,"mode":mode, **r[mode]})
        t3df=pd.DataFrame(rows)
        t3df.to_csv(TABLES_DIR/"T3_gating_raw.csv", index=False)
        mc=["approval_rate","default_rate_among_approved","review_rate","policy_violation_rate"]
        seed_ci(t3df,["dgp","mode"],mc).to_csv(TABLES_DIR/"T3_gating_agg.csv", index=False)

        # tau_E sensitivity
        t3e=[]
        for (d,s),r in t3.items():
            if "tau_e_sensitivity" in r:
                for te,v in r["tau_e_sensitivity"].items():
                    t3e.append({"dgp":d,"seed":s,"tau_e":float(te), **v})
        if t3e:
            t3edf=pd.DataFrame(t3e)
            t3edf.to_csv(TABLES_DIR/"T3_tau_e_raw.csv", index=False)
            seed_ci(t3edf,["dgp","tau_e"],["approval_rate","default_rate_among_approved","review_rate","evidence_fail_rate"]).to_csv(TABLES_DIR/"T3_tau_e_agg.csv", index=False)
        print(f"  Saved T3_gating_agg.csv + T3_tau_e_agg.csv")

    # T4/T5
    if args.experiment in ["t4t5","all"]:
        print("\n[T4/T5] Review")
        t45 = {}
        for d in args.dgp:
            for s in seeds:
                print(f"  DGP{d} s{s}...", end=" ", flush=True)
                t0=time.time()
                try:
                    t45[(d,s)] = run_t4t5(cfg,d,s)
                    print(f"OK {time.time()-t0:.1f}s")
                except Exception as e:
                    print(f"ERR {e}")
                    t45[(d,s)] = {"error":str(e)}
        json.dump({f"{k[0]}_{k[1]}":v for k,v in t45.items()},
                  open(RESULTS_DIR/"T4_T5_raw.json","w"), indent=2)
        rows=[]
        for (d,s),r in t45.items():
            if isinstance(r, str) or (isinstance(r, dict) and "error" in r): continue
            for ck,m in r.items():
                if isinstance(m, dict) and "error" not in m:
                    rows.append({"dgp":d,"seed":s,"config":ck, **m})
        t45df=pd.DataFrame(rows)
        t45df.to_csv(TABLES_DIR/"T4_T5_review_raw.csv", index=False)
        mc=["pct_reviewed","bad_loan_capture","default_rate_among_approved","total_cost","cost_per_applicant"]
        seed_ci(t45df,["dgp","config"],mc).to_csv(TABLES_DIR/"T4_T5_review_agg.csv", index=False)
        print(f"  Saved T4_T5_review_agg.csv")

    # T6
    if args.experiment in ["t6","all"]:
        print("\n[T6] History")
        t6 = {}
        for d in args.dgp:
            for s in seeds:
                print(f"  DGP{d} s{s}...", end=" ", flush=True)
                t0=time.time()
                try:
                    t6[(d,s)] = run_t6(cfg,d,s)
                    print(f"OK {time.time()-t0:.1f}s")
                except Exception as e:
                    print(f"ERR {e}")
                    t6[(d,s)] = {"error":str(e)}
        json.dump({f"{k[0]}_{k[1]}":v for k,v in t6.items()},
                  open(RESULTS_DIR/"T6_raw.json","w"), indent=2)
        rows=[]
        for (d,s),r in t6.items():
            if isinstance(r, str) or (isinstance(r, dict) and "error" in r): continue
            for hk,m in r.items():
                if isinstance(m, dict):
                    rows.append({"dgp":d,"seed":s,"H":hk, **m})
        t6df=pd.DataFrame(rows)
        t6df.to_csv(TABLES_DIR/"T6_history_raw.csv", index=False)
        mc=["roc_auc","pr_auc","brier","ece","calibration_slope","gini","ks","evidence_mean","evidence_fail_rate"]
        seed_ci(t6df,["dgp","H"],mc).to_csv(TABLES_DIR/"T6_history_agg.csv", index=False)
        print(f"  Saved T6_history_agg.csv")

    print("\n" + "="*70)
    print("ALL DONE")
    print(f"Results: {RESULTS_DIR}")
    print(f"Tables:  {TABLES_DIR}")
    print("="*70)


if __name__ == "__main__":
    main()
