### T5_risk_baselines_home_credit

Equal-tuning risk baselines on Home Credit.

Source: `research\tables\benchmarks\risk_baselines_home_credit.csv`

| dataset     | model    | tuning   |   roc_auc |   pr_auc |   brier_score |    ece |   gini |     ks |   calibration_intercept |   calibration_slope |   calibration_slope_ols |
|:------------|:---------|:---------|----------:|---------:|--------------:|-------:|-------:|-------:|------------------------:|--------------------:|------------------------:|
| home_credit | lgbm     | tuned    |    0.762  |   0.2516 |        0.0674 | 0.002  | 0.524  | 0.3899 |                  0.061  |              1.0261 |                  0.0746 |
| home_credit | xgb      | tuned    |    0.7609 |   0.2496 |        0.0675 | 0.0023 | 0.5218 | 0.387  |                  0.0522 |              1.0218 |                  0.0746 |
| home_credit | catboost | tuned    |    0.7588 |   0.2474 |        0.0677 | 0.0026 | 0.5176 | 0.3857 |                  0.0512 |              1.0197 |                  0.074  |
| home_credit | lgbm     | default  |    0.7586 |   0.2471 |        0.0677 | 0.0025 | 0.5172 | 0.382  |                  0.0591 |              1.0254 |                  0.0754 |
| home_credit | xgb      | default  |    0.7568 |   0.2447 |        0.0678 | 0.0025 | 0.5136 | 0.3809 |                  0.0546 |              1.0224 |                  0.0755 |
| home_credit | catboost | default  |    0.7528 |   0.2391 |        0.068  | 0.0031 | 0.5055 | 0.3804 |                  0.0534 |              1.0209 |                  0.0764 |
| home_credit | rf       | tuned    |    0.7362 |   0.2231 |        0.0689 | 0.0046 | 0.4723 | 0.3481 |                  0.0808 |              1.0347 |                  0.0825 |
| home_credit | rf       | default  |    0.7358 |   0.2224 |        0.0689 | 0.0035 | 0.4716 | 0.3489 |                  0.0789 |              1.0336 |                  0.0824 |
| home_credit | lr       | default  |    0.6769 |   0.1621 |        0.0716 | 0.0047 | 0.3537 | 0.2645 |                  0.0999 |              1.0428 |                  0.0725 |
| home_credit | lr       | tuned    |    0.6716 |   0.1569 |        0.0719 | 0.0048 | 0.3432 | 0.2587 |                  0.1207 |              1.0516 |                  0.0707 |
