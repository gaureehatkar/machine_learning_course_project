"""
Risk-layer benchmark models (Phase 2).

Provides:
  WoELR  — optbinning BinningProcess + LogisticRegression
  LGBMModel — LightGBM
  CatBoostModel — CatBoost

All models expose:
  fit(X_train, y_train)
  predict_raw(X) -> np.ndarray  (uncalibrated probabilities)

After fit, apply src.calibration.platt.fit_platt on validation set,
then evaluate with src.evaluation.metrics.compute_all_metrics on test set.

Follows identical train-only fitting protocol as src.models.train_models.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Any


# ── WoE + Logistic Regression ─────────────────────────────────────────────────

@dataclass
class WoELR:
    """
    Weight-of-Evidence binning (optbinning) followed by Logistic Regression.
    Fit on training data only; transform applied to val and test.
    """
    max_n_bins: int = 10
    min_bin_size: float = 0.05
    C: float = 1.0
    solver: str = "lbfgs"
    max_iter: int = 1000
    random_state: int = 42

    _binning: Any = field(default=None, init=False, repr=False)
    _lr: Any = field(default=None, init=False, repr=False)
    feature_names_: list = field(default_factory=list, init=False, repr=False)

    def fit(self, X: np.ndarray, y: np.ndarray,
            feature_names: list[str] | None = None) -> "WoELR":
        from optbinning import BinningProcess
        from sklearn.linear_model import LogisticRegression

        if feature_names is None:
            feature_names = [f"f{i}" for i in range(X.shape[1])]
        self.feature_names_ = feature_names

        self._binning = BinningProcess(
            variable_names=feature_names,
            max_n_bins=self.max_n_bins,
            min_bin_size=self.min_bin_size,
        )
        X_woe = self._binning.fit_transform(X, y)

        self._lr = LogisticRegression(
            C=self.C, solver=self.solver,
            max_iter=self.max_iter, random_state=self.random_state
        )
        self._lr.fit(X_woe, y)
        return self

    def predict_raw(self, X: np.ndarray) -> np.ndarray:
        X_woe = self._binning.transform(X)
        return self._lr.predict_proba(X_woe)[:, 1]


# ── LightGBM ──────────────────────────────────────────────────────────────────

@dataclass
class LGBMModel:
    n_estimators: int = 300
    learning_rate: float = 0.05
    max_depth: int = 6
    num_leaves: int = 63
    min_child_samples: int = 20
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    random_state: int = 42
    n_jobs: int = -1
    verbose: int = -1

    _model: Any = field(default=None, init=False, repr=False)

    def fit(self, X: np.ndarray, y: np.ndarray, **kwargs) -> "LGBMModel":
        from lightgbm import LGBMClassifier
        self._model = LGBMClassifier(
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            max_depth=self.max_depth,
            num_leaves=self.num_leaves,
            min_child_samples=self.min_child_samples,
            subsample=self.subsample,
            colsample_bytree=self.colsample_bytree,
            random_state=self.random_state,
            n_jobs=self.n_jobs,
            verbose=self.verbose,
        )
        self._model.fit(X, y)
        return self

    def predict_raw(self, X: np.ndarray) -> np.ndarray:
        return self._model.predict_proba(X)[:, 1]


# ── CatBoost ──────────────────────────────────────────────────────────────────

@dataclass
class CatBoostModel:
    iterations: int = 300
    learning_rate: float = 0.05
    depth: int = 6
    random_state: int = 42
    verbose: int = 0

    _model: Any = field(default=None, init=False, repr=False)

    def fit(self, X: np.ndarray, y: np.ndarray, **kwargs) -> "CatBoostModel":
        from catboost import CatBoostClassifier
        self._model = CatBoostClassifier(
            iterations=self.iterations,
            learning_rate=self.learning_rate,
            depth=self.depth,
            random_state=self.random_state,
            verbose=self.verbose,
            allow_writing_files=False,
        )
        self._model.fit(X, y)
        return self

    def predict_raw(self, X: np.ndarray) -> np.ndarray:
        return self._model.predict_proba(X)[:, 1]


# ── Factory ───────────────────────────────────────────────────────────────────

def make_baseline(name: str, cfg: dict):
    """
    Create a baseline model from benchmarks.yaml config.

    name: "woe_logreg" | "lgbm" | "catboost"
    """
    if name == "woe_logreg":
        c = cfg["woe_logreg"]
        return WoELR(
            max_n_bins=c["max_n_bins"],
            min_bin_size=c["min_bin_size"],
            C=c["C"], solver=c["solver"],
            max_iter=c["max_iter"], random_state=c["random_state"],
        )
    if name == "lgbm":
        c = cfg["lightgbm"]
        return LGBMModel(
            n_estimators=c["n_estimators"],
            learning_rate=c["learning_rate"],
            max_depth=c["max_depth"],
            num_leaves=c["num_leaves"],
            min_child_samples=c["min_child_samples"],
            subsample=c["subsample"],
            colsample_bytree=c["colsample_bytree"],
            random_state=c["random_state"],
            n_jobs=c.get("n_jobs", -1),
            verbose=c.get("verbose", -1),
        )
    if name == "catboost":
        c = cfg["catboost"]
        return CatBoostModel(
            iterations=c["iterations"],
            learning_rate=c["learning_rate"],
            depth=c["depth"],
            random_state=c["random_state"],
            verbose=c.get("verbose", 0),
        )
    raise ValueError(f"Unknown baseline: {name!r}")
