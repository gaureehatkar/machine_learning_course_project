"""
Risk Model Baselines for SynthGigCredit Benchmarking.
Implements:
  1. WoE-LR (OptBinning BinningProcess + LogisticRegression)
  2. LightGBM (LGBMClassifier)
  3. CatBoost (CatBoostClassifier)
  4. Random Forest (SimpleImputer + RandomForestClassifier)
  5. XGBoost (XGBClassifier)

Provides model factory, hyperparameter search spaces, and prediction wrappers.
"""
from __future__ import annotations
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from typing import Any
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from optbinning import BinningProcess
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier
from catboost import CatBoostClassifier


class WoELogisticRegression(BaseEstimator, ClassifierMixin):
    """OptBinning BinningProcess + LogisticRegression wrapper."""
    def __init__(self, C: float = 1.0, max_iter: int = 1000, random_state: int = 42):
        self.C = C
        self.max_iter = max_iter
        self.random_state = random_state
        self.binning_process = None
        self.clf = None
        self.feature_names_ = None

    def fit(self, X: np.ndarray | pd.DataFrame, y: np.ndarray) -> "WoELogisticRegression":
        if isinstance(X, pd.DataFrame):
            self.feature_names_ = list(X.columns)
            X_df = X
        else:
            self.feature_names_ = [f"f_{i}" for i in range(X.shape[1])]
            X_df = pd.DataFrame(X, columns=self.feature_names_)

        self.binning_process = BinningProcess(
            variable_names=self.feature_names_,
            max_n_bins=5,
            min_prebin_size=0.05,
        )
        X_woe = self.binning_process.fit_transform(X_df, y)
        self.clf = LogisticRegression(
            C=self.C,
            max_iter=self.max_iter,
            random_state=self.random_state,
            solver="lbfgs",
        )
        self.clf.fit(X_woe, y)
        return self

    def predict_proba(self, X: np.ndarray | pd.DataFrame) -> np.ndarray:
        if isinstance(X, pd.DataFrame):
            X_df = X[self.feature_names_]
        else:
            X_df = pd.DataFrame(X, columns=self.feature_names_)
        X_woe = self.binning_process.transform(X_df)
        return self.clf.predict_proba(X_woe)

    def predict(self, X: np.ndarray | pd.DataFrame) -> np.ndarray:
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)


class RandomForestBaseline(BaseEstimator, ClassifierMixin):
    """Median Imputer + Random Forest Classifier."""
    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int | None = 6,
        min_samples_split: int = 5,
        max_features: Any = "sqrt",
        random_state: int = 42,
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.max_features = max_features
        self.random_state = random_state
        self.pipeline = None

    def fit(self, X: np.ndarray | pd.DataFrame, y: np.ndarray) -> "RandomForestBaseline":
        X_arr = X.values if isinstance(X, pd.DataFrame) else np.asarray(X)
        rf = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            max_features=self.max_features,
            random_state=self.random_state,
            n_jobs=1,
        )
        self.pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("rf", rf),
        ])
        self.pipeline.fit(X_arr, y)
        return self

    def predict_proba(self, X: np.ndarray | pd.DataFrame) -> np.ndarray:
        X_arr = X.values if isinstance(X, pd.DataFrame) else np.asarray(X)
        return self.pipeline.predict_proba(X_arr)

    def predict(self, X: np.ndarray | pd.DataFrame) -> np.ndarray:
        X_arr = X.values if isinstance(X, pd.DataFrame) else np.asarray(X)
        return self.pipeline.predict(X_arr)


# ── Model Factory ─────────────────────────────────────────────────────────────

