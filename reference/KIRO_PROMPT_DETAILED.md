# KIRO PROMPT — SynthGigCredit-IN: Make the Paper Submission-Ready

You are working in the repository `machine_learning_course_project` (SynthGigCredit-IN: policy-constrained credit decisioning for thin-file gig workers in India). Experiments T1–T9 already exist. Your job is to (1) fix known problems, (2) run the benchmark and baseline experiments, (3) fix the statistics, (4) generate figures and paper tables, and (5) produce documentation and reproducibility artifacts — so the research paper can be written entirely from measured numbers.

Work **phase by phase**. After every phase write a report (format in §3), then continue unless an acceptance check fails. If an acceptance check fails, **stop and report**. If something is missing or ambiguous (a column, a file, a rule), **stop and ask — never guess or invent**.

---

## 0. Ground rules (apply to every phase)

1. **Never modify or overwrite existing result files**: `results/authentic/T1_results.json`, `research/tables/T2_*.csv … T9_*.csv`, `results/gate_g0_report.json`, existing `predictions_*.npz`. Write everything new to `results/benchmarks/` and `research/tables/benchmarks/` (subfolders per phase). Never edit existing synthetic datasets; verify with file hashes (§Phase 1 preflight).
2. **Same protocol as existing experiments**: fit on train only; Platt-calibrate on validation only; select τ on validation only; touch the test set once per experiment; stratified 60/20/20 split with `split_seed = 1000 + dataset_seed`; Home Credit split seed 42; synthetic seeds 1–10 × DGP1/DGP2 (seed 0 is the G0 seed and is **not** an experimental seed — it may be used for hyperparameter tuning only, see Phase 5). Train on `features_full`, validate/test on `features_visible`.
3. **Statistics**: mean ± 95% CI across seeds using `scipy.stats.t.ppf(0.975, n-1)` computed from n. Never hardcode 2.262. Paired seed-level tests for comparisons (Phase 8).
4. **No expected results in code, comments, docs or reports.** Older prompts predicted outcomes (e.g., "D4 still has lower default rate at matched coverage", "baselines will have 21% capture"). **Ignore all such predictions.** Report whatever the runs show, in either direction. If a baseline matches or beats the proposed method, say so plainly.
5. **Never invent numbers, rules, columns or citations.** If a run fails or data is missing, say why and what is needed.
6. **All hyperparameters and settings go in YAML** under `configs/` (extend `configs/benchmarks.yaml`; add `configs/policy_rules/v2/`). Every run writes a manifest JSON (git commit, config hash, seeds, package versions, timestamp, command) next to its outputs.
7. **Tests**: keep the existing tests (121) passing; add unit tests for every new function. Run the full suite at the end of every phase.
8. **Deterministic**: fixed seeds everywhere; same command → same outputs.
9. **Aggregated table schema** (all new CSVs): `dataset, dgp, method, metric, n, mean, std, ci95, ci_lo, ci_hi`. Per-seed raw table alongside every aggregate (`*_per_seed.csv`).

### Existing code to reuse (do not rewrite)
`src/evaluation/metrics.py` (15 metrics incl. Gini, KS, **logistic** calibration slope), `src/calibration/platt.py`, `src/decisions/{gate,review,tau}.py`, `src/policy/*` (Kleene engine, loader, versioning), `src/benchmarks/risk_baselines.py` (WoELR, LGBMModel, CatBoostModel — written, never run), `src/benchmarks/abstention.py` (margin_to_threshold, SplitConformalClassifier — written, never run), `configs/benchmarks.yaml`, `configs/experiment.yaml`, `research/run_all_research.py`, `research/run_fairness.py`, `src/evaluation/statistical_tests.py`.

---

## 1. Report format (after every phase)

Write `results/benchmarks/reports/PHASE_<n>_REPORT.md` containing: (a) what ran (commands, configs), (b) files written, (c) key numbers (tables inline), (d) anomalies and deviations from this prompt (with reason), (e) acceptance checks pass/fail, (f) open questions. Keep it factual; no interpretation beyond what the numbers show.

---

## PHASE 1 — Preflight and calibration-slope fix

**Background.** The reported calibration slope ≈ 0.075 came from an OLS regression of y on logit(p). For a calibrated model that slope ≈ E[p(1−p)] (Home Credit: 0.0807 × 0.9193 = 0.0742 = the reported LR slope), so it is an estimator artifact, not evidence of miscalibration. The correct calibration slope is from a **logistic** regression of y on logit(p) (ideal 1, intercept 0).

