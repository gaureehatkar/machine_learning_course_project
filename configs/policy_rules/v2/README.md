# Policy Rules v2

This folder contains corrected policy rule files for SynthGigCredit-IN.

## Status

**ALL RULES IN THIS FOLDER ARE UNVERIFIED.**
Every rule must be verified against official Government of India texts
(Gazette notifications, PIB press releases, MUDRA official website, RBI circulars)
before use in production or in any public claim.

## Why a new folder?

The legacy rules in `configs/policy_rules/` contain:
- An income cap on applicants (not supported by any PMMY clause found)
- A JanSamarth rule file (JanSamarth is a portal, not a scheme)
- Age bands whose source clauses have not been located

## What is here

- `pmmy.yaml` — PMMY (Pradhan Mantri Mudra Yojana) rules
- `occupation_mapping.yaml` — explicit occupation → policy attribute mapping

## What is NOT here

- No JanSamarth rule file. JanSamarth links ~13 schemes (PMMY, PMEGP, etc.).
  Add per-scheme files (e.g., pmegp.yaml) only once official eligibility is supplied.
- No age band for PMMY (no official clause found).
- No applicant income cap for PMMY (₹10L / ₹20L is a **loan ceiling**, not income cap).

## Sources consulted (not verified against official texts)

- MUDRA press release on Tarun Plus (loan ceiling raised to ₹20L, Oct 2024)
- PIB budget announcement 2024-25
- Secondary summaries — NOT official clauses

## To mark a rule as verified

Set `rule_set_status: VERIFIED` in the YAML **only** after a human reads
the actual official clause and confirms it matches the condition exactly.
