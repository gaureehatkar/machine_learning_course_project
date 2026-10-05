"""Seeding utilities — deterministic, reproducible RNG management.

Separate RNG substreams are maintained for:
  - static / observation-window draws (applicant attributes, months 1-12)
  - outcome-window draws (months 13-24, default flag)

This ensures the cutoff-invariance property (T-D9):
  perturbing outcome-window draws leaves every feature column bit-identical.
"""
from __future__ import annotations

import numpy as np


# ── Seed derivation ────────────────────────────────────────────────────────────

def static_seed(base_seed: int) -> int:
    """Seed for static applicant attributes and observation-window draws."""
    return base_seed * 1000 + 1


def outcome_seed(base_seed: int) -> int:
    """Seed for outcome-window (months 13-24) draws. Kept separate from static."""
    return base_seed * 1000 + 2


def split_seed(dataset_seed: int) -> int:
    """Seed for train/val/test stratified split."""
    return 1000 + dataset_seed


def model_seed(dataset_seed: int) -> int:
    """Seed for model random_state."""
    return dataset_seed


def review_seed(dataset_seed: int) -> int:
    """Seed for R0 random review strategy."""
    return 2000 + dataset_seed


# ── RNG factory ───────────────────────────────────────────────────────────────

def make_rng(seed: int) -> np.random.Generator:
    """Return a seeded numpy Generator (PCG64)."""
    return np.random.default_rng(seed)


def make_static_rng(base_seed: int) -> np.random.Generator:
    return make_rng(static_seed(base_seed))


def make_outcome_rng(base_seed: int) -> np.random.Generator:
    return make_rng(outcome_seed(base_seed))
