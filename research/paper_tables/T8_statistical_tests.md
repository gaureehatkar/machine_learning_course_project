### T8_statistical_tests

Paired tests: primary Bonferroni, secondary Holm.

Source: `research\tables\benchmarks\statistical_tests.csv`

contrast,family,dgp,metric,a_label,b_label,n,mean_a,mean_b,mean_diff,ci_lo,ci_hi,t,df,p,p_adjusted,method,significant,cohen_d_z
A_vs_C_XGB_ROC_AUC,primary,DGP1,roc_auc,A_xgb,C_xgb,10,0.921824,0.918238,-0.003587,-0.005987,-0.001186,-3.3798,9,0.0081291710973379,0.0243875132920137,Bonferroni,False,-1.0688
D1_vs_D4_matched_coverage_DR,primary,DGP1,default_rate_among_approved,D4,D1,10,0.01749,0.00325,-0.01424,-0.016008,-0.012472,-18.2218,9,2.0607104514167734e-08,6.18213135425032e-08,Bonferroni,True,-5.7622
R0_vs_R3_capture_B20,primary,DGP1,bad_loan_capture,R0,R3,10,0.210779,0.405753,0.194974,0.151312,0.238637,10.1017,9,3.2890006239450457e-06,9.867001871835136e-06,Bonferroni,True,3.1944
A_vs_C_XGB_ROC_AUC,primary,DGP2,roc_auc,A_xgb,C_xgb,10,0.915237,0.913237,-0.002,-0.003489,-0.000511,-3.0388,9,0.0140458868589921,0.0421376605769765,Bonferroni,False,-0.9609
D1_vs_D4_matched_coverage_DR,primary,DGP2,default_rate_among_approved,D4,D1,10,0.02526,0.00513,-0.02013,-0.022613,-0.017647,-18.3421,9,1.9450162901701225e-08,5.835048870510368e-08,Bonferroni,True,-5.8003
R0_vs_R3_capture_B20,primary,DGP2,bad_loan_capture,R0,R3,10,0.212646,0.370943,0.158297,0.119302,0.197292,9.183,9,7.239497496695838e-06,2.1718492490087517e-05,Bonferroni,True,2.9039
XGB_C_vs_woe_lr_ROC_AUC,secondary_baselines,DGP1,roc_auc,xgb,woe_lr,10,0.92124,0.91183,-0.00941,-0.011309,-0.007511,-11.2072,9,1.375220809635512e-06,5.500883238542048e-06,Holm,True,-3.544
XGB_C_vs_rf_ROC_AUC,secondary_baselines,DGP1,roc_auc,xgb,rf,10,0.92124,0.91783,-0.00341,-0.005469,-0.001351,-3.7462,9,0.0045811162868772,0.0137433488606316,Holm,True,-1.1847
XGB_C_vs_lgbm_ROC_AUC,secondary_baselines,DGP1,roc_auc,xgb,lgbm,10,0.92124,0.92212,0.00088,-3.2e-05,0.001792,2.1822,9,0.0569707443640684,0.1139414887281368,Holm,False,0.6901
XGB_C_vs_catboost_ROC_AUC,secondary_baselines,DGP1,roc_auc,xgb,catboost,10,0.92124,0.92116,-8e-05,-0.00151,0.00135,-0.1266,9,0.902064489997959,0.902064489997959,Holm,False,-0.04
XGB_C_vs_woe_lr_ROC_AUC,secondary_baselines,DGP2,roc_auc,xgb,woe_lr,10,0.91449,0.9062,-0.00829,-0.010016,-0.006564,-10.8677,9,1.782711711728612e-06,7.130846846914448e-06,Holm,True,-3.4367
XGB_C_vs_rf_ROC_AUC,secondary_baselines,DGP2,roc_auc,xgb,rf,10,0.91449,0.91032,-0.00417,-0.005472,-0.002868,-7.2467,9,4.833270651408847e-05,0.0001449981195422,Holm,True,-2.2916
XGB_C_vs_lgbm_ROC_AUC,secondary_baselines,DGP2,roc_auc,xgb,lgbm,10,0.91449,0.9153,0.00081,0.000164,0.001456,2.8346,9,0.0195748180869564,0.0391496361739128,Holm,True,0.8964
XGB_C_vs_catboost_ROC_AUC,secondary_baselines,DGP2,roc_auc,xgb,catboost,10,0.91449,0.91512,0.00063,-0.000202,0.001462,1.7125,9,0.1209662175420394,0.1209662175420394,Holm,False,0.5415
R0_vs_R1_capture_B20,secondary,DGP1,bad_loan_capture,R0,R1,10,0.210779,0.482855,0.272076,0.22809,0.316063,13.9924,9,2.0604274728467506e-07,2.0604274728467506e-07,Holm,True,4.4248
R0_vs_R1_capture_B20,secondary,DGP2,bad_loan_capture,R0,R1,10,0.212646,0.45039,0.237744,0.205496,0.269992,16.6773,9,4.4786667000685844e-08,8.957333400137169e-08,Holm,True,5.2738
R0_vs_R1_capture_B30,secondary,DGP1,bad_loan_capture,R0,R1,10,0.308879,0.724493,0.415615,0.374666,0.456564,22.96,9,2.6794922670497373e-09,8.038476801149214e-09,Holm,True,7.2606
R0_vs_R1_capture_B30,secondary,DGP2,bad_loan_capture,R0,R1,10,0.300301,0.693632,0.393331,0.359137,0.427525,26.0215,9,8.819076557265814e-10,3.527630622906326e-09,Holm,True,8.2287
A_vs_C_XGB_ROC_AUC_pooled,exploratory_pooled,pooled,roc_auc,A_xgb,C_xgb,20,0.918531,0.915737,-0.002793,-0.004121,-0.001466,-4.4032,19,0.0003054945817033,0.0003054945817033,none,True,-0.9846

