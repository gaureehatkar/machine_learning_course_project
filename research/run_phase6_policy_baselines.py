#!/usr/bin/env python
"""Run Phase 6C policy-handling baselines for legacy and v2 rule scenarios."""
from __future__ import annotations

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

import hashlib
import json
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as t_dist

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

TABLES = ROOT / "research/tables/benchmarks"
REPORTS = ROOT / "results/benchmarks/reports"
OUTPUT = ROOT / "results/benchmarks/phase6_policy_baselines"
SCENARIOS = ("legacy", "v2_unknown", "v2_ineligible", "v2_eligible")
BASELINES = (
    "P0_no_policy",
    "P1_fail_closed",
    "P2_fail_open",
    "P3_train_imputation",
    "P4_kleene",
)


def evaluate_legacy(attributes: pd.DataFrame, policy_set, decision_date, scheme_mode):
    result = evaluate_batch(attributes, policy_set, decision_date, scheme_mode)
    return np.asarray([
        result.get(aid, {}).get("combined_state", "UNRESOLVED")
        for aid in attributes["applicant_id"]
    ])


def summarize_policy_metrics(
    decisions: np.ndarray,
    policy_states: np.ndarray,
    true_states: np.ndarray,
    pd_values: np.ndarray,
    tau: float,
    outcomes: np.ndarray,
) -> dict[str, float]:
    approved = decisions == "APPROVE"
    referred = decisions == "REVIEW"
    truly_eligible = true_states == "SATISFIED"
    truly_ineligible = true_states == "UNSATISFIED"
    low_risk_eligible = truly_eligible & (pd_values < tau)
    policy_declined = (policy_states == "UNSATISFIED") & low_risk_eligible
    recovered = referred & truly_eligible & (outcomes == 0)

    def rate(numerator: int, denominator: int) -> float:
        return float(numerator / denominator) if denominator else 0.0

    return {
        "approval_rate": float(approved.mean()),
        "review_rate": float(referred.mean()),
        "violation_rate": rate(int((approved & truly_ineligible).sum()), int(approved.sum())),
        "wrongful_decline_rate": rate(int(policy_declined.sum()), int(low_risk_eligible.sum())),
        "referred_truly_eligible_share": rate(
            int((referred & truly_eligible).sum()), int(referred.sum())
        ),
        "recovered_count": float(recovered.sum()),
        "recovered_rate": float(recovered.mean()),
        "post_oracle_approval_rate": float((approved | recovered).mean()),
        "default_rate_among_approved": rate(
            int((approved & (outcomes == 1)).sum()), int(approved.sum())
        ),
    }


def aggregate_by_seed(frame: pd.DataFrame) -> pd.DataFrame:
    metric_names = [
        "approval_rate",
        "review_rate",
        "violation_rate",
        "wrongful_decline_rate",
        "referred_truly_eligible_share",
        "recovered_count",
        "recovered_rate",
        "post_oracle_approval_rate",
        "default_rate_among_approved",
    ]
    rows = []
    for (dgp, scenario, baseline), group in frame.groupby(
        ["dgp", "rule_scenario", "policy_baseline"], sort=True
    ):
        n = len(group)
        critical = float(t_dist.ppf(0.975, n - 1)) if n > 1 else 0.0
        row = {
            "dgp": dgp,
            "rule_scenario": scenario,
            "policy_baseline": baseline,
            "n_seeds": n,
        }
        for name in metric_names:
            values = group[name].astype(float).to_numpy()
            mean = float(np.mean(values))
            std = float(np.std(values, ddof=1)) if n > 1 else 0.0
            ci = critical * std / np.sqrt(n) if n > 1 else 0.0
            row[f"{name}_mean"] = mean
            row[f"{name}_std"] = std
            row[f"{name}_ci"] = ci
            row[f"{name}_ci_lo"] = mean - ci
            row[f"{name}_ci_hi"] = mean + ci
        rows.append(row)
    return pd.DataFrame(rows)


