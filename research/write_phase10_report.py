#!/usr/bin/env python
"""Write a Phase 10 report from the current docs, artifacts, claim scan, and JUnit file."""
from __future__ import annotations

import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
REPORT = ROOT / "results/benchmarks/reports/PHASE_10_REPORT.md"
JUNIT = REPORT.parent / "phase10_junit.xml"
REQUIRED = [
    "README.md",
    "Makefile",
    "requirements.lock",
    "research/BENCHMARK_RESULTS.md",
    "research/CLAIMS_AUDIT.md",
    "FINAL_PROJECT_TECHNICAL_DOCUMENTATION_v2.md",
    "EXPERIMENT_RESULTS_v2.md",
    "app/api/README.md",
    "scripts/check_forbidden_claims.py",
]
SUPERSEDED = [
    "FINAL_PROJECT_TECHNICAL_DOCUMENTATION.md",
    "FINAL_PROJECT_ARCHITECTURE.md",
    "research/RESEARCH_IMPLEMENTATION_STATUS.md",
]
BANNER = (
    "SUPERSEDED — see research/BENCHMARK_RESULTS.md and *_v2.md; "
    "predates the calibration-slope and policy-rule corrections"
)


def check_tests() -> tuple[dict[str, int] | None, str]:
    if not JUNIT.is_file():
        return None, "NOT RUN: Phase 10 JUnit report is missing"
    root = ET.parse(JUNIT).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    counts = {key: 0 for key in ("tests", "failures", "errors", "skipped")}
    for suite in suites:
        for key in counts:
            counts[key] += int(suite.attrib.get(key, "0"))
    counts["passed"] = counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"]
    status = "PASS" if counts["failures"] == counts["errors"] == 0 else "FAIL"
    return counts, status


def run_claim_scan() -> tuple[str, str]:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_forbidden_claims.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (proc.stdout + proc.stderr).strip() or "(no scanner output)"
    status = "PASS" if proc.returncode == 0 else f"FAIL (exit {proc.returncode})"
    return status, output


def main() -> int:
    missing = [path for path in REQUIRED if not (ROOT / path).is_file()]
    missing += [path for path in SUPERSEDED if not (ROOT / path).is_file()]
    missing += [
        path for path in (
            "results/benchmarks/tuned_params.json",
            "research/tables/benchmarks/statistical_tests.csv",
            "research/tables/benchmarks/risk_baselines_synthetic.csv",
            "research/tables/benchmarks/policy_baselines.csv",
            "research/tables/benchmarks/review_baselines.csv",
        ) if not (ROOT / path).is_file()
    ]
    banner_ok = all(
        (ROOT / path).read_text(encoding="utf-8", errors="replace").splitlines()[0] == BANNER
        for path in SUPERSEDED
        if (ROOT / path).is_file()
    )
    summary = (ROOT / "research/BENCHMARK_RESULTS.md").read_text(encoding="utf-8", errors="replace")
    tech_doc = (ROOT / "FINAL_PROJECT_TECHNICAL_DOCUMENTATION_v2.md").read_text(encoding="utf-8", errors="replace")
    policy_status_ok = "UNVERIFIED" in summary and "UNVERIFIED" in tech_doc

    figures = ROOT / "research/figures"
    figure_count = sum((figures / f"F{i}.{ext}").is_file() for i in range(1, 12) for ext in ("png", "pdf"))
    paper_tables = ROOT / "research/paper_tables"
    markdown_tables = len(list(paper_tables.glob("*.md"))) if paper_tables.is_dir() else 0
    latex_tables = len(list(paper_tables.glob("*.tex"))) if paper_tables.is_dir() else 0
    figures_ok = figure_count == 22
    tables_ok = markdown_tables > 0 and latex_tables > 0

    tests, tests_status = check_tests()
    claim_status, claim_output = run_claim_scan()
    docs_ok = not missing and banner_ok and policy_status_ok
    passed = docs_ok and figures_ok and tables_ok and tests_status == "PASS" and claim_status == "PASS"

    if tests is None:
        test_counts = "JUnit summary unavailable"
    else:
        test_counts = (
            f"{tests['passed']} passed, {tests['failures']} failed, "
            f"{tests['errors']} errors, {tests['skipped']} skipped "
            f"({tests['tests']} collected)"
        )

    report = f"""# Phase 10 Report: Documentation and reproducibility

**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}

## (a) What ran
- `make reproduce` is the configured Phase 1–10 entry point. This Phase 10 report records the final documentation and artifact audit after Phase 9.
- Claim scanner: `python -u scripts/check_forbidden_claims.py` (rerun by this report writer).
- Full suite: `pytest -q --junitxml=results/benchmarks/reports/phase10_junit.xml`.

## (b) Files and artifacts checked
{chr(10).join(f'- `{path}`' for path in REQUIRED)}
- Superseded banners in `{SUPERSEDED[0]}`, `{SUPERSEDED[1]}`, and `{SUPERSEDED[2]}`.
- Phase outputs: tuned parameters, statistical tests, risk/policy/review baselines, F1–F11 PNG/PDF, and Markdown/LaTeX paper tables.
- JUnit details: `results/benchmarks/reports/phase10_junit.xml`.

## (c) Key numbers
- Figures present: {figure_count}/22.
- Generated paper tables present: {markdown_tables} Markdown and {latex_tables} LaTeX files.
- Test result: {test_counts}.
- Claim scanner: {claim_status}.

## (d) Anomalies and deviations
- WoE-LR was excluded after a native `optbinning`/`ropwr` crash on this Windows environment; the other five risk model families ran.
- V6 expected-loss review ranking was skipped because no exposure field exists in the synthetic data.
- Phase 11 was not run.
- Policy provenance remains UNVERIFIED pending review against official text.

## (e) Acceptance checks
| Check | Status |
|---|---|
| Required docs and benchmark artifacts exist | {"PASS" if not missing else "FAIL: " + ", ".join(missing)} |
| Superseded banners match the requested text | {"PASS" if banner_ok else "FAIL"} |
| Current docs keep policy rules UNVERIFIED | {"PASS" if policy_status_ok else "FAIL"} |
| F1–F11 PNG and PDF files exist | {"PASS" if figures_ok else "FAIL"} |
| Markdown and LaTeX paper tables exist | {"PASS" if tables_ok else "FAIL"} |
| Forbidden-claim scan | {claim_status} |
| Full test suite | {tests_status} |

## (f) Open questions
- Official policy clauses need human verification before any rule set can be marked VERIFIED.

### Claim scan output
```text
{claim_output}
```
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")
    if not passed:
        print(f"Phase 10 acceptance checks failed; see {REPORT}", file=sys.stderr)
        return 1
    print(f"Phase 10 acceptance checks passed; see {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