**Tasks**
1. **Preflight (read-only):** list the repo; compute and store SHA-256 of every file under `data/synthetic/**`, `results/**`, `research/tables/**` → `results/benchmarks/preflight_hashes.json`. Confirm which exist: `results/authentic/predictions_xgb.npz`, `predictions_lr.npz`, per-seed predictions for T2/T6 (probably not). Report what is missing.
2. **Verify `metrics.py`**: identify the logistic slope function. Keep the OLS version as `calibration_slope_ols_deprecated` (do not delete). Clip p to [1e-6, 1−1e-6]. Use `LogisticRegression(C=1e6, solver="lbfgs")` or `statsmodels.Logit` (no regularisation).
3. **Unit tests** (new): (i) simulated perfectly calibrated data (n ≥ 200k) → logistic slope in [0.95, 1.05], intercept ≈ 0; (ii) overconfident data `p = sigmoid(2·logit(p0))` → slope ≈ 0.5; (iii) underconfident → slope > 1; (iv) on calibrated data, the OLS slope ≈ mean(p(1−p)) (documents the artifact).
4. **Re-run T1** into new files: `results/benchmarks/T1_v2/T1_results_v2.json` with ROC-AUC, PR-AUC, Brier, ECE, logistic slope + intercept, Gini, KS for LR and XGB; save `predictions_lr.npz` and `predictions_xgb.npz` (keys `y_test`, `p_raw_test`, `p_cal_test`, `y_val`, `p_raw_val`, `p_cal_val`) to `results/benchmarks/T1_v2/`. Requires `data/authentic/application_train.csv`; if absent, stop and tell me.
5. **Re-run T2 and T6** (all seeds 1–10 × DGP1/DGP2) writing to `results/benchmarks/T2_v2/` and `T6_v2/`, saving per-seed test predictions as `.npz` this time. Compute the logistic slope/intercept.
6. **Old-vs-new table** `research/tables/benchmarks/calibration_old_vs_new.csv`: for T1, T2 (all configs), T6 (all H): old OLS slope (from the existing tables), new logistic slope, and **also** ROC-AUC/Brier/ECE old vs re-run (these must match the existing numbers to within 1e-6; if not, report the differences — it signals non-reproducibility).

**Acceptance checks**: tests pass; AUC/Brier/ECE reproduce; hashes of existing files unchanged afterwards. If the new logistic slope is outside [0.8, 1.2] anywhere, **do not explain it away** — investigate (Platt fit direction, validation/test shift, visible-vs-full view) and report.

---

## PHASE 2 — Policy rules v2, ground truth, and re-runs

**Background (from external checks of secondary sources — humans must verify against official text):**
- PMMY covers non-corporate micro units doing non-farm income-generating activities; allied agriculture activities (poultry, dairy, bee-keeping, horticulture, fisheries) are included.
- ₹10 lakh in PMMY is the **loan ceiling** (not an applicant income cap). It was raised to ₹20 lakh effective 2024-10-24 (Union Budget 2024-25). Tarun Plus (₹10–20 lakh) requires a previously repaid Tarun loan.
- JanSamarth is a **portal** linking ~13 credit-linked schemes (sources differ on 4 vs 6 categories), each with its own eligibility. PMMY is one of those schemes, so "JanSamarth OR PMMY" double-counts.
- Existing rules (`jan_samarth.yaml`: age [18,60], income ≤ ₹10L, nonfarm=1; `pmmy.yaml`: age [18,65], income ≤ ₹10L, non_agriculture=1) include an income cap and age bands for which **no supporting official clause has been found**.

