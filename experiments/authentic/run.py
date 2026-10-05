"""
Home Credit authentic experiment — T1 (TECH_DOC §16.1)

Validates LR/XGBoost/calibration/metrics pipeline on authentic credit data.
Uses application_train.csv only (bureau tables unused).
Split: stratified 60/20/20, seed 42.
"""
from __future__ import annotations
import argparse, json, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
warnings.filterwarnings("ignore")

from src.utils.config_loader import load_config
from src.models.train_models import train_model, WinsorisedScaler
from src.calibration.platt import fit_platt
from src.evaluation.metrics import compute_all_metrics, pr_auc, roc_auc, brier, ece

NUMERIC_FEATURES = [
    "AMT_INCOME_TOTAL","AMT_CREDIT","AMT_ANNUITY","AMT_GOODS_PRICE",
    "EXT_SOURCE_1","EXT_SOURCE_2","EXT_SOURCE_3",
    "CNT_CHILDREN","CNT_FAM_MEMBERS","REGION_RATING_CLIENT",
]
CATEGORICAL_FEATURES = [
    "NAME_CONTRACT_TYPE","NAME_INCOME_TYPE","NAME_EDUCATION_TYPE",
    "FLAG_OWN_CAR","FLAG_OWN_REALTY",
]
DERIVED = {
    "credit_income_ratio": lambda df: df["AMT_CREDIT"] / (df["AMT_INCOME_TOTAL"] + 1),
    "annuity_income_ratio": lambda df: df["AMT_ANNUITY"] / (df["AMT_INCOME_TOTAL"] + 1),
    "credit_term": lambda df: df["AMT_CREDIT"] / (df["AMT_ANNUITY"] + 1),
    "age_years": lambda df: df["DAYS_BIRTH"] / -365,
    "years_employed": lambda df: np.where(
        df["DAYS_EMPLOYED"] == 365243, np.nan, df["DAYS_EMPLOYED"] / -365
    ),
    "employed_flag": lambda df: (df["DAYS_EMPLOYED"] == 365243).astype(int),
}
TARGET = "TARGET"


def load_and_prepare(data_path: str):
    print(f"Loading {data_path}...")
    df = pd.read_csv(data_path)
    print(f"  Loaded: {len(df):,} rows, {df.shape[1]} cols. Default rate: {df[TARGET].mean():.3f}")

    # Derived features
    for name, fn in DERIVED.items():
        df[name] = fn(df)

    numeric_cols = NUMERIC_FEATURES + list(DERIVED.keys())
    cat_cols = CATEGORICAL_FEATURES

    # Split
    sss = StratifiedShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
    idx = np.arange(len(df))
    train_val_idx, test_idx = next(sss.split(idx, df[TARGET].values))
    sss2 = StratifiedShuffleSplit(n_splits=1, test_size=0.25, random_state=43)
    tv = train_val_idx
    train_rel, val_rel = next(sss2.split(tv, df[TARGET].values[tv]))
    train_idx = tv[train_rel]
    val_idx = tv[val_rel]

    print(f"  Split — train:{len(train_idx):,} val:{len(val_idx):,} test:{len(test_idx):,}")

    df_train = df.iloc[train_idx].copy()
    df_val   = df.iloc[val_idx].copy()
    df_test  = df.iloc[test_idx].copy()

    # Impute numeric
    imp = SimpleImputer(strategy="median")
    df_train[numeric_cols] = imp.fit_transform(df_train[numeric_cols])
    df_val[numeric_cols]   = imp.transform(df_val[numeric_cols])
    df_test[numeric_cols]  = imp.transform(df_test[numeric_cols])

    # One-hot encode categoricals
    enc = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
    cat_train = enc.fit_transform(df_train[cat_cols].astype(str))
    cat_val   = enc.transform(df_val[cat_cols].astype(str))
    cat_test  = enc.transform(df_test[cat_cols].astype(str))
    cat_names = enc.get_feature_names_out(cat_cols).tolist()

    X_train = np.hstack([df_train[numeric_cols].values, cat_train])
    X_val   = np.hstack([df_val[numeric_cols].values, cat_val])
    X_test  = np.hstack([df_test[numeric_cols].values, cat_test])
    y_train = df_train[TARGET].values
    y_val   = df_val[TARGET].values
    y_test  = df_test[TARGET].values
    feature_names = numeric_cols + cat_names

    return X_train, X_val, X_test, y_train, y_val, y_test, feature_names


def run_authentic(cfg_path: str):
    cfg = load_config(cfg_path)
    model_cfg = load_config("configs/models.yaml")
    data_path = "data/authentic/application_train.csv"

    X_train, X_val, X_test, y_train, y_val, y_test, feat_names = load_and_prepare(data_path)

    results = {}
    out_dir = Path("results/authentic")
    out_dir.mkdir(parents=True, exist_ok=True)

    for family in ["logreg", "xgb"]:
        print(f"\n--- Training {family.upper()} ---")
        from sklearn.linear_model import LogisticRegression
        from xgboost import XGBClassifier

        if family == "logreg":
            ws = WinsorisedScaler()
            X_tr = ws.fit_transform(X_train)
            X_v  = ws.transform(X_val)
            X_te = ws.transform(X_test)
            lr_cfg = model_cfg["models"]["logreg"]
            model = LogisticRegression(
                C=lr_cfg["C"], max_iter=lr_cfg["max_iter"],
                solver=lr_cfg["solver"], penalty=lr_cfg["penalty"],
                random_state=42
            )
            model.fit(X_tr, y_train)
            p_raw_val  = model.predict_proba(X_v)[:, 1]
            p_raw_test = model.predict_proba(X_te)[:, 1]
        else:
            xgb_cfg = model_cfg["models"]["xgb"]
            model = XGBClassifier(
                n_estimators=xgb_cfg["n_estimators"],
                max_depth=xgb_cfg["max_depth"],
                learning_rate=xgb_cfg["learning_rate"],
                subsample=xgb_cfg["subsample"],
                colsample_bytree=xgb_cfg["colsample_bytree"],
                use_label_encoder=False,
                eval_metric="logloss",
                random_state=42, verbosity=0
            )
            model.fit(X_train, y_train)
            p_raw_val  = model.predict_proba(X_val)[:, 1]
            p_raw_test = model.predict_proba(X_test)[:, 1]

        # Platt calibration on validation
        cal = fit_platt(p_raw_val, y_val)
        p_cal_val  = cal.transform(p_raw_val)
        p_cal_test = cal.transform(p_raw_test)

        metrics = compute_all_metrics(y_test, p_cal_test)
        metrics["prevalence"] = float(y_test.mean())
        results[family] = metrics

        print(f"  Test ROC-AUC:  {metrics['roc_auc']:.4f}")
        print(f"  Test PR-AUC:   {metrics['pr_auc']:.4f}  (baseline: {metrics['prevalence_baseline']:.4f})")
        print(f"  Test Brier:    {metrics['brier']:.4f}")
        print(f"  Test ECE:      {metrics['ece']:.4f}")
        print(f"  Calib slope:   {metrics['calibration_slope']:.4f}  intercept: {metrics['calibration_intercept']:.4f}")

    # Save results
    out_path = out_dir / "T1_results.json"
    with out_path.open("w") as fh:
        json.dump(results, fh, indent=2)
    print(f"\nT1 results saved to {out_path}")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/models.yaml")
    args = parser.parse_args()
    run_authentic(args.config)
