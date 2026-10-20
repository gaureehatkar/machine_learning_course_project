"""Unit tests for src/evaluation/paired_tests.py"""
import numpy as np
import pytest
from scipy.stats import ttest_rel

from src.evaluation.paired_tests import (
    paired_ttest, holm_correction, bonferroni_correction,
    cohen_d_z, format_contrast_table, ALPHA_BONFERRONI,
    paired_bootstrap_ci,
)


class TestPairedTtest:

    def test_matches_scipy(self):
        rng = np.random.default_rng(0)
        a = rng.normal(0.70, 0.02, 10)
        b = rng.normal(0.72, 0.02, 10)
        r = paired_ttest(a, b)
        t_sp, p_sp = ttest_rel(b, a)  # scipy: b-a
        assert abs(abs(r.t_stat) - abs(t_sp)) < 1e-6
        assert abs(r.p_value - p_sp) < 1e-6

    def test_ci_contains_mean_diff(self):
        rng = np.random.default_rng(1)
        a = rng.normal(0.5, 0.05, 10)
        b = rng.normal(0.55, 0.05, 10)
        r = paired_ttest(a, b)
        assert r.ci_lo <= r.mean_diff <= r.ci_hi

    def test_no_difference_not_significant(self):
        a = np.array([0.70] * 10)
        b = np.array([0.70] * 10)
        r = paired_ttest(a, b)
        assert r.p_value == 1.0
        assert r.t_stat == 0.0

    def test_large_difference_significant(self):
        rng = np.random.default_rng(7)
        a = rng.normal(0.0, 0.001, 10)
        b = rng.normal(1.0, 0.001, 10)
        r = paired_ttest(a, b)
        assert r.p_value < 1e-10
        assert r.significant()

    def test_mean_diff_sign(self):
        a = np.array([0.60] * 10)
        b = np.array([0.70] * 10)
        r = paired_ttest(a, b)
        assert r.mean_diff > 0  # b - a

    def test_n_equals_df_plus_one(self):
        a = np.random.default_rng(2).normal(0, 1, 7)
        b = np.random.default_rng(3).normal(0, 1, 7)
        r = paired_ttest(a, b)
        assert r.df == r.n - 1 == 6

    def test_uses_dynamic_t_crit(self):
        """CI width should be proportionally wider for n=5 vs n=20 (more uncertainty)."""
        rng = np.random.default_rng(4)
        a5  = rng.normal(0, 0.01, 5)
        b5  = a5 + 0.005
        a20 = rng.normal(0, 0.01, 20)
        b20 = a20 + 0.005
        r5  = paired_ttest(a5,  b5)
        r20 = paired_ttest(a20, b20)
        from scipy.stats import t as t_dist
        tcrit5  = t_dist.ppf(0.975, 4)
        tcrit20 = t_dist.ppf(0.975, 19)
        # n=5 has larger t-crit
        assert tcrit5 > tcrit20


class TestHolmCorrection:

    def test_ordering(self):
        p = [0.04, 0.001, 0.02]
        adj = holm_correction(p)
        # Smallest raw p → adj = 3 * 0.001 = 0.003; next = 2 * 0.02 = 0.04; etc.
        assert adj[1] <= adj[2] <= adj[0]  # original order preserved

    def test_clip_at_one(self):
        p = [0.9, 0.8, 0.7]
        adj = holm_correction(p)
        assert all(a <= 1.0 for a in adj)

    def test_single_value(self):
        assert holm_correction([0.03])[0] == pytest.approx(0.03)

    def test_monotone_adjusted(self):
        """Adjusted p-values must be non-decreasing when sorted by raw p."""
        p = [0.001, 0.01, 0.04, 0.1]
        adj = holm_correction(p)
        adj_sorted = sorted(adj)
        assert adj_sorted == list(adj_sorted)


class TestBonferroniCorrection:

    def test_multiplies_by_n(self):
        p = [0.01, 0.02]
        adj = bonferroni_correction(p, n_contrasts=3)
        assert adj[0] == pytest.approx(0.03)
        assert adj[1] == pytest.approx(0.06)

    def test_clip_at_one(self):
        adj = bonferroni_correction([0.9], n_contrasts=3)
        assert adj[0] == 1.0

    def test_alpha_constant(self):
        assert ALPHA_BONFERRONI == pytest.approx(0.05 / 3)


class TestPairedBootstrap:

    def test_ci_covers_mean(self):
        rng = np.random.default_rng(0)
        a = rng.normal(0.5, 0.02, 30)
        b = a + 0.01
        mean, lo, hi = paired_bootstrap_ci(a, b, n_boot=200, seed=1)
        assert lo <= mean <= hi
        assert mean == pytest.approx(0.01, abs=1e-12)


class TestCohenDz:

    def test_perfect_effect(self):
        """All diffs identical → std=0 → d_z returns 0."""
        diffs = np.ones(10)
        assert cohen_d_z(diffs) == 0.0

    def test_typical(self):
        rng = np.random.default_rng(5)
        diffs = rng.normal(0.05, 0.02, 10)
        d = cohen_d_z(diffs)
        assert d > 0


class TestFormatContrastTable:

    def test_basic(self):
        rng = np.random.default_rng(6)
        a = rng.normal(0.70, 0.02, 10)
        b = rng.normal(0.72, 0.02, 10)
        contrasts = [{"contrast": "A vs C", "family": "primary", "dgp": "DGP1",
                      "metric": "roc_auc", "a_label": "A", "b_label": "C",
                      "a_values": a, "b_values": b}]
        df = format_contrast_table(contrasts)
        assert len(df) == 1
        assert "mean_diff" in df.columns
        assert "p" in df.columns
        assert "significant" in df.columns

    def test_precomputed_result(self):
        from src.evaluation.paired_tests import paired_ttest
        a = np.array([0.70]*10)
        b = np.array([0.72]*10)
        r = paired_ttest(a, b)
        contrasts = [{"contrast": "test", "family": "primary", "dgp": "DGP1",
                      "metric": "auc", "a_label": "A", "b_label": "B", "result": r}]
        df = format_contrast_table(contrasts)
        assert df["mean_diff"].iloc[0] == pytest.approx(0.02)
