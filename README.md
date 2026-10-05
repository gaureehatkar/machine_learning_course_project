# Policy-Constrained Credit Decisioning with Evidence-Quality Gating
### For Thin-File Gig/Platform Workers — Research Prototype v1.2

> **Architecture frozen. Implementation follows IMPLEMENTATION_PLAN.md v1.2.**
> G0 is the next gate — currently BLOCKED on two human-set thresholds and licence confirmation.

---

## What this project does

Three separate layers combined into one credit decision:

1. **Risk layer** — LR + XGBoost estimates probability of default from 12 financial features
2. **Evidence layer** — scores whether history and data completeness are sufficient to trust the estimate  
3. **Policy layer** — deterministic Kleene three-valued evaluation of JanSamarth/PMMY eligibility rules

Decision engine combines them → **APPROVE / REVIEW / DECLINE** with reason codes and SHAP explanations.

```
RISK ≠ EVIDENCE QUALITY ≠ POLICY ELIGIBILITY
```

---

## Quick start

```bash
# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
pytest tests/ -v

# Run Home Credit authentic experiment (T1)
python -m experiments.authentic.run --config configs/models.yaml

# Generate synthetic data (g0_seed only — for testing)
python -m src.data_generation.generate_data --config configs/experiment.yaml --dgp 1 --seed 0

# Build features
python -m src.feature_engineering.build_features --config configs/experiment.yaml --dgp 1 --seed 0 --view full

# Run Streamlit demo
streamlit run app/main.py
```

---

## Data

| Dataset | Location | Status |
|---|---|---|
| Home Credit `application_train.csv` | `data/authentic/` | ✅ Present |
| Afsharinia & Gurtoo gig-worker survey | `data/authentic/` | ✅ Present |
| SynthGigCredit-IN-v1 (generated) | `data/synthetic/` | Generate with `make generate` |

**Dataset 2 freeze record:** `docs/dataset2_freeze.md`

---

## Gate G0 — status: BLOCKED

Before G0 can run you must:
1. Confirm licence on https://data.mendeley.com/datasets/j6hd2dfsh8/1 and update `configs/experiment.yaml`
2. Set `g0.max_roc_auc` in `configs/experiment.yaml` (e.g. 0.97)
3. Set `g0.policy_corr_tol` in `configs/experiment.yaml` (e.g. 0.05)

Then run: `python -m src.data_validation.gate_g0 --config configs/experiment.yaml`

---

## Policy rules — status: UNVERIFIED

All policy rule content in `configs/policy_rules/` is **UNVERIFIED placeholder**.
Task 10b: verify current JanSamarth/PMMY documents and replace.
See `docs/policy_rule_verification.md`.

---

## Project structure

```
src/
  data_generation/    # SynthGigCredit-IN-v1 DGP generator
  feature_engineering/# 23-column feature builder (sets A, B, C)
  evidence/           # Evidence score E = 0.5·H/12 + 0.25·AA + 0.25·ULI
  policy/             # Kleene rule engine + loader + versioning
  models/             # LR + XGBoost + Platt calibration
  decisions/          # D1-D4 gating + tau selection + review allocation
  evaluation/         # Metrics + bootstrap + seed-level CIs
  explainability/     # TreeSHAP + explanation JSON
  data_validation/    # Gate G0
experiments/
  authentic/          # Home Credit T1
  ablation/           # A/B/C feature sets T2
  gating/             # D1-D4 T3
  review/             # Review allocation T4/T5
  history/            # Forced-H experiment T6
app/
  main.py             # Streamlit demo
configs/
  experiment.yaml     # All parameters
  models.yaml         # Model hyperparameters
  policy_rules/       # UNVERIFIED rule fixtures
docs/
  dataset2_freeze.md  # Dataset 2 freeze record
tests/                # pytest suite
```

---

## Claim boundary

All synthetic results are **simulation evidence under stated assumptions** — not real-world lending performance.
The Home Credit experiment validates the modelling pipeline on authentic credit data.
