"""
Logistic Regression Explainability — Coefficients and Odds Ratios

Provides interpretable LR explanations:
  - Model coefficients (log-odds per unit feature change)
  - Odds ratios (exp(coefficient)) — multiplicative change in odds
  - Feature contributions (coefficient × feature value)
  - Calibrated predictions and contribution ranking

TECH_DOC §16.5: LR explainability exports coefficients, not SHAP.
Works ONLY with Logistic Regression (family='logreg').
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.models.train_models import FittedModel


def get_lr_coefficients(fitted_model: FittedModel) -> pd.DataFrame:
    """
    Extract LR coefficients and compute odds ratios.
    
    Parameters
    ----------
    fitted_model : FittedModel with family='logreg'
    
    Returns
    -------
    coefficients_df : DataFrame with columns:
      - feature: feature name
      - coefficient: log-odds (β in logit)
      - odds_ratio: exp(β)
      - p_change_per_unit: approximate % change in probability per unit (for reference)
    """
    if fitted_model.family != "logreg":
        raise ValueError(
            f"LR coefficients only available for Logistic Regression. "
            f"Model family is {fitted_model.family!r}."
        )
    
    model = fitted_model.model
    feature_cols = fitted_model.feature_cols
    
    # Extract coefficients from the fitted LR model
    coeffs = model.coef_[0]  # shape (n_features,)
    intercept = model.intercept_[0]
    
    # Compute odds ratios (exp of coefficients)
    odds_ratios = np.exp(coeffs)
    
    # Approximate % change in probability per unit
    # For small changes: ΔP/ΔX ≈ β · P(Y=1) · (1-P(Y=1))
    # At population default rate ~15%: P(Y=1) ≈ 0.15
    # So ΔP/ΔX ≈ β · 0.15 · 0.85 ≈ β · 0.1275
    p_default = 0.15  # approximate population rate
    p_change_per_unit = coeffs * p_default * (1 - p_default)
    
    df = pd.DataFrame({
        "feature": feature_cols,
        "coefficient": coeffs,
        "odds_ratio": odds_ratios,
        "p_change_per_unit": p_change_per_unit,
    })
    
    # Sort by absolute coefficient magnitude
    df["abs_coeff"] = np.abs(df["coefficient"])
    df = df.sort_values("abs_coeff", ascending=False).drop(columns=["abs_coeff"])
    
    return df.reset_index(drop=True)


def get_intercept(fitted_model: FittedModel) -> float:
    """
    Get the intercept (bias term) from an LR model.
    
    Returns baseline log-odds (log(p/(1-p)) at mean feature values).
    """
    if fitted_model.family != "logreg":
        raise ValueError(
            f"LR intercept only available for Logistic Regression. "
            f"Model family is {fitted_model.family!r}."
        )
    return float(fitted_model.model.intercept_[0])


def compute_feature_contributions(
    fitted_model: FittedModel,
    applicant_features: pd.DataFrame | dict,
    top_n: int = 5,
) -> dict:
    """
    Compute feature contributions to log-odds for one applicant.
    
    Parameters
    ----------
    fitted_model : FittedModel with family='logreg'
    applicant_features : single row DataFrame or dict of feature values
    top_n : return top N features by absolute contribution
    
    Returns
    -------
    contributions : dict with:
      - "intercept": baseline log-odds
      - "features": list of top N contributions, each with:
        - "feature": feature name
        - "value": applicant's feature value
        - "coefficient": model coefficient
        - "contribution": coefficient × value (log-odds contribution)
        - "odds_ratio_contribution": exp(contribution)
    """
    if fitted_model.family != "logreg":
        raise ValueError(
            f"LR contributions only available for Logistic Regression. "
            f"Model family is {fitted_model.family!r}."
        )
    
    # Normalize input
    if isinstance(applicant_features, dict):
        applicant_features = pd.DataFrame([applicant_features])
    elif isinstance(applicant_features, pd.DataFrame):
        applicant_features = applicant_features.iloc[[0]]  # ensure single row
    
    model = fitted_model.model
    feature_cols = fitted_model.feature_cols
    intercept = model.intercept_[0]
    coeffs = model.coef_[0]
    
    # Extract feature values and preprocess (apply same scaler as training)
    X_raw = applicant_features[feature_cols].values.astype(np.float64)
    
    if fitted_model.preprocessor is not None:
        X_scaled = fitted_model.preprocessor.transform(X_raw)
        # For interpretation, we need to show the SCALED features
        feature_values = X_scaled[0]
    else:
        # XGBoost case shouldn't happen here, but handle it
        feature_values = X_raw[0]
    
    # Compute contributions
    contributions = coeffs * feature_values
    sorted_idx = np.argsort(np.abs(contributions))[::-1][:top_n]
    
    result = {
        "intercept": float(intercept),
        "features": [
            {
                "feature": feature_cols[i],
                "value": float(feature_values[i]),
                "coefficient": float(coeffs[i]),
                "contribution": float(contributions[i]),
                "odds_ratio_contribution": float(np.exp(contributions[i])),
            }
            for i in sorted_idx
        ],
        "total_log_odds": float(intercept + contributions.sum()),
    }
    
    return result


def lr_explanation(
    fitted_model: FittedModel,
    applicant_id: str,
    features_df: pd.DataFrame,
    applicant_idx: int,
    top_n: int = 5,
) -> dict:
    """
    Generate a complete LR explanation for one applicant.
    
    Parameters
    ----------
    fitted_model : FittedModel with family='logreg'
    applicant_id : identifier string
    features_df : feature DataFrame (for extracting applicant row)
    applicant_idx : row index in features_df
    top_n : top N features to report
    
    Returns
    -------
    explanation : dict with:
      - "model": "logreg"
      - "applicant_id": applicant_id
      - "coefficients": global LR coefficients (top N by magnitude)
      - "contributions": applicant-specific contributions (top N)
      - "predicted_pd": raw PD from the model
    """
    if fitted_model.family != "logreg":
        raise ValueError(
            f"LR explanation only available for Logistic Regression. "
            f"Model family is {fitted_model.family!r}."
        )
    
    # Get coefficients
    coeffs_df = get_lr_coefficients(fitted_model)
    top_coeffs = coeffs_df.head(top_n).to_dict("records")
    
    # Get applicant-specific contributions
    applicant_row = features_df.iloc[[applicant_idx]]
    contribs = compute_feature_contributions(fitted_model, applicant_row, top_n=top_n)
    
    # Get predicted PD
    predicted_pd = float(fitted_model.predict_raw(applicant_row)[0])
    
    return {
        "model": "logreg",
        "applicant_id": applicant_id,
        "predicted_pd": round(predicted_pd, 4),
        "top_coefficients": top_coeffs,
        "feature_contributions": contribs["features"],
        "total_log_odds": round(contribs["total_log_odds"], 4),
        "intercept": round(contribs["intercept"], 4),
    }
