"""
Risk model training (TECH_DOC §11, ARCHITECTURE Diagram 4)

Model A — Logistic Regression:
  Pipeline: winsorise(train 1/99 pct) → StandardScaler → LogReg(C=1.0, lbfgs, L2)
  Interpretable, standard for scorecards, easy to calibrate.

Model B — XGBoost:
  Raw features, native NaN handling.
  100 trees, depth 4, lr 0.1, subsample 0.8, colsample 0.8
  No scale_pos_weight (would distort calibration).

Feature sets:
  A (7), B (5), C = A∪B (12)
  ASSERTION: model input columns == exactly the named set (no evidence/policy cols)

2 DGPs × 10 seeds × 2 families × 3 sets = 120 synthetic fits
+ 2 authentic fits (Home Credit).

Module contract (IMPLEMENTATION_PLAN §4):
  train_model(features_train, feature_set, family, cfg) -> FittedModel
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from src.feature_engineering.build_features import FEATURE_SET_A, FEATURE_SET_B, FEATURE_SET_C


# ── Feature set assertion ──────────────────────────────────────────────────────

FEATURE_SETS = {
    "A": FEATURE_SET_A,
    "B": FEATURE_SET_B,
    "C": FEATURE_SET_C,
}


def _assert_feature_set(df: pd.DataFrame, feature_set: str) -> list[str]:
    """Assert that the DataFrame contains exactly the required feature columns."""
    cols = FEATURE_SETS[feature_set.upper()]
    missing = [c for c in cols if c not in df.columns]
    assert not missing, (
        f"Feature set {feature_set} requires columns {missing} which are missing. "
        "Check that evidence/policy columns are not accidentally included."
    )
    # Assert no evidence or policy columns sneaked into the model
    forbidden = [
        "history_length", "aa_completeness", "uli_completeness",
        "jan_samarth_state", "pmmy_state", "e_shram_registered",
    ]
    extra = [c for c in forbidden if c in cols]
    assert not extra, (
        f"Forbidden columns found in feature set {feature_set}: {extra}. "
        "Evidence and policy variables must NEVER enter the PD model."
    )
    return cols


class WinsorisedScaler:
    """Winsorise to (train 1/99 pct) then StandardScale. Fit on train only."""

    def __init__(self, lower_pct: float = 1.0, upper_pct: float = 99.0):
        self.lower_pct = lower_pct
        self.upper_pct = upper_pct
        self.lower_: np.ndarray | None = None
        self.upper_: np.ndarray | None = None
        self.scaler = StandardScaler()

    def fit(self, X: np.ndarray) -> "WinsorisedScaler":
        self.lower_ = np.nanpercentile(X, self.lower_pct, axis=0)
        self.upper_ = np.nanpercentile(X, self.upper_pct, axis=0)
        X_clip = np.clip(X, self.lower_, self.upper_)
        # Impute NaN with column median for LR (can't handle NaN natively)
        self.medians_ = np.nanmedian(X_clip, axis=0)
        X_imp = np.where(np.isnan(X_clip), self.medians_, X_clip)
        self.scaler.fit(X_imp)
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        X_clip = np.clip(X, self.lower_, self.upper_)
        X_imp = np.where(np.isnan(X_clip), self.medians_, X_clip)
        return self.scaler.transform(X_imp)

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).transform(X)


# ── FittedModel wrapper ────────────────────────────────────────────────────────

class FittedModel:
    """Wraps a trained model with metadata for reproducibility and evaluation."""

    def __init__(
        self,
        model,
        feature_set: str,
        family: str,
        feature_cols: list[str],
        preprocessor=None,
        seed: int = 0,
        dgp_id: int | None = None,
        dataset_seed: int | None = None,
    ):
        self.model = model
        self.feature_set = feature_set
        self.family = family
        self.feature_cols = feature_cols
        self.preprocessor = preprocessor  # WinsorisedScaler for LR; None for XGB
        self.seed = seed
        self.dgp_id = dgp_id
        self.dataset_seed = dataset_seed

    def predict_raw(self, features: pd.DataFrame) -> np.ndarray:
        """Return raw probability scores (before Platt calibration)."""
        X = features[self.feature_cols].values.astype(np.float64)
        if self.preprocessor is not None:
            X = self.preprocessor.transform(X)
        proba = self.model.predict_proba(X)
        return proba[:, 1]

    def __repr__(self) -> str:
        return (
            f"FittedModel(family={self.family!r}, set={self.feature_set!r}, "
            f"dgp={self.dgp_id}, seed={self.dataset_seed})"
        )


# ── Train function ─────────────────────────────────────────────────────────────

def train_model(
    features_train: pd.DataFrame,
    feature_set: str,
    family: str,
    cfg: dict[str, Any],
    seed: int | None = None,
    dgp_id: int | None = None,
    dataset_seed: int | None = None,
) -> FittedModel:
    """
    Train a risk model on the training split.

    Parameters
    ----------
    features_train : feature table, training rows only
    feature_set    : "A", "B", or "C"
    family         : "logreg" or "xgb"
    cfg            : experiment or models config
    seed           : random_state for the model
    """
    feature_set = feature_set.upper()
    family = family.lower()

    cols = _assert_feature_set(features_train, feature_set)
    y_train = features_train["default_flag"].values.astype(np.int8)
    X_raw = features_train[cols].values.astype(np.float64)

    model_cfg = cfg.get("models", {})

    if family == "logreg":
        lr_cfg = model_cfg.get("logreg", {})
        rs = seed if seed is not None else lr_cfg.get("random_state", 42)

        preprocessor = WinsorisedScaler()
        X_train = preprocessor.fit_transform(X_raw)

        model = LogisticRegression(
            C=float(lr_cfg.get("C", 1.0)),
            max_iter=int(lr_cfg.get("max_iter", 1000)),
            solver=lr_cfg.get("solver", "lbfgs"),
            penalty=lr_cfg.get("penalty", "l2"),
            random_state=rs,
        )
        model.fit(X_train, y_train)

    elif family == "xgb":
        xgb_cfg = model_cfg.get("xgb", {})
        rs = seed if seed is not None else xgb_cfg.get("random_state", 42)

        preprocessor = None  # XGBoost handles NaN natively
        model = XGBClassifier(
            n_estimators=int(xgb_cfg.get("n_estimators", 100)),
            max_depth=int(xgb_cfg.get("max_depth", 4)),
            learning_rate=float(xgb_cfg.get("learning_rate", 0.1)),
            subsample=float(xgb_cfg.get("subsample", 0.8)),
            colsample_bytree=float(xgb_cfg.get("colsample_bytree", 0.8)),
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=rs,
            verbosity=0,
        )
        model.fit(X_raw, y_train)

    else:
        raise ValueError(f"Unknown model family: {family!r}. Use 'logreg' or 'xgb'.")

    return FittedModel(
        model=model,
        feature_set=feature_set,
        family=family,
        feature_cols=cols,
        preprocessor=preprocessor,
        seed=rs,
        dgp_id=dgp_id,
        dataset_seed=dataset_seed,
    )


def predict_raw(fitted_model: FittedModel, features: pd.DataFrame) -> np.ndarray:
    """Module-contract function: predict raw scores from a FittedModel."""
    return fitted_model.predict_raw(features)
