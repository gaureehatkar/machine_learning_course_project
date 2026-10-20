# Phase 4 Report: Matched-Coverage Comparison & Coverage-Risk Curve

**Date**: 2026-10-19  
**Status**: COMPLETE (100%)  
**Objective**: Evaluate gate mechanisms under matched coverage conditions on the test set by tuning unconstrained gate D1's risk threshold $\tau$ on validation to match the realized coverage of multi-stage gates D2, D3, and D4. Evaluate under legacy and v2 rule scenarios, and extract full empirical D1 coverage-risk curves for Figure F3.

---

## 1. Executive Summary & Critical Nuance

In standard unconstrained evaluations, Gate D4 exhibits lower approval rates than Gate D1 because D4 enforces policy compliance (e.g. non-farm criteria, evidence thresholds). 

When Gate D1's threshold $\tau$ is explicitly tuned on the validation set to match Gate D4's coverage:
- **D1 realizes a lower default rate among approved than D4** (e.g., in DGP1: D1 DR = 0.0033 vs D4 DR = 0.0175, $p < 0.0001$; in DGP2: D1 DR = 0.0051 vs D4 DR = 0.0253, $p < 0.0001$).
- **Neutral Interpretation**: Gate D1 selects exclusively on predicted probability of default ($PD_i < \tau$). To achieve ~41% coverage, D1 admits only the lowest ~41% of risk scores. In contrast, Gate D4 must satisfy statutory compliance rules (PMMY / Jan Samarth), meaning high-scoring, low-risk applicants who fail policy criteria are declined or reviewed, while slightly higher risk applicants who meet statutory rules are approved.
- **True Policy Compliance**: Gate D1 achieves lower default risk at the cost of **severe policy violations** (~7.7% violation rate). Gate D4 guarantees **0.0000% policy violations**, demonstrating that the multi-stage architecture trades marginal portfolio credit risk for legal and regulatory compliance.

---

## 2. Matched-Coverage Contrast Results (Table T4 Benchmark)

Paired Student's t-test ($N=10$ seeds, $df=9$) comparing D1 (tuned to match Dx coverage) against Dx:

### Legacy Policy Rules:
| DGP | Comparison | Matched Coverage (Test) | D1 Default Rate | Dx Default Rate | Difference (D1 - Dx) | 95% CI of Difference | t-stat | p-value | Significant (Bonferroni $\alpha=0.05/3$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **DGP1** | D1 vs D2 (Risk + Evidence) | ~0.505 | 0.0098 | 0.0191 | -0.0094 | [-0.0111, -0.0076] | -11.82 | <0.0001 | Yes |
| **DGP1** | D1 vs D3 (Risk + Policy) | ~0.443 | 0.0060 | 0.0172 | -0.0112 | [-0.0128, -0.0097] | -16.17 | <0.0001 | Yes |
| **DGP1** | D1 vs D4 (Full Gate) | ~0.412 | 0.0033 | 0.0175 | -0.0142 | [-0.0160, -0.0125] | -18.05 | <0.0001 | Yes |
| **DGP2** | D1 vs D2 | ~0.506 | 0.0141 | 0.0262 | -0.0121 | [-0.0142, -0.0099] | -12.53 | <0.0001 | Yes |
| **DGP2** | D1 vs D3 | ~0.444 | 0.0093 | 0.0250 | -0.0157 | [-0.0174, -0.0140] | -21.34 | <0.0001 | Yes |
| **DGP2** | D1 vs D4 | ~0.413 | 0.0051 | 0.0253 | -0.0202 | [-0.0226, -0.0177] | -18.65 | <0.0001 | Yes |

### Policy v2 Scenarios (D1 vs D4 at Matched Coverage):
| DGP | Scenario | Matched Coverage (Test) | D1 Default Rate | D4 Default Rate | Difference (D1 - D4) | 95% CI of Difference | p-value |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **DGP1** | `v2_unknown` | ~0.435 | 0.0053 | 0.0179 | -0.0126 | [-0.0145, -0.0108] | <0.0001 |
| **DGP1** | `v2_ineligible` | ~0.435 | 0.0053 | 0.0179 | -0.0126 | [-0.0145, -0.0108] | <0.0001 |
| **DGP1** | `v2_eligible` | ~0.494 | 0.0090 | 0.0172 | -0.0082 | [-0.0098, -0.0066] | <0.0001 |
| **DGP2** | `v2_unknown` | ~0.436 | 0.0083 | 0.0252 | -0.0169 | [-0.0192, -0.0146] | <0.0001 |
| **DGP2** | `v2_ineligible` | ~0.436 | 0.0083 | 0.0252 | -0.0169 | [-0.0192, -0.0146] | <0.0001 |
| **DGP2** | `v2_eligible` | ~0.496 | 0.0131 | 0.0250 | -0.0119 | [-0.0141, -0.0097] | <0.0001 |

---

## 3. Empirical D1 Coverage-Risk Curve (For Figure F3)

- Evaluated across 100 $\tau$ points $\in [0.005, 0.995]$.
- Shows monotonic increase in default rate among approved as coverage expands:
  - At 20% coverage: DGP1 DR $\approx 0.0004$, DGP2 DR $\approx 0.0008$.
  - At 40% coverage: DGP1 DR $\approx 0.0029$, DGP2 DR $\approx 0.0045$.
  - At 60% coverage: DGP1 DR $\approx 0.0182$, DGP2 DR $\approx 0.0258$.
  - At 80% coverage: DGP1 DR $\approx 0.0461$, DGP2 DR $\approx 0.0610$.
  - At 100% coverage: DGP1 DR $\approx 0.0825$ (base prevalence), DGP2 DR $\approx 0.0984$.
- Saved table: [`research/tables/benchmarks/d1_coverage_curve.csv`](file:///c:/Users/DELL/Desktop/ml-project%20-%20Copy/research/tables/benchmarks/d1_coverage_curve.csv).
