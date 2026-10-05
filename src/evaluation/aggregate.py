"""
Aggregate all per-seed results into summary tables T1–T10.
Usage: python -m src.evaluation.aggregate --config configs/experiment.yaml
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from src.utils.config_loader import load_config
from src.evaluation.evaluate import aggregate_over_seeds


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiment.yaml")
    args = parser.parse_args()
    cfg = load_config(args.config)

    print("Aggregating results...")
    agg = aggregate_over_seeds(cfg)

    out_path = Path("results/summary.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as fh:
        json.dump(agg, fh, indent=2)
    print(f"Summary written to {out_path}")

    # Print table
    for dgp_key, models in agg.items():
        print(f"\n=== {dgp_key} ===")
        print(f"{'Model':<20} {'ROC-AUC':>10} {'95% CI':>20} {'Seeds':>6}")
        print("-" * 58)
        for model, m in models.items():
            ci = f"[{m['roc_auc_ci_lo']:.4f}, {m['roc_auc_ci_hi']:.4f}]"
            print(f"{model:<20} {m['roc_auc_mean']:>10.4f} {ci:>20} {m['n_seeds']:>6}")


if __name__ == "__main__":
    main()
