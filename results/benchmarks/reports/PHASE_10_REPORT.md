# Phase 10 Report: Documentation and reproducibility

**Date:** 2026-10-22 18:59 UTC

## (a) What ran
- `make reproduce` is the configured Phase 1–10 entry point. This Phase 10 report records the final documentation and artifact audit after Phase 9.
- Claim scanner: `python -u scripts/check_forbidden_claims.py` (rerun by this report writer).
- Full suite: `pytest -q --junitxml=results/benchmarks/reports/phase10_junit.xml`.

## (b) Files and artifacts checked
- `README.md`
- `Makefile`
- `requirements.lock`
- `research/BENCHMARK_RESULTS.md`
- `research/CLAIMS_AUDIT.md`
- `FINAL_PROJECT_TECHNICAL_DOCUMENTATION_v2.md`
- `EXPERIMENT_RESULTS_v2.md`
- `app/api/README.md`
- `scripts/check_forbidden_claims.py`
- Superseded banners in `FINAL_PROJECT_TECHNICAL_DOCUMENTATION.md`, `FINAL_PROJECT_ARCHITECTURE.md`, and `research/RESEARCH_IMPLEMENTATION_STATUS.md`.
- Phase outputs: tuned parameters, statistical tests, risk/policy/review baselines, F1–F11 PNG/PDF, and Markdown/LaTeX paper tables.
- JUnit details: `results/benchmarks/reports/phase10_junit.xml`.

## (c) Key numbers
- Figures present: 22/22.
- Generated paper tables present: 17 Markdown and 16 LaTeX files.
- Test result: 181 passed, 0 failed, 0 errors, 0 skipped (181 collected).
- Claim scanner: PASS.

## (d) Anomalies and deviations
- WoE-LR was excluded after a native `optbinning`/`ropwr` crash on this Windows environment; the other five risk model families ran.
- V6 expected-loss review ranking was skipped because no exposure field exists in the synthetic data.
- Phase 11 was not run.
- Policy provenance remains UNVERIFIED pending review against official text.

## (e) Acceptance checks
| Check | Status |
|---|---|
| Required docs and benchmark artifacts exist | PASS |
| Superseded banners match the requested text | PASS |
| Current docs keep policy rules UNVERIFIED | PASS |
| F1–F11 PNG and PDF files exist | PASS |
| Markdown and LaTeX paper tables exist | PASS |
| Forbidden-claim scan | PASS |
| Full test suite | PASS |

## (f) Open questions
- Official policy clauses need human verification before any rule set can be marked VERIFIED.

### Claim scan output
```text
PASSED: no forbidden phrases in paper/ and v2 docs.
```
