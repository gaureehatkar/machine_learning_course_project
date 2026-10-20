# Claims audit

Status labels: **supported** (measured in a cited file), **by construction** (follows from the DGP or oracle), **not supported**.

Policy rule sets are **UNVERIFIED**. Do not read this file as a legal verification of PMMY/JanSamarth.

| Claim sentence candidate | Source file | Status |
|---|---|---|
| Logistic calibration slope on Home Credit after Platt is near 1 (LR 1.013, XGB 1.022). | `research/tables/benchmarks/calibration_old_vs_new.csv` | supported |
| OLS calibration slope ≈ 0.074 on Home Credit is an estimator artifact, not evidence of slope-0.07 miscalibration. | `calibration_old_vs_new.csv`; `src/evaluation/metrics.py` | supported |
| Gig-only features (Set B) have ROC-AUC ≈ 0.50 on the synthetic DGPs. | `research/tables/T2_ablation_agg.csv` | supported |
| Combined Set C XGB does not improve ROC-AUC over Set A XGB on DGP1 (0.9182 vs 0.9218). | `research/tables/T2_ablation_agg.csv` | supported |
| D4 approval rate is lower than D1 (DGP1 0.4115 vs 0.7015). | `research/tables/T3_gating_agg.csv` | supported |
| D4 policy violation rate is 0.000 in T3; D1 is 0.0735 (DGP1). | `research/tables/T3_gating_agg.csv` | by construction (hard policy gate + generator eligibility) |
| At matched coverage, D1 default-among-approved is lower than D4 (DGP1 difference −0.0142). | `research/tables/benchmarks/matched_coverage.csv` | supported |
| D4 has lower default rate than D1 at matched coverage. | `matched_coverage.csv` | not supported (opposite direction) |
| R1 bad-loan capture at 20% budget exceeds R0 (DGP1 0.4829 vs 0.2108). | `review_baselines.csv`; T4 raw | supported (perfect-oracle reviewer) |
| Margin / split conformal / Mondrian are separate improvements over R1. | `review_rank_equivalence.csv` | not supported (identical referred sets to R1 at B=20%) |
| Expected-loss ranking (V6) outperforms PD ranking. | Phase 3 exposure audit | not supported (no exposure column; V6 skipped) |
| e-Shram registered applicants have ~1–2pp higher approval driven by policy-gate correlation. | `T9_fairness_aggregated.csv` | not supported (disparity +0.53pp, CI crosses 0) |
| e-Shram approval disparity is consistent with independence in the DGP. | `T9_fairness_aggregated.csv`; generator `policy_effect_delta` | by construction |
| XGBoost outperforms LR by ~1–2pp AUC on all datasets. | T1 v2; T2 agg | not supported as a uniform 1–2pp claim (Home Credit +1.85pp AUC; DGP1 A +0.81pp) |
| KS > 0.6 is excellent in consumer credit (applied to synthetic T6). | `T6_history_agg.csv` | not supported (synthetic DGP; external verbal benchmark not measured here) |
| Policy rules v2 are official legal PMMY text. | `configs/policy_rules/v2/` `rule_set_status` | not supported (UNVERIFIED placeholders) |
| The method works for real gig workers in India. | Home Credit is consumer loans; synthetic is simulated | not supported |
| Impossible with a single score. | `single_score_vs_pipeline.csv` | not supported (DR difference ≈ 0 at matched coverage on that table) |
| There is no existing system for this problem. | not evaluated | not supported |
| Platt-calibrated models underpredict default. | logistic slope T1 ≈ 1.01 | not supported |
| Results generalize temporally. | no time-split | not supported |
| Perfect human review is a realistic operations assumption. | `src/decisions/review.py` oracle | by construction (simulation) |
| T6 evidence scores change with forced H. | `T6_history_agg.csv` evidence_mean constant 0.599 | not supported |
| Gig latents (tenure, multi-platform, σ_m) rank defaults. | `dgp_latent_diagnostic.csv` AUC ≈ 0.50 | not supported |
| Income-process `rho` ranks defaults (AUC ≈ 0.71). | `dgp_latent_diagnostic.csv` | supported (synthetic only) |
| CatBoost/LGBM/XGB Set-C AUCs overlap within seed CIs. | `risk_baselines_synthetic.csv` | supported (AUC columns; ignore slope columns in that file) |
| 20% review budget is more cost-efficient than 30%. | `cost_sensitivity.csv` | not supported unless compared at the same C_R (grid exists; no automatic winner) |