def get_baseline_model(family: str, params: dict | None = None, seed: int = 42):
    p = params.copy() if params else {}
    family = family.lower()

    if family in ("lr", "logreg", "logistic_regression"):
        return Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("lr", LogisticRegression(
                C=p.get("C", 1.0),
                max_iter=p.get("max_iter", 1000),
                solver=p.get("solver", "lbfgs"),
                random_state=seed,
            )),
        ])

    if family in ("woe_lr", "woe-lr", "scorecard"):
        c_val = p.get("C", 1.0)
        return WoELogisticRegression(C=c_val, random_state=seed)

    elif family in ("rf", "random_forest"):
        return RandomForestBaseline(
            n_estimators=p.get("n_estimators", 100),
            max_depth=p.get("max_depth", 6),
            min_samples_split=p.get("min_samples_split", 5),
            max_features=p.get("max_features", "sqrt"),
            random_state=seed,
        )

    elif family in ("lgbm", "lightgbm"):
        return LGBMClassifier(
            n_estimators=p.get("n_estimators", 100),
            max_depth=p.get("max_depth", 4),
            learning_rate=p.get("learning_rate", 0.1),
            num_leaves=p.get("num_leaves", 31),
            subsample=p.get("subsample", 0.8),
            subsample_freq=1,
            colsample_bytree=p.get("colsample_bytree", 0.8),
            random_state=seed,
            n_jobs=1,
            verbose=-1,
        )

    elif family in ("catboost", "cat"):
        return CatBoostClassifier(
            iterations=p.get("iterations", 100),
            depth=p.get("depth", 4),
            learning_rate=p.get("learning_rate", 0.1),
            l2_leaf_reg=p.get("l2_leaf_reg", 3.0),
            random_seed=seed,
            verbose=False,
            thread_count=1,
        )

    elif family in ("xgb", "xgboost"):
        return XGBClassifier(
            n_estimators=p.get("n_estimators", 100),
            max_depth=p.get("max_depth", 4),
            learning_rate=p.get("learning_rate", 0.1),
            subsample=p.get("subsample", 0.8),
            colsample_bytree=p.get("colsample_bytree", 0.8),
            random_state=seed,
            n_jobs=1,
            eval_metric="logloss",
        )
    else:
        raise ValueError(f"Unknown baseline model family: {family}")


# ── Hyperparameter Search Spaces ──────────────────────────────────────────────

SEARCH_SPACES = {
    "lr": {
        "C": [0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    },
    "woe_lr": {
        "C": [0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    },
    "rf": {
        "n_estimators": [50, 100],
        "max_depth": [4, 6],
        "min_samples_split": [5, 10],
        "max_features": ["sqrt", "log2"],
    },
    "lgbm": {
        "n_estimators": [50, 100, 150],
        "max_depth": [3, 4, 6],
        "learning_rate": [0.03, 0.05, 0.1],
        "num_leaves": [15, 31],
        "subsample": [0.8, 1.0],
        "colsample_bytree": [0.8, 1.0],
    },
    "catboost": {
        "iterations": [50, 100, 150],
        "depth": [3, 4, 6],
        "learning_rate": [0.03, 0.05, 0.1],
        "l2_leaf_reg": [1.0, 3.0, 5.0],
    },
    "xgb": {
        "n_estimators": [50, 100, 150],
        "max_depth": [3, 4, 6],
        "learning_rate": [0.03, 0.05, 0.1],
        "subsample": [0.8, 1.0],
        "colsample_bytree": [0.8, 1.0],
    },
}


def sample_hyperparameters(
    family: str,
    n_iter: int = 30,
    seed: int = 42,
    search_space: dict[str, list] | None = None,
) -> list[dict]:
    """Deterministically draw parameter dictionaries from a supplied search space."""
    rng = np.random.RandomState(seed)
    space = search_space if search_space is not None else SEARCH_SPACES[family]
    samples = []
    keys = sorted(space.keys())

    for _ in range(n_iter):
        draw = {}
        for k in keys:
            vals = space[k]
            idx = rng.randint(0, len(vals))
            draw[k] = vals[idx]
        samples.append(draw)
    return samples


def get_tuned_params(
    tuned: dict,
    dataset: str,
    family: str,
    feature_set: str = "C",
) -> dict:
    """Read both feature-set-specific v2 parameters and earlier flat caches."""
    if dataset not in tuned:
        raise KeyError(f"No tuned parameters found for dataset {dataset!r}")
    dataset_params = tuned[dataset]
    if feature_set in dataset_params and family in dataset_params[feature_set]:
        result = dataset_params[feature_set][family].get("best_params")
        if result is None:
            raise KeyError(
                f"Missing best_params for {dataset}/{feature_set}/{family}"
            )
        return result
    if family in dataset_params:
        result = dataset_params[family].get("best_params")
        if result is None:
            raise KeyError(f"Missing best_params for {dataset}/{family}")
        return result
    raise KeyError(
        f"No tuned parameters found for {dataset}/{feature_set}/{family}"
    )
