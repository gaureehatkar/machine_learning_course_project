"""
Prediction utilities — raw scores and calibrated PD.

Separation (TECH_DOC §3, §12):
  train → fit models
  validation → fit Platt calibration and τ
  test → touched ONCE for final evaluation (logged in manifest)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.models.train_models import FittedModel
from src.calibration.platt import PlattCalibrator


def get_raw_scores(
    model: FittedModel,
    features: pd.DataFrame,
) -> np.ndarray:
    """Return raw (uncalibrated) probability scores."""
    return model.predict_raw(features)


def get_calibrated_pd(
    model: FittedModel,
    calibrator: PlattCalibrator,
    features: pd.DataFrame,
) -> np.ndarray:
    """Return Platt-calibrated PD estimates."""
    raw = model.predict_raw(features)
    return calibrator.transform(raw)


def score_split(
    model: FittedModel,
    calibrator: PlattCalibrator,
    features_df: pd.DataFrame,
    split: str,
) -> pd.DataFrame:
    """
    Score one split (train / val / test) and return a DataFrame with:
      applicant_id, default_flag, pd_raw, pd_calibrated

    NOTE: Test set should be touched EXACTLY ONCE per experiment.
    """
    subset = features_df[features_df["split"] == split].copy()
    raw = get_raw_scores(model, subset)
    cal = get_calibrated_pd(model, calibrator, subset)

    return pd.DataFrame({
        "applicant_id": subset["applicant_id"].values,
        "default_flag": subset["default_flag"].values,
        "pd_raw": raw,
        "pd_calibrated": cal,
    })
