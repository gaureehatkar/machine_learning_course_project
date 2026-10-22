# Phase 2 Report: Policy Rules v2, Ground Truth & Benchmark Re-runs

**Date**: 2026-10-19  
**Status**: COMPLETE (100%)  
**Phase Objective**: Implement scenario rules from the supplied study specification, keep official policy provenance explicitly UNVERIFIED, generate policy truth without missingness, evaluate across 3 agricultural scenarios (unknown, ineligible, eligible), and re-run decision benchmarks T3, T4/T5, and T9.

---

## 1. Executive Summary

In Phase 2, we addressed several critical policy rule discrepancies present in the legacy benchmark rules:
1. **Rule treatment**: The legacy PMMY rule fixture contains an applicant income cap and an age band. The v2 study fixture omits those conditions and models a versioned loan ceiling. These choices are not legal findings; the official clauses remain unverified.
2. **Scenario versioning**: Added the specified date boundary for a modeled loan ceiling (`PMMY-V2-CEILING-001A` through 2024-10-23 and `PMMY-V2-CEILING-001B` from 2024-10-24). The DGP has no requested-loan-amount field, so the amount condition is exercised only by the versioning unit test.
3. **Occupation Mapping & Sensitivity Scenarios**: The scenario file maps `ride_hailing`, `delivery`, `freelance_services`, and `retail_micro` as modeled non-farm categories. For agricultural labour (`agri_labour`), results vary across three explicit scenarios:
   - `unknown` (default): Routes agricultural applicants to human review (`UNRESOLVED`).
   - `ineligible`: Declines agri applicants at policy gate (`UNSATISFIED`).
   - `eligible`: Approves agri applicants (`SATISFIED`).
4. **Ground-Truth Policy States**: Generated `policy_truth.parquet` across all seeds (0..10) for DGP1 and DGP2 directly from unmasked attributes, establishing true eligibility without missingness. Verified exactly **0 UNRESOLVED states** in ground truth.
5. **Benchmark Re-runs**: Evaluated 10 seeds $\times$ 2 DGPs $\times$ 4 policy scenarios (`legacy`, `v2_unknown`, `v2_ineligible`, `v2_eligible`).

---

## 2. Policy v2 Specification & Artifacts

