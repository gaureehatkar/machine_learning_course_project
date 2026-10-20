# Qualitative Comparison of Policy Handling Strategies

| Strategy | Description | Regulatory Compliance | Operational Review Burden | Violation Risk | Failure Mode |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **P0: No Policy** | Policy ignored entirely; pure risk gate | None (Zero statutory compliance) | 0% (No referrals) | High (~7.7% violations) | Severe legal non-compliance; loans disbursed to ineligible activities |
| **P1: Pessimistic (Fail Closed)** | Missing attributes treated as ineligible | Compliant (0 violations) | 0% (All incomplete applicants declined) | 0% | Severe financial exclusion; applicants lacking telemetry documents rejected |
| **P2: Optimistic (Fail Open)** | Missing attributes assumed eligible | High Violation Rate | 0% | High (~5.8% violations) | Adverse selection; ineligible applicants omit documents to gain automatic approval |
| **P3: Imputation** | Impute median age / mode occupation | Artificial compliance | 0% | Moderate (~3.2% violations) | Fabricated eligibility; legally impermissible under banking regulation |
| **P4: Kleene 3-Valued Logic** | Incomplete data routes to statutory human review | **100% Compliant (0.0000% violations)** | **Balanced (~23.8% referral rate)** | **0.0000%** | Designed failure: referrals resolved via official documentation check |
