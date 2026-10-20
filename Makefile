.PHONY: all reproduce phase1 phase2 phase3 phase4 phase5 phase6 phase7 phase8 phase9 phase10 test figures tables audit clean lock

all: reproduce

# Regenerate benchmark artifacts without changing the original T1–T9 tables.
reproduce: phase10

phase1:
	python -u research/phase1_preflight_and_t1.py
	python -u research/recompute_t2_t6_v2.py
	python -u research/save_t2_t6_npz_and_update_calibration.py
	pytest -q

phase2: phase1
	python -u research/generate_policy_truth.py
	python -u research/run_phase2_policy_v2.py
	pytest -q

phase3: phase2
	python -u research/run_phase3_diagnostics.py
	pytest -q

phase4: phase3
	python -u research/phase4_matched_coverage.py
	pytest -q

phase5: phase4
	python -u research/run_phase5_risk_baselines.py
	pytest -q

phase6: phase5
	python -u research/run_phase6_architecture_and_policy.py
	pytest -q

phase7: phase6
	python -u research/run_phase7_review_baselines.py
	pytest -q

phase8: phase7
	python -u research/run_phase8_statistical_tests.py
	pytest -q

phase9: phase8
	python -u research/make_figures.py
	python -u research/make_paper_tables.py
	python -u research/write_phase9_report.py
	pytest -q

phase10: phase9
	python -u scripts/check_forbidden_claims.py
	pytest -q
	python -u research/write_phase10_report.py

figures:
	python -u research/make_figures.py

tables:
	python -u research/make_paper_tables.py

test:
	pytest -v

audit:
	python -u scripts/check_forbidden_claims.py

lock:
	pip freeze > requirements.lock
