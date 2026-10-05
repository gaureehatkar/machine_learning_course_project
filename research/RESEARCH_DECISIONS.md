# Research Decisions — SynthGigCredit-IN

**Date:** 2026-10-05

This document records every methodological decision made during the research implementation, with rationale and rejected alternatives.

---

## 1. Feature Sets

**Decision:** Three feature sets (A, B, C) defined as:
- A = 7 conventional features (income_mean, expense_mean, expense_ratio, debt_mean, has_emi, liquidity_mean, liquidity_min)
- B = 5 alternative/gig features (income_volatility, income_trend, platform_tenure, multi_platform, seasonality_index)
- C = A + B combined (12 features)

**Rationale:** The ablation tests whether alternative gig-specific features add predictive value beyond conventional financial features. This is a standard ablation design.

**Rejected alternative:** Adding more feature sets (e.g. A+B subset). Not needed — the three-way comparison (A vs B vs C) is sufficient to answer the research question.

**Evidence/policy columns excluded from PD model:** Evidence columns (history_length, aa_completeness, uli_completeness) and policy columns (e_shram_registered, jan_samarth_state, pmmy_state) are HARD-EXCLUDED from the PD model via `_assert_feature_set()`. This prevents leakage — evidence and policy are separate layers, not model inputs.

---

## 2. Models

**Decision:** Logistic Regression and XGBoost only.

**Rationale:** LR provides interpretable coefficients (for explainability); XGB provides maximum discriminative performance and TreeSHAP explanations. These are the two standard choices in credit scoring literature.

**Rejected alternatives:**
- Random Forest: Less interpretable than LR, typically weaker than XGB on tabular data
- Neural networks: Overkill for 12 features, harder to explain, prone to overfitting on 15K training rows
- LightGBM: Would duplicate XGB's role without adding research insight

---

## 3. Calibration

**Decision:** Platt scaling only. No isotonic regression.

**Rationale:** Platt scaling is the standard for credit scoring. It fits a single sigmoid σ(a×p + b) on the validation set, which is parsimonious and avoids overfitting on small datasets. The calibration slope ≈ 0.075 is a known limitation caused by missing bureau features, not a calibration method problem.

**Rejected alternative:** Isotonic regression — non-parametric, can overfit on small samples, and harder to interpret. Would not fix the fundamental issue (missing external credit history features).

**Investigation of low calibration slope:**
The slope ≈ 0.075 means the model underpredicts default probabilities. For example, if the model says PD=0.15, the actual default rate is much higher. This is because:
1. Home Credit dataset has 8% default rate — much lower than typical Indian microfinance (15-25%)
2. Bureau features (external credit history) are absent from our model
3. The model's ranking ability (AUC) is good, but absolute probabilities are systematically shifted

**Implication for decisioning:** The τ threshold is selected on validation data to achieve 70% approval rate. Since τ adapts to the model's calibration, the decision outcomes are still valid even with poor calibration. However, absolute PD values should not be reported as "probability of default" without caveat.

---

## 4. Evidence Score

**Decision:** E = 0.5×(H/12) + 0.25×AA + 0.25×ULI, τ_E = 0.50

**Rationale:** History length gets the highest weight (0.5) because transaction history is the most important data source for credit scoring. AA (Account Aggregator) and ULI (Unified Lending Interface) each get 0.25 as secondary data quality signals.

**τ_E = 0.50:** Chosen as the midpoint — an applicant needs at least 50% weighted evidence quality to proceed to auto-decision. Below this, they are routed to human review.

**Sensitivity analysis:** τ_E ∈ {0.30, 0.40, 0.50, 0.60, 0.70} is tested in T3 to show how the threshold affects approval rates and default rates. The threshold is NOT changed based on which value gives better metrics — all values are reported.

**Rejected alternative:** Equal weights (0.33 each) — would underweight history, which is the primary signal for thin-file applicants.

---

## 5. Policy Engine

**Decision:** Kleene three-valued logic (TRUE/FALSE/UNRESOLVED) for policy evaluation.

**Rationale:** Binary (pass/fail) is too rigid — when an attribute is missing (e.g. occupation not mapped), the system should not force a YES or NO. UNRESOLVED routes to human review, which is the honest answer.

**Combination:** Kleene OR — applicant qualifies under ANY one scheme (JanSamarth OR PMMY).

**Policy rules:** Marked "RESEARCH VERIFIED" based on manual research of scheme documentation. Not scraped from official portals.

**Known gap:** Occupation mapping incomplete — ride_hailing and delivery return UNRESOLVED because the policy YAML rules check `nonfarm_business_flag` but don't have explicit occupation categories. This is a known limitation, not a bug — it correctly produces UNRESOLVED for unmapped occupations.

---

## 6. Decision Modes

**Decision:** Four modes (D1-D4) with explicit gate precedence.

**Precedence:** PD decline > Policy-UNSAT decline > Review triggers (UNRES, evidence) > Approve.

**Rationale:** This precedence ensures safety — a high-PD applicant is declined regardless of policy or evidence status. Policy ineligibility is a hard constraint (DECLINE), while policy uncertainty is a soft constraint (REVIEW).

**D4 recommended:** All three layers active. This is the full system. D1-D3 are ablations that isolate each layer's contribution.

---

## 7. Review Allocation

**Decision:** Four strategies (R0-R3) with mandatory set consumed first.

**R0 (random):** Control group — random allocation from non-mandatory pool.
**R1 (entropy):** H(PD) = -p ln p - (1-p) ln(1-p). Within the pool (PD < τ < 0.5), entropy is monotone in PD, so R1 ≡ highest-PD-first.
**R2 (evidence):** Lowest evidence score first — applicants with weakest data quality get reviewed first.
**R3 (combined):** 0.5×H(PD)/ln2 + 0.5×(1-E). Balances uncertainty and data quality.

