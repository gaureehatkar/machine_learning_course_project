"""Unit tests for Phase 7 review-allocation helpers."""
from __future__ import annotations

import numpy as np
import pytest

from src.benchmarks.abstention import (
    allocate_by_budget,
    compute_allocation_scores,
)


def test_allocate_uses_floor_not_ceil():
    scores = np.arange(10, dtype=float)
    # B=0.25 → floor(2.5)=2, not ceil=3
    ref = allocate_by_budget(scores, 0.25)
    assert ref.sum() == 2


def test_mandatory_consumed_first():
    scores = np.array([0.1, 0.9, 0.8, 0.2])
    mand = np.array([True, False, False, True])
    ref = allocate_by_budget(scores, 0.5, mandatory_mask=mand)  # K=floor(2)=2
    assert ref[0] and ref[3]
    assert not ref[1] and not ref[2]


def test_r1_monotone_in_pd_below_half():
    rng = np.random.RandomState(0)
    pd_pool = rng.uniform(0.01, 0.49, size=200)
    scores = compute_allocation_scores(
        pd_pool, None, tau=0.5, pd_val=pd_pool, y_val=np.zeros(200), strategy="R1"
    )
    # Entropy increasing in PD for PD < 0.5
    order_pd = np.argsort(pd_pool)
    assert np.all(np.diff(scores[order_pd]) >= -1e-12)


def test_v6_raises_without_exposure():
    pd_pool = np.array([0.1, 0.2, 0.3])
    with pytest.raises(ValueError, match="exposure"):
        compute_allocation_scores(
            pd_pool, None, 0.4, pd_pool, np.zeros(3), strategy="V6"
        )


def test_strategy_aliases():
    pd_pool = np.linspace(0.05, 0.45, 20)
    y = (pd_pool > 0.25).astype(int)
    a = compute_allocation_scores(pd_pool, y, 0.5, pd_pool, y, "V0_random", seed=1)
    b = compute_allocation_scores(pd_pool, y, 0.5, pd_pool, y, "R0", seed=1)
    assert np.allclose(a, b)


def test_v2_margin_prioritizes_near_tau():
    pd_pool = np.array([0.10, 0.40, 0.25])
    tau = 0.30
    scores = compute_allocation_scores(
        pd_pool, None, tau, pd_pool, np.zeros(3), strategy="V2_margin"
    )
    # |0.25-0.30|=0.05 smallest margin → highest score among these
    assert scores.argmax() == 2
