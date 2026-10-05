"""
SynthGigCredit-IN-v1 — Data Generating Process (v1.1 spec, v1.2 consistency fixes)

DGP specification source: FINAL_PROJECT_TECHNICAL_DOCUMENTATION.md §10.3

Key invariants (§10.5):
  - Every model feature must be computable using information available no later
    than the observation cutoff (end of month 12).
  - Static attributes (platform_tenure, multi_platform, e_shram_registered,
    aa_completeness, uli_completeness, history_length, policy attributes) are
    defined AS OF the cutoff. They do NOT accrue during months 13-24.
  - Separate RNG substreams for static/observation draws vs outcome draws
    ensures T-D9 (cutoff invariance): perturbing months 13-24 leaves every
    feature column bit-identical.

DGP-1 default rule: L_t < 0 for 2 consecutive months within t=13..24
DGP-2 default rule: same OR L_t < -10000 in any month of t=13..24
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils.seeding import make_static_rng, make_outcome_rng


# ── Internal helpers ──────────────────────────────────────────────────────────

def _draw_static_attributes(rng: np.random.Generator, n: int, cfg: dict) -> dict:
    """
    Draw all per-applicant static attributes using the static RNG substream.
    These are cutoff-dated values — they never change based on outcome-window draws.
    """
    dgp_cfg = cfg["dgp"]

    # Baseline monthly income: LogNormal(mu=9.9, sigma=0.4)
    # => median ~19,900 INR, mean ~21,600 INR  (literature-informed, provisional)
    b = rng.lognormal(
        mean=dgp_cfg["mu_income"],
        sigma=dgp_cfg["sigma_income"],
        size=n,
    )

    # Per-applicant volatility: U(0.15, 0.40)  (literature-informed range, provisional)
    # Reduced by multi_platform and tenure (drawn below)
    # We draw multi_platform first, then tenure, then compute sigma_m
    multi_platform = (rng.random(n) < dgp_cfg["multi_platform_prob"]).astype(np.int8)

    # Platform tenure AS OF the observation cutoff (end of month 12)
    # U{1..24} integers; values >12 mean activity began before month 1
    # Static; no accrual in months 13-24  (§10.5 fix)
    tenure_cutoff = rng.integers(1, dgp_cfg["tenure_max_at_cutoff"] + 1, size=n)

    # Volatility with hooks from multi_platform and tenure (spec §10.3)
    sigma_m_base = rng.uniform(0.15, 0.40, size=n)
    sigma_m = (
        sigma_m_base
        * (1 - 0.15 * multi_platform)
        * (1 - 0.15 * tenure_cutoff / 24)
    )

    # Monthly income growth rate: N(0, 0.01)
    g = rng.normal(0.0, 0.01, size=n)

    # Seasonal amplitude: U(0.05, 0.35); phase: U(0, 2π)  (literature-informed, provisional)
    amp = rng.uniform(dgp_cfg["amp_min"], dgp_cfg["amp_max"], size=n)
    phase = rng.uniform(0, 2 * np.pi, size=n)

    # Expense ratio: U(0.45, 0.85)
    rho = rng.uniform(dgp_cfg["rho_min"], dgp_cfg["rho_max"], size=n)

    # EMI holder: Bernoulli(0.30)
    has_emi = (rng.random(n) < dgp_cfg["emi_prob"]).astype(np.int8)
    # EMI amount drawn once per applicant (re-drawn monthly per spec note §10.3)
    # We store the per-applicant EMI scale here; monthly re-draw happens in simulation
    emi_base = rng.uniform(dgp_cfg["emi_min"], dgp_cfg["emi_max"], size=n)

    # Initial liquidity: LogNormal(mu_L0, sigma_L0=0.8)
    L0 = rng.lognormal(mean=dgp_cfg["mu_L0"], sigma=dgp_cfg["sigma_L0"], size=n)

    # e-Shram registered: Bernoulli(0.64)  (methodological assumption, not empirical)
    e_shram = (rng.random(n) < dgp_cfg["e_shram_prob"]).astype(np.int8)

    # Visible history H_i drawn from {3,6,9,12} with stated probabilities
    h_vals = list(cfg["dgp"]["history_probs"].keys())
    h_probs = list(cfg["dgp"]["history_probs"].values())
    history_length = rng.choice(h_vals, size=n, p=h_probs).astype(np.int8)

    # AA and ULI completeness: U(0,1), mutually independent, independent of H_i and Y
    aa_completeness = rng.uniform(0, 1, size=n).astype(np.float32)
    uli_completeness = rng.uniform(0, 1, size=n).astype(np.float32)

    return dict(
        b=b, sigma_m=sigma_m, g=g, amp=amp, phase=phase,
        rho=rho, has_emi=has_emi, emi_base=emi_base, L0=L0,
        multi_platform=multi_platform, tenure_cutoff=tenure_cutoff,
        e_shram_registered=e_shram,
        history_length=history_length,
        aa_completeness=aa_completeness,
        uli_completeness=uli_completeness,
    )


def _draw_policy_attributes(rng: np.random.Generator, n: int, cfg: dict) -> dict:
    """
    Draw raw policy attributes (separate table).
    PROVISIONAL: attribute set was designed around UNVERIFIED JanSamarth/PMMY criteria (OD-6).
    After Task 10b, if verified rules need different attributes, revise and re-run G0 check 7.
    All attributes dated as of the observation cutoff.
    """
    dgp_cfg = cfg["dgp"]
    missing_rate = dgp_cfg["attr_missing_rate"]  # 5% MCAR on age and occupation

    # Age: Normal(34, 11) clipped [18, 70]
    age_raw = rng.normal(34, 11, size=n)
    age = np.clip(age_raw, 18, 70).astype(np.float32)
    # Apply 5% MCAR missingness
    missing_age_mask = rng.random(n) < missing_rate
    age = np.where(missing_age_mask, np.nan, age)

    # Occupation category distribution (PROVISIONAL — depends on UNVERIFIED rule content)
    occ_keys = list(dgp_cfg["occupation_probs"].keys())
    occ_probs = list(dgp_cfg["occupation_probs"].values())
    occupation = rng.choice(occ_keys, size=n, p=occ_probs)
    # Apply 5% MCAR missingness
    missing_occ_mask = rng.random(n) < missing_rate
    occupation = np.where(missing_occ_mask, None, occupation)

    # Non-farm business flag: 0 iff agri_labour, else 1
    nonfarm_business_flag = np.where(occupation == "agri_labour", 0, 1).astype(np.float32)
    # If occupation is missing, nonfarm is also unknown
    nonfarm_business_flag = np.where(occupation == None, np.nan, nonfarm_business_flag)

    return dict(age=age, occupation_category=occupation, nonfarm_business_flag=nonfarm_business_flag)


def _simulate_monthly(
    static: dict,
    n: int,
    dgp_id: int,
    cfg: dict,
    obs_rng: np.random.Generator,
    outcome_rng: np.random.Generator,
) -> pd.DataFrame:
    """
    Simulate 24 monthly records per applicant.
    Months 1-12: observation window (features derived from here)
    Months 13-24: outcome window (default_flag derived from here ONLY)

    Uses SEPARATE RNG substreams:
      obs_rng    — for months 1-12 draws
      outcome_rng — for months 13-24 draws
    This guarantees T-D9 cutoff invariance.
    """
    dgp_cfg = cfg["dgp"]
    obs_months = cfg["data"]["obs_months"]       # 12
    outcome_months = cfg["data"]["outcome_months"]  # 12
    total_months = obs_months + outcome_months    # 24

    b = static["b"]
    sigma_m = static["sigma_m"]
    g = static["g"]
    amp = static["amp"]
    phase = static["phase"]
    rho = static["rho"]
    has_emi = static["has_emi"]
    emi_base = static["emi_base"]
    L0 = static["L0"]

    # ── Vectorized simulation — all applicants × all months at once ──────────
    # Shape convention: (n, T) where T = obs_months or outcome_months

    # ── Observation window (months 1-12) ──────────────────────────────────────
    t_obs = np.arange(1, obs_months + 1, dtype=np.float64)  # (12,)

    eps_obs = np.exp(
        obs_rng.normal(-sigma_m[:, None] ** 2 / 2, sigma_m[:, None], size=(n, obs_months))
    )  # (n, 12), mean ≈ 1

    if dgp_id == 2:
        shock_mask_obs = obs_rng.random((n, obs_months)) < dgp_cfg["shock_prob"]
        shock_factor_obs = np.where(
            shock_mask_obs,
            1 - dgp_cfg["shock_mag"] * obs_rng.integers(0, 2, size=(n, obs_months)),
            1.0,
        )
    else:
        shock_factor_obs = np.ones((n, obs_months))

    emi_obs = np.where(
        has_emi[:, None],
        obs_rng.uniform(dgp_cfg["emi_min"], dgp_cfg["emi_max"], size=(n, obs_months)),
        0.0,
    )
    rho_noise_obs = obs_rng.normal(0, 2000, size=(n, obs_months))

    # income[i, t] = b[i] * (1+g[i])^t * (1 + amp[i]*sin(2π t/12 + φ[i])) * eps * shock
    growth_obs = (1 + g[:, None]) ** t_obs[None, :]                    # (n, 12)
    seasonal_obs = 1 + amp[:, None] * np.sin(2 * np.pi * t_obs[None, :] / 12 + phase[:, None])
    income_obs = np.maximum(
        b[:, None] * growth_obs * seasonal_obs * eps_obs * shock_factor_obs, 0.0
    )  # (n, 12)

    expense_obs = np.maximum(rho[:, None] * b[:, None] + rho_noise_obs, 0.0)  # (n, 12)
    debt_obs = emi_obs  # (n, 12)

    # Liquidity recursion — cumulative sum with initial condition L0
    cash_flow_obs = income_obs - expense_obs - debt_obs        # (n, 12)
    liquidity_obs = L0[:, None] + np.cumsum(cash_flow_obs, axis=1)  # (n, 12)
    # Correct: L_t = L0 + Σ_{s=1}^{t} cashflow_s; but L0 should be the
    # balance BEFORE month 1, so L_1 = L0 + cf_1. cumsum gives exactly that.

    shock_flag_obs = (shock_factor_obs < 1.0).astype(np.int8)  # (n, 12)

    # ── Outcome window (months 13-24) ─────────────────────────────────────────
    t_out = np.arange(obs_months + 1, obs_months + outcome_months + 1, dtype=np.float64)

    eps_out = np.exp(
        outcome_rng.normal(-sigma_m[:, None] ** 2 / 2, sigma_m[:, None], size=(n, outcome_months))
    )

    s_inc = dgp_cfg["s_inc"]
    income_level_shift = outcome_rng.normal(-s_inc ** 2 / 2, s_inc, size=n)
    lvl_out = np.exp(income_level_shift)  # (n,) per-applicant multiplier

    s_rho = dgp_cfg["s_rho"]
    rho_shift = outcome_rng.normal(0, s_rho, size=n)
    rho_out = rho + rho_shift  # (n,)

    if dgp_id == 2:
        shock_mask_out = outcome_rng.random((n, outcome_months)) < dgp_cfg["shock_prob"]
        shock_factor_out = np.where(
            shock_mask_out,
            1 - dgp_cfg["shock_mag"] * outcome_rng.integers(0, 2, size=(n, outcome_months)),
            1.0,
        )
    else:
        shock_factor_out = np.ones((n, outcome_months))

    emi_out = np.where(
        has_emi[:, None],
        outcome_rng.uniform(dgp_cfg["emi_min"], dgp_cfg["emi_max"], size=(n, outcome_months)),
        0.0,
    )
    rho_noise_out = outcome_rng.normal(0, 2000, size=(n, outcome_months))

    growth_out = (1 + g[:, None]) ** t_out[None, :]
    seasonal_out = 1 + amp[:, None] * np.sin(2 * np.pi * t_out[None, :] / 12 + phase[:, None])
    income_out = np.maximum(
        b[:, None] * growth_out * seasonal_out * eps_out * lvl_out[:, None] * shock_factor_out,
        0.0,
    )  # (n, 12)

    expense_out = np.maximum(rho_out[:, None] * b[:, None] + rho_noise_out, 0.0)
    debt_out = emi_out

    # Liquidity in outcome window — continues from end of obs window
    L_end_obs = liquidity_obs[:, -1]  # (n,) — balance after month 12
    cash_flow_out = income_out - expense_out - debt_out
    liquidity_out = L_end_obs[:, None] + np.cumsum(cash_flow_out, axis=1)  # (n, 12)

    shock_flag_out = (shock_factor_out < 1.0).astype(np.int8)

    # ── Build monthly DataFrame (vectorized — no Python inner loop) ───────────
    applicant_ids = np.array([f"A{i:06d}" for i in range(n)])  # (n,)

    # Stack obs and outcome windows
    income_all   = np.hstack([income_obs,    income_out])    # (n, 24)
    expense_all  = np.hstack([expense_obs,   expense_out])
    debt_all     = np.hstack([debt_obs,      debt_out])
    liq_all      = np.hstack([liquidity_obs, liquidity_out])
    shock_all    = np.hstack([shock_flag_obs, shock_flag_out])
    months_all   = np.arange(1, 25, dtype=np.int8)  # (24,)

    # Repeat applicant_ids n × 24 and tile months 24 × n
    aid_col   = np.repeat(applicant_ids, 24)            # (n*24,)
    month_col = np.tile(months_all, n)                  # (n*24,)

    monthly_df = pd.DataFrame({
        "applicant_id":    aid_col,
        "month":           month_col,
        "income":          income_all.ravel().astype(np.float64),
        "expense":         expense_all.ravel().astype(np.float64),
        "debt_payment":    debt_all.ravel().astype(np.float64),
        "liquidity":       liq_all.ravel().astype(np.float64),
        "income_shock_flag": shock_all.ravel().astype(np.int8),
    })

    # ── Compute default_flag (outcome window only) ─────────────────────────────
    # DGP-1: L_t < 0 for 2 consecutive months within t=13..24
    # DGP-2: same OR L_t < -10,000 in any month of t=13..24
    negative = liquidity_out < 0.0                          # (n, 12)
    consec   = negative[:, :-1] & negative[:, 1:]           # (n, 11)
    dgp1_default = consec.any(axis=1)

    if dgp_id == 1:
        default_flag = dgp1_default.astype(np.int8)
    else:
        severe_negative = (liquidity_out < -10_000.0).any(axis=1)
        default_flag = (dgp1_default | severe_negative).astype(np.int8)

    return monthly_df, default_flag
