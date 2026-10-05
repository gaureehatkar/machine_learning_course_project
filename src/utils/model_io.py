"""
src/utils/model_io.py

Save/load utility for FittedModel + PlattCalibrator pairs.
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

import joblib

if TYPE_CHECKING:
    from src.models.train_models import FittedModel
    from src.calibration.platt import PlattCalibrator

_REQUIRED_KEYS = ("model", "calibrator")


def save_model(fitted_model: "FittedModel", calibrator: "PlattCalibrator", path: str) -> None:
    """Save a FittedModel + PlattCalibrator pair together as a single joblib file.

    Args:
        fitted_model: trained FittedModel instance.
        calibrator: fitted PlattCalibrator instance.
        path: destination file path (parent directories are created if needed).
    """
    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    payload = {"model": fitted_model, "calibrator": calibrator}
    joblib.dump(payload, path)


def load_model(path: str) -> "tuple[FittedModel, PlattCalibrator]":
    """Load a FittedModel + PlattCalibrator pair from a joblib file.

    Args:
        path: path to a file previously written by save_model().

    Returns:
        (fitted_model, calibrator) tuple.

    Raises:
        FileNotFoundError: if path does not exist.
        ValueError: if the loaded object is missing expected keys (integrity check).
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model file not found: {path}")

    payload = joblib.load(path)

    if not isinstance(payload, dict) or not all(k in payload for k in _REQUIRED_KEYS):
        raise ValueError(
            f"Loaded object at '{path}' failed integrity check: "
            f"expected a dict with keys {_REQUIRED_KEYS}, got "
            f"{type(payload).__name__} with keys "
            f"{list(payload.keys()) if isinstance(payload, dict) else 'N/A'}"
        )

    return payload["model"], payload["calibrator"]
