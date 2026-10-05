"""Run manifest — records git commit, config hash, package versions, seeds, data SHA-256."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import subprocess
import time
from pathlib import Path
from typing import Any


_TRACKED_PACKAGES = [
    "numpy", "pandas", "scikit-learn", "xgboost", "shap",
    "pyarrow", "pyyaml", "scipy", "statsmodels", "streamlit",
    "plotly", "matplotlib", "seaborn", "pytest",
]


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def _package_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for pkg in _TRACKED_PACKAGES:
        try:
            versions[pkg] = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            versions[pkg] = "not_installed"
    return versions


def file_sha256(path: str | Path) -> str:
    path = Path(path)
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(
    run_id: str,
    cfg: dict[str, Any],
    cfg_hash: str,
    data_files: list[str | Path],
    extra: dict[str, Any] | None = None,
) -> Path:
    """Write results/<run_id>/run_manifest.json and return the path."""
    out_dir = Path("results") / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "run_id": run_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_commit": _git_commit(),
        "config_hash": cfg_hash,
        "package_versions": _package_versions(),
        "data_files": {str(p): file_sha256(p) for p in data_files if Path(p).exists()},
    }
    if extra:
        manifest.update(extra)

    manifest_path = out_dir / "run_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, default=str)
    return manifest_path
