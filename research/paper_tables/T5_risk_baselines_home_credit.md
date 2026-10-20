### T5_risk_baselines_home_credit

Equal-tuning risk baselines on Home Credit.

Source: `research\tables\benchmarks\risk_baselines_home_credit.csv`

dataset,model,tuning,roc_auc,pr_auc,brier_score,calibration_intercept,calibration_slope,calibration_slope_ols
home_credit,lgbm,default,0.758,0.2442,0.0677,-5.2649,0.0936,0.0031
home_credit,xgb,default,0.7568,0.2447,0.0678,-5.2926,0.097,0.0031
home_credit,catboost,default,0.7528,0.2391,0.068,-5.2926,0.097,0.003
home_credit,catboost,tuned,0.7465,0.2302,0.0684,-5.4721,0.0916,0.0028
home_credit,lgbm,tuned,0.746,0.2297,0.0685,-5.8523,0.0929,0.0027
home_credit,xgb,tuned,0.7448,0.2286,0.0685,-5.7771,0.0952,0.0027
home_credit,woe_lr,default,0.7432,0.2244,0.0687,-6.094,0.0843,0.0026
home_credit,woe_lr,tuned,0.743,0.2241,0.0687,-6.1257,0.0842,0.0026
home_credit,rf,tuned,0.7362,0.2231,0.0689,-7.212,0.1197,0.0025
home_credit,rf,default,0.7358,0.2224,0.0689,-7.2396,0.1177,0.0025

