#!/usr/bin/env python
"""
Phase 0 — Re-run T1 with fixed (logistic) calibration slope.

Outputs (none overwrite existing files):
  results/authentic/predictions_lr.npz    — y_test, p_cal_test
  results/authentic/predictions_xgb.npz  — y_test, p_cal_test
  results/authentic/T1_results_v2.json   — all metrics with new slope
"""
from __future__ import annotations
import json, sys, warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")

from src.models.train_models import WinsorisedScaler
from src.calibration.platt import fit_platt
from src.evaluation.metrics import compute_all_metrics, calibration_slope_ols_deprecated
from src.utils.config_loader import load_config


def load_and_prepare_v2(data_path: str):
    """
    Numpy-2.x-safe data loading.
    Uses sparse OHE + per-split .toarray() to avoid the pandas block
    consolidation memory error introduced in numpy>=2.
    """
    import pandas as pd
    from sklearn.model_selection import StratifiedShuffleSplit
    from sklearn.preprocessing import OneHotEncoder
    from sklearn.impute import SimpleImputer

    NUMERIC = [
        "AMT_INCOME_TOTAL","AMT_CREDIT","AMT_ANNUITY","AMT_GOODS_PRICE",
        "EXT_SOURCE_1","EXT_SOURCE_2","EXT_SOURCE_3",
        "CNT_CHILDREN","CNT_FAM_MEMBERS","REGION_RATING_CLIENT",
    ]
    CATEGORICAL = ["NAME_CONTRACT_TYPE","NAME_INCOME_TYPE","NAME_EDUCATION_TYPE",
                   "FLAG_OWN_CAR","FLAG_OWN_REALTY"]
    DERIVED_FUNS = {
        "credit_income_ratio": lambda d: d["AMT_CREDIT"] / (d["AMT_INCOME_TOTAL"] + 1),
        "annuity_income_ratio": lambda d: d["AMT_ANNUITY"] / (d["AMT_INCOME_TOTAL"] + 1),
        "credit_term": lambda d: d["AMT_CREDIT"] / (d["AMT_ANNUITY"] + 1),
        "age_years": lambda d: d["DAYS_BIRTH"] / -365,
        "years_employed": lambda d: np.where(
            d["DAYS_EMPLOYED"] == 365243, np.nan, d["DAYS_EMPLOYED"] / -365),
        "employed_flag": lambda d: (d["DAYS_EMPLOYED"] == 365243).astype(int),
    }
    TARGET = "TARGET"

    print(f"Loading {data_path}...")
    df = pd.read_csv(data_path)
    print(f"  {len(df):,} rows, {df.shape[1]} cols  default={df[TARGET].mean():.3f}")

    for name, fn in DERIVED_FUNS.items():
        df[name] = fn(df)
    numeric_cols = NUMERIC + list(DERIVED_FUNS.keys())

    sss  = StratifiedShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
    idx  = np.arange(len(df))
    tv_idx, test_idx = next(sss.split(idx, df[TARGET].values))
    sss2 = StratifiedShuffleSplit(n_splits=1, test_size=0.25, random_state=43)
    tr_rel, va_rel = next(sss2.split(tv_idx, df[TARGET].values[tv_idx]))
    train_idx = tv_idx[tr_rel]; val_idx = tv_idx[va_rel]
    print(f"  Split — train:{len(train_idx):,} val:{len(val_idx):,} test:{len(test_idx):,}")

    df_tr = df.iloc[train_idx].copy()
    df_va = df.iloc[val_idx].copy()
    df_te = df.iloc[test_idx].copy()

    imp = SimpleImputer(strategy="median")
    df_tr[numeric_cols] = imp.fit_transform(df_tr[numeric_cols])
    df_va[numeric_cols] = imp.transform(df_va[numeric_cols])
    df_te[numeric_cols] = imp.transform(df_te[numeric_cols])

    # Sparse OHE avoids numpy-2.x pandas consolidation OOM
    enc    = OneHotEncoder(handle_unknown="ignore")
    cat_tr = enc.fit_transform(df_tr[CATEGORICAL].astype(str)).toarray()
    cat_va = enc.transform(df_va[CATEGORICAL].astype(str)).toarray()
    cat_te = enc.transform(df_te[CATEGORICAL].astype(str)).toarray()
    cat_names = enc.get_feature_names_out(CATEGORICAL).tolist()

    X_train = np.hstack([df_tr[numeric_cols].values, cat_tr]).astype(np.float32)
    X_val   = np.hstack([df_va[numeric_cols].values, cat_va]).astype(np.float32)
    X_test  = np.hstack([df_te[numeric_cols].values, cat_te]).astype(np.float32)

    return (X_train, X_val, X_test,
            df_tr[TARGET].values.astype(float),
            df_va[TARGET].values.astype(float),
            df_te[TARGET].values.astype(float),
            numeric_cols + cat_names)


