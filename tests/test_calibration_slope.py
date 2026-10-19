"""
Unit tests for calibration_slope_intercept() — logistic version.

Requirements:
  - Perfectly calibrated model → slope ≈ 1, intercept ≈ 0
  - Overconfident model (probs too extreme) → slope < 1
  - OLS deprecated function still importable and returns a float pair
"""
from __future__ import annotations

import numpy as np
import pytest
from scipy.special import expit, logit

from src.evaluation.metrics import (
    calibration_slope_intercept,
    calibration_slope_ols_deprecated,
)


def _simulate_calibrated(n: int = 5000, prevalence: float = 0.15, seed: int = 0):
    """Simulate perfectly calibrated binary data."""
    rng = np.random.default_rng(seed)
    # True latent score from Normal
    eta = rng.normal(0, 1, n)
    # Intercept chosen so mean(p) ~ prevalence
    intercept = logit(prevalence)
    p_true = expit(intercept + eta)
    y = rng.binomial(1, p_true).astype(float)
    # Perfectly calibrated model: p_pred = p_true
    return y, p_true


def _simulate_overconfident(n: int = 5000, prevalence: float = 0.15, factor: float = 2.0, seed: int = 1):
    """Simulate overconfident predictions: logit(p_pred) = factor * logit(p_true)."""
    rng = np.random.default_rng(seed)
    eta = rng.normal(0, 1, n)
    intercept = logit(prevalence)
    p_true = expit(intercept + eta)
    y = rng.binomial(1, p_true).astype(float)
    # Overconfident: predicted logit is stretched
    p_pred = expit(factor * (intercept + eta))
    return y, p_true, p_pred


class TestCalibrationSlopeLogistic:

    def test_perfectly_calibrated_slope_near_1(self):
        """Perfectly calibrated model should give slope ≈ 1."""
        y, p = _simulate_calibrated(n=5000, prevalence=0.15, seed=42)
        slope, intercept = calibration_slope_intercept(y, p)
        assert 0.85 <= slope <= 1.15, f"Expected slope ≈ 1, got {slope:.4f}"

    def test_perfectly_calibrated_intercept_near_0(self):
        """Perfectly calibrated model should give intercept ≈ 0."""
        y, p = _simulate_calibrated(n=5000, prevalence=0.15, seed=42)
        slope, intercept = calibration_slope_intercept(y, p)
        assert -0.3 <= intercept <= 0.3, f"Expected intercept ≈ 0, got {intercept:.4f}"

    def test_overconfident_slope_less_than_1(self):
        """Overconfident model (predictions too extreme) → slope < 1."""
        y, p_true, p_pred = _simulate_overconfident(n=5000, prevalence=0.15, factor=2.0, seed=0)
        slope, _ = calibration_slope_intercept(y, p_pred)
        assert slope < 0.9, f"Expected slope < 0.9 for overconfident model, got {slope:.4f}"

    def test_low_prevalence_slope_still_near_1(self):
        """Logistic slope should be ~1 regardless of prevalence (unlike OLS)."""
        y8, p8 = _simulate_calibrated(n=5000, prevalence=0.08, seed=5)
        y30, p30 = _simulate_calibrated(n=5000, prevalence=0.30, seed=6)
        slope8, _ = calibration_slope_intercept(y8, p8)
        slope30, _ = calibration_slope_intercept(y30, p30)
        # Both should be near 1, unlike OLS which gives different values
        assert 0.8 <= slope8 <= 1.2, f"8% prevalence: slope={slope8:.4f}"
        assert 0.8 <= slope30 <= 1.2, f"30% prevalence: slope={slope30:.4f}"

    def test_ols_deprecated_gives_prevalence_dependent_value(self):
        """OLS deprecated version gives slope ≈ p*(1-p), not 1."""
        y8, p8 = _simulate_calibrated(n=5000, prevalence=0.08, seed=7)
        slope_ols, _ = calibration_slope_ols_deprecated(y8, p8)
        # For 8% prevalence, OLS slope ≈ 0.08 * 0.92 ≈ 0.074
        assert slope_ols < 0.2, f"OLS slope should be small (~0.074), got {slope_ols:.4f}"

    def test_ols_deprecated_still_importable_returns_floats(self):
        """Deprecated OLS function must still work to avoid breaking old code."""
        y, p = _simulate_calibrated(n=200, seed=99)
        result = calibration_slope_ols_deprecated(y, p)
        assert len(result) == 2
        assert all(isinstance(v, float) for v in result)

    def test_returns_floats(self):
        """Return types must be float."""
        y, p = _simulate_calibrated(n=200, seed=10)
        slope, intercept = calibration_slope_intercept(y, p)
        assert isinstance(slope, float)
        assert isinstance(intercept, float)

    def test_clipping_prevents_inf(self):
        """p=0 and p=1 must not cause inf logit."""
        y = np.array([0, 1, 0, 1, 0, 1], dtype=float)
        p = np.array([0.0, 1.0, 0.1, 0.9, 0.2, 0.8])
        slope, intercept = calibration_slope_intercept(y, p)
        assert np.isfinite(slope)
        assert np.isfinite(intercept)
