# Benchmark Results — SynthGigCredit-IN

**Audit status: INCOMPLETE — do not treat this as submission-ready.** The Phase 1 preflight manifest was incomplete; Phase 5 baseline artifacts do not meet the requested tuning/slope protocol; Phase 6 lacks required policy metrics and scenarios; and Phase 9 fails the F10 acceptance check. See `results/benchmarks/reports/PHASE_1_REPORT.md`, `PHASE_5_REPORT.md`, `PHASE_6_REPORT.md`, and `PHASE_9_REPORT.md`. The current installed XGBoost/NumPy environment also crashes during model import. Policy rules are **UNVERIFIED**.

The sections below summarize prior measured outputs; where the audit reports identify a protocol or metric issue, do not use those outputs as final paper results.

## What ran

Prior Phase 1–8 runs wrote outputs under `results/benchmarks/` and `research/tables/benchmarks/`. The audit verified 140 tests passing and regenerated Phase 8 paired tests from available per-seed files. Phase 1, 5, 6, and 9 acceptance checks are not all met; Phase 10's report was not reached.

Reproduce (long; Phase 5–7 dominate runtime): `make reproduce`

Measured Phase 7 wall time on this host: ~10.8 h (one seed stalled ~8.5 h; remaining seeds typically 2–40 s). Phase 5 previously reported 1220.8 s in `results/benchmarks/reports/PHASE_5_REPORT.md` (that report’s inline AUC table was hardcoded and is not the source of truth; use the CSVs).

---

## Main findings (neutral)

- **Home Credit ranking (T1 v2).** LR ROC-AUC 0.7383, XGB 0.7568. Logistic calibration slope 1.013 (LR) and 1.022 (XGB). Source: `results/benchmarks/T1_v2/T1_results_v2.json`, `research/tables/benchmarks/calibration_old_vs_new.csv`.
- **Feature sets (T2).** Set B (gig-only) ROC-AUC ≈ 0.50. Set A and Set C are close; on DGP1, A_xgb mean AUC 0.9218 vs C_xgb 0.9182. Source: `research/tables/T2_ablation_agg.csv`.
- **Matched coverage (Phase 4).** At validation-matched approval rates, D1 has a **lower** default rate among approved than D4 (DGP1 D1−D4 = −0.0142, 95% CI [−0.0160, −0.0125]). D4 still has zero policy-violation rate in T3; D1 does not. Source: `research/tables/benchmarks/matched_coverage.csv`, `research/tables/T3_gating_agg.csv`.
- **Review (Phase 7, legacy, B=0.20).** DGP1 bad-loan capture: R0 0.2108 ± 0.0297; R1 0.4829 ± 0.0523; R3 0.4058 ± 0.0389; V7 oracle 1.000. V2 margin and split/Mondrian conformal referred sets were **identical to R1** in every seed (Spearman ρ with PD = 1.0). V6 skipped (no exposure column). Source: `research/tables/benchmarks/review_baselines.csv`, `review_rank_equivalence.csv`.
- **e-Shram (T9).** Approval-rate disparity (yes − no) DGP1 0.0053 ± 0.0135 (CI crosses zero). Source: `research/tables/T9_fairness_aggregated.csv`.
- **Policy rules v2.** Status UNVERIFIED. Agri scenarios change D4 review/approval; violation among approved remains 0.000 in the v2-vs-legacy table. Source: `research/tables/benchmarks/policy_v2_vs_legacy.csv`, `configs/policy_rules/v2/`.

---

## Old vs new calibration

OLS of y on logit(p) recovers ≈ prevalence×(1−prevalence), not slope 1. Logistic slope of y on logit(p) is near 1 after Platt on Home Credit and T2 A/C.

| Source | Finding |
|---|---|
| `calibration_old_vs_new.csv` T1 LR | OLS 0.0742, logistic 1.0132; AUC old/new agree to ~1e-5 |
| T1 XGB | OLS 0.0755, logistic 1.0224; AUC identical |
| T2 A/C | logistic slopes 0.98–1.01; B (no signal) slopes far from 1 |
| T6 H=1 | logistic slope 0.81 (train on H=12, score forced-H; distribution shift) |

**Phase 5 CSV caveat.** `risk_baselines_synthetic.csv` `calibration_slope_mean` ≈ 0.12–0.13 because `evaluate_predictions` previously called `calibration_slope_intercept(p, y)` (arguments swapped). The code is fixed; the CSV has not been regenerated. Do not use those slope columns. AUC/PR/Brier in the same file are from sklearn and remain usable.

---

## Matched coverage

Source: `research/tables/benchmarks/matched_coverage.csv` (legacy; per-seed in `results/benchmarks/matched_coverage/matched_coverage_raw.csv`).

| DGP | comparison | mean D1 DR | mean Dx DR | D1−Dx | 95% CI |
|---|---|---:|---:|---:|---|
| DGP1 | D1 vs D2 | 0.0098 | 0.0191 | −0.0094 | [−0.0111, −0.0076] |
| DGP1 | D1 vs D3 | 0.0060 | 0.0172 | −0.0112 | [−0.0128, −0.0097] |
| DGP1 | D1 vs D4 | 0.0033 | 0.0175 | −0.0142 | [−0.0160, −0.0125] |
| DGP2 | D1 vs D4 | 0.0051 | 0.0253 | −0.0202 | [−0.0226, −0.0177] |

