"""Evidence engine tests (IMPLEMENTATION_PLAN §6)."""
import numpy as np
import pytest

from src.evidence.compute_evidence import compute_evidence, evidence_status


@pytest.fixture
def cfg():
    return {
        "evidence": {
            "weights": {"history": 0.5, "aa": 0.25, "uli": 0.25},
            "tau_e": 0.5,
        }
    }


def test_H12_AA0_ULI0_equals_0_5(cfg):
    """H=12, AA=0, ULI=0 → E = 0.5 (exactly at threshold)."""
    e = compute_evidence(np.array([12]), np.array([0.0]), np.array([0.0]), cfg)
    assert float(e.iloc[0]) == pytest.approx(0.5)


def test_H6_AA0_ULI0_below_threshold(cfg):
    """H=6, AA=0, ULI=0 → E = 0.25 (INSUFFICIENT)."""
    e = compute_evidence(np.array([6]), np.array([0.0]), np.array([0.0]), cfg)
    assert float(e.iloc[0]) == pytest.approx(0.25)


def test_H12_AA1_ULI1_equals_1(cfg):
    """H=12, AA=1, ULI=1 → E = 1.0."""
    e = compute_evidence(np.array([12]), np.array([1.0]), np.array([1.0]), cfg)
    assert float(e.iloc[0]) == pytest.approx(1.0)


def test_bounds_always_0_1(cfg):
    """E must always be in [0, 1]."""
    rng = np.random.default_rng(42)
    h = rng.integers(1, 13, size=100)
    aa = rng.random(100)
    uli = rng.random(100)
    e = compute_evidence(h, aa, uli, cfg)
    assert (e >= 0).all() and (e <= 1).all()


def test_missing_aa_treated_as_zero(cfg):
    """Missing AA (NaN) should be treated as 0."""
    e_nan = compute_evidence(np.array([6]), np.array([np.nan]), np.array([0.0]), cfg)
    e_zero = compute_evidence(np.array([6]), np.array([0.0]), np.array([0.0]), cfg)
    assert float(e_nan.iloc[0]) == pytest.approx(float(e_zero.iloc[0]))


def test_sufficient_insufficient_threshold(cfg):
    """E >= 0.5 → SUFFICIENT; E < 0.5 → INSUFFICIENT."""
    scores = np.array([0.0, 0.25, 0.49, 0.5, 0.75, 1.0])
    status = evidence_status(scores, cfg)
    expected = ["INSUFFICIENT", "INSUFFICIENT", "INSUFFICIENT",
                "SUFFICIENT", "SUFFICIENT", "SUFFICIENT"]
    assert list(status) == expected