**Tasks**
1. **Read-only review** of `configs/policy_rules/*.yaml`, `docs/policy_rule_verification.md`, `src/policy/*`. Report what clause/source each existing rule cites. If a clause supports a rule, keep it and say so.
2. **Create `configs/policy_rules/v2/`** (do not touch the old files):
   - `pmmy.yaml` — conditions: (a) enterprise is non-corporate; (b) activity is non-farm income-generating **or** allied-agriculture; (c) loan ceiling versioned by decision date: ≤ ₹10,00,000 effective until 2024-10-23, ≤ ₹20,00,000 effective from 2024-10-24 (two versions of one rule). Do **not** include an income cap or age band unless a human supplies an official clause. `on_missing: UNKNOWN`.
   - `occupation_mapping.yaml` — explicit mapping `occupation_category → {non_farm_activity: SATISFIED | UNSATISFIED | UNKNOWN}` for ride_hailing, delivery, freelance, retail_micro, agri. **Do not decide the `agri` mapping silently.** Implement three scenarios (config flag `agri_scenario`): `unknown` (default; → UNRESOLVED), `ineligible`, `eligible`. Report results for all three.
   - Provenance block for every rule: `document`, `clause`, `page_or_url`, `retrieved_on`, `verified_by`. Fill with the placeholder `<TO BE FILLED FROM OFFICIAL MUDRA / PIB / GAZETTE TEXT>`; set `rule_set_status: UNVERIFIED`. **Never set VERIFIED.**
   - Do not create a JanSamarth rule file. Add a README note in the folder: JanSamarth is a portal; add per-scheme files (e.g., PMEGP) only once official rules are supplied.
   - If the DGP has no loan-amount/requested-amount attribute, the ceiling rule cannot be evaluated in experiments: implement it for the versioning unit test only (same applicant, requested ₹15 lakh → UNSATISFIED on 2024-10-23, SATISFIED on 2024-10-24) and say so.
3. **Ground-truth eligibility.** Inspect the generator to find where the 5% MCAR masking of age/occupation happens. Produce `true_policy_state` (computed from **unmasked** attributes, under each rule set) as a **new** file per dataset (`policy_truth.parquet`). Constraint: existing datasets must remain bit-identical (verify against preflight hashes). If the unmasked values are not persisted and cannot be regenerated without altering RNG streams, **stop and ask me**.
4. **Re-run T3, T4/T5 and T9** under: (i) legacy rules (reproduce old numbers as a check), (ii) v2 core with each `agri_scenario`. Outputs to `results/benchmarks/policy_v2/`. Table `policy_v2_vs_legacy.csv` with approval, review rate, violation rate (define: share of **approved** applicants who are truly ineligible), bad-loan capture, default among approved.
5. **Unit tests**: Kleene AND/OR/NOT truth tables; versioning boundary dates; mapping scenarios; ground-truth consistency (no UNRESOLVED in truth).

**Acceptance checks**: legacy re-run matches existing T3/T4/T5/T9 numbers within 1e-6; hashes of old data unchanged; no rule set marked VERIFIED.

---

## PHASE 3 — Diagnostics (read-only analysis)

1. **DGP latent check.** Using `latent_params.parquet` for analysis only (never as a model feature): for each DGP × seed compute ROC-AUC and Spearman correlation vs `default_flag` of true volatility σ_m, income growth g, platform_tenure, multi_platform, seasonal amplitude. Also AUC of Set B observed features. Table `dgp_latent_diagnostic.csv`. Do not modify the DGP. State plainly whether gig-related latents carry signal.
2. **Policy-state breakdown.** For T3 under each rule set: counts of SATISFIED / UNSATISFIED / UNRESOLVED and what causes each (occupation, age, missingness). Confirm whether ride_hailing/delivery resolve correctly in the experiment pipeline (the API had a known mapping gap; the experiments should not).
3. **Exposure check.** Report whether any loan-amount/exposure column exists (needed for expected-loss ranking in Phase 7).

---

## PHASE 4 — Matched-coverage comparison

**Definition (to avoid test-set peeking):** for each seed/DGP and each Dx ∈ {D2, D3, D4}: take Dx's approval rate on the **validation** set; tune D1's τ on **validation** to hit that same approval rate; evaluate both on test. Report realized test coverage for both (they may drift).

**Metrics per comparison**: realized coverage (both), default rate among approved (both), approved defaults per 1,000 applicants, difference (D1 − Dx) with paired t-test over 10 seeds (df = 9), 95% CI of the difference, per DGP. Also coverage-risk curve data for D1 (τ sweep) with D2/D3/D4 operating points marked.

Output `research/tables/benchmarks/matched_coverage.csv`. Report the result **whichever direction it goes**. Run under legacy and v2 rules.

---

## PHASE 5 — Risk-model baselines (equal tuning)

**Models**: ours — LR, XGBoost; baselines — WoE scorecard + logistic regression (`optbinning.BinningProcess` + `LogisticRegression`), Random Forest, LightGBM, CatBoost. Wrappers exist for WoE-LR/LGBM/CatBoost; add RF; verify all handle NaN (XGB/LGBM/CatBoost native; WoE handles missing as a bin; RF/LR need imputation fitted on train only).

