"""
Feature engineering tests (IMPLEMENTATION_PLAN §6)
Toy series give exact values for each formula.
"""
import math
import numpy as np
import pytest

from src.feature_engineering.build_features import (
    _income_mean, _expense_mean, _expense_ratio,
    _debt_mean, _has_emi, _liquidity_mean, _liquidity_min,
    _income_volatility, _income_trend, _seasonality_index,
    FEATURE_SET_C, ALL_COLUMNS_ORDERED,
)


# ── Set A tests ───────────────────────────────────────────────────────────────

def test_income_mean():
    income = np.array([10000.0, 20000.0, 30000.0])
    assert _income_mean(income) == pytest.approx(20000.0)


def test_expense_ratio():
    income = np.array([20000.0, 20000.0])
    expense = np.array([10000.0, 10000.0])
    assert _expense_ratio(expense, income) == pytest.approx(0.5)


def test_expense_ratio_zero_income():
    """Zero income → NaN expense ratio."""
    result = _expense_ratio(np.array([100.0]), np.array([0.0]))
    assert math.isnan(result)


def test_has_emi_true():
    assert _has_emi(np.array([0.0, 5000.0, 0.0])) == 1


def test_has_emi_false():
    assert _has_emi(np.array([0.0, 0.0, 0.0])) == 0


def test_liquidity_min():
    L = np.array([5000.0, -1000.0, 2000.0])
    assert _liquidity_min(L) == pytest.approx(-1000.0)


# ── Set B tests ───────────────────────────────────────────────────────────────

def test_income_volatility_constant():
    """Constant income → volatility = 0."""
    income = np.array([10000.0] * 6)
    assert _income_volatility(income) == pytest.approx(0.0)


def test_income_volatility_nan_H1():
    """H < 2 → NaN."""
    assert math.isnan(_income_volatility(np.array([10000.0])))


def test_income_trend_nan_H2():
    """H < 3 → NaN."""
    assert math.isnan(_income_trend(np.array([10000.0, 12000.0])))


def test_income_trend_positive():
    """Monotonically increasing income → positive trend."""
    income = np.array([10000.0, 11000.0, 12000.0, 13000.0, 14000.0])
    trend = _income_trend(income)
    assert trend > 0, f"Expected positive trend, got {trend}"


def test_income_trend_negative():
    """Monotonically decreasing income → negative trend."""
    income = np.array([14000.0, 13000.0, 12000.0, 11000.0, 10000.0])
    trend = _income_trend(income)
    assert trend < 0


def test_seasonality_index_nan_not_H12():
    """H != 12 → NaN seasonality."""
    assert math.isnan(_seasonality_index(np.ones(6)))
    assert math.isnan(_seasonality_index(np.ones(3)))


def test_seasonality_index_pure_sine():
    """Pure sine wave with known amplitude → seasonality index = amplitude/mean."""
    t = np.arange(1, 13)
    mean_income = 20000.0
    amp = 0.2 * mean_income
    income = mean_income + amp * np.sin(2 * np.pi * t / 12)
    idx = _seasonality_index(income)
    # Expected: amp / mean = 0.2
    assert idx == pytest.approx(0.2, abs=0.05), f"Expected ~0.2, got {idx:.4f}"


# ── Feature set assertion ─────────────────────────────────────────────────────

def test_feature_set_C_has_12_columns():
    assert len(FEATURE_SET_C) == 12


def test_all_columns_ordered_has_23():
    assert len(ALL_COLUMNS_ORDERED) == 23


def test_no_evidence_policy_in_C():
    """Evidence and policy columns must NOT be in set C."""
    forbidden = {
        "history_length", "aa_completeness", "uli_completeness",
        "jan_samarth_state", "pmmy_state", "e_shram_registered",
    }
    c_set = set(FEATURE_SET_C)
    overlap = forbidden & c_set
    assert not overlap, f"Forbidden columns found in feature set C: {overlap}"