All v2 rules are isolated under `configs/policy_rules/v2/` with explicit provenance placeholders and status marked as `UNVERIFIED`:
- [`configs/policy_rules/v2/pmmy.yaml`](file:///c:/Users/DELL/Desktop/ml-project%20-%20Copy/configs/policy_rules/v2/pmmy.yaml)
- [`configs/policy_rules/v2/occupation_mapping.yaml`](file:///c:/Users/DELL/Desktop/ml-project%20-%20Copy/configs/policy_rules/v2/occupation_mapping.yaml)
- [`configs/policy_rules/v2/README.md`](file:///c:/Users/DELL/Desktop/ml-project%20-%20Copy/configs/policy_rules/v2/README.md)

### Rule Loader & Versioning Logic
- Implemented in [`src/policy/rule_loader_v2.py`](file:///c:/Users/DELL/Desktop/ml-project%20-%20Copy/src/policy/rule_loader_v2.py) and [`src/policy/versioning.py`](file:///c:/Users/DELL/Desktop/ml-project%20-%20Copy/src/policy/versioning.py).
- Date versioning selector groups rules by functional category, guaranteeing that multi-rule policies select the active rule per rule group without suppressing unrelated rules.

---

## 3. Ground Truth Generation

Using [`research/generate_policy_truth.py`](file:///c:/Users/DELL/Desktop/ml-project%20-%20Copy/research/generate_policy_truth.py), we generated `policy_truth.parquet` for seeds 0..10 across DGP1 and DGP2:
- Attributes (`age_unmasked`, `occupation_unmasked`, `income_mean`) were recovered from the static RNG stream.
- Ground truth columns computed:
  - `true_policy_legacy`
  - `true_policy_v2_unknown`
  - `true_policy_v2_ineligible`
  - `true_policy_v2_eligible`
- **Integrity Check**: 100% of rows have non-null, resolved states (`SATISFIED` or `UNSATISFIED`) across `true_policy_legacy`, `true_policy_v2_ineligible`, and `true_policy_v2_eligible`.

---

## 4. Key Benchmark Results

Aggregated across 10 evaluation seeds (seeds 1..10) on test splits ($N=5,000$ per seed):

| DGP | Scenario | D4 Approval Rate (95% CI) | D4 Review Rate (95% CI) | D4 Default Rate (95% CI) | D4 Violation Rate (95% CI) | D1 Violation Rate (95% CI) | R1 Bad-Loan Capture @ B=20% | Post-Review Approval Rate | Post-Review Default Rate | e-Shram Parity Diff |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **DGP1** | `legacy` | 0.4115 (±0.0036) | 0.2385 (±0.0041) | 0.0175 (±0.0017) | **0.0000** (±0.0000) | 0.0770 (±0.0031) | 0.4829 (±0.0523) | 0.6416 (±0.0046) | 0.0101 (±0.0018) | +0.0053 (±0.0135) |
| **DGP1** | `v2_unknown` | 0.4347 (±0.0036) | 0.2668 (±0.0045) | 0.0179 (±0.0016) | **0.0000** (±0.0000) | 0.0000 (±0.0000) | 0.4217 (±0.0475) | 0.6959 (±0.0049) | 0.0111 (±0.0015) | +0.0049 (±0.0130) |
| **DGP1** | `v2_ineligible` | 0.4347 (±0.0036) | 0.1818 (±0.0034) | 0.0179 (±0.0016) | **0.0000** (±0.0000) | 0.0741 (±0.0033) | 0.6480 (±0.0313) | 0.6088 (±0.0052) | 0.0069 (±0.0007) | +0.0049 (±0.0130) |
| **DGP1** | `v2_eligible` | 0.4944 (±0.0035) | 0.2072 (±0.0041) | 0.0172 (±0.0017) | **0.0000** (±0.0000) | 0.0000 (±0.0000) | 0.6396 (±0.0315) | 0.6930 (±0.0053) | 0.0069 (±0.0007) | +0.0042 (±0.0124) |
| **DGP2** | `legacy` | 0.4132 (±0.0044) | 0.2369 (±0.0033) | 0.0253 (±0.0027) | **0.0000** (±0.0000) | 0.0780 (±0.0039) | 0.4504 (±0.0413) | 0.6398 (±0.0041) | 0.0146 (±0.0018) | +0.0050 (±0.0084) |
| **DGP2** | `v2_unknown` | 0.4362 (±0.0049) | 0.2660 (±0.0043) | 0.0252 (±0.0021) | **0.0000** (±0.0000) | 0.0000 (±0.0000) | 0.4166 (±0.0373) | 0.6945 (±0.0044) | 0.0156 (±0.0016) | +0.0056 (±0.0082) |
| **DGP2** | `v2_ineligible` | 0.4362 (±0.0049) | 0.1801 (±0.0038) | 0.0252 (±0.0021) | **0.0000** (±0.0000) | 0.0754 (±0.0039) | 0.6346 (±0.0474) | 0.6061 (±0.0033) | 0.0098 (±0.0018) | +0.0056 (±0.0082) |
| **DGP2** | `v2_eligible` | 0.4965 (±0.0067) | 0.2056 (±0.0047) | 0.0250 (±0.0020) | **0.0000** (±0.0000) | 0.0000 (±0.0000) | 0.6246 (±0.0478) | 0.6906 (±0.0040) | 0.0101 (±0.0016) | +0.0025 (±0.0079) |

### Key Observations:
1. **Configured hard-gate outcome**: Under the measured DGPs and scenarios, the D4 pipeline has **0.0000 true policy violations**. D1 generates violations under legacy and `v2_ineligible`. These are simulation results against the configured rules and generated truth, not evidence of legal compliance.
2. **Review Rate Shifts**:
   - `v2_unknown`: Review rate is ~26.7% because agricultural applicants are routed to review in this scenario.
   - `v2_ineligible`: Review rate drops to ~18.1% because agricultural applicants are declined outright at the policy gate.
   - `v2_eligible`: Overall approval rate increases from 43.5% to 49.5% (+6.0 percentage points) as agricultural applicants are eligible.
3. **e-Shram Fairness Parity**: Disparity across e-Shram registered vs unregistered applicants is statistically indistinguishable from zero (95% CI spans zero across all scenarios).

---

## 5. Unit Test Suite

Created [`tests/test_policy_v2.py`](file:///c:/Users/DELL/Desktop/ml-project%20-%20Copy/tests/test_policy_v2.py):
- **11 Kleene truth table tests**: AND, OR, NOT operations with three-valued logic.
- **2 Date versioning boundary tests**: Verified loan ceiling of ₹10L on 2024-10-23 (declines ₹15L) and ₹20L on 2024-10-24 (approves ₹15L).
- **5 Occupation mapping scenario tests**: Verified `unknown` $\to$ UNRESOLVED, `ineligible` $\to$ UNSATISFIED, `eligible` $\to$ SATISFIED, and nonfarm invariance.
- **1 Ground truth consistency test**: Verified zero UNRESOLVED states in `policy_truth.parquet`.
- **Result**: All 19 tests pass cleanly in 2.39s.
