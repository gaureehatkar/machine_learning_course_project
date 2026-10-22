#!/usr/bin/env python
"""
Phase 9 — Figures F1–F11 from measured CSVs / npz only.
PNG 300 dpi and PDF → research/figures/
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, roc_auc_score

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

FIG = ROOT / "research/figures"
BENCH = ROOT / "research/tables/benchmarks"
TABLES = ROOT / "research/tables"
T1 = ROOT / "results/benchmarks/T1_v2"
REPORTS = ROOT / "results/benchmarks/reports"
FIG.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.size": 10,
    "axes.labelsize": 11,
    "legend.fontsize": 8,
    "figure.dpi": 120,
    "axes.grid": True,
    "grid.alpha": 0.35,
    "grid.linestyle": "--",
    "legend.framealpha": 0.92,
})


def save(fig, name):
    fig.savefig(FIG / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"  {name}")


def make_f1():
    """ROC curves LR and XGB (T1)."""
    fig, ax = plt.subplots(figsize=(5.2, 5.0))
    for lab, fn, col in [("LR", "predictions_lr.npz", "#2166ac"),
                         ("XGB", "predictions_xgb.npz", "#b2182b")]:
        p = np.load(T1 / fn)
        y, s = p["y_test"], p["p_cal_test"]
        fpr, tpr, _ = roc_curve(y, s)
        auc = roc_auc_score(y, s)
        ax.plot(fpr, tpr, color=col, lw=2, label=f"{lab} (AUC={auc:.3f})")
    ax.plot([0, 1], [0, 1], "k--", lw=1, label="Chance")
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title("Home Credit ROC (test)")
    ax.legend(loc="lower right")
    save(fig, "F1")


def make_f2():
    """Ablation A/B/C × LR/XGB, both DGPs."""
    df = pd.read_csv(TABLES / "T2_ablation_agg.csv")
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.2), sharey=True)
    configs = ["A_logreg", "A_xgb", "B_logreg", "B_xgb", "C_logreg", "C_xgb"]
    x = np.arange(len(configs))
    for ax, dgp, title in zip(axes, [1, 2], ["DGP1", "DGP2"]):
        sub = df[df["dgp"] == dgp].set_index("config")
        means = [sub.loc[c, "roc_auc_mean"] if c in sub.index else np.nan for c in configs]
        cis = [sub.loc[c, "roc_auc_ci"] if c in sub.index else 0 for c in configs]
        ax.bar(x, means, yerr=cis, capsize=3, color="#4d4d4d", ecolor="black")
        ax.set_xticks(x)
        ax.set_xticklabels(configs, rotation=45, ha="right")
        ax.set_title(title)
        ax.set_ylabel("ROC-AUC (mean ± 95% CI)")
        ax.set_ylim(0.45, 1.0)
    fig.tight_layout()
    save(fig, "F2")


def make_f3():
    """D1–D4 approval vs default among approved; matched-coverage D1 overlay."""
    t3 = pd.read_csv(TABLES / "T3_gating_agg.csv")
    mc = pd.read_csv(BENCH / "matched_coverage.csv")
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.4), sharey=True)
    colors = {"D1": "#d95f02", "D2": "#7570b3", "D3": "#e7298a", "D4": "#1b9e77"}
    for ax, dgp in zip(axes, [1, 2]):
        sub = t3[t3["dgp"] == dgp]
        for _, r in sub.iterrows():
            m = r["mode"]
            ax.errorbar(
                r["approval_rate_mean"], r["default_rate_among_approved_mean"],
                xerr=r["approval_rate_ci"], yerr=r["default_rate_among_approved_ci"],
                fmt="o", color=colors.get(m, "k"), label=m, capsize=3, ms=7,
            )
        # matched-coverage D1 vs D4 operating point from Phase 4
        row = mc[(mc["dgp"] == f"DGP{dgp}") & (mc["comparison"] == "D1_vs_D4")]
        if len(row):
            ax.axhline(
                row["mean_d1_dr"].iloc[0], color=colors["D1"], ls=":", lw=1.2,
                label="D1 DR at matched cov.",
            )
            ax.axhline(
                row["mean_dx_dr"].iloc[0], color=colors["D4"], ls=":", lw=1.2,
                label="D4 DR (matched)",
            )
        ax.set_xlabel("Approval rate")
        ax.set_title(f"DGP{dgp}")
        ax.legend(loc="upper left")
    axes[0].set_ylabel("Default rate among approved")
    fig.tight_layout()
    save(fig, "F3")


def make_f4():
    """τ_E sensitivity: approval and evidence-fail vs τ_E."""
    df = pd.read_csv(TABLES / "T3_tau_e_agg.csv")
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.0), sharex=True)
    for dgp, col in [(1, "#2166ac"), (2, "#b2182b")]:
        sub = df[df["dgp"] == dgp].sort_values("tau_e")
        axes[0].errorbar(
            sub["tau_e"], sub["approval_rate_mean"], yerr=sub["approval_rate_ci"],
            marker="o", color=col, capsize=3, label=f"DGP{dgp}",
        )
        axes[1].errorbar(
            sub["tau_e"], sub["evidence_fail_rate_mean"], yerr=sub["evidence_fail_rate_ci"],
            marker="s", color=col, capsize=3, label=f"DGP{dgp}",
        )
    axes[0].set_ylabel("Approval rate")
    axes[1].set_ylabel("Evidence-fail rate")
    for ax in axes:
        ax.set_xlabel(r"$\tau_E$")
        ax.legend(loc="best")
    fig.tight_layout()
    save(fig, "F4")


def make_f5():
    """Review frontier: capture vs budget. Equivalent-to-R1 drawn once."""
    df = pd.read_csv(BENCH / "review_baselines.csv")
    rank = pd.read_csv(BENCH / "review_rank_equivalence.csv")
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.3), sharey=True)
    # methods to plot: skip those equivalent to R1 except R1 itself
    skip_if_equiv = {"V2_margin", "V3_split_conformal", "V4_mondrian_conformal"}
    style = {
        "V0_random": ("#999999", "o", "R0 random"),
        "V1_R1_high_pd": ("#b2182b", "s", "R1 (V2/V3/V4 equiv.)"),
        "V1_R2_low_evidence": ("#4daf4a", "^", "R2 evidence"),
        "V1_R3_hybrid": ("#377eb8", "D", "R3 hybrid"),
        "V5_scross": ("#984ea3", "v", "SCROSS-style (simpl.)"),
        "V7_oracle": ("#000000", "P", "V7 upper bound"),
    }
    for ax, dgp in zip(axes, ["DGP1", "DGP2"]):
        sub = df[(df["dgp"] == dgp) & (df["rule_scenario"] == "legacy")]
        eq = rank[(rank["dgp"] == dgp) & (rank["rule_scenario"] == "legacy")]
        equiv = set(eq.loc[eq["rank_status"] == "equivalent_to_R1", "method"])
        for method, (c, mk, lab) in style.items():
            if method in skip_if_equiv and method in equiv:
                continue
            mdf = sub[sub["method"] == method].sort_values("budget")
            if mdf.empty:
                continue
            ax.errorbar(
                mdf["budget"], mdf["bad_loan_capture_mean"],
                yerr=mdf["bad_loan_capture_ci95"], color=c, marker=mk,
                capsize=2, label=lab,
            )
        ax.set_xlabel("Review budget B")
        ax.set_title(dgp)
        ax.legend(loc="lower right", fontsize=7)
    axes[0].set_ylabel("Bad-loan capture (pool)")
    fig.tight_layout()
    save(fig, "F5")


def make_f6():
    """History sensitivity: AUC and ECE vs H_num, dual axis."""
    path = BENCH / "T6_history_agg_v2_Hnum.csv"
    if not path.exists():
        t6 = pd.read_csv(TABLES / "T6_history_agg_v2.csv")
        if "H_num" not in t6.columns:
            t6["H_num"] = t6["H"].astype(str).str.replace("H", "", regex=False).astype(int)
        t6.to_csv(path, index=False)
    df = pd.read_csv(path)
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.0))
    for ax, dgp in zip(axes, [1, 2]):
        sub = df[df["dgp"] == dgp].sort_values("H_num")
        ax.errorbar(
            sub["H_num"], sub["roc_auc_mean"], yerr=sub["roc_auc_ci"],
            color="#2166ac", marker="o", capsize=3, label="ROC-AUC",
        )
        ax.set_xlabel("Forced history H (months)")
        ax.set_ylabel("ROC-AUC", color="#2166ac")
        ax2 = ax.twinx()
        ax2.errorbar(
            sub["H_num"], sub["ece_mean"], yerr=sub["ece_ci"],
            color="#b2182b", marker="s", capsize=3, label="ECE",
        )
        ax2.set_ylabel("ECE", color="#b2182b")
        ax.set_title(f"DGP{dgp}")
        ax.set_xticks(sorted(sub["H_num"].unique()))
    fig.tight_layout()
    save(fig, "F6")


def make_f7():
    """Reliability diagram T1, 10 quantile bins."""
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 4.4), sharey=True)
    cal = pd.read_csv(BENCH / "calibration_old_vs_new.csv")
    for ax, lab, fn in [
        (axes[0], "LR", "predictions_lr.npz"),
        (axes[1], "XGB", "predictions_xgb.npz"),
    ]:
        p = np.load(T1 / fn)
        y, s = p["y_test"], np.clip(p["p_cal_test"], 1e-6, 1 - 1e-6)
        qs = np.quantile(s, np.linspace(0, 1, 11))
        qs[0], qs[-1] = 0.0, 1.0
        xs, ys = [], []
        for i in range(10):
            m = (s >= qs[i]) & (s <= qs[i + 1] if i == 9 else s < qs[i + 1])
            if m.sum() == 0:
                continue
            xs.append(float(s[m].mean()))
            ys.append(float(y[m].mean()))
        ax.plot([0, 1], [0, 1], "k--", lw=1)
        ax.plot(xs, ys, "o-", color="#2166ac")
        cfg = "logreg" if lab == "LR" else "xgb"
        row = cal[(cal["experiment"] == "T1") & (cal["config"] == cfg)]
        slope = float(row["slope_logistic"].iloc[0]) if len(row) else np.nan
        ax.set_title(f"{lab} (logistic slope={slope:.3f})")
        ax.set_xlabel("Mean predicted PD")
        ax.set_xlim(0, 0.4)
        ax.set_ylim(0, 0.4)
    axes[0].set_ylabel("Observed default rate")
    fig.tight_layout()
    save(fig, "F7")


def make_f8():
    """Risk baselines AUC with CI, Home Credit and synthetic."""
    syn = pd.read_csv(BENCH / "risk_baselines_synthetic.csv")
    hc = pd.read_csv(BENCH / "risk_baselines_home_credit.csv")
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.4))
    # synthetic: feature C tuned
    ax = axes[0]
    sub = syn[(syn["feature_set"] == "C") & (syn["tuning"] == "tuned")]
    models = sorted(sub["model"].unique())
    x = np.arange(len(models))
    w = 0.35
    for i, dgp in enumerate(["DGP1", "DGP2"]):
        s = sub[sub["dgp"] == dgp].set_index("model")
        means = [s.loc[m, "roc_auc_mean"] for m in models]
        cis = [s.loc[m, "roc_auc_ci"] for m in models]
        ax.bar(x + (i - 0.5) * w, means, w, yerr=cis, capsize=3, label=dgp)
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=30, ha="right")
    ax.set_ylabel("ROC-AUC (mean ± 95% CI)")
    ax.set_title("Synthetic Set C, tuned")
    ax.legend(loc="lower right")
    ax.set_ylim(0.85, 0.95)
    ax = axes[1]
    hc2 = hc.sort_values("roc_auc", ascending=False)
    ax.bar(hc2["model"] + "\n" + hc2["tuning"], hc2["roc_auc"], color="#4d4d4d")
    ax.set_ylabel("ROC-AUC")
    ax.set_title("Home Credit")
    ax.tick_params(axis="x", rotation=40)
    fig.tight_layout()
    save(fig, "F8")


def make_f9():
    df = pd.read_csv(BENCH / "architecture_model_agnostic.csv")
    metrics = [
        ("violation_rate_mean", "violation_rate_ci", "Policy violation rate"),
        ("bad_loan_capture_mean", "bad_loan_capture_ci", "R1 bad-loan capture"),
        ("default_rate_among_approved_mean", "default_rate_among_approved_ci", "Default among approved"),
    ]
    models = sorted(df["model"].unique())
    fig, axes = plt.subplots(1, 3, figsize=(11.0, 3.8))
    x = np.arange(len(models))
    combinations = [
        ("DGP1", 0.20), ("DGP1", 0.30),
        ("DGP2", 0.20), ("DGP2", 0.30),
    ]
    w = 0.18
    for ax, (mcol, ccol, title) in zip(axes, metrics):
        for i, (dgp, budget) in enumerate(combinations):
            s = df[(df["dgp"] == dgp) & (df["budget"] == budget)].set_index("model")
            offset = (i - (len(combinations) - 1) / 2) * w
            ax.bar(
                x + offset,
                [s.loc[m, mcol] for m in models],
                w,
                yerr=[s.loc[m, ccol] for m in models],
                capsize=2,
                label=f"{dgp}, B={budget:.0%}",
            )
        ax.set_xticks(x)
        ax.set_xticklabels(models, rotation=40, ha="right")
        ax.set_title(title)
        ax.legend(fontsize=6, loc="best")
    fig.tight_layout()
    save(fig, "F9")


def make_f10():
    df = pd.read_csv(BENCH / "policy_baselines.csv")
    scenarios = ["legacy", "v2_unknown", "v2_ineligible", "v2_eligible"]
    fig, axes = plt.subplots(2, 4, figsize=(16.0, 8.0), sharey=True)
    metrics = [
        ("violation_rate_mean", "violation_rate_ci", "violation"),
        ("wrongful_decline_rate_mean", "wrongful_decline_rate_ci", "wrongful decline"),
        ("review_rate_mean", "review_rate_ci", "review"),
    ]
    for row_idx, dgp in enumerate(["DGP1", "DGP2"]):
        for col_idx, scenario in enumerate(scenarios):
            ax = axes[row_idx, col_idx]
            sub = df[(df["dgp"] == dgp) & (df["rule_scenario"] == scenario)]
            sub = sub.set_index("policy_baseline").reindex([
                "P0_no_policy",
                "P1_fail_closed",
                "P2_fail_open",
                "P3_train_imputation",
                "P4_kleene",
            ])
            x = np.arange(len(sub))
            w = 0.25
            for i, (m, c, lab) in enumerate(metrics):
                ax.bar(
                    x + (i - 1) * w, sub[m], w, yerr=sub[c], capsize=2, label=lab,
                )
            ax.set_xticks(x)
            ax.set_xticklabels(["P0", "P1", "P2", "P3", "P4"])
            ax.set_title(f"{dgp} · {scenario}")
            if row_idx == 0 and col_idx == 0:
                ax.legend(fontsize=7)
    axes[0, 0].set_ylabel("Rate (mean ± 95% CI)")
    axes[1, 0].set_ylabel("Rate (mean ± 95% CI)")
    fig.tight_layout()
    save(fig, "F10")


def make_f11():
    df = pd.read_csv(BENCH / "matched_coverage.csv")
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ylabels = []
    y = []
    x = []
    xerr_lo = []
    xerr_hi = []
    for _, r in df.iterrows():
        ylabels.append(f"{r['dgp']} {r['comparison']}")
        y.append(len(ylabels) - 1)
        x.append(r["mean_diff_dr"])
        xerr_lo.append(r["mean_diff_dr"] - r["ci_lo"])
        xerr_hi.append(r["ci_hi"] - r["mean_diff_dr"])
    ax.errorbar(x, y, xerr=[xerr_lo, xerr_hi], fmt="o", color="#2166ac", capsize=3)
    ax.axvline(0, color="k", lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels(ylabels)
    ax.set_xlabel("Default-rate difference (D1 − Dx) at matched coverage")
    fig.tight_layout()
    save(fig, "F11")


def main():
    print("Phase 9 figures")
    make_f1()
    make_f2()
    make_f3()
    make_f4()
    make_f5()
    make_f6()
    make_f7()
    make_f8()
    make_f9()
    make_f10()
    make_f11()
if __name__ == "__main__":
    main()
