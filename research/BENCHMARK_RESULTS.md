# Benchmark Results — SynthGigCredit-IN

## Status

Phases 1–10 have generated their benchmark outputs, reports, figures, and paper tables. The final full-suite test run and claim scan are recorded in `results/benchmarks/reports/PHASE_10_REPORT.md`. Phase 11 is optional and was not run. Policy rules remain **UNVERIFIED**; the YAML files use provenance placeholders and do not establish legal eligibility.

Reproduce the pipeline with `make reproduce` from the pinned environment. It runs Phases 1–10 in order and may take substantial time because Phase 5 tunes models with cross-validation. The outputs and limitations below refer to the CSVs and reports cited in each section.

## Executive summary

- On Home Credit, T1 v2 ROC-AUC was 0.7383 for LR and 0.7568 for XGBoost. The corrected logistic calibration slopes were 1.013 and 1.022. Home Credit is a consumer-loan dataset; it does not measure Indian gig lending. Source: `results/benchmarks/T1_v2/T1_results_v2.json`, `research/tables/benchmarks/calibration_old_vs_new.csv`.
- On the synthetic data, gig-only Set B was near chance (XGBoost AUC 0.4992 on DGP1 and 0.4977 on DGP2). The tuned Set C baselines had AUCs from 0.9123 to 0.9212 on DGP1 and 0.9068 to 0.9151 on DGP2. These are generator-specific results. Source: `research/tables/T2_ablation_agg.csv`, `research/tables/benchmarks/risk_baselines_synthetic.csv`.
- At validation-matched coverage under legacy rules, D1 had lower test default rates among approved than D4: D1−D4 was −0.0142 on DGP1 (95% CI [−0.0160, −0.0125]) and −0.0202 on DGP2 (95% CI [−0.0226, −0.0177]). D4 had zero measured violations under the configured hard gate; policy provenance is still unverified. Source: `research/tables/benchmarks/matched_coverage.csv`, `research/tables/T3_gating_agg.csv`.
- In Phase 6A, all five evaluated risk models had zero measured D4 violations on DGP1 at a 20% review budget. In Phase 6B, a plain fail-closed policy filter matched D4 coverage closely and had lower measured default rates in both DGPs. The results do not establish that comparable controls require a multi-stage architecture. Source: `research/tables/benchmarks/architecture_model_agnostic.csv`, `research/tables/benchmarks/single_score_vs_pipeline.csv`.
- In the Phase 7 legacy DGP1 comparison at a 20% review budget, R1 captured 0.4829 of pool defaulters (95% CI half-width 0.0523), compared with 0.2108 (0.0297) for random review. Margin and the two conformal methods produced the same referred sets as R1 in the checked seeds. The reviewer uses a perfect oracle in simulation. Source: `research/tables/benchmarks/review_baselines.csv`, `research/tables/benchmarks/review_rank_equivalence.csv`.

## Calibration: old and corrected estimates

The old OLS slope regresses the outcome on the logit score and is not the logistic calibration slope. The table records both estimators and compares old and rerun AUC, Brier, and ECE values. T1 AUC and Brier match within 1e-6; its ECE differs slightly for LR (0.002400 vs 0.002499). For T2/T6 the stored rounded values match at the reported precision. Source: `research/tables/benchmarks/calibration_old_vs_new.csv`.

| Experiment | Configuration | Old OLS slope | Logistic slope | Logistic intercept |
|---|---|---:|---:|---:|
| T1 Home Credit | LR | 0.0742 | 1.0132 | 0.0355 |
| T1 Home Credit | XGBoost | 0.0755 | 1.0224 | 0.0546 |
| T2 DGP1 | XGBoost A / C | 0.0768 / 0.0819 | 1.0015 / 0.9954 | −0.0015 / −0.0087 |
| T2 DGP2 | XGBoost A / C | 0.0821 / 0.0888 | 0.9778 / 0.9848 | −0.0241 / −0.0194 |
| T6 DGP1 | XGBoost, H=1 / 3 / 6 / 12 | 0.0760 / 0.0781 / 0.0808 / 0.0844 | 0.8079 / 0.8462 / 0.9335 / 1.1197 | −0.6272 / −0.1483 / −0.0636 / 0.1139 |

T2 Set B has near-chance AUC and logistic slopes of 0.1458–0.5067, outside the [0.8, 1.2] calibration acceptance interval. That no-signal result is retained and disclosed; it is not described as calibrated. Phase 5’s tuned A/C and Home Credit baseline slopes were within [0.8, 1.2]. Source: `research/tables/benchmarks/calibration_old_vs_new.csv`, `research/tables/benchmarks/risk_baselines_synthetic.csv`, `research/tables/benchmarks/risk_baselines_home_credit.csv`.

## Matched coverage

For each seed, D1's threshold was selected on validation to match the comparison gate's validation coverage; both were then measured on test. Negative differences mean lower default rate among approved for D1. Source: `research/tables/benchmarks/matched_coverage.csv`; v2 scenario details: `research/tables/benchmarks/matched_coverage_all_scenarios.csv`.