Direction: D1 default-among-approved is lower at matched coverage. T3 D1 policy_violation_rate_mean DGP1 = 0.0735. D4 = 0.0000. Source: `research/tables/T3_gating_agg.csv`.

---

## Risk baselines

Source: `research/tables/benchmarks/risk_baselines_synthetic.csv` (tuned, Set C, ROC-AUC mean ± ci column `roc_auc_ci`).

DGP1 Set C tuned: lgbm 0.9221 ± 0.0019; catboost 0.9212 ± 0.0021; xgb 0.9212 ± 0.0022 (file order by AUC). DGP1 Set A tuned xgb 0.9223 ± 0.0022.

Home Credit: see `risk_baselines_home_credit.csv` (single split; no seed CI).

---

## Architecture baselines (6A)

Source: `architecture_model_agnostic.csv`. DGP1 D4 default-among-approved: lgbm 0.0164 ± 0.0015; xgb 0.0168 ± 0.0018; catboost 0.0169 ± 0.0020; rf 0.0186 ± 0.0020; woe_lr 0.0197 ± 0.0017. R1 capture at 20% differs by model (rf 0.2934 ± 0.0743; xgb 0.2616 ± 0.0622).

Single-score vs D4 at matched coverage: `single_score_vs_pipeline.csv` — DGP1 default-rate difference −0.0001 ± 0.0001 (essentially tied on that metric).

---

## Policy baselines (6C)

Source: `policy_baselines.csv`. DGP1 violation_rate_mean: P0 0.0758 ± 0.0038; P1 0.0000; P2 0.0039 ± 0.0010; P3 0.0039 ± 0.0010; P4 0.0000. Review rate: P4 0.2386 ± 0.0033; P1 0.1721 ± 0.0031. Wrongful-decline is not a column in this CSV.

Qualitative notes: `results/benchmarks/policy_qualitative.md`.

---

## Review baselines and rank-equivalence

Source: `review_baselines.csv` (legacy, B=0.20 excerpt in `PHASE_7_REPORT.md`). V6 not run: Phase 3 found no loan-amount/exposure column (`PHASE_3_REPORT.md`). V5 is labelled SCROSS-style (simplified).

`review_rank_equivalence.csv`: V1_R1, V2_margin, V3_split_conformal, V4_mondrian_conformal have Spearman ρ=1 with PD and `frac_identical_to_r1_b20=1.0` on legacy DGP1. Present those as equivalent to R1, not separate wins. Within pool PD < τ < 0.5, |PD−τ| = τ−PD is monotone in PD.

---

## Cost sensitivity

Source: `cost_sensitivity.csv`. Common C_R grid {0.05, 0.10, 0.20} with C_FP=1 and C_FN/C_FP ∈ {1,3,5}, both B=0.20 and 0.30. Example DGP1 legacy V0 B=0.20 C_FN ratio=1: cost 0.260 at C_R=0.05 vs 0.280 at C_R=0.20. Do not claim 20% budget is more cost-efficient unless it holds at the same C_R; compare cells in this file.

---

## Statistical tests

Source: `research/tables/benchmarks/statistical_tests.csv` (written by Phase 8). Primary family: Bonferroni m=3 per DGP. Secondary: Holm. Contrasts: A vs C XGB AUC (T2 raw); D1 vs D4 matched-coverage DR (Phase 4 raw, diff = D1−D4); R0 vs R3 capture at 20% (Phase 7 per-seed).

---

## DGP diagnostic

Source: `dgp_latent_diagnostic.csv`. `rho` Spearman ≈ 0.24 (DGP1) / 0.26 (DGP2), ROC-AUC ≈ 0.71. `platform_tenure` and `multi_platform` AUC ≈ 0.50. Gig-related latents as named in the prompt (σ_m, tenure, multi-platform, seasonal amp) do **not** carry standalone ranking signal; income-process `rho` and `g` do.

---

## Limitations

- Synthetic default labels; results that follow from the DGP (policy violations → 0 under a hard gate, R2 vs R0, e-Shram independence) are true **by construction** where the generator encodes them.
- Perfect-oracle reviewer (referred defaulter / true-UNSATISFIED declined).
- Home Credit is Home Credit Default Risk (consumer loans), not Indian gig lending.
- No temporal validation.
- Policy rules UNVERIFIED (`configs/policy_rules/v2/` provenance placeholders).
- T6 trains on H=12 and scores forced-H views without refit; evidence score is constant across H (`T6_history_agg.csv` evidence_mean ≈ 0.599).
- Synthetic AUC/KS reflect the DGP, not field performance.
- Phase 11 (second real dataset proxy) was not run.

---

## Source index

| Artifact | Path |
|---|---|
| T1 v2 | `results/benchmarks/T1_v2/` |
| Calibration erratum | `research/tables/benchmarks/calibration_old_vs_new.csv` |
| T2–T9 originals | `research/tables/T*_*.csv` |
| Matched coverage | `research/tables/benchmarks/matched_coverage.csv` |
| Risk baselines | `research/tables/benchmarks/risk_baselines_*.csv` |
| Review | `research/tables/benchmarks/review_*.csv`, `cost_sensitivity.csv` |
| Stats | `research/tables/benchmarks/statistical_tests.csv` |
| Figures | `research/figures/F1`–`F9` and `F11` PNG/PDF; F10 is pending the Phase 6 policy-baseline rerun |
| Claims | `research/CLAIMS_AUDIT.md` |