**Equal tuning protocol (identical for every model including ours):**
- Search: random search, N = 30 trials (config), 5-fold stratified CV on **train only**, scoring ROC-AUC, fixed search seed. Search spaces in `configs/benchmarks.yaml`.
- **Synthetic**: tune on the G0 seed (seed 0) datasets per DGP and per feature set; freeze hyperparameters; evaluate on seeds 1–10. (Seed 0 is not an experimental seed.)
- **Home Credit**: tune with CV inside the train split.
- Save chosen hyperparameters to `results/benchmarks/tuned_params.json`.
- Also report each model at default parameters (a "defaults" column), so tuning effects are visible.

**Datasets / views**: Home Credit (same features as T1); synthetic feature sets A and C (train `features_full`, val/test `features_visible`).

**Calibration**: Platt on validation for every model. **Metrics**: ROC-AUC, PR-AUC, Brier, ECE, Gini, KS, logistic slope + intercept.

**Outputs**: `risk_baselines_home_credit.csv`, `risk_baselines_synthetic.csv` (aggregated + per-seed). Paired seed-level tests vs XGB-C (synthetic) with Holm correction across baselines (Phase 8 utilities).

---

## PHASE 6 — Architecture and policy baselines

### 6A. Model-agnostic architecture (A1)
For each risk model M ∈ {XGB (ours), LR, WoE-LR, RF, LGBM, CatBoost}: calibrated PD → τ on validation for 70% D1 approval (as in existing runs) → D4 → R1 review at 20% and 30% budgets. Metrics: violation rate, approval rate, review rate, default among approved, bad-loan capture, cost. Table `architecture_model_agnostic.csv`.

### 6B. Single score + plain filter at matched coverage (A2)
Risk model only + plain policy filter (P1 and P2 below), **no evidence gate, no review**. τ tuned on validation to match D4's validation approval rate; evaluate on test. Compare to D4 (and to D4+R1 after oracle review). Table `single_score_vs_pipeline.csv`.

### 6C. Policy baselines (same rule set, different handling)
- **P0** no policy check (D1)
- **P1** plain if/else; missing attribute ⇒ ineligible
- **P2** plain if/else; missing attribute ⇒ eligible
- **P3** impute-then-check: median/mode fitted on train, then two-valued logic
- **P4** Kleene engine (UNRESOLVED ⇒ REVIEW)

Use `true_policy_state` (Phase 2). **Definitions (use exactly):**
- *violation_rate* = #approved with true UNSATISFIED / #approved.
- *wrongful_decline_rate* = #(declined by the policy step, true SATISFIED, PD < τ) / #(true SATISFIED, PD < τ).
- *review_rate* = #referred / N.
- *referred_truly_eligible_share* and *recovered* = referred ∧ true SATISFIED ∧ Y = 0 (approved after oracle). Oracle for policy review: referred true-UNSATISFIED ⇒ DECLINE; referred defaulter ⇒ DECLINE; otherwise APPROVE (document this extension of the existing oracle).
- *coverage* = approval rate.
Run for every rule scenario (legacy, v2 with each `agri_scenario`). Table `policy_baselines.csv`. Also a qualitative note file (`policy_qualitative.md`) containing: reason codes / provenance fields emitted by the Kleene engine, date-based version switch demonstration (from the Phase 2 unit test), and conflict handling (RULE_CONFLICT → UNRESOLVED). **No predicted outcomes** — report measured numbers only.

---

## PHASE 7 — Review-allocation baselines and cost

**Pool and budget logic: identical to `src/decisions/review.py`** — pool P = {PD < τ ∧ policy ≠ UNSATISFIED}; mandatory set = UNRESOLVED consumed first; K = ⌊B·|P|⌋ with B ∈ {0.20, 0.30}; same perfect oracle. Run all on DGP1/DGP2 × 10 seeds, under legacy and v2 rules.

**Strategies**
- V0 R0 random; V1 R1, R2, R3 (existing)
- V2 margin-to-threshold (|PD − τ| smallest first)
- V3 split conformal reject (α = 0.10; calibrate on validation; rank by ambiguity of the prediction set, ties broken by PD)
- V4 class-conditional (Mondrian) conformal reject (per-class calibration)
- V5 SCROSS/AUCROSS-style selective classification (Pugnana et al.): cross-fitted out-of-fold confidence scores, quantile-based threshold, refer lowest confidence first. If the papers' exact algorithms cannot be consulted, implement the simplified cross-fitted confidence-quantile version, **name it "SCROSS-style (simplified)"**, and state it does not reproduce the paper.
- V6 expected-loss ranking (PD × exposure) — **only if an exposure column exists (Phase 3.3)**; otherwise skip and document. Do not invent exposures.
- V7 perfect-ranking upper bound (refer true defaulters in the pool first, up to K); random (V0) is the lower bound.

