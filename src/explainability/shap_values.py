"""
SHAP explainability (TECH_DOC §16.6, ARCHITECTURE Diagram 10)

TreeSHAP on XGBoost-C (feature set C, test set only).
Global: mean|SHAP| per feature.
Local: SHAP values for individual applicants.

For Logistic Regression: use coefficient-based explanations (see lr_coefficients.py).

Post-hoc only. Explanation output is for the demo and report — not a risk decision.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.models.train_models import FittedModel
from src.feature_engineering.build_features import FEATURE_SET_C


def compute_shap_values(
    fitted_model: FittedModel,
    features_df: pd.DataFrame,
) -> np.ndarray:
    """
    Compute TreeSHAP values for XGBoost model.

    Parameters
    ----------
    fitted_model : FittedModel with family="xgb"
    features_df  : feature table rows to explain

    Returns
    -------
    shap_values : np.ndarray of shape (n_applicants, n_features)
    """
    try:
        import shap
    except ImportError:
        raise ImportError("shap package required: pip install shap")

    if fitted_model.family != "xgb":
        raise ValueError(
            "TreeSHAP is implemented for XGBoost only. "
            "For Logistic Regression, use get_lr_coefficients() from lr_coefficients module."
        )

    X = features_df[fitted_model.feature_cols].values.astype(np.float64)
    explainer = shap.TreeExplainer(fitted_model.model)
    shap_vals = explainer.shap_values(X)
    return shap_vals


def global_shap_summary(
    shap_values: np.ndarray,
    feature_cols: list[str],
) -> pd.DataFrame:
    """
    Global feature importance: mean |SHAP value| per feature.
    Returns DataFrame sorted by importance descending.
    """
    mean_abs = np.abs(shap_values).mean(axis=0)
    return (
        pd.DataFrame({"feature": feature_cols, "mean_abs_shap": mean_abs})
        .sort_values("mean_abs_shap", ascending=False)
        .reset_index(drop=True)
    )


def local_shap_explanation(
    shap_values: np.ndarray,
    features_df: pd.DataFrame,
    applicant_idx: int,
    feature_cols: list[str],
    top_n: int = 5,
) -> list[dict]:
    """
    Local SHAP explanation for one applicant.
    Returns top_n features sorted by |SHAP| descending.
    """
    shap_row = shap_values[applicant_idx]
    sorted_idx = np.argsort(np.abs(shap_row))[::-1][:top_n]
    results = []
    for i in sorted_idx:
        results.append({
            "feature": feature_cols[i],
            "shap": float(shap_row[i]),
            "value": float(features_df.iloc[applicant_idx][feature_cols[i]]),
        })
    return results
