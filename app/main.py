"""
Streamlit Demo — Policy-Constrained Credit Decisioning
(ARCHITECTURE §12, Diagram 10)

Illustrative on synthetic applicants only.
No real lending integration.

Layout:
  1. Sidebar: select applicant / mode / generate random
  2. Main: risk panel, evidence panel, policy panel, decision + explanation
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.config_loader import load_config
from src.evidence.compute_evidence import compute_evidence, evidence_status
from src.policy.rule_loader import load_policy_set
from src.policy.rule_engine import evaluate_policy, combine_schemes
from src.policy.versioning import select_version
from src.policy.kleene import State, PolicyVersionError
from src.decisions.gate import make_decision, Decision
from src.explainability.explain import explain


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Credit Decisioning Demo",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

CFG_PATH = ROOT / "configs" / "experiment.yaml"
MODEL_CFG_PATH = ROOT / "configs" / "models.yaml"


@st.cache_resource
def load_cfg():
    return load_config(str(CFG_PATH))


@st.cache_resource
def load_policies():
    rules_dir = ROOT / "configs" / "policy_rules"
    return load_policy_set(str(rules_dir))


def _try_load_model_and_data():
    """Attempt to load a trained model and feature data. Returns None if not available."""
    out_dir = ROOT / "data" / "synthetic" / "dgp1" / "seed1"
    features_path = out_dir / "features_visible.parquet"
    if features_path.exists():
        return pd.read_parquet(features_path)
    return None


# ── Applicant generator ───────────────────────────────────────────────────────

def generate_random_applicant(cfg: dict) -> dict:
    """Generate a random synthetic applicant for demo purposes."""
    rng = np.random.default_rng()
    dgp = cfg["dgp"]

    income = float(rng.lognormal(dgp["mu_income"], dgp["sigma_income"]) * 1.0)
    expense_ratio = float(rng.uniform(dgp["rho_min"], dgp["rho_max"]))
    has_emi = bool(rng.random() < dgp["emi_prob"])
    emi = float(rng.uniform(dgp["emi_min"], dgp["emi_max"])) if has_emi else 0.0
    liquidity = float(rng.lognormal(dgp["mu_L0"], dgp["sigma_L0"]))
    volatility = float(rng.uniform(0.15, 0.40))
    trend = float(rng.normal(0, 0.01))
    platform_tenure = int(rng.integers(1, 25))
    multi_platform = bool(rng.random() < dgp["multi_platform_prob"])

    h_vals = list(cfg["dgp"]["history_probs"].keys())
    h_probs = list(cfg["dgp"]["history_probs"].values())
    history_length = int(rng.choice(h_vals, p=h_probs))

    aa_completeness = float(rng.uniform(0, 1))
    uli_completeness = float(rng.uniform(0, 1))
    e_shram = bool(rng.random() < dgp["e_shram_prob"])

    occ_keys = list(dgp["occupation_probs"].keys())
    occ_probs = list(dgp["occupation_probs"].values())
    occupation = str(rng.choice(occ_keys, p=occ_probs))
    age = float(np.clip(rng.normal(34, 11), 18, 70))
    annual_income = income * 12

    return {
        "income_mean": income,
        "expense_mean": income * expense_ratio,
        "expense_ratio": expense_ratio,
        "debt_mean": emi,
        "has_emi": int(has_emi),
        "liquidity_mean": liquidity,
        "liquidity_min": liquidity * float(rng.uniform(0.3, 0.9)),
        "income_volatility": volatility,
        "income_trend": trend,
        "platform_tenure": platform_tenure,
        "multi_platform": int(multi_platform),
        "seasonality_index": float(rng.uniform(0.05, 0.25)),
        "history_length": history_length,
        "aa_completeness": aa_completeness,
        "uli_completeness": uli_completeness,
        "e_shram_registered": int(e_shram),
        "age": age,
        "occupation_category": occupation,
        "annual_income": annual_income,
        "nonfarm_business_flag": 0 if occupation == "agri_labour" else 1,
    }


def _naive_pd_estimate(applicant: dict) -> float:
    """
    Simple heuristic PD estimate for demo (when no trained model is available).
    Uses liquidity_min, expense_ratio, income_volatility.
    Not a real model — for demo visualization only.
    """
    lr = applicant.get("liquidity_min", 10000) / (applicant.get("income_mean", 20000) + 1e-6)
    er = applicant.get("expense_ratio", 0.6)
    vol = applicant.get("income_volatility", 0.3)

    # Higher expense ratio and volatility → higher PD; higher liquidity → lower PD
    score = 0.05 + 0.3 * max(0, er - 0.5) + 0.2 * vol + 0.1 * max(0, -lr)
    return float(np.clip(score, 0.01, 0.95))


# ── Main app ──────────────────────────────────────────────────────────────────

def main():
    cfg = load_cfg()
    policy_set = load_policies()

    # ── Sidebar ───────────────────────────────────────────────────────────────
    st.sidebar.title("⚙️ Settings")
    st.sidebar.markdown("---")

    mode = st.sidebar.selectbox(
        "Decision mode",
        ["D1", "D2", "D3", "D4"],
        index=3,
        help=(
            "D1: ML only | D2: ML + Policy | "
            "D3: ML + Evidence | D4: ML + Policy + Evidence"
        ),
    )

    tau = st.sidebar.slider("PD threshold τ", 0.05, 0.60, 0.25, 0.01,
                             help="Approval threshold. D1 at 0.25 ≈ 70% approval rate.")
    tau_e = float(cfg["evidence"]["tau_e"])

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "**⚠️ DEMO NOTICE**\n\n"
        "This demo uses **synthetic applicants** and **UNVERIFIED policy fixtures**.\n\n"
        "Policy rules are placeholders — not verified JanSamarth/PMMY documents.\n\n"
        "No real lending decisions are made."
    )

    # ── Main content ──────────────────────────────────────────────────────────
    st.title("💳 Policy-Constrained Credit Decisioning")
    st.markdown(
        "**Policy-Constrained Credit Decisioning with Evidence-Quality Gating "
        "for Thin-File Gig/Platform Workers** — Research Prototype"
    )
    st.markdown(
        "> Risk ≠ Evidence Quality ≠ Policy Eligibility  \n"
        "> Three separate layers, combined in the decision engine."
    )

    col_gen, col_info = st.columns([1, 3])
    with col_gen:
        if st.button("🎲 Generate Random Applicant", type="primary"):
            st.session_state["applicant"] = generate_random_applicant(cfg)

    if "applicant" not in st.session_state:
        st.session_state["applicant"] = generate_random_applicant(cfg)

    applicant = st.session_state["applicant"]

    # ── Applicant editor ──────────────────────────────────────────────────────
    with st.expander("✏️ Edit Applicant Attributes", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            applicant["income_mean"] = st.number_input(
                "Monthly Income (₹)", 5000, 100000,
                int(applicant["income_mean"]), step=1000
            )
            applicant["expense_ratio"] = st.slider("Expense Ratio", 0.1, 1.0,
                                                    float(applicant["expense_ratio"]), 0.05)
            applicant["has_emi"] = st.checkbox("Has EMI", bool(applicant["has_emi"]))
        with c2:
            applicant["history_length"] = st.selectbox(
                "History Length (months)", [3, 6, 9, 12],
                index=[3, 6, 9, 12].index(int(applicant["history_length"]))
            )
            applicant["aa_completeness"] = st.slider("AA Completeness", 0.0, 1.0,
                                                       float(applicant["aa_completeness"]), 0.05)
            applicant["uli_completeness"] = st.slider("ULI Completeness", 0.0, 1.0,
                                                        float(applicant["uli_completeness"]), 0.05)
        with c3:
            applicant["age"] = st.slider("Age", 18, 70, int(applicant["age"]))
            applicant["occupation_category"] = st.selectbox(
                "Occupation", list(cfg["dgp"]["occupation_probs"].keys()),
                index=list(cfg["dgp"]["occupation_probs"].keys()).index(
                    applicant["occupation_category"]
                )
            )
            applicant["nonfarm_business_flag"] = 0 if applicant["occupation_category"] == "agri_labour" else 1
            applicant["annual_income"] = applicant["income_mean"] * 12

    st.markdown("---")

    # ── Compute outputs ───────────────────────────────────────────────────────
    pd_calibrated = _naive_pd_estimate(applicant)

    ev_score = float(compute_evidence(
        np.array([applicant["history_length"]]),
        np.array([applicant["aa_completeness"]]),
        np.array([applicant["uli_completeness"]]),
        cfg,
    ).iloc[0])
    ev_status = "SUFFICIENT" if ev_score >= tau_e else "INSUFFICIENT"

    # Policy evaluation
    decision_date = date.fromisoformat(cfg["policy"]["decision_date"])
    policy_evals = {}
    scheme_states = []
    for pid in ["jan_samarth", "pmmy"]:
        try:
            rules = select_version(policy_set, pid, decision_date)
            pe = evaluate_policy(rules, {
                "age": applicant["age"],
                "annual_income": applicant["annual_income"],
                "nonfarm_business_flag": applicant["nonfarm_business_flag"],
                "occupation_category": applicant["occupation_category"],
            })
        except PolicyVersionError:
            from src.policy.rule_engine import PolicyEvaluation
            pe = PolicyEvaluation(
                policy_id=pid, policy_version="N/A",
                effective_from="N/A", effective_to=None,
                state=State.UNRESOLVED, reason_codes=["NO_ACTIVE_VERSION"]
            )
        policy_evals[pid] = pe
        scheme_states.append(pe.state)

    combined_policy = combine_schemes(scheme_states, cfg["policy"]["scheme_mode"])

    decision = make_decision(
        pd=pd_calibrated,
        evidence_score=ev_score,
        policy_state=combined_policy.value,
        mode=mode,
        tau=tau,
        tau_e=tau_e,
    )

    # ── Decision banner ───────────────────────────────────────────────────────
    decision_color = {
        "APPROVE": "🟢",
        "REVIEW": "🟡",
        "DECLINE": "🔴",
    }
    st.subheader(
        f"{decision_color[decision.decision]} Decision: **{decision.decision}** "
        f"({'mode ' + mode}) "
        + (f"— {decision.reason_code}" if decision.reason_code else "— All gates passed")
    )

    # ── Three panels ──────────────────────────────────────────────────────────
    col_risk, col_evid, col_pol = st.columns(3)

    with col_risk:
        st.subheader("📊 Risk Layer")
        pd_pct = pd_calibrated * 100
        tau_pct = tau * 100
        st.metric("Estimated PD", f"{pd_pct:.1f}%")
        st.metric("Threshold τ", f"{tau_pct:.1f}%")
        gate_pass = pd_calibrated < tau
        st.markdown(f"**PD gate:** {'✅ Pass' if gate_pass else '❌ Fail (DECLINE)'}")

        st.markdown("**Top risk factors (demo — heuristic):**")
        factors = [
            ("expense_ratio", applicant["expense_ratio"], f"{applicant['expense_ratio']:.2f}"),
            ("income_volatility", applicant["income_volatility"], f"{applicant['income_volatility']:.3f}"),
            ("liquidity_min", applicant["liquidity_min"], f"₹{applicant['liquidity_min']:,.0f}"),
        ]
        for feat, _, val in factors:
            st.markdown(f"- `{feat}`: {val}")
        st.caption("⚠️ Heuristic PD — no trained model loaded. Run `make generate` then train.")

    with col_evid:
        st.subheader("🔍 Evidence Layer")
        st.metric("Evidence Score E", f"{ev_score:.3f}", delta=f"threshold {tau_e}")
        st.metric("Status", ev_status)

        h = applicant["history_length"]
        aa = applicant["aa_completeness"]
        uli = applicant["uli_completeness"]
        st.markdown(f"**Breakdown:**")
        st.markdown(f"- History: {h}/12 months → contributes {0.5 * h/12:.3f}")
        st.markdown(f"- AA completeness: {aa:.2f} → contributes {0.25 * aa:.3f}")
        st.markdown(f"- ULI completeness: {uli:.2f} → contributes {0.25 * uli:.3f}")
        st.markdown(f"- **E = {ev_score:.3f}** ({'≥' if ev_score >= tau_e else '<'} {tau_e})")

        ev_gate_matters = mode in ("D3", "D4")
        if ev_gate_matters:
            st.markdown(f"**Evidence gate (active in {mode}):** {'✅ Sufficient' if ev_status == 'SUFFICIENT' else '⚠️ Insufficient → REVIEW'}")
        else:
            st.markdown(f"**Evidence gate:** not active in {mode}")

    with col_pol:
        st.subheader("📋 Policy Layer")
        st.markdown(
            "⚠️ **UNVERIFIED** — policy rules are placeholders until Task 10b."
        )

        pol_gate_matters = mode in ("D2", "D4")

        for pid, pe in policy_evals.items():
            state_icon = {"SATISFIED": "✅", "UNSATISFIED": "❌", "UNRESOLVED": "❓"}
            icon = state_icon.get(pe.state.value, "❓")
            st.markdown(f"**{pid.replace('_', ' ').title()}**: {icon} {pe.state.value}")
            for rr in pe.rule_results:
                st.caption(f"  └ [{rr.group}] → {rr.state.value}")

        st.markdown(f"**Combined ({cfg['policy']['scheme_mode']}):** {combined_policy.value}")
        if pol_gate_matters:
            if combined_policy.value == "UNSATISFIED":
                st.markdown("**Policy gate:** ❌ DECLINE (POLICY_INELIGIBLE)")
            elif combined_policy.value == "UNRESOLVED":
                st.markdown("**Policy gate:** ⚠️ REVIEW (POLICY_UNRESOLVED)")
            else:
                st.markdown("**Policy gate:** ✅ Pass")
        else:
            st.markdown(f"**Policy gate:** not active in {mode}")

    # ── Explanation JSON ──────────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("📄 Full Explanation JSON", expanded=False):
        exp_json = explain(
            applicant_id="DEMO_APPLICANT",
            pd_calibrated=pd_calibrated,
            tau=tau,
            decision=decision,
            evidence_score=ev_score,
            evidence_status=ev_status,
            history_length=int(applicant["history_length"]),
            tau_e=tau_e,
            policy_evaluation=policy_evals.get("jan_samarth"),
            shap_reasons=[
                {"feature": "expense_ratio", "shap": 0.0, "value": applicant["expense_ratio"]},
                {"feature": "liquidity_min", "shap": 0.0, "value": applicant["liquidity_min"]},
            ],
            mode=mode,
        )
        st.json(exp_json)

    # ── Architecture note ─────────────────────────────────────────────────────
    st.markdown("---")
    st.caption(
        "Architecture: Risk (PD model) ≠ Evidence (data completeness) ≠ Policy (scheme eligibility). "
        "Separate layers combined by the Decision Engine. "
        "All synthetic findings are simulation evidence under stated assumptions — "
        "not real-world lending performance."
    )


if __name__ == "__main__":
    main()
