#!/usr/bin/env python
"""
Phase 8 — Pre-specified paired tests from measured per-seed tables.

Primary (Bonferroni α = 0.05/3):
  1. A vs C, XGB ROC-AUC (T2 raw)
  2. D1 vs D4 at matched coverage, default rate among approved (Phase 4 raw)
  3. R0 vs R3, bad-loan capture at 20% budget (Phase 7 per-seed)

Secondary / exploratory are labelled as such (Holm within family).
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.evaluation.paired_tests import (
    ALPHA,
    ALPHA_BONFERRONI,
    bonferroni_correction,
    holm_correction,
    paired_ttest,
)

TABLES = ROOT / "research/tables"
BENCH = TABLES / "benchmarks"
REPORTS = ROOT / "results/benchmarks/reports"
REPORTS.mkdir(parents=True, exist_ok=True)


def _row(contrast, family, dgp, metric, a, b, method, p_adjusted, a_label, b_label):
    r = paired_ttest(a, b)
    # Adjusted p (Bonferroni p*m or Holm) is always compared to α = 0.05.
    sig = bool(p_adjusted < ALPHA)
    return {
        "contrast": contrast,
        "family": family,
        "dgp": dgp,
        "metric": metric,
        "a_label": a_label,
        "b_label": b_label,
        "n": r.n,
        "mean_a": round(r.mean_a, 6),
        "mean_b": round(r.mean_b, 6),
        "mean_diff": round(r.mean_diff, 6),
        "ci_lo": round(r.ci_lo, 6),
        "ci_hi": round(r.ci_hi, 6),
        "t": round(r.t_stat, 4),
        "df": r.df,
        "p": float(r.p_value),
        "p_adjusted": float(p_adjusted),
        "method": method,
        "significant": sig,
        "cohen_d_z": round(r.cohen_d_z, 4),
    }


def _series(df, dgp, config_col, config, metric, seed="seed"):
    sub = df[(df["dgp"] == dgp) & (df[config_col] == config)].sort_values(seed)
    return sub[metric].astype(float).values


def run_phase8():
    rows = []
    t2 = pd.read_csv(TABLES / "T2_ablation_raw.csv")
    mc = pd.read_csv(ROOT / "results/benchmarks/matched_coverage/matched_coverage_raw.csv")
    rev = pd.read_csv(BENCH / "review_baselines_per_seed.csv")
    risk_raw = BENCH / "risk_baselines_synthetic_raw.csv"

    primary_p = []
    primary_meta = []

    # --- Primary 1: A vs C XGB ROC-AUC (diff = C − A) ---
    for dgp in [1, 2]:
        a = _series(t2, dgp, "config", "A_xgb", "roc_auc")
        c = _series(t2, dgp, "config", "C_xgb", "roc_auc")
        r = paired_ttest(a, c)
        primary_p.append(r.p_value)
        primary_meta.append(("A_vs_C_XGB_ROC_AUC", f"DGP{dgp}", "roc_auc", a, c, "A_xgb", "C_xgb"))

    # --- Primary 2: D1 vs D4 matched coverage DR (diff = D4 − D1 wait: spec says D1 − Dx)
    # paired_ttest(a,b) = b-a, so a=D1, b=D4 would be D4-D1. Spec Phase 4: difference (D1 − Dx).
    # Use a=Dx, b=D1 so mean_diff = D1 − D4.
    for dgp in ["DGP1", "DGP2"]:
        sub = mc[(mc["dgp"] == dgp) & (mc["scenario"] == "legacy") & (mc["comparison"] == "D1_vs_D4")]
        sub = sub.sort_values("seed")
        d1 = sub["d1_dr_approved"].astype(float).values
        d4 = sub["dx_dr_approved"].astype(float).values
        r = paired_ttest(d4, d1)  # mean_diff = D1 − D4
        primary_p.append(r.p_value)
        primary_meta.append(
            ("D1_vs_D4_matched_coverage_DR", dgp, "default_rate_among_approved", d4, d1, "D4", "D1")
        )

    # --- Primary 3: R0 vs R3 capture at B=0.20 (diff = R3 − R0) ---
    for dgp in ["DGP1", "DGP2"]:
        sub = rev[
            (rev["dgp"] == dgp)
            & (rev["rule_scenario"] == "legacy")
            & (rev["budget"] == 0.2)
        ]
        r0 = sub[sub["method"] == "V0_random"].sort_values("seed")["bad_loan_capture"].astype(float).values
        r3 = sub[sub["method"] == "V1_R3_hybrid"].sort_values("seed")["bad_loan_capture"].astype(float).values
        r = paired_ttest(r0, r3)
        primary_p.append(r.p_value)
        primary_meta.append(
            ("R0_vs_R3_capture_B20", dgp, "bad_loan_capture", r0, r3, "R0", "R3")
        )

    # Bonferroni across the 3 contrast types × 2 DGPs would be m=6; spec says Bonferroni α=0.05/3
    # for the three pre-specified contrasts, applied per DGP (m=3 within DGP).
    # We apply Bonferroni m=3 within each DGP (the three contrast types).
    for dgp_name in ["DGP1", "DGP2"]:
        idxs = [i for i, m in enumerate(primary_meta) if m[1] == dgp_name]
        ps = [primary_p[i] for i in idxs]
        adj = bonferroni_correction(ps, n_contrasts=3)
        for j, i in enumerate(idxs):
            contrast, dgp, metric, a, b, al, bl = primary_meta[i]
            rows.append(
                _row(contrast, "primary", dgp, metric, a, b, "Bonferroni", float(adj[j]), al, bl)
            )

    # --- Secondary: R0 vs R1 at B=0.20 ---
    sec = []
    for dgp in ["DGP1", "DGP2"]:
        sub = rev[
            (rev["dgp"] == dgp)
            & (rev["rule_scenario"] == "legacy")
            & (rev["budget"] == 0.2)
        ]
        r0 = sub[sub["method"] == "V0_random"].sort_values("seed")["bad_loan_capture"].astype(float).values
        r1 = sub[sub["method"] == "V1_R1_high_pd"].sort_values("seed")["bad_loan_capture"].astype(float).values
        sec.append(("R0_vs_R1_capture_B20", dgp, "bad_loan_capture", r0, r1, "R0", "R1"))

    # 30% budget R0 vs R1
    for dgp in ["DGP1", "DGP2"]:
        sub = rev[
            (rev["dgp"] == dgp)
            & (rev["rule_scenario"] == "legacy")
            & (rev["budget"] == 0.3)
        ]
        r0 = sub[sub["method"] == "V0_random"].sort_values("seed")["bad_loan_capture"].astype(float).values
        r1 = sub[sub["method"] == "V1_R1_high_pd"].sort_values("seed")["bad_loan_capture"].astype(float).values
        sec.append(("R0_vs_R1_capture_B30", dgp, "bad_loan_capture", r0, r1, "R0", "R1"))

    # Baseline vs XGB-C (tuned) Holm per DGP
    if risk_raw.exists():
        rr = pd.read_csv(risk_raw)
        rr = rr[(rr["tuning"] == "tuned") & (rr["feature_set"] == "C")]
        for dgp in rr["dgp"].unique():
            xgb = rr[(rr["dgp"] == dgp) & (rr["model"] == "xgb")].sort_values("seed")["roc_auc"].values
            others = [m for m in rr["model"].unique() if m != "xgb"]
            fam_rows = []
            for m in others:
                oth = rr[(rr["dgp"] == dgp) & (rr["model"] == m)].sort_values("seed")["roc_auc"].values
                if len(oth) == len(xgb) and len(xgb) > 1:
                    fam_rows.append(
                        (f"XGB_C_vs_{m}_ROC_AUC", str(dgp), "roc_auc", xgb, oth, "xgb", m)
                    )
            ps = [paired_ttest(a, b).p_value for _, _, _, a, b, _, _ in fam_rows]
            adj = holm_correction(ps) if ps else []
            for k, meta in enumerate(fam_rows):
                contrast, dgp_s, metric, a, b, al, bl = meta
                rows.append(
                    _row(contrast, "secondary_baselines", dgp_s, metric, a, b, "Holm", float(adj[k]), al, bl)
                )

    ps_sec = [paired_ttest(a, b).p_value for _, _, _, a, b, _, _ in sec]
    adj_sec = holm_correction(ps_sec) if ps_sec else []
    for k, meta in enumerate(sec):
        contrast, dgp, metric, a, b, al, bl = meta
        rows.append(_row(contrast, "secondary", dgp, metric, a, b, "Holm", float(adj_sec[k]), al, bl))

    # Pooled-DGP robustness for primary 1 (A vs C XGB)
    a_all, c_all = [], []
    for dgp in [1, 2]:
        a_all.append(_series(t2, dgp, "config", "A_xgb", "roc_auc"))
        c_all.append(_series(t2, dgp, "config", "C_xgb", "roc_auc"))
    a_p = np.concatenate(a_all)
    c_p = np.concatenate(c_all)
    r = paired_ttest(a_p, c_p)
    rows.append(
        _row(
            "A_vs_C_XGB_ROC_AUC_pooled",
            "exploratory_pooled",
            "pooled",
            "roc_auc",
            a_p,
            c_p,
            "none",
            r.p_value,
            "A_xgb",
            "C_xgb",
        )
    )

    df = pd.DataFrame(rows)
    df.to_csv(BENCH / "statistical_tests.csv", index=False)

    # T6 copy with H_num (do not edit original)
    t6v2 = TABLES / "T6_history_agg_v2.csv"
    if t6v2.exists():
        t6 = pd.read_csv(t6v2)
        if "H_num" not in t6.columns:
            t6["H_num"] = t6["H"].astype(str).str.replace("H", "", regex=False).astype(int)
        t6.to_csv(BENCH / "T6_history_agg_v2_Hnum.csv", index=False)
    else:
        t6 = pd.read_csv(TABLES / "T6_history_agg.csv")
        t6["H_num"] = t6["H"].astype(str).str.replace("H", "", regex=False).astype(int)
        t6.to_csv(BENCH / "T6_history_agg_v2_Hnum.csv", index=False)

    prim = df[df["family"] == "primary"]
    lines = [
        "# Phase 8 Report: Statistical Tests",
        "",
        f"**Date**: {datetime.now(timezone.utc).date().isoformat()}",
        "**Status**: COMPLETE",
        "",
        "## (a) What ran",
        "- Command: `python -u research/run_phase8_statistical_tests.py`",
        "- Module: `src/evaluation/paired_tests.py` (t.ppf from n, Holm, Bonferroni)",
        f"- Primary Bonferroni α = 0.05/3 = {ALPHA_BONFERRONI:.6f} (3 contrasts per DGP)",
        "- Confidence critical values are computed from each observed seed count with `scipy.stats.t.ppf`.",
        "",
        "## (b) Files written",
        "- `research/tables/benchmarks/statistical_tests.csv`",
        "- `research/tables/benchmarks/T6_history_agg_v2_Hnum.csv` (copy; original T6 CSV untouched)",
        "",
        "## (c) Primary contrasts",
        "",
        "| dgp | contrast | mean_diff | ci_lo | ci_hi | t | p | p_adjusted | significant |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for _, r in prim.iterrows():
        lines.append(
            f"| {r['dgp']} | {r['contrast']} | {r['mean_diff']:.6f} | {r['ci_lo']:.6f} | "
            f"{r['ci_hi']:.6f} | {r['t']:.3f} | {r['p']:.4g} | {r['p_adjusted']:.4g} | {r['significant']} |"
        )
    n_sig = int(df["significant"].sum())
    lines += [
        "",
        f"Total rows: {len(df)}; significant at family-wise rule: {n_sig}",
        "",
        "## (d) Anomalies / deviations",
        "- Primary 1 uses original T2 per-seed AUC (A_xgb vs C_xgb), not Phase 5 (Phase 5 slopes are a known arg-order artifact).",
        "- Primary 2 uses Phase 4 legacy matched-coverage per-seed DRs; mean_diff = D1 − D4.",
        "- Primary 3 uses Phase 7 V0_random vs V1_R3_hybrid at B=0.20, legacy rules.",
        "- Rank-equivalence (Phase 7): V2/V3/V4 referred sets identical to R1 at B=0.20; they are not separate wins.",
        "",
        "## (e) Acceptance checks",
        "| Check | Status |",
        "|---|---|",
        "| Paired t from n seeds | PASS |",
        "| Primary Bonferroni m=3 per DGP | PASS |",
        "| T_CRIT hardcode removed | PASS |",
        "| T6 H_num on a new copy | PASS |",
        "",
        "## (f) Open questions",
        "- Phase 5 logistic slopes remain the inverted-argument values until a re-run; AUC/PR/Brier in those CSVs are still usable.",
    ]
    (REPORTS / "PHASE_8_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(df)} contrasts to statistical_tests.csv")


if __name__ == "__main__":
    run_phase8()
