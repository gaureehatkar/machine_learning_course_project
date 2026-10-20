import numpy as np
import pandas as pd
import pytest

from src.benchmarks.risk_baselines import (
    get_baseline_model,
    get_tuned_params,
    sample_hyperparameters,
)


def test_lr_baseline_imputes_missing_values():
    X = pd.DataFrame({"income": [1.0, np.nan, 3.0, 4.0], "age": [20, 30, np.nan, 50]})
    y = np.array([0, 0, 1, 1])
    model = get_baseline_model("lr", seed=7)

    model.fit(X, y)

    probabilities = model.predict_proba(X)[:, 1]
    assert np.isfinite(probabilities).all()
    assert ((probabilities >= 0) & (probabilities <= 1)).all()


def test_tuned_parameter_lookup_supports_feature_sets_and_legacy_cache():
    tuned = {
        "dgp1": {
            "A": {"lr": {"best_params": {"C": 0.1}}},
            "C": {"lr": {"best_params": {"C": 1.0}}},
        },
        "dgp2": {"lr": {"best_params": {"C": 2.0}}},
    }

    assert get_tuned_params(tuned, "dgp1", "lr", "A") == {"C": 0.1}
    assert get_tuned_params(tuned, "dgp1", "lr", "C") == {"C": 1.0}
    assert get_tuned_params(tuned, "dgp2", "lr", "C") == {"C": 2.0}
    with pytest.raises(KeyError, match="No tuned parameters found"):
        get_tuned_params(tuned, "missing", "lr")


def test_hyperparameter_sampler_returns_requested_trial_count():
    candidates = sample_hyperparameters(
        "lr", n_iter=30, seed=12, search_space={"C": [0.1, 1.0]}
    )

    assert len(candidates) == 30
    assert all(set(candidate) == {"C"} for candidate in candidates)
