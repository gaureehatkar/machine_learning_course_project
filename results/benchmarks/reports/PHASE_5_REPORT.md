# Phase 5 Report: Risk-Model Baselines with Equal Tuning

**Date**: 2026-10-22
**Final invocation execution time**: 671.3s (tuning results resumed from the saved checkpoint)

## (a) What ran
- Command: `python -u research/run_phase5_risk_baselines.py`
- Equal tuning: N=30 random-search draws, 5-fold CV on train only.
- Synthetic tuning is separate for each DGP and feature set (A/C), using seed 0 training data.
- Home Credit uses all 184,506 training rows; no tuning subsample.
- Calibration: Platt on validation; logistic slope via `calibration_slope_intercept(y, p)`.
- Fix applied this run: argument order was previously swapped (p, y), producing slopes ≈ 0.12.

## (b) Files written
- `research/tables/benchmarks/risk_baselines_synthetic.csv` (+ `_raw.csv`)
- `research/tables/benchmarks/risk_baselines_home_credit.csv`
- `results/benchmarks/tuned_params.json`
- `results/benchmarks/tuned_params_manifest.json`

## (c) Key numbers — synthetic tuned (from CSV)

| DGP | feature_set | model | ROC-AUC mean | ci95 | logistic slope mean | ECE mean |
|---|---|---|---:|---:|---:|---:|
| DGP1 | A | catboost | 0.9230 | 0.0024 | 1.0020 | 0.0084 |
| DGP1 | A | lgbm | 0.9225 | 0.0019 | 1.0031 | 0.0088 |
| DGP1 | A | xgb | 0.9217 | 0.0022 | 0.9995 | 0.0081 |
| DGP1 | A | rf | 0.9212 | 0.0026 | 1.0053 | 0.0085 |
| DGP1 | A | lr | 0.9124 | 0.0034 | 1.0000 | 0.0097 |
| DGP1 | C | catboost | 0.9212 | 0.0021 | 0.9962 | 0.0099 |
| DGP1 | C | lgbm | 0.9210 | 0.0018 | 1.0010 | 0.0097 |
| DGP1 | C | xgb | 0.9210 | 0.0026 | 0.9964 | 0.0092 |
| DGP1 | C | rf | 0.9181 | 0.0023 | 0.9996 | 0.0091 |
| DGP1 | C | lr | 0.9123 | 0.0032 | 0.9990 | 0.0089 |
| DGP2 | A | catboost | 0.9170 | 0.0035 | 0.9842 | 0.0096 |
| DGP2 | A | lgbm | 0.9160 | 0.0036 | 0.9778 | 0.0101 |
| DGP2 | A | xgb | 0.9152 | 0.0038 | 0.9790 | 0.0092 |
| DGP2 | A | rf | 0.9147 | 0.0034 | 0.9878 | 0.0091 |
| DGP2 | A | lr | 0.9069 | 0.0039 | 0.9808 | 0.0094 |
| DGP2 | C | catboost | 0.9151 | 0.0040 | 0.9834 | 0.0119 |
| DGP2 | C | lgbm | 0.9148 | 0.0041 | 0.9821 | 0.0100 |
| DGP2 | C | xgb | 0.9137 | 0.0043 | 0.9831 | 0.0091 |
| DGP2 | C | rf | 0.9103 | 0.0037 | 0.9905 | 0.0093 |
| DGP2 | C | lr | 0.9068 | 0.0041 | 0.9779 | 0.0090 |

## (c) Key numbers — Home Credit

| model | tuning | ROC-AUC | logistic slope | ECE |
|---|---|---:|---:|---:|
| lgbm | tuned | 0.7620 | 1.0261 | 0.0020 |
| xgb | tuned | 0.7609 | 1.0218 | 0.0023 |
| catboost | tuned | 0.7588 | 1.0197 | 0.0026 |
| lgbm | default | 0.7586 | 1.0254 | 0.0025 |
| xgb | default | 0.7568 | 1.0224 | 0.0025 |
| catboost | default | 0.7528 | 1.0209 | 0.0031 |
| rf | tuned | 0.7362 | 1.0347 | 0.0046 |
| rf | default | 0.7358 | 1.0336 | 0.0035 |
| lr | default | 0.6769 | 1.0428 | 0.0047 |
| lr | tuned | 0.6716 | 1.0516 | 0.0048 |

## (d) Anomalies / deviations
- Prior report contained hardcoded numbers inconsistent with CSV; this report is CSV-driven.
- WoE-LR was excluded because importing optbinning/ropwr crashes Python on this Windows environment; LR, RF, LightGBM, CatBoost, and XGBoost ran.
- Logistic slopes outside [0.8, 1.2]: NONE

## (e) Acceptance checks
| Logistic slope in [0.8, 1.2] | PASS |
| Outputs written | PASS |
| Report from measured numbers | PASS |

## (f) Open questions
- None.
