#!/usr/bin/env python
"""Write the Phase 10 report for documentation and reproducibility artifacts."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.parent
REPORT = ROOT / "results/benchmarks/reports/PHASE_10_REPORT.md"
REQUIRED = [
    "research/BENCHMARK_RESULTS.md",
    "research/CLAIMS_AUDIT.md",
    "FINAL_PROJECT_TECHNICAL_DOCUMENTATION_v2.md",
    "EXPERIMENT_RESULTS_v2.md",
    "requirements.lock",
    "scripts/check_forbidden_claims.py",
]


def main() -> None:
    missing = [path for path in REQUIRED if not (ROOT / path).is_file()]
    contents = {
        path: (ROOT / path).read_text(encoding="utf-8", errors="replace")
        for path in REQUIRED
        if (ROOT / path).is_file()
    }
    policy_docs = [
        "FINAL_PROJECT_TECHNICAL_DOCUMENTATION_v2.md",
        "research/BENCHMARK_RESULTS.md",
    ]
    policy_status_ok = all(
        "UNVERIFIED" in contents.get(path, "") for path in policy_docs
    )
    passed = not missing and policy_status_ok

    report = f"""# Phase 10 Report: Documentation and reproducibility

## (a) What ran
- Documentation/reproducibility artifacts were checked after the benchmark outputs, figure/table generation, and claim scan.
- `make reproduce` is the single configured entry point for Phases 1–10.

## (b) Files checked
{chr(10).join(f"- `{path}`" for path in REQUIRED)}
- Superseded banners: `FINAL_PROJECT_TECHNICAL_DOCUMENTATION.md`, `FINAL_PROJECT_ARCHITECTURE.md`, and `research/RESEARCH_IMPLEMENTATION_STATUS.md`.

## (c) Key numbers
No new numeric findings were computed in this documentation phase. See `research/BENCHMARK_RESULTS.md` and its cited source CSVs.

## (d) Anomalies and deviations
- Policy provenance remains UNVERIFIED pending official-source review.
- Phase 11 was not run.

## (e) Acceptance checks
| Check | Status |
|---|---|
| Required documentation/reproducibility files exist | {"PASS" if not missing else "FAIL: " + ", ".join(missing)} |
| Current benchmark summary keeps policy rules UNVERIFIED | {"PASS" if policy_status_ok else "FAIL"} |
| Claim scan and full tests | PASS if preceding Makefile commands exit successfully |

## (f) Open questions
- Human verification of official policy clauses is still required before any rule set can be marked VERIFIED.
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")
    if not passed:
        raise RuntimeError("Phase 10 acceptance checks failed; see PHASE_10_REPORT.md")


if __name__ == "__main__":
    main()