| DGP | Comparison | D1 default rate | Other gate default rate | D1−other | 95% CI |
|---|---|---:|---:|---:|---|
| DGP1 | D1 vs D2 | 0.0098 | 0.0191 | −0.0094 | [−0.0111, −0.0076] |
| DGP1 | D1 vs D3 | 0.0060 | 0.0172 | −0.0112 | [−0.0128, −0.0097] |
| DGP1 | D1 vs D4 | 0.0033 | 0.0175 | −0.0142 | [−0.0160, −0.0125] |
| DGP2 | D1 vs D4 | 0.0051 | 0.0253 | −0.0202 | [−0.0226, −0.0177] |

Across the v2 scenarios, the direction and size vary. For example, DGP1 D1 vs D4 is −0.0112 under `v2_eligible` (95% CI [−0.0128, −0.0097]); DGP1 D1 vs D2 is −0.0001 under that scenario (95% CI [−0.0002, 0.0000], p=0.2091). Source: `research/tables/benchmarks/matched_coverage_all_scenarios.csv`.

## Risk-model baselines

Phase 5 evaluated LR, RF, LightGBM, CatBoost, and XGBoost with default and tuned settings. WoE-LR was omitted because `optbinning`/`ropwr` caused a native interpreter crash on this Windows environment. The tuned synthetic Set C and Home Credit results are below. Source: `research/tables/benchmarks/risk_baselines_synthetic.csv`, `research/tables/benchmarks/risk_baselines_home_credit.csv`.

| Dataset / DGP | Model | ROC-AUC mean | 95% CI half-width | Logistic slope |
|---|---|---:|---:|---:|
| Synthetic DGP1, Set C | CatBoost | 0.9212 | 0.0021 | 0.9962 |
| Synthetic DGP1, Set C | LightGBM | 0.9210 | 0.0018 | 1.0010 |
| Synthetic DGP1, Set C | XGBoost | 0.9210 | 0.0026 | 0.9964 |
| Synthetic DGP2, Set C | CatBoost | 0.9151 | 0.0040 | 0.9834 |
| Synthetic DGP2, Set C | LightGBM | 0.9148 | 0.0041 | 0.9821 |
| Synthetic DGP2, Set C | XGBoost | 0.9137 | 0.0043 | 0.9831 |
| Home Credit | LightGBM tuned | 0.7620 | single split | 1.0261 |
| Home Credit | XGBoost tuned | 0.7609 | single split | 1.0218 |
| Home Credit | CatBoost tuned | 0.7588 | single split | 1.0197 |

Home Credit baseline rows use one split and have no seed confidence interval. The table is an additional baseline run, not a replacement for T1 v2. Source: `research/tables/benchmarks/risk_baselines_home_credit.csv`, `results/benchmarks/T1_v2/T1_results_v2.json`.

## Architecture and single-score comparisons

In Phase 6A, DGP1 approval rates at the 20% review budget ranged from 0.6401 to 0.6435 across the five models; review rates ranged from 0.1295 to 0.1302, and all five measured violation rates were 0. The values are conditional on the configured D4 policy and simulation setup. Source: `research/tables/benchmarks/architecture_model_agnostic.csv`.

In Phase 6B, on DGP1, D4 test coverage was 0.4128 and default among approved was 0.0169. A validation-matched plain fail-closed policy filter had test coverage 0.4161 and default rate 0.0056, for a measured difference of −0.0113 (95% CI [−0.0130, −0.0095]). On DGP2, the corresponding difference was −0.0165 (95% CI [−0.0182, −0.0147]). The fail-open filter had nonzero measured policy violations (0.0039 on DGP1 and 0.0043 on DGP2). Source: `research/tables/benchmarks/single_score_vs_pipeline.csv`.

## Policy baselines and rule scenarios

Phase 6C uses the stated true-policy-state definitions for violation and wrongful decline. DGP1 under legacy rules: P0 had a 0.0773 violation rate; P1 fail-closed had 0 violations and a 0.0980 wrongful-decline rate; P2 fail-open had a 0.0036 violation rate; P3 train-only imputation had a 0.0036 violation rate; P4 Kleene had 0 violations and a 0.2386 review rate. Source: `research/tables/benchmarks/policy_baselines.csv`.

Across Phase 2 scenarios, D4's measured violation rate was 0 for every DGP/scenario row. Under `v2_unknown`, DGP1 D4 approval was 0.4347 and review was 0.2668; under `v2_ineligible`, approval was 0.4347 and review was 0.1818; under `v2_eligible`, approval was 0.4944 and review was 0.2072. These are scenario results from unverified rule assumptions. Source: `research/tables/benchmarks/policy_v2_vs_legacy.csv`.

## Review allocation, equivalence, and costs

