# Phase 7 Report: Review-Allocation Baselines

**Date**: 2026-10-22
**Status**: COMPLETE

## (a) What ran
- Command: `python -u research/run_phase7_review_baselines.py`
- Strategies: V0_random, V1_R1_high_pd, V1_R2_low_evidence, V1_R3_hybrid, V2_margin, V3_split_conformal, V4_mondrian_conformal, V5_scross, V7_oracle
- V6 SKIPPED (no exposure column).
- Rule scenarios: ['legacy', 'v2_unknown', 'v2_ineligible', 'v2_eligible']
- Seeds 1–10 × DGP1/DGP2; budgets [0.05, 0.1, 0.15, 0.2, 0.25, 0.3]

## (b) Files written
- `research/tables/benchmarks/review_baselines.csv` (+ `_per_seed.csv`)
- `research/tables/benchmarks/review_rank_equivalence.csv`
- `research/tables/benchmarks/cost_sensitivity.csv`
- `results/benchmarks/review_baselines/manifest.json`

## (c) Key numbers (legacy, B=0.20)

| DGP | method | bad_loan_capture mean | ci95 | default_among_approved mean |
|---|---|---:|---:|---:|
| DGP1 | V0_random | 0.2108 | 0.0297 | 0.0153 |
| DGP1 | V1_R1_high_pd | 0.4829 | 0.0523 | 0.0101 |
| DGP1 | V1_R2_low_evidence | 0.2285 | 0.0289 | 0.0149 |
| DGP1 | V1_R3_hybrid | 0.4058 | 0.0389 | 0.0115 |
| DGP1 | V2_margin | 0.4829 | 0.0523 | 0.0101 |
| DGP1 | V3_split_conformal | 0.4829 | 0.0523 | 0.0101 |
| DGP1 | V4_mondrian_conformal | 0.4829 | 0.0523 | 0.0101 |
| DGP1 | V5_scross | 0.1090 | 0.0261 | 0.0172 |
| DGP1 | V7_oracle | 1.0000 | 0.0000 | 0.0000 |
| DGP2 | V0_random | 0.2126 | 0.0332 | 0.0208 |
| DGP2 | V1_R1_high_pd | 0.4504 | 0.0413 | 0.0146 |
| DGP2 | V1_R2_low_evidence | 0.2058 | 0.0341 | 0.0210 |
| DGP2 | V1_R3_hybrid | 0.3709 | 0.0404 | 0.0167 |
| DGP2 | V2_margin | 0.4504 | 0.0413 | 0.0146 |
| DGP2 | V3_split_conformal | 0.4504 | 0.0413 | 0.0146 |
| DGP2 | V4_mondrian_conformal | 0.4504 | 0.0413 | 0.0146 |
| DGP2 | V5_scross | 0.0998 | 0.0302 | 0.0237 |
| DGP2 | V7_oracle | 1.0000 | 0.0000 | 0.0000 |

## (d) Anomalies / deviations
- V6 not run (no exposure); documented, not invented.
- V5 is SCROSS-style (simplified).
- Prior Phase 7 draft script had non-matching strategy names and a hardcoded report; replaced.

## (e) Acceptance checks
| Check | Status |
|---|---|
| Outputs written | PASS |
| V6 skipped without inventing exposure | PASS |
| Pool definition matches review.py | PASS |
| Report numbers from CSVs only | PASS |

## (f) Open questions
- None blocking Phase 8.
