.PHONY: setup test generate gate features train calibrate decisions evaluate demo all clean

PYTHON = python
CONFIG = configs/experiment.yaml
DGP ?= 1
SEED ?= 1

setup:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest tests/ -v --tb=short

# ── Data generation ────────────────────────────────────────────────────────────
generate:
	$(PYTHON) -m src.data_generation.generate --config $(CONFIG) --dgp $(DGP) --seed $(SEED)

generate-g0:
	$(PYTHON) -m src.data_generation.generate --config $(CONFIG) --dgp 1 --seed 0
	$(PYTHON) -m src.data_generation.generate --config $(CONFIG) --dgp 2 --seed 0

generate-all:
	@for dgp in 1 2; do \
		for seed in 0 1 2 3 4 5 6 7 8 9 10; do \
			$(PYTHON) -m src.data_generation.generate --config $(CONFIG) --dgp $$dgp --seed $$seed; \
		done; \
	done

# ── Gate G0 ────────────────────────────────────────────────────────────────────
gate:
	$(PYTHON) -m src.data_validation.gate_g0 --config $(CONFIG)

# ── Features ───────────────────────────────────────────────────────────────────
features:
	$(PYTHON) -m src.feature_engineering.build --config $(CONFIG) --dgp $(DGP) --seed $(SEED) --view full
	$(PYTHON) -m src.feature_engineering.build --config $(CONFIG) --dgp $(DGP) --seed $(SEED) --view visible

features-all:
	@for dgp in 1 2; do \
		for seed in 1 2 3 4 5 6 7 8 9 10; do \
			$(PYTHON) -m src.feature_engineering.build --config $(CONFIG) --dgp $$dgp --seed $$seed --view full; \
			$(PYTHON) -m src.feature_engineering.build --config $(CONFIG) --dgp $$dgp --seed $$seed --view visible; \
		done; \
	done

# ── Experiments ────────────────────────────────────────────────────────────────
authentic:
	$(PYTHON) -m experiments.authentic.run --config configs/models.yaml

ablation:
	$(PYTHON) -m experiments.ablation.run --config $(CONFIG) --dgp $(DGP) --seed $(SEED)

gating:
	$(PYTHON) -m experiments.gating.run --config $(CONFIG) --dgp $(DGP) --seed $(SEED)

review:
	$(PYTHON) -m experiments.review.run --config $(CONFIG) --dgp $(DGP) --seed $(SEED)

history:
	$(PYTHON) -m experiments.history.run --config $(CONFIG) --dgp $(DGP) --seed $(SEED)

fairness:
	$(PYTHON) -m experiments.fairness.run --config $(CONFIG) --dgp $(DGP) --seed $(SEED)

# ── Aggregate results ──────────────────────────────────────────────────────────
evaluate:
	$(PYTHON) -m src.evaluation.aggregate --config $(CONFIG)

# ── Demo ───────────────────────────────────────────────────────────────────────
demo:
	streamlit run app/main.py

# ── Full pipeline ──────────────────────────────────────────────────────────────
all: generate-all gate features-all ablation gating review history fairness evaluate

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache
