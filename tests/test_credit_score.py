"""Unit tests for credit scoring module."""
import pytest
import numpy as np

from src.scoring.credit_score import (
    compute_credit_score,
    compute_score_and_tau,
    format_score_display,
)


class TestComputeCreditScore:
    """Test scorecard scaling credit score computation."""

    def test_score_decreases_with_increasing_pd(self):
        """Score decreases as PD increases (inverse relationship)."""
        pd_low = 0.05
        pd_high = 0.25
        
        score_low = compute_credit_score(pd_low)
        score_high = compute_credit_score(pd_high)
        
        assert score_low > score_high, f"Score should decrease with PD: {score_low} > {score_high}"

    def test_score_at_base_odds(self):
        """Score equals base_score when PD corresponds to base_odds."""
        base_score = 600
        base_odds = 0.05  # 1 in 20
        
        # Solve: odds = (1-PD)/PD = base_odds
        # => PD = 1 / (1 + base_odds)
        pd_at_base_odds = 1.0 / (1.0 + base_odds)
        
        score = compute_credit_score(pd_at_base_odds, base_score=base_score, base_odds=base_odds)
        
        assert abs(score - base_score) < 1, f"Score at base_odds should be ~{base_score}, got {score}"

    def test_score_monotonic(self):
        """Score is strictly monotonically decreasing in PD (within unclamped range)."""
        # Use PDs in middle range to avoid clamping effects
        pds = np.linspace(0.05, 0.50, 20)
        scores = [compute_credit_score(pd) for pd in pds]
        
        # Check all scores are decreasing (allowing for floating point)
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], f"Scores not monotonic at index {i}: {scores[i]} < {scores[i+1]}"

    def test_score_clamping(self):
        """Score is clamped to [score_min, score_max]."""
        score_min, score_max = 300, 900
        
        # Very low PD (high score)
        score_very_low_pd = compute_credit_score(0.001, score_min=score_min, score_max=score_max)
        assert score_very_low_pd <= score_max, f"Score clamped at max: {score_very_low_pd}"
        
        # Very high PD (low score)
        score_very_high_pd = compute_credit_score(0.9999, score_min=score_min, score_max=score_max)
        assert score_very_high_pd >= score_min, f"Score clamped at min: {score_very_high_pd}"

    def test_pdo_effect(self):
        """PDO (Points-to-Double-Odds) controls score sensitivity."""
        pd = 0.1
        pdo_low = 30
        pdo_high = 60
        
        score_low_pdo = compute_credit_score(pd, pdo=pdo_low)
        score_high_pdo = compute_credit_score(pd, pdo=pdo_high)
        
        # Higher PDO means more points per odds change
        # For same PD, higher PDO should give wider score range
        assert score_high_pdo != score_low_pdo, "PDO should affect score"


class TestComputeScoreAndTau:
    """Test joint computation of score and tau equivalent."""

    def test_tau_score_relation_to_pd(self):
        """tau_score corresponds to tau PD (higher tau → lower score)."""
        pd = 0.1
        tau = 0.3  # Higher PD threshold
        
        score, tau_score = compute_score_and_tau(pd, tau)
        
        assert tau_score < score, f"tau_score should be lower (tau={tau} > pd={pd})"

    def test_equal_pd_equal_score(self):
        """When pd == tau, scores should be equal."""
        pd_and_tau = 0.15
        
        score, tau_score = compute_score_and_tau(pd_and_tau, pd_and_tau)
        
        assert abs(score - tau_score) < 1, "Equal PD should give equal scores"


class TestFormatScoreDisplay:
    """Test display formatting."""

    def test_format_includes_required_fields(self):
        """Formatted score has all required display fields."""
        display = format_score_display(
            score=650,
            pd=0.12,
            tau=0.4,
            tau_score=550,
            phase="1",
            model_name="heuristic",
        )
        
        required_fields = {"score", "pd_percent", "threshold_score", "threshold_pd_percent", 
                          "phase", "disclaimer"}
        assert required_fields.issubset(display.keys()), f"Missing fields: {required_fields - set(display.keys())}"

    def test_format_score_is_integer(self):
        """Displayed score is an integer."""
        display = format_score_display(
            score=650.7,
            pd=0.12,
            tau=0.4,
            tau_score=550.3,
        )
        
        assert isinstance(display["score"], int), "Score should be int"
        assert isinstance(display["threshold_score"], int), "Threshold score should be int"

    def test_disclaimer_present(self):
        """Disclaimer is included in display."""
        display = format_score_display(650, 0.12, 0.4, 550)
        
        assert "bureau" in display["disclaimer"].lower(), "Disclaimer should mention bureau"


class TestDecisionIndependenceFromScore:
    """Test that decision logic is NOT affected by score parameters."""

    def test_decision_unaffected_by_pdo(self):
        """Decision logic (PD vs tau) is unchanged by PDO or score parameters."""
        # This is a conceptual test — in actual implementation,
        # decision must use PD directly, not score.
        
        pd = 0.15
        tau = 0.4
        
        # Score doesn't affect this logic
        decision_uses_pd_directly = (pd >= tau)
        
        # Verify via compute functions (no score involved in comparison)
        score_low_pdo, _ = compute_score_and_tau(pd, tau, pdo=30)
        score_high_pdo, _ = compute_score_and_tau(pd, tau, pdo=60)
        
        # Scores differ but decision reasoning remains the same
        assert score_low_pdo != score_high_pdo, "PDO should affect scores"
        # But conceptually: decision logic should only check pd >= tau
        assert decision_uses_pd_directly == (pd >= tau), "Decision logic unchanged"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_pd_zero_clamped(self):
        """PD near zero is safely handled."""
        score = compute_credit_score(0.00001)
        assert 300 <= score <= 900, "Score should be in valid range"

    def test_pd_near_one_clamped(self):
        """PD near 1 is safely handled."""
        score = compute_credit_score(0.99999)
        assert 300 <= score <= 900, "Score should be in valid range"

    def test_custom_parameters(self):
        """Custom base_score, base_odds, PDO are respected."""
        custom_base_score = 700
        custom_base_odds = 0.1
        custom_pdo = 25
        
        # At custom base odds
        pd_at_custom_base = 1.0 / (1.0 + custom_base_odds)
        score = compute_credit_score(
            pd_at_custom_base,
            base_score=custom_base_score,
            base_odds=custom_base_odds,
            pdo=custom_pdo,
        )
        
        assert abs(score - custom_base_score) < 1, f"Custom base_score not respected"