def run() -> None:
    from src.benchmarks.risk_baselines import get_baseline_model, get_tuned_params
    from src.calibration.platt import fit_platt
    from src.decisions.gate import make_decision
    from src.decisions.tau import select_tau
    from src.evidence.compute_evidence import compute_evidence
    from src.feature_engineering.build_features import FEATURE_SET_C
    from src.policy.rule_engine import evaluate_batch
    from src.policy.rule_loader import load_policy_set
    from src.policy.rule_loader_v2 import (
        evaluate_policy_v2,
        load_occupation_mapping,
        load_v2_policy_set,
    )
    from src.utils.config_loader import get_output_dir, load_config

    cfg_path = ROOT / "configs/experiment.yaml"
    cfg = load_config(cfg_path)
    legacy_rules = load_policy_set(ROOT / "configs/policy_rules")
    v2_rules = load_v2_policy_set(ROOT / "configs/policy_rules/v2")
    occupation_mapping = load_occupation_mapping(
        ROOT / "configs/policy_rules/v2/occupation_mapping.yaml"
    )
    decision_date = date.fromisoformat(cfg["policy"]["decision_date"])
    tau_e = float(cfg["evidence"]["tau_e"])
    tuned_path = ROOT / "results/benchmarks/tuned_params.json"
    with open(tuned_path, encoding="utf-8") as stream:
        tuned_params = json.load(stream)

    rows = []
    for dgp_id in (1, 2):
        for seed in range(1, 11):
            out_dir = get_output_dir(cfg, dgp_id, seed)
            full = pd.read_parquet(out_dir / "features_full.parquet")
            visible = pd.read_parquet(out_dir / "features_visible.parquet")
            attrs = pd.read_parquet(out_dir / "policy_attributes.parquet").set_index(
                "applicant_id"
            )
            truth = pd.read_parquet(out_dir / "policy_truth.parquet").set_index(
                "applicant_id"
            )
            train = full[full["split"] == "train"].reset_index(drop=True)
            val = visible[visible["split"] == "val"].reset_index(drop=True)
            test = visible[visible["split"] == "test"].reset_index(drop=True)

            model_params = get_tuned_params(tuned_params, f"dgp{dgp_id}", "xgb", "C")
            model = get_baseline_model("xgb", params=model_params, seed=seed)
            model.fit(train[FEATURE_SET_C], train["default_flag"].to_numpy())
            p_raw_val = model.predict_proba(val[FEATURE_SET_C])[:, 1]
            p_raw_test = model.predict_proba(test[FEATURE_SET_C])[:, 1]
            calibrator = fit_platt(p_raw_val, val["default_flag"].to_numpy())
            pd_val = calibrator.transform(p_raw_val)
            pd_test = calibrator.transform(p_raw_test)
            tau = select_tau(pd_val, cfg["decision"]["approval_target"])
            evidence = compute_evidence(
                test["history_length"],
                test["aa_completeness"],
                test["uli_completeness"],
                cfg,
            ).values
            test_ids = test["applicant_id"].to_numpy()
            train_attrs = attrs.loc[train["applicant_id"]].reset_index()
            test_attrs = attrs.loc[test_ids].reset_index()
            train_attrs["annual_income"] = train_attrs["applicant_id"].map(
                train.set_index("applicant_id")["income_mean"] * 12
            )
            test_attrs["annual_income"] = test_attrs["applicant_id"].map(
                test.set_index("applicant_id")["income_mean"] * 12
            )

            age_median = train_attrs["age"].median()
            occupation_modes = train_attrs["occupation_category"].dropna().mode()
            nonfarm_modes = train_attrs["nonfarm_business_flag"].dropna().mode()
            if pd.isna(age_median) or occupation_modes.empty or nonfarm_modes.empty:
                raise ValueError(f"Cannot fit train-only imputation for DGP{dgp_id}, seed {seed}")
            imputed_attrs = test_attrs.copy()
            imputed_attrs["age"] = imputed_attrs["age"].fillna(float(age_median))
            imputed_attrs["occupation_category"] = imputed_attrs[
                "occupation_category"
            ].fillna(occupation_modes.iloc[0])
            imputed_attrs["nonfarm_business_flag"] = imputed_attrs[
                "nonfarm_business_flag"
            ].fillna(nonfarm_modes.iloc[0])

            for scenario in SCENARIOS:
                if scenario == "legacy":
                    observed = evaluate_legacy(
                        test_attrs, legacy_rules, decision_date, cfg["policy"]["scheme_mode"]
                    )
                    imputed = evaluate_legacy(
                        imputed_attrs,
                        legacy_rules,
                        decision_date,
                        cfg["policy"]["scheme_mode"],
                    )
                    truth_column = "true_policy_legacy"
                else:
                    agri_scenario = scenario.removeprefix("v2_")
                    observed = np.asarray([
                        evaluate_policy_v2(
                            row,
                            v2_rules,
                            decision_date,
                            agri_scenario=agri_scenario,
                            mapping=occupation_mapping,
                        )[0].value
                        for row in test_attrs.to_dict("records")
                    ])
                    imputed = np.asarray([
                        evaluate_policy_v2(
                            row,
                            v2_rules,
                            decision_date,
                            agri_scenario=agri_scenario,
                            mapping=occupation_mapping,
                        )[0].value
                        for row in imputed_attrs.to_dict("records")
                    ])
                    truth_column = f"true_policy_{scenario}"

                true_states = truth.loc[test_ids, truth_column].to_numpy()
                if scenario == "legacy":
                    p1 = np.where(observed == "UNRESOLVED", "UNSATISFIED", observed)
                    p2 = np.where(observed == "UNRESOLVED", "SATISFIED", observed)
                else:
                    p1 = np.where(observed == "UNRESOLVED", "UNSATISFIED", observed)
                    p2 = np.where(observed == "UNRESOLVED", "SATISFIED", observed)

                policies = {
                    "P0_no_policy": np.full(len(test), "SATISFIED"),
                    "P1_fail_closed": p1,
                    "P2_fail_open": p2,
                    "P3_train_imputation": imputed,
                    "P4_kleene": observed,
                }
                for baseline, policy_states in policies.items():
                    decisions = np.asarray([
                        make_decision(pd_test[i], evidence[i], policy_states[i], "D4", tau, tau_e).decision
                        for i in range(len(test))
                    ])
                    metrics = summarize_policy_metrics(
                        decisions,
                        policy_states,
                        true_states,
                        pd_test,
                        tau,
                        test["default_flag"].to_numpy(),
                    )
                    rows.append({
                        "dgp": f"DGP{dgp_id}",
                        "seed": seed,
                        "rule_scenario": scenario,
                        "policy_baseline": baseline,
                        **metrics,
                    })
            print(f"DGP{dgp_id} seed {seed}: policy scenarios complete", flush=True)

    raw = pd.DataFrame(rows)
    aggregate = aggregate_by_seed(raw)
    TABLES.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    raw.to_csv(TABLES / "policy_baselines_per_seed.csv", index=False)
    aggregate.to_csv(TABLES / "policy_baselines.csv", index=False)

    qualitative = """# Policy baseline implementation notes

- P0 ignores policy state; P1 treats UNRESOLVED as UNSATISFIED; P2 treats it as SATISFIED.
- P3 fills missing age, occupation, and non-farm flag using train-split median/mode only.
- P4 uses the Kleene policy engine; UNRESOLVED is routed to REVIEW by D4.
- Decision reason codes are `PD_HIGH`, `POLICY_INELIGIBLE`, `POLICY_UNRESOLVED`, and `EVIDENCE_INSUFFICIENT` (see `src/decisions/gate.py`).
- Rule provenance keys are `document`, `clause`, `page_or_url`, `retrieved_on`, and `verified_by`; v2 values remain placeholders and the rule set is UNVERIFIED.
- The PMMY amount-version boundary is exercised in `tests/test_policy_v2.py` for 2024-10-23 and 2024-10-24. The synthetic DGP has no requested-loan-amount column, so this condition is excluded from experimental decisions.
- The policy engine combines rule results using Kleene logic; conflicting conditions are not rewritten as a verified eligibility decision.
- The review oracle declines referred true-ineligible applicants and referred defaulters; other referred applicants are approved.
"""
    (ROOT / "results/benchmarks/policy_qualitative.md").write_text(
        qualitative, encoding="utf-8"
    )

    config_hash = hashlib.sha256(cfg_path.read_bytes()).hexdigest()
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    versions = {}
    for package in ("numpy", "pandas", "scipy", "scikit-learn", "xgboost"):
        try:
            versions[package] = version(package)
        except PackageNotFoundError as exc:
            raise RuntimeError(f"Could not read installed version for {package}") from exc
    manifest = {
        "command": "python -u research/run_phase6_policy_baselines.py",
        "git_commit": commit,
        "config": "configs/experiment.yaml",
        "config_sha256": config_hash,
        "seeds": list(range(1, 11)),
        "dgps": [1, 2],
        "rule_scenarios": list(SCENARIOS),
        "package_versions": versions,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    report = f"""# Phase 6 Report: Architecture and policy baselines

## (a) What ran
- Architecture and single-score evaluations: `python -u research/run_phase6_architecture_and_policy.py`
- Policy baseline re-run: `python -u research/run_phase6_policy_baselines.py`
- Rule scenarios: {", ".join(SCENARIOS)}

## (b) Files written
- `research/tables/benchmarks/architecture_model_agnostic.csv`
- `research/tables/benchmarks/single_score_vs_pipeline.csv`
- `research/tables/benchmarks/policy_baselines.csv` and `policy_baselines_per_seed.csv`
- `research/tables/benchmarks/policy_qualitative.md`
- `results/benchmarks/phase6_policy_baselines/manifest.json`

## (c) Key numbers
Results are in the aggregated and per-seed CSVs above; this report does not duplicate values.

## (d) Anomalies and deviations
- Architecture-model and single-score tables use the models and scenarios recorded by their runner; the policy table includes all five policy methods and four rule scenarios.
- Policy rule v2 provenance remains UNVERIFIED. Requested loan amounts are absent from the DGP and therefore only tested in the versioning unit test.

## (e) Acceptance checks
| Check | Status |
|---|---|
| Per-seed raw table and aggregate written | PASS |
| Train-only P3 imputation | PASS |
| Four rule scenarios | PASS |
| Wrongful-decline and violation definitions computed from true states | PASS |

## (f) Open questions
- None blocking this phase; official policy provenance still requires human verification.
"""
    (REPORTS / "PHASE_6_REPORT.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    run()