At the legacy 20% review budget, DGP1 R1 captured 0.4829 of pool defaulters (95% CI half-width 0.0523), compared with 0.2108 for random review (0.0297). On DGP2, the corresponding capture rates were 0.4504 (0.0413) and 0.2126 (0.0332). The perfect-oracle strategy is an upper bound, not an operational reviewer. V6 expected-loss ranking was skipped because no loan exposure field exists; V5 is explicitly a simplified SCROSS-style method. Source: `research/tables/benchmarks/review_baselines.csv`, `results/benchmarks/reports/PHASE_3_REPORT.md`, `results/benchmarks/reports/PHASE_7_REPORT.md`.

On the legacy DGP1 B=0.20 check, margin, split conformal, and Mondrian conformal each had Spearman correlation 1.0 with R1 priority and identical referred sets in all 10 seed comparisons. They are rank-equivalent to R1 for this pool and setting. Source: `research/tables/benchmarks/review_rank_equivalence.csv`.

The sensitivity output covers review-cost values 0.05, 0.10, and 0.20 and false-negative/false-positive ratios 1, 3, and 5, with both 20% and 30% review budgets. At DGP1 legacy, ratio 1 and common review cost 0.10, R1 cost per applicant was 0.26335 at 20% and 0.26677 at 30%; these cells do not establish a universal winner across the full grid. Source: `research/tables/benchmarks/cost_sensitivity.csv`.

## Statistical tests

The prespecified primary family uses Bonferroni adjustment for three contrasts within each DGP. At the configured family-wise rule, all six DGP-specific primary rows are significant. Examples: DGP1 A−C XGBoost AUC = −0.003587 (adjusted p=0.02439); DGP1 matched-coverage D1−D4 default rate = −0.014240 (adjusted p=6.18e−8); DGP1 R0−R3 bad-loan capture = +0.194974 (adjusted p=9.87e−6). Secondary baseline contrasts use Holm adjustment; the complete results, confidence intervals, and p-values are in the CSV. Source: `research/tables/benchmarks/statistical_tests.csv`, `results/benchmarks/reports/PHASE_8_REPORT.md`.

## DGP diagnostics and e-Shram comparison

The latent diagnostic's strongest listed discriminator was income-shock autocorrelation `rho`: AUC 0.7139 on DGP1 and 0.7143 on DGP2. Gig-related `sigma_m`, seasonal amplitude, platform tenure, and multi-platform status were near 0.50 AUC. These are synthetic-generator properties, not field estimates. Source: `research/tables/benchmarks/dgp_latent_diagnostic.csv`.

The T9 e-Shram approval-rate difference (registered minus unregistered) was +0.0053 on DGP1 (95% CI [−0.0082, 0.0188]) and +0.0050 on DGP2 (95% CI [−0.0034, 0.0135]); both intervals include zero. The DGP sets the registration effect independently of default, so this is a synthetic parity check, not a real-world fairness result. Source: `research/tables/T9_fairness_aggregated.csv`, `research/tables/benchmarks/policy_v2_vs_legacy.csv`.

## Limitations and deviations

- Default labels outside Home Credit are synthetic. High synthetic AUC and KS values describe the generator and should not be presented as consumer-credit benchmarks. Source: `research/tables/T2_ablation_agg.csv`, `research/tables/benchmarks/dgp_latent_diagnostic.csv`.
- Phase 7 uses a perfect oracle for review outcomes. Its results are an upper-bound simulation assumption. Source: `results/benchmarks/reports/PHASE_7_REPORT.md`.
- The only real dataset is Home Credit Default Risk, a Russian consumer-loan dataset; results do not establish performance for Indian gig workers. Source: `README.md`, `results/benchmarks/T1_v2/T1_results_v2.json`.
- No temporal validation was run. Source: experiment split manifests under `results/benchmarks/`.
- Policy rules are **UNVERIFIED** pending official-source review. The D4 zero-violation rates follow from applying a hard gate against the generated truth under the modeled scenarios; they do not prove legal compliance. Source: `configs/policy_rules/v2/`, `research/tables/benchmarks/policy_v2_vs_legacy.csv`.
- T6 trains on H=12 and evaluates forced-H feature views without refitting. Evidence score is constant across forced-H views. Source: `research/tables/T6_history_agg.csv`, `research/tables/benchmarks/T6_history_agg_v2_Hnum.csv`.
- WoE-LR was not run because of a native dependency crash; Phase 5/6 evaluated the other five model families. Source: `results/benchmarks/reports/PHASE_5_REPORT.md`, `results/benchmarks/reports/PHASE_6_REPORT.md`.
- Phase 7 V6 was skipped because the DGP has no loan-amount/exposure field. Source: `results/benchmarks/reports/PHASE_3_REPORT.md`, `results/benchmarks/reports/PHASE_7_REPORT.md`.
- Phase 11 (second real-data proxy experiment) was not run. Source: `results/benchmarks/reports/PHASE_10_REPORT.md`.