**Rank-equivalence check (required).** Within the pool (PD < τ < 0.5), margin, entropy, confidence and (likely) conformal ambiguity are monotone in PD. For each strategy compute the Spearman rank correlation of its priority scores with PD within the pool, and report the fraction of seeds where the referred set is identical to R1's. Report "equivalent to R1" where it holds; do not present equivalent methods as separate wins.

**Metrics**: bad-loan capture, default rate among approved, review efficiency, cost per applicant.

**Cost (fix the confound).** Use **one common review cost C_R** for both budgets (config; default 0.1). Sensitivity grid: C_FN/C_FP ∈ {1, 3, 5} with C_FP = 1, and C_R ∈ {0.05, 0.1, 0.2}. Report cost for every cell. Do not claim "20% budget is more cost-efficient" unless it survives a common C_R.

Outputs: `review_baselines.csv`, `review_rank_equivalence.csv`, `cost_sensitivity.csv`.

---

## PHASE 8 — Statistics

Create `src/evaluation/paired_tests.py` (with tests) providing: paired t-test over per-seed differences (df = n − 1), mean difference with CI, Cohen's d_z, optional paired bootstrap (applicant level, n = 1000, existing helper), Holm correction, Bonferroni.

**Primary contrasts (pre-specified; per DGP; Bonferroni α = 0.05/3):**
1. A vs C, XGB ROC-AUC.
2. D1 vs D4 at **matched coverage**, default rate among approved (Phase 4).
3. R0 vs **R3**, bad-loan capture at the 20% budget.

**Secondary / exploratory** (label explicitly): R0 vs R1; all baseline-vs-ours comparisons (Holm across baselines per metric family); 30% budget; pooled-DGP robustness.

Also: replace the hardcoded `T_CRIT = 2.262` in `research/run_all_research.py` with `scipy.stats.t.ppf(0.975, n-1)` computed from the actual seed count (`float(t_dist.ppf(0.975, n_seeds-1)) if n_seeds > 1 else 0.0`); add `H_num` to a **new** copy of the T6 table (do not edit the old CSV). Output `statistical_tests.csv` with columns: contrast, family, dgp, metric, mean_diff, ci_lo, ci_hi, t, df, p, p_adjusted, method (Bonferroni/Holm), significant.

---

## PHASE 9 — Figures and paper tables

Use matplotlib (+ seaborn style), academic look, labelled axes with units, 95% CI shown, legends inside the figure, PNG 300 dpi **and** PDF, saved to `research/figures/`. A single script `research/make_figures.py` regenerates all.

| Fig | Content | Data |
|---|---|---|
| F1 | ROC curves LR and XGB (T1), AUC in legend | `T1_v2/predictions_*.npz` |
| F2 | Ablation bars A/B/C × LR/XGB, both DGPs, CI | T2 tables |
| F3 | D1–D4 trade-off: approval vs default among approved, CI; matched-coverage D1 operating point overlaid | T3 + Phase 4 |
| F4 | τ_E sensitivity: approval and evidence-fail rate vs τ_E | T3 τ_E |
| F5 | Review frontier: bad-loan capture vs budget for R0, R1–R3, baselines, upper bound; equivalent methods drawn once and annotated | Phase 7 |
| F6 | History sensitivity: AUC and ECE vs H (numeric order, dual axis) | T6 (H_num) |
| F7 | Reliability diagram (T1, 10 quantile bins, y = x line), logistic slope in caption. Show what the data shows — do not add narrative about "compression". | T1_v2 predictions |
| F8 | Risk baselines: AUC/KS with CI, Home Credit and synthetic | Phase 5 |
| F9 | Model-agnostic architecture: violation, review capture, default among approved across risk models | Phase 6A |
| F10 | Policy baselines: violation rate vs wrongful-decline rate vs review rate (P0–P4) | Phase 6C |
| F11 | Matched-coverage default-rate difference with CI per comparison | Phase 4 |

Also `research/make_paper_tables.py`: emit each table as LaTeX (`booktabs`) **and** Markdown into `research/paper_tables/` from the CSVs only (no hand-typed numbers).

---

