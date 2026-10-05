# Policy Rule Verification Record
## Task 10b — Status: INCOMPLETE (blocking for final policy-dependent results)

All policy rule content in `configs/policy_rules/` is currently marked
`UNVERIFIED — MUST BE REPLACED WITH VERIFIED OFFICIAL SOURCE`.

Policy-dependent results (T3, T4, T5, T10, explanation demos) remain PROVISIONAL
until this document is completed and `policy.rule_set_status` is set to `VERIFIED`
in `configs/experiment.yaml`.

---

## What needs to be done

For each rule in `configs/policy_rules/jan_samarth.yaml` and `pmmy.yaml`:

1. Find the current authoritative document (JanSamarth portal / PMMY official gazette)
2. Transcribe the exact eligibility criteria with:
   - Source document name and version
   - Effective date
   - Clause number and page
   - Exact text of the criterion
   - Name of person who verified it
   - Date of verification

---

## JanSamarth — verification status

| Rule | Criterion | Source | Verified? |
|---|---|---|---|
| Age eligibility | 18–60 years | UNVERIFIED | ❌ |
| Income cap | ≤ ₹10 lakh/year | UNVERIFIED | ❌ |
| Occupation / non-farm | Non-farm business | UNVERIFIED | ❌ |

**Source to check:** https://www.jansamarth.in/

---

## PMMY (Pradhan Mantri Mudra Yojana) — verification status

| Rule | Criterion | Source | Verified? |
|---|---|---|---|
| Age eligibility | 18–65 years | UNVERIFIED | ❌ |
| Income cap | ≤ ₹10 lakh/year | UNVERIFIED | ❌ |
| Enterprise type | Non-agri activities | UNVERIFIED | ❌ |

**Source to check:** https://www.mudra.org.in/

---

## Verification record (fill when done)

```
Policy: JanSamarth
Document: <fill>
Version / effective date: <fill>
Clause / page: <fill>
Criterion: <fill>
Verified by: <fill>
Verified on: <fill>
```

```
Policy: PMMY
Document: <fill>
Version / effective date: <fill>
Clause / page: <fill>
Criterion: <fill>
Verified by: <fill>
Verified on: <fill>
```

---

## After verification is complete

1. Replace all `<UNVERIFIED>` values in `configs/policy_rules/*.yaml` with verified values
2. Set `policy.rule_set_status: VERIFIED` in `configs/experiment.yaml`
3. Re-run G0 check 7 (policy independence)
4. Re-run T3, T4, T5, T10 experiments — results change from PROVISIONAL to final
