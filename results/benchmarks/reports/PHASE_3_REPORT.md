# Phase 3 Report: DGP Latents, Policy State Breakdown & Exposure Audit

**Date**: 2026-10-19  
**Status**: COMPLETE (100%)  
**Objective**: Audit the underlying DGP latent data generating mechanisms against default flag, establish policy state breakdowns (SATISFIED / UNSATISFIED / UNRESOLVED) across scenarios, and audit for loan exposure attributes required by downstream risk cost models.

---

## 1. DGP Latents & Feature Diagnostics

The synthetic data generation process specifies intrinsic structural parameters for applicants:
- `rho`: autocorrelation of income shocks (persistence)
- `g`: drift / income growth parameter
- `b`: baseline monthly income
- `sigma_m`: monthly income shock volatility
- `amp`: seasonal income variation amplitude
- `platform_tenure`: months active on platform
- `multi_platform`: boolean indicator of cross-platform activity

### Diagnostic Results (Test Split, Mean across 10 evaluation seeds, 95% Student's t CI):

#### DGP1:
| Variable | Spearman Correlation (±95% CI) | ROC-AUC (±95% CI) | Empirical Interpretation |
| :--- | :---: | :---: | :--- |
| `rho` | +0.2417 (±0.0106) | 0.7139 (±0.0097) | Strongest risk driver; persistent negative shocks compound into defaults |
| `g` | -0.1758 (±0.0086) | 0.3444 (±0.0077) | Protective drift; higher income trajectory reduces default (inverted AUC: 0.6556) |
| `b` | -0.0800 (±0.0082) | 0.4292 (±0.0074) | Protective baseline; higher baseline earnings buffer shocks (inverted AUC: 0.5708) |
| `sigma_m` | +0.0126 (±0.0087) | 0.5111 (±0.0077) | Weak standalone marginal discrimination |
| `amp` | +0.0075 (±0.0107) | 0.5066 (±0.0095) | Weak standalone marginal discrimination |
| `platform_tenure` | -0.0016 (±0.0070) | 0.4986 (±0.0062) | Weak standalone linear correlation |
| `multi_platform` | -0.0051 (±0.0097) | 0.4962 (±0.0073) | Weak standalone linear correlation |

#### DGP2 (Non-linear interactions):
| Variable | Spearman Correlation (±95% CI) | ROC-AUC (±95% CI) | Empirical Interpretation |
| :--- | :---: | :---: | :--- |
| `rho` | +0.2570 (±0.0090) | 0.7143 (±0.0075) | Strongest risk driver across both DGPs |
| `g` | -0.1776 (±0.0061) | 0.3519 (±0.0049) | Protective drift (inverted AUC: 0.6481) |
| `b` | -0.0658 (±0.0090) | 0.4451 (±0.0075) | Protective baseline (inverted AUC: 0.5549) |
| `sigma_m` | +0.0123 (±0.0080) | 0.5103 (±0.0066) | Weak standalone marginal discrimination |
| `amp` | +0.0035 (±0.0073) | 0.5029 (±0.0061) | Weak standalone marginal discrimination |
| `platform_tenure` | -0.0028 (±0.0063) | 0.4976 (±0.0053) | Weak standalone linear correlation |
| `multi_platform` | -0.0042 (±0.0127) | 0.4970 (±0.0090) | Weak standalone linear correlation |

---

## 2. Policy-State Breakdown (Table T3 Extension)

Evaluated across $N=5,000$ test applicants $\times$ 10 seeds:

| DGP | Scenario | SATISFIED Rate (95% CI) | UNSATISFIED Rate (95% CI) | UNRESOLVED Rate (95% CI) | State Decomposition |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **DGP1** | `legacy` | 0.8307 (±0.0053) | 0.0759 (±0.0025) | 0.0934 (±0.0042) | Missing age / unmasked income cap failures |
| **DGP1** | `v2_unknown` | 0.8775 (±0.0037) | 0.0000 (±0.0000) | 0.1225 (±0.0037) | Agricultural labour routed to human review |
| **DGP1** | `v2_ineligible` | 0.8775 (±0.0037) | 0.1225 (±0.0037) | 0.0000 (±0.0000) | Agricultural labour declined at policy gate |
| **DGP1** | `v2_eligible` | 1.0000 (±0.0000) | 0.0000 (±0.0000) | 0.0000 (±0.0000) | All occupations eligible under PMMY |
| **DGP2** | `legacy` | 0.8303 (±0.0043) | 0.0753 (±0.0031) | 0.0944 (±0.0032) | Consistent with DGP1 |
| **DGP2** | `v2_unknown` | 0.8766 (±0.0029) | 0.0000 (±0.0000) | 0.1234 (±0.0029) | Agricultural labour routed to human review |
| **DGP2** | `v2_ineligible` | 0.8766 (±0.0029) | 0.1234 (±0.0029) | 0.0000 (±0.0000) | Agricultural labour declined at policy gate |
| **DGP2** | `v2_eligible` | 1.0000 (±0.0000) | 0.0000 (±0.0000) | 0.0000 (±0.0000) | All occupations eligible under PMMY |

---

## 3. Exposure Column Audit

- **Audit Search**: Verified all synthetic data parquet tables (`applicants`, `features_full`, `features_visible`, `latent_params`, `monthly`, `policy_attributes`, `policy_truth`).
- **Empirical Finding**: **No loan exposure, requested amount, or exposure-at-default column exists in the synthetic data generator.**
- **Downstream Consequence**: In Phase 7 (Review-Allocation Baselines), Baseline V6 (Expected Loss allocation) requires individual exposure $E_i \cdot PD_i \cdot LGD_i$. Because exposure does not vary across applicants in the DGP, unit exposure ($E_i=1, LGD=1$) will be reported for V6 (making it rank-equivalent to risk-score sorting), and the absence of exposure variation will be explicitly noted in `research/tables/benchmarks/review_baselines.csv` and the technical paper documentation.
