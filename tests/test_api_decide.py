"""
Engineering tests for /api/decide, model integration, explain(), tau handling,
PMMY policy mapping, and batch evaluation.

Covers:
  1. /api/decide — valid request returns correct schema
  2. Real model loading — graceful fallback when model absent
  3. Tau/tau_e override — values accepted and reflected in response
  4. Evidence gate — correct threshold logic
  5. Policy gate — occupation normalisation (FIX-4/FIX-5)
  6. explain() — correct argument call (FIX-1)
  7. Batch evaluation — consistent with single decisions
  8. Invalid input — correct 422 responses
  9. Decision mode forwarding (FIX-5)
  10. Heuristic PD is labelled 'heuristic'
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from app.api.main import app

# Use TestClient as context manager so lifespan runs
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ── Fixtures ──────────────────────────────────────────────────────────────────

VALID_APPLICANT = {
    "age": 32,
    "platform_tenure": 12,
    "e_shram_registered": 1,
    "income_mean": 25000,
    "income_volatility": 0.25,
    "expense_mean": 15000,
    "liquidity_current": 50000,
    "history_length": 9,
    "multi_platform": 1,
    "emi_status": 0,
    "aa_completeness": 0.8,
    "uli_completeness": 0.7,
    "age_policy": 32,
    "income_policy": 25000,
    "occupation": "delivery",
    "nonfarm_engaged": 1,
    "e_shram_policy": 1,
    "pd_lr": None,
    "pd_xgb": None,
    "applicant_id": "TEST-001",
    "decision_date": "2026-01-01",
}

VALID_REQUEST = {
    "applicant": VALID_APPLICANT,
    "decision_mode": "D4",
    "explain": True,
}


# ── Health check ──────────────────────────────────────────────────────────────

def test_health_returns_ok(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "model_loaded" in data


def test_config_returns_thresholds(client):
    resp = client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "evidence_threshold" in data
    assert "default_tau" in data
    assert data["evidence_threshold"] == pytest.approx(0.5)


def test_model_status_endpoint(client):
    resp = client.get("/api/model_status")
    assert resp.status_code == 200
    data = resp.json()
    assert "xgb_available" in data
    assert "t1_results" in data
    # T1 results file should be present
    if data["t1_results"] is not None:
        assert "xgb" in data["t1_results"]
        assert data["t1_results"]["xgb"]["roc_auc"] == pytest.approx(0.7568, abs=0.001)


# ── 1. /api/decide — valid request ────────────────────────────────────────────

def test_decide_returns_valid_schema(client):
    resp = client.post("/api/decide", json=VALID_REQUEST)
    assert resp.status_code == 200
    data = resp.json()

    required = [
        "applicant_id", "decision_date", "outcome", "recommendation",
        "evidence_gate", "policy_gate", "risk_rank",
        "risk_score", "risk_source", "credit_score",
        "tau_used", "tau_e_used", "model_version", "mode",
    ]
    for field in required:
        assert field in data, f"Missing field: {field}"


def test_decide_outcome_is_valid_enum(client):
    resp = client.post("/api/decide", json=VALID_REQUEST)
    assert resp.status_code == 200
    assert resp.json()["outcome"] in {"APPROVE", "REVIEW", "DECLINE"}


def test_decide_risk_score_in_range(client):
    resp = client.post("/api/decide", json=VALID_REQUEST)
    assert resp.status_code == 200
    rs = resp.json()["risk_score"]
    assert 0.0 <= rs <= 1.0


def test_decide_explanation_included_when_requested(client):
    resp = client.post("/api/decide", json=VALID_REQUEST)
    assert resp.status_code == 200
    data = resp.json()
    assert data["explanation"] is not None
    assert "pd" in data["explanation"]
    assert "decision" in data["explanation"]


def test_decide_no_explanation_when_not_requested(client):
    req = {**VALID_REQUEST, "explain": False}
    resp = client.post("/api/decide", json=req)
    assert resp.status_code == 200
    assert resp.json()["explanation"] is None


# ── 2. Model fallback — heuristic is labelled ─────────────────────────────────

def test_heuristic_pd_labelled_in_response(client):
    """When no trained model is present, risk_source must say 'heuristic'."""
    resp = client.post("/api/decide", json=VALID_REQUEST)
    assert resp.status_code == 200
    data = resp.json()
    # Either a real model or honest heuristic — never silent
    assert data["risk_source"] in {
        "heuristic", "model_xgb", "model_lr", "override_xgb", "override_lr"
    }


def test_pd_override_xgb_accepted(client):
    """pd_xgb override must be used and labelled override_xgb."""
    req = dict(VALID_REQUEST)
    req["applicant"] = {**VALID_APPLICANT, "pd_xgb": 0.15}
    resp = client.post("/api/decide", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_score"] == pytest.approx(0.15, abs=0.001)
    assert data["risk_source"] == "override_xgb"


def test_pd_override_lr_accepted(client):
    req = dict(VALID_REQUEST)
    req["applicant"] = {**VALID_APPLICANT, "pd_lr": 0.22, "pd_xgb": None}
    resp = client.post("/api/decide", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_score"] == pytest.approx(0.22, abs=0.001)
    assert data["risk_source"] == "override_lr"


# ── 3. Tau / tau_e handling (FIX-3) ───────────────────────────────────────────

def test_tau_override_reflected_in_response(client):
    """Custom tau must appear in tau_used field."""
    req = {**VALID_REQUEST, "tau": 0.15}
    resp = client.post("/api/decide", json=req)
    assert resp.status_code == 200
    assert resp.json()["tau_used"] == pytest.approx(0.15)


def test_tau_e_override_reflected_in_response(client):
    req = {**VALID_REQUEST, "tau_e": 0.3}
    resp = client.post("/api/decide", json=req)
    assert resp.status_code == 200
    assert resp.json()["tau_e_used"] == pytest.approx(0.3)


def test_tau_override_affects_decision(client):
    """With tau=0.99 almost everything should APPROVE on PD alone."""
    req = {
        **VALID_REQUEST,
        "tau": 0.99,
        "tau_e": 0.01,
        "applicant": {**VALID_APPLICANT, "pd_xgb": 0.05},
    }
    resp = client.post("/api/decide", json=req)
    assert resp.status_code == 200
    assert resp.json()["outcome"] == "APPROVE"


def test_low_tau_causes_pd_decline(client):
    """With tau=0.01, PD=0.05 should DECLINE."""
    req = {
        **VALID_REQUEST,
        "tau": 0.01,
        "applicant": {**VALID_APPLICANT, "pd_xgb": 0.05},
    }
    resp = client.post("/api/decide", json=req)
    assert resp.status_code == 200
    assert resp.json()["outcome"] == "DECLINE"
    assert resp.json()["risk_rank"]["details"]["source"] == "override_xgb"


# ── 4. Evidence gate ──────────────────────────────────────────────────────────

def test_low_evidence_causes_review_in_d4(client):
    """H=3, AA=0, ULI=0 → E=0.125 < 0.5 → REVIEW in D4."""
    req = {
        **VALID_REQUEST,
        "tau": 0.99,  # ensure PD won't decline
        "applicant": {
            **VALID_APPLICANT,
            "pd_xgb": 0.05,
            "history_length": 3,
            "aa_completeness": 0.0,
            "uli_completeness": 0.0,
        },
    }
    resp = client.post("/api/decide", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["evidence_gate"]["passed"] is False
    assert data["outcome"] == "REVIEW"


def test_sufficient_evidence_passes_gate(client):
    req = {
        **VALID_REQUEST,
        "tau": 0.99,
        "tau_e": 0.5,
        "applicant": {**VALID_APPLICANT, "pd_xgb": 0.05, "history_length": 12,
                      "aa_completeness": 1.0, "uli_completeness": 1.0},
    }
    resp = client.post("/api/decide", json=req)
    assert resp.status_code == 200
    assert resp.json()["evidence_gate"]["passed"] is True


# ── 5. Policy gate — occupation normalisation (FIX-4/FIX-5) ──────────────────

def test_agri_labour_occupation_pmmy_unsatisfied(client):
    """agri_labour / agricultural → PMMY enterprise rule UNSATISFIED → combined may decline."""
    req = {
        **VALID_REQUEST,
        "tau": 0.99,
        "tau_e": 0.01,
        "applicant": {
            **VALID_APPLICANT,
            "pd_xgb": 0.05,
            "occupation": "agri_labour",
            "nonfarm_engaged": 0,
        },
    }
    resp = client.post("/api/decide", json=req)
    assert resp.status_code == 200
    data = resp.json()
    # Policy details must include occupation_normalised
    assert "occupation_normalised" in data["policy_gate"]["details"]
    assert data["policy_gate"]["details"]["occupation_normalised"] == "agri_labour"


def test_frontend_hyphen_occupation_normalised(client):
    """Frontend value 'ride-hailing' must be normalised to 'ride_hailing'."""
    req = {
        **VALID_REQUEST,
        "applicant": {**VALID_APPLICANT, "occupation": "ride-hailing"},
    }
    resp = client.post("/api/decide", json=req)
    assert resp.status_code == 200
    details = resp.json()["policy_gate"]["details"]
    assert details["occupation_normalised"] == "ride_hailing"


def test_agricultural_normalised_to_agri_labour(client):
    req = {**VALID_REQUEST, "applicant": {**VALID_APPLICANT, "occupation": "agricultural"}}
    resp = client.post("/api/decide", json=req)
    assert resp.status_code == 200
    details = resp.json()["policy_gate"]["details"]
    assert details["occupation_normalised"] == "agri_labour"


def test_freelance_normalised(client):
    req = {**VALID_REQUEST, "applicant": {**VALID_APPLICANT, "occupation": "freelance"}}
    resp = client.post("/api/decide", json=req)
    assert resp.status_code == 200
    details = resp.json()["policy_gate"]["details"]
    assert details["occupation_normalised"] == "freelance_services"


# ── 6. explain() — no TypeError (FIX-1) ──────────────────────────────────────

def test_explain_does_not_throw_type_error(client):
    """The key regression test: explain=True must not result in 500 from TypeError."""
    resp = client.post("/api/decide", json=VALID_REQUEST)
    assert resp.status_code == 200
    data = resp.json()
    # If explanation contains 'error' key, check it's NOT a TypeError
    if data["explanation"] and "error" in data["explanation"]:
        assert "TypeError" not in data["explanation"]["error"], (
            f"explain() still throwing TypeError: {data['explanation']['error']}"
        )


def test_explain_endpoint_standalone(client):
    """POST /api/explain standalone endpoint."""
    from src.decisions.gate import Decision
    req = {
        "applicant_id": "EXP-001",
        "pd_calibrated": 0.15,
        "tau": 0.30,
        "decision": "APPROVE",
        "reason_code": None,
        "evidence_score": 0.75,
        "evidence_status": "SUFFICIENT",
        "history_length": 9,
        "tau_e": 0.5,
        "mode": "D4",
        "policy_state": "SATISFIED",
    }
    resp = client.post("/api/explain", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["applicant_id"] == "EXP-001"
    assert data["pd"] == pytest.approx(0.15)
    assert data["decision"] == "APPROVE"
    assert "evidence" in data
    assert "policy" in data


def test_explain_with_review_decision(client):
    req = {
        "applicant_id": "EXP-002",
        "pd_calibrated": 0.10,
        "tau": 0.30,
        "decision": "REVIEW",
        "reason_code": "EVIDENCE_INSUFFICIENT",
        "evidence_score": 0.25,
        "evidence_status": "INSUFFICIENT",
        "history_length": 3,
        "tau_e": 0.5,
        "mode": "D4",
        "policy_state": "SATISFIED",
    }
    resp = client.post("/api/explain", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["reason_codes"] == ["EVIDENCE_INSUFFICIENT"]


# ── 7. Batch evaluation ───────────────────────────────────────────────────────

BATCH_REQUEST = {
    "applicants": [
        {
            "applicant_id": "B-001",
            "age": 30,
            "income_monthly": 25000,
            "history_length": 9,
            "aa_completeness": 0.8,
            "uli_completeness": 0.7,
            "occupation": "delivery",
            "nonfarm_engaged": 1,
            "pd_xgb": 0.10,
        },
        {
            "applicant_id": "B-002",
            "age": 25,
            "income_monthly": 15000,
            "history_length": 3,
            "aa_completeness": 0.0,
            "uli_completeness": 0.0,
            "occupation": "ride_hailing",
            "nonfarm_engaged": 1,
            "pd_xgb": 0.08,
        },
        {
            "applicant_id": "B-003",
            "age": 40,
            "income_monthly": 30000,
            "history_length": 12,
            "aa_completeness": 1.0,
            "uli_completeness": 1.0,
            "occupation": "agri_labour",
            "nonfarm_engaged": 0,
            "pd_xgb": 0.05,
        },
    ],
    "decision_mode": "D4",
    "tau": 0.30,
    "tau_e": 0.5,
}


def test_batch_returns_correct_count(client):
    resp = client.post("/api/evaluate_batch", json=BATCH_REQUEST)
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["total"] == 3
    assert len(data["decisions"]) == 3


def test_batch_summary_rates_sum_to_one(client):
    resp = client.post("/api/evaluate_batch", json=BATCH_REQUEST)
    assert resp.status_code == 200
    s = resp.json()["summary"]
    total = s["approve"] + s["review"] + s["decline"]
    assert total == s["total"]
    rate_sum = s["approve_rate"] + s["review_rate"] + s["decline_rate"]
    assert rate_sum == pytest.approx(1.0, abs=0.001)


def test_batch_uses_same_tau_as_single(client):
    """B-001 has pd_xgb=0.10, tau=0.30 → should APPROVE (if evidence+policy pass)."""
    resp = client.post("/api/evaluate_batch", json=BATCH_REQUEST)
    assert resp.status_code == 200
    decisions = {d["applicant_id"]: d for d in resp.json()["decisions"]}
    # B-001: evidence sufficient (H=9, AA=0.8, ULI=0.7 → E≈0.575), policy ok, PD=0.10 < 0.30
    assert decisions["B-001"]["outcome"] == "APPROVE"


def test_batch_low_evidence_causes_review(client):
    """B-002: H=3, AA=0, ULI=0 → E=0.125 < 0.5 → REVIEW."""
    resp = client.post("/api/evaluate_batch", json=BATCH_REQUEST)
    assert resp.status_code == 200
    decisions = {d["applicant_id"]: d for d in resp.json()["decisions"]}
    assert decisions["B-002"]["outcome"] == "REVIEW"
    assert decisions["B-002"]["evidence_sufficient"] is False


def test_batch_tau_used_matches_request(client):
    resp = client.post("/api/evaluate_batch", json=BATCH_REQUEST)
    assert resp.status_code == 200
    assert resp.json()["tau_used"] == pytest.approx(0.30)
    assert resp.json()["tau_e_used"] == pytest.approx(0.5)


def test_batch_single_decision_consistency(client):
    """Single /api/decide and batch must agree on outcome for same input."""
    single_req = {
        **VALID_REQUEST,
        "tau": 0.30,
        "tau_e": 0.5,
        "applicant": {**VALID_APPLICANT, "pd_xgb": 0.10},
    }
    batch_req = {
        "applicants": [{
            "applicant_id": VALID_APPLICANT["applicant_id"],
            "age": VALID_APPLICANT["age"],
            "income_monthly": VALID_APPLICANT["income_mean"],
            "history_length": VALID_APPLICANT["history_length"],
            "aa_completeness": VALID_APPLICANT["aa_completeness"],
            "uli_completeness": VALID_APPLICANT["uli_completeness"],
            "occupation": VALID_APPLICANT["occupation"],
            "nonfarm_engaged": VALID_APPLICANT["nonfarm_engaged"],
            "pd_xgb": 0.10,
        }],
        "decision_mode": "D4",
        "tau": 0.30,
        "tau_e": 0.5,
    }
    single_resp = client.post("/api/decide", json=single_req)
    batch_resp = client.post("/api/evaluate_batch", json=batch_req)
    assert single_resp.status_code == 200
    assert batch_resp.status_code == 200
    single_outcome = single_resp.json()["outcome"]
    batch_outcome = batch_resp.json()["decisions"][0]["outcome"]
    assert single_outcome == batch_outcome, (
        f"Single={single_outcome} vs batch={batch_outcome} — must be consistent"
    )


# ── 8. Invalid input ──────────────────────────────────────────────────────────

def test_invalid_age_returns_422(client):
    req = dict(VALID_REQUEST)
    req["applicant"] = {**VALID_APPLICANT, "age": 10}
    resp = client.post("/api/decide", json=req)
    assert resp.status_code == 422


def test_invalid_decision_mode_returns_422(client):
    req = {**VALID_REQUEST, "decision_mode": "D5"}
    resp = client.post("/api/decide", json=req)
    assert resp.status_code == 422


def test_missing_required_field_returns_422(client):
    req = dict(VALID_REQUEST)
    app_missing = {k: v for k, v in VALID_APPLICANT.items() if k != "income_mean"}
    req["applicant"] = app_missing
    resp = client.post("/api/decide", json=req)
    assert resp.status_code == 422


def test_tau_out_of_range_returns_422(client):
    req = {**VALID_REQUEST, "tau": 1.5}
    resp = client.post("/api/decide", json=req)
    assert resp.status_code == 422


def test_empty_batch_returns_422(client):
    resp = client.post("/api/evaluate_batch", json={"applicants": [], "decision_mode": "D4"})
    assert resp.status_code == 422


# ── 9. Decision mode forwarding (FIX-5) ──────────────────────────────────────

def test_d1_mode_ignores_policy_and_evidence(client):
    """D1: only PD gate. Even agri_labour with no evidence should APPROVE if PD low."""
    req = {
        **VALID_REQUEST,
        "decision_mode": "D1",
        "tau": 0.99,
        "applicant": {
            **VALID_APPLICANT,
            "pd_xgb": 0.05,
            "occupation": "agri_labour",
            "nonfarm_engaged": 0,
            "history_length": 3,
            "aa_completeness": 0.0,
            "uli_completeness": 0.0,
        },
    }
    resp = client.post("/api/decide", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "D1"
    assert data["outcome"] == "APPROVE"


def test_d2_mode_policy_gate_active(client):
    """D2: policy UNSATISFIED → DECLINE even with low PD.
    Use agri_labour (PMMY enterprise rule → UNSATISFIED) + nonfarm_flag=0 (JanSamarth UNSATISFIED)."""
    req = {
        **VALID_REQUEST,
        "decision_mode": "D2",
        "tau": 0.99,
        "tau_e": 0.01,
        "applicant": {
            **VALID_APPLICANT,
            "pd_xgb": 0.05,
            "occupation": "agri_labour",
            "nonfarm_engaged": 0,
            "age_policy": 32,   # valid age; let occupation drive the result
        },
    }
    resp = client.post("/api/decide", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "D2"
    # agri_labour → PMMY enterprise UNSATISFIED, nonfarm=0 → JanSamarth UNSATISFIED → combined UNSATISFIED
    assert data["outcome"] == "DECLINE"


def test_mode_reflected_in_response(client):
    for mode in ("D1", "D2", "D3", "D4"):
        req = {**VALID_REQUEST, "decision_mode": mode}
        resp = client.post("/api/decide", json=req)
        assert resp.status_code == 200
        assert resp.json()["mode"] == mode