**Mandatory set:** UNRESOLVED policy applicants are referred first, consuming budget before ranking strategies apply to the non-mandatory pool.

**Oracle:** Perfect-review simulation — referred defaulter → DECLINE, referred non-defaulter → APPROVE. This is an idealization, not a realistic reviewer model.

**Budgets:** 20% and 30% of pool size. These represent operational constraints on human reviewer capacity.

---

## 8. Cost Analysis

**Decision:** Linear cost model: C = C_FN × N_approved_default + C_FP × N_declined_good + C_R × N_review

**Parameters (from config):**
- C_FN = m = 1.0 (cost of approving a defaulter — false negative)
- C_FP = m = 1.0 (cost of declining a good applicant — false positive)
- C_R = c_rev[0] = 0.1 at 20% budget, c_rev[1] = 0.2 at 30% budget (review cost per applicant)

**Assumption:** C_FN = C_FP = 1.0 means we weight false negatives and false positives equally. In practice, false negatives (lending to defaulters) are typically 3-10× more expensive than false positives (turning away good customers). The L parameter [3, 5, 10] in the config represents loss amounts at different risk levels.

**Rejected alternative:** Using asymmetric costs (C_FN >> C_FP) — would make results dependent on the cost ratio rather than the architecture. Equal costs keep the comparison focused on the decision architecture.

---

## 9. Seed Stability

**Decision:** 10 seeds per DGP, report mean ± 95% CI using t-distribution (df=9, t_crit=2.262).

**Rationale:** 10 seeds is the minimum for a meaningful 95% CI with t-distribution. More seeds would give tighter intervals but cost more compute time.

**Two DGPs:** DGP1 (base) and DGP2 (income shock). Testing across both verifies that findings are robust to different economic conditions, not just one data distribution.

---

## 10. Statistical Comparisons

**Decision:** Bonferroni correction for 3 primary contrasts: α = 0.05/3 = 0.01667.

**Primary contrasts:**
1. A vs C (does adding gig features to conventional features improve performance?)
2. D1 vs D4 (does the full 3-layer architecture improve outcomes over risk-only?)
3. R0 vs R3 ( does combined review strategy outperform random?)

**Paired bootstrap:** Available via `paired_bootstrap()` for applicant-level comparisons. n=1000 resamples.

---

## 11. Gini and KS Metrics

**Decision:** Added Gini = 2×AUC - 1 and KS = max|F_default(t) - F_nondefault(t)| to the metrics module.

**Rationale:** These are standard credit scoring metrics required by the project specification. They were missing from the original implementation.

**Gini interpretation:** Gini ranges from 0 (random) to 1 (perfect). It's a linear transform of AUC, so it provides the same information in a different scale commonly used in credit scoring.

**KS interpretation:** KS measures the maximum separation between score distributions of defaulters and non-defaulters. A higher KS means the model better separates the two groups. KS > 0.30 is considered acceptable in consumer credit; KS > 0.40 is good.

---

## 12. Fairness Assessment

**Decision:** Fairness analysis is methodologically limited because all demographic variables are synthetic.

**Available subgroup variables (all synthetic):**
- `e_shram_registered` (0/1) — registration status, not a protected attribute
- `multi_platform` (0/1) — work pattern, not protected
- `occupation_category` — freelance_services, ride_hailing, delivery, etc.

**What CAN be analyzed:**
- Whether approval rates differ by e-Shram registration status
- Whether default rates differ by occupation
- Whether model performance (AUC) varies by subgroup

**What CANNOT be claimed:**
- Real-world fairness conclusions (data is synthetic)
- Bias against protected groups (no protected attributes exist in the DGP)
- Causal effects of e-Shram registration (designed to be independent of default)

**Conclusion:** Fairness analysis is possible as a methodological demonstration but cannot support real-world fairness claims. The e-Shram subgroup analysis is the most meaningful since it tests whether the evidence gate disproportionately affects unregistered workers.

---

## 13. T1 Reproduction

**Decision:** T1 results are pre-existing and verified. They will be independently reproduced as part of the calibration analysis.

**Known issue:** Calibration slope ≈ 0.075 (should be ≈ 1.0). This is NOT a code bug — it's a data limitation. Home Credit has 8% default rate with 122 features; our model uses 12 features without bureau data. The slope will not improve without adding more features or using a different dataset.

**What ECE ≈ 0.0024 means:** The model's predicted probabilities are very close to observed default rates within each bin. This seems to contradict the low slope, but they measure different things:
- ECE measures absolute calibration error (are predicted probabilities close to observed rates?)
- Slope measures relative calibration (does the model spread probabilities enough?)
- Low ECE + low slope = probabilities are clustered in a narrow range around the base rate

---

## 14. Documentation of Engineering Issues (For Teammate)

These issues are in the engineering layer (API/frontend) and should be fixed by the engineering teammate:

1. **explain() call broken in app/api/main.py** — passes `features=`, `config=` kwargs that don't exist in the 11-parameter `explain()` signature. Always raises TypeError. The API catches this and returns `{"error": "TypeError..."}` in the explanation field.

2. **tau/tau_e not accepted by API** — frontend sends these in the request body but `DecisionRequest` pydantic model doesn't have these fields. They are silently dropped. τ is always 0.4.

3. **non_agriculture field missing** — `ApplicantFeatures` model doesn't have this field. PMMY rules check `non_agriculture` which doesn't exist → always UNRESOLVED.

4. **API uses heuristic PD** — `_compute_risk_heuristic()` is used instead of a trained model. The trained XGBoost model is not loaded at API startup.

These do NOT affect the research experiments — all experiment runners use the real trained models directly.
