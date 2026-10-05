"""Configuration loader — reads and validates YAML configs, enforces critical assertions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


def load_config(path: str | Path) -> dict[str, Any]:
    """Load a YAML config file and return as a dict."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    _validate_experiment_config(cfg)
    return cfg


def _validate_experiment_config(cfg: dict[str, Any]) -> None:
    """Assert critical invariants from the spec."""
    if "data" not in cfg:
        return  # models.yaml — no assertions needed

    data = cfg["data"]
    g0_seed = data.get("g0_seed", 0)
    seeds = data.get("seeds", [])

    # Assertion: g0_seed must NOT be in the experimental seeds list
    assert g0_seed not in seeds, (
        f"g0_seed ({g0_seed}) must not appear in data.seeds {seeds}. "
        "g0_seed is reserved for Gate G0 validation only."
    )

    # Assertion: policy_effect_delta must be 0 in all main-study runs
    delta = cfg.get("dgp", {}).get("policy_effect_delta", 0.0)
    assert delta == 0.0, (
        f"policy_effect_delta must be 0.0 in all main-study runs, got {delta}. "
        "Set it only in experiments/methodology_validation/."
    )


def config_hash(cfg: dict[str, Any]) -> str:
    """Return a SHA-256 hex digest of the config (for run manifests)."""
    serialised = json.dumps(cfg, sort_keys=True, default=str)
    return hashlib.sha256(serialised.encode()).hexdigest()


def get_output_dir(cfg: dict[str, Any], dgp_id: int, seed: int) -> Path:
    """Return the output directory for a given DGP / seed pair."""
    base = Path(cfg["data"].get("output_dir", "data/synthetic"))
    return base / f"dgp{dgp_id}" / f"seed{seed}"