def run():
    data_path = ROOT / "data/authentic/application_train.csv"
    if not data_path.exists():
        print(f"MISSING: {data_path}")
        print("Download application_train.csv from Kaggle → data/authentic/")
        sys.exit(1)

    cfg     = load_config(ROOT / "configs/models.yaml")
    out_dir = ROOT / "results/authentic"
    out_dir.mkdir(parents=True, exist_ok=True)

    X_train, X_val, X_test, y_train, y_val, y_test, feat_names = load_and_prepare_v2(str(data_path))

    results_v2 = {}
    for family in ["logreg", "xgb"]:
        print(f"\n--- {family.upper()} ---")
        from sklearn.linear_model import LogisticRegression
        from xgboost import XGBClassifier

        lr_cfg  = cfg["models"]["logreg"]
        xgb_cfg = cfg["models"]["xgb"]

        if family == "logreg":
            ws  = WinsorisedScaler()
            Xtr = ws.fit_transform(X_train)
            Xv  = ws.transform(X_val)
            Xte = ws.transform(X_test)
            model = LogisticRegression(
                C=lr_cfg["C"], max_iter=lr_cfg["max_iter"],
                solver=lr_cfg["solver"], random_state=42,
            )
            model.fit(Xtr, y_train)
            p_raw_val  = model.predict_proba(Xv)[:, 1]
            p_raw_test = model.predict_proba(Xte)[:, 1]
        else:
            model = XGBClassifier(
                n_estimators=xgb_cfg["n_estimators"],
                max_depth=xgb_cfg["max_depth"],
                learning_rate=xgb_cfg["learning_rate"],
                subsample=xgb_cfg["subsample"],
                colsample_bytree=xgb_cfg["colsample_bytree"],
                use_label_encoder=False, eval_metric="logloss",
                random_state=42, verbosity=0,
            )
            model.fit(X_train, y_train)
            p_raw_val  = model.predict_proba(X_val)[:, 1]
            p_raw_test = model.predict_proba(X_test)[:, 1]

        cal        = fit_platt(p_raw_val, y_val)
        p_cal_test = cal.transform(p_raw_test)

        # Save predictions for ROC / calibration figures
        np.savez_compressed(out_dir / f"predictions_{family}.npz",
                            y_test=y_test.astype(np.float32),
                            p_cal_test=p_cal_test.astype(np.float32))

        metrics = compute_all_metrics(y_test, p_cal_test)
        # Also record deprecated OLS slope for comparison table
        slope_ols, icept_ols = calibration_slope_ols_deprecated(y_test, p_cal_test)
        metrics["calibration_slope_ols_deprecated"] = slope_ols
        metrics["calibration_intercept_ols_deprecated"] = icept_ols
        metrics["prevalence"] = float(y_test.mean())

        results_v2[family] = metrics
        print(f"  ROC-AUC: {metrics['roc_auc']:.4f}")
        print(f"  Cal slope (logistic): {metrics['calibration_slope']:.4f}  (OLS was: {slope_ols:.4f})")
        print(f"  Gini: {metrics['gini']:.4f}   KS: {metrics['ks']:.4f}")

    out = out_dir / "T1_results_v2.json"
    with open(out, "w") as f:
        json.dump(results_v2, f, indent=2)
    print(f"\nSaved: {out}")
    return results_v2


if __name__ == "__main__":
    run()
