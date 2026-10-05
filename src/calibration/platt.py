"""
Platt calibration — own implementation, no dependence on version-sensitive
scikit-learn calibration APIs (TECH_DOC §12).

Platt scaling: p_cal = σ(A · logit(p_raw) + B)
  A, B fitted by maximum likelihood on the VALIDATION set only.
  Implementation: 1-D logistic regression on logit(clip(p, eps, 1-eps)).

Why Platt over isotonic (§12):
  5,000 validation applicants with ~15% positives → isotonic overfitting risk.

SEPARATION (§3):
  Calibration is fit on VALIDATION set → never sees test rows.
  τ is also fit on validation.
  g0_seed is UNRELATED to Platt (it seeds Gate G0 only).
"""
from __future__ import annotations

import numpy as np


_CLIP_EPS = 1e-6


class PlattCalibrator:
    """
    Platt calibration model.
    Fit on validation set; transform applied to any split.
    """

    def __init__(self, clip_eps: float = _CLIP_EPS):
        self.clip_eps = clip_eps
        self.A: float | None = None
        self.B: float | None = None
        self._fitted = False

    # ── Fit ───────────────────────────────────────────────────────────────────

    def fit(self, p_raw: np.ndarray, y: np.ndarray) -> "PlattCalibrator":
        """
        Fit Platt calibration on raw scores and true labels (validation set).

        Parameters
        ----------
        p_raw : raw probability scores (before calibration), shape (n,)
        y     : true binary labels, shape (n,)
        """
        p = np.clip(np.asarray(p_raw, dtype=np.float64), self.clip_eps, 1 - self.clip_eps)
        y = np.asarray(y, dtype=np.float64)

        # logit transform of raw scores
        logits = np.log(p / (1.0 - p))

        # Fit 1-D logistic regression: y ~ sigmoid(A * logit + B)
        # Minimise log-loss via scipy optimize
        from scipy.optimize import minimize

        def neg_log_likelihood(params: np.ndarray) -> float:
            A, B = params
            z = A * logits + B
            # Numerically stable log-sigmoid
            log_p = -np.logaddexp(0, -z)
            log_1mp = -np.logaddexp(0, z)
            return -float(np.sum(y * log_p + (1 - y) * log_1mp))

        result = minimize(
            neg_log_likelihood,
            x0=np.array([1.0, 0.0]),
            method="L-BFGS-B",
        )
        self.A, self.B = float(result.x[0]), float(result.x[1])
        self._fitted = True
        return self

    # ── Transform ─────────────────────────────────────────────────────────────

    def transform(self, p_raw: np.ndarray) -> np.ndarray:
        """
        Apply calibration to raw scores.

        p_cal = σ(A · logit(p_raw) + B)

        Returns calibrated probabilities in (0, 1).
        """
        if not self._fitted:
            raise RuntimeError("PlattCalibrator must be fitted before transform.")
        p = np.clip(np.asarray(p_raw, dtype=np.float64), self.clip_eps, 1 - self.clip_eps)
        logits = np.log(p / (1.0 - p))
        z = self.A * logits + self.B
        return _sigmoid(z)

    # ── Convenience: fit_transform ────────────────────────────────────────────

    def fit_transform(self, p_raw: np.ndarray, y: np.ndarray) -> np.ndarray:
        return self.fit(p_raw, y).transform(p_raw)

    def __repr__(self) -> str:
        if self._fitted:
            return f"PlattCalibrator(A={self.A:.4f}, B={self.B:.4f})"
        return "PlattCalibrator(unfitted)"


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-z))


# ── Convenience functions ──────────────────────────────────────────────────────

def fit_platt(p_raw_val: np.ndarray, y_val: np.ndarray) -> PlattCalibrator:
    """Fit a PlattCalibrator on validation scores and labels."""
    cal = PlattCalibrator()
    cal.fit(p_raw_val, y_val)
    return cal
