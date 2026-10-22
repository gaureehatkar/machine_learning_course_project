#!/usr/bin/env python
"""Scan paper/ (md/tex) for phrases that overclaim the measured results."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
PAPER = ROOT / "paper"

PATTERNS = [
    (r"works for real gig workers", "real-gig overclaim"),
    (r"impossible with (a )?single[- ]score", "single-score impossibility"),
    (r"no existing system", "novelty overclaim"),
    (r"outperforms existing methods", "needs a table reference"),
    (r"underprediction", "calibration underprediction narrative"),
]


def policy_verified_hits(text: str) -> list[str]:
    hits = []
    for m in re.finditer(r".{0,40}\bverified\b.{0,40}", text, flags=re.IGNORECASE):
        window = m.group(0).lower()
        if "policy" in window or "rule" in window:
            hits.append(m.group(0).strip())
    return hits


def outperforms_without_table(text: str) -> list[str]:
    hits = []
    for m in re.finditer(r".{0,80}outperforms existing methods.{0,80}", text, flags=re.IGNORECASE):
        window = m.group(0)
        if not re.search(r"(Table|Tab\.|statistical_tests|review_baselines|risk_baselines)", window):
            hits.append(window.strip())
    return hits


def shap_api_demo_hits(text: str) -> list[str]:
    hits = []
    for m in re.finditer(r"SHAP explanations", text, flags=re.IGNORECASE):
        window = text[max(0, m.start() - 120): min(len(text), m.end() + 120)]
        if re.search(r"\b(api|demo|app|endpoint)\b", window, flags=re.IGNORECASE):
            hits.append(window.strip().replace("\n", " "))
    return hits


def main() -> int:
    files = []
    if PAPER.exists():
        files.extend(PAPER.rglob("*.md"))
        files.extend(PAPER.rglob("*.tex"))
    # also scan v2 result docs
    for extra in [
        ROOT / "research/BENCHMARK_RESULTS.md",
        ROOT / "EXPERIMENT_RESULTS_v2.md",
        ROOT / "FINAL_PROJECT_TECHNICAL_DOCUMENTATION_v2.md",
    ]:
        if extra.exists():
            files.append(extra)

    warnings = []
    if not files:
        print("No paper/ files and no v2 docs yet; nothing to scan.")
        return 0

    for fp in files:
        text = fp.read_text(encoding="utf-8", errors="replace")
        for pat, reason in PATTERNS:
            if pat == r"outperforms existing methods":
                continue
            if re.search(pat, text, flags=re.IGNORECASE):
                warnings.append(f"{fp.relative_to(ROOT)}: {reason} / {pat}")
        for h in policy_verified_hits(text):
            warnings.append(f"{fp.relative_to(ROOT)}: verified near policy/rules: {h!r}")
        for h in outperforms_without_table(text):
            warnings.append(f"{fp.relative_to(ROOT)}: outperforms existing methods without table ref: {h!r}")
        for h in shap_api_demo_hits(text):
            warnings.append(f"{fp.relative_to(ROOT)}: SHAP claim in API/demo context: {h!r}")

    if warnings:
        print(f"WARN {len(warnings)} forbidden-phrase hits:")
        for w in warnings:
            print(" -", w)
        return 1
    print("PASSED: no forbidden phrases in paper/ and v2 docs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
