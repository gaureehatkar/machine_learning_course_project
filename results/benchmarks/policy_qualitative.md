# Policy baseline implementation notes

- P0 ignores policy state; P1 treats UNRESOLVED as UNSATISFIED; P2 treats it as SATISFIED.
- P3 fills missing age, occupation, and non-farm flag using train-split median/mode only.
- P4 uses the Kleene policy engine; UNRESOLVED is routed to REVIEW by D4.
- Decision reason codes are `PD_HIGH`, `POLICY_INELIGIBLE`, `POLICY_UNRESOLVED`, and `EVIDENCE_INSUFFICIENT` (see `src/decisions/gate.py`).
- Rule provenance keys are `document`, `clause`, `page_or_url`, `retrieved_on`, and `verified_by`; v2 values remain placeholders and the rule set is UNVERIFIED.
- The PMMY amount-version boundary is exercised in `tests/test_policy_v2.py` for 2024-10-23 and 2024-10-24. The synthetic DGP has no requested-loan-amount column, so this condition is excluded from experimental decisions.
- The policy engine combines rule results using Kleene logic; conflicting conditions are not rewritten as a verified eligibility decision.
- The review oracle declines referred true-ineligible applicants and referred defaulters; other referred applicants are approved.