## PHASE 10 — Documentation, reproducibility, claim hygiene

1. **`research/BENCHMARK_RESULTS.md`**: executive summary (what ran, main findings stated neutrally); old-vs-new calibration; matched coverage; risk baselines; architecture baselines; policy baselines; review baselines + rank-equivalence; cost sensitivity; statistical tests (Bonferroni primary / Holm secondary); DGP diagnostic; limitations (synthetic default labels; perfect-oracle reviewer; results true by construction — policy violations → 0, R2 ≈ R0, e-Shram parity, R1 > R0 with a perfect oracle; Home Credit is Russian consumer loans; no temporal validation; policy rules UNVERIFIED; T6 trains on H=12 and scores forced-H views without refit and the evidence score is constant across H; synthetic AUC/KS reflect the DGP). Every number must cite its source file.
2. **Superseded banners**: prepend a one-line banner ("SUPERSEDED — see research/BENCHMARK_RESULTS.md and *_v2.md; predates the calibration-slope and policy-rule corrections") to `FINAL_PROJECT_TECHNICAL_DOCUMENTATION.md`, `FINAL_PROJECT_ARCHITECTURE.md`, `RESEARCH_IMPLEMENTATION_STATUS.md`. Do not otherwise edit them. Create `FINAL_PROJECT_TECHNICAL_DOCUMENTATION_v2.md` reflecting the current system (rules status UNVERIFIED, API/frontend present, heuristic PD in the demo unless replaced).
3. **Fix two wrong sentences** in a **copy** (`EXPERIMENT_RESULTS_v2.md`): (i) summary item 7 (e-Shram "~1–2pp higher approval driven by policy gate correlation") → replace with the T9 result (+0.5pp, CI crosses zero, independent by design); (ii) "XGBoost outperforms LR by ~1–2pp AUC" → use the measured difference; remove "KS > 0.6 is excellent in consumer credit" for synthetic data.
4. **Reproducibility**: `Makefile` target `reproduce` that regenerates all new results, tables and figures from the raw data; `requirements.lock` (pip freeze); README section with exact commands and expected runtimes (measured); data-availability notes (Home Credit from Kaggle, not redistributed; Dataset 2 CC BY 4.0, DOI 10.17632/j6hd2dfsh8.1).
5. **Claim audit**: `research/CLAIMS_AUDIT.md` — a table: claim sentence candidate → source file → status (supported / by construction / not supported). Plus `scripts/check_forbidden_claims.py` that scans `paper/` (md/tex) and warns on: "works for real gig workers", "impossible with single-score", "no existing system", "verified" (near "policy"/"rules"), "underprediction" (calibration), "outperforms existing methods" (without a table reference), "SHAP explanations" (API/demo context).
6. Run the full test suite and report counts.

---

## PHASE 11 (OPTIONAL — only if Phases 1–10 are complete)

Second real dataset so one result does not depend on the synthetic generator. On Home Credit, define a **labelled proxy** for evidence sufficiency from document-flag and external-score availability (e.g., fraction of present flags/fields), run the evidence-gate (D3-style) and review experiments (R0, R1, R2, R3, margin, conformal), and report as a proxy-based real-data check. Policy is not applicable here. State clearly that the proxy is an assumption. Skip if it takes more than a few hours.

---

## 12. What to send back to me (the paper author)

- After **Phase 2**: `calibration_old_vs_new.csv`, `policy_v2_vs_legacy.csv`.
- After **Phase 4**: `dgp_latent_diagnostic.csv` and `matched_coverage.csv`.
- After **Phase 7**: `risk_baselines_*.csv`, `architecture_model_agnostic.csv`, `policy_baselines.csv`, `review_baselines.csv`, `review_rank_equivalence.csv`.
- After **Phase 10**: `statistical_tests.csv`, `BENCHMARK_RESULTS.md`, `CLAIMS_AUDIT.md`.

## 13. Definition of done

- All new results reproducible with one command; old results untouched (hash-verified).
- Logistic calibration slope used everywhere; old OLS shown once as an erratum.
- Matched-coverage result reported in whichever direction it falls.
- Policy rules v2 created, UNVERIFIED, with provenance placeholders and three `agri` scenarios.
- All baselines run under the equal-tuning protocol with common review cost.
- Paired tests with p-values; primary contrasts Bonferroni, baselines Holm.
- 11 figures + LaTeX/Markdown tables generated from CSVs.
- Claims audit complete; no forbidden phrases in the draft.
- Tests pass.
