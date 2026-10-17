#!/usr/bin/env python3
"""
train_lgbm_meta.py — Meta-Labeling Secondary Modell (López de Prado)

A secondary modell BINÁRIS: trade(1) / no-trade(0)
A side (irány) már a primary modelltől jön (Slope_Close_14 alapján).

Logika:
  1. Primary modell (Slope_Close_14 > 0 → Long, < 0 → Short) megadja a side-t
  2. Secondary modell bináris predikciót ad: P(trade) = probability
  3. Ha P(trade) > threshold → trade (a side-dal)
  4. Ha P(trade) <= threshold → pass (nincs trade)

Értékelés:
  - Csak a trade-eket számoljuk (ahol secondary modell 1-et mond)
  - Profit: Long PT=+2.0, Long SL=-1.0, Short PT=+2.0, Short SL=-1.0
  - Opposite: a primary side rossz volt (SL hit)
"""
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
import joblib
import json
import os
import argparse

BASE = '/data/dev/projects/z-ai-copilot'

EXCLUDE = ['Start_Timestamp', 'End_Timestamp',
           'Open', 'High', 'Low', 'Close',
           'Target_Label', 'Side', 'Target_Meta']


def get_all_features(df):
    return [c for c in df.columns if c not in EXCLUDE and df[c].dtype != 'object']


def load_features(feature_file):
    if not feature_file:
        return None
    with open(feature_file) as f:
        return [line.strip() for line in f if line.strip()]


def evaluate_meta(y_test, probs, sides, th_trade=0.5):
    """
    Meta-labeling értékelés.

    y_test: a valódi Target_Meta (0/1) — 1=PT hit, 0=SL/vertical
    probs: secondary modell P(trade=1)
    sides: primary modell side (-1/+1)
    th_trade: küszöb, felette trade

    Profit számolás:
      Ha secondary mond trade (P > th) és Target_Meta=1 → PT hit → +2.0 profit
      Ha secondary mond trade (P > th) és Target_Meta=0 → SL hit → -1.0 profit (opposite!)
      Ha secondary mond pass → nincs trade
    """
    p_trade = probs[:, 1] if probs.shape[1] > 1 else probs

    preds_trade = (p_trade > th_trade).astype(int)

    n_trades = preds_trade.sum()
    n_wins = ((preds_trade == 1) & (y_test == 1)).sum()
    n_opposite = ((preds_trade == 1) & (y_test == 0)).sum()

    profit = n_wins * 2.0 - n_opposite * 1.0
    win_rate = n_wins / n_trades * 100 if n_trades > 0 else 0
    opp_rate = n_opposite / n_trades * 100 if n_trades > 0 else 0

    # Long/Short breakdown
    long_mask = (sides == 1) & (preds_trade == 1)
    short_mask = (sides == -1) & (preds_trade == 1)
    n_long = long_mask.sum()
    n_short = short_mask.sum()
    long_wins = ((long_mask) & (y_test == 1)).sum()
    short_wins = ((short_mask) & (y_test == 1)).sum()

    return {
        'n_trades': int(n_trades),
        'n_wins': int(n_wins),
        'n_opposite': int(n_opposite),
        'n_long': int(n_long),
        'n_short': int(n_short),
        'long_wins': int(long_wins),
        'short_wins': int(short_wins),
        'win_rate': round(win_rate, 1),
        'opposite_rate': round(opp_rate, 1),
        'profit': round(profit, 2),
        'avg_per_trade': round(profit / n_trades, 3) if n_trades > 0 else 0,
    }


def run_shap(clf, X_train, y_train, features, out_dir):
    print('\n=== SHAP ANALÍZIS ===')
    try:
        import shap
        sample_size = min(5000, len(X_train))
        X_sample = X_train.sample(n=sample_size, random_state=42)
        explainer = shap.TreeExplainer(clf)
        shap_values = explainer.shap_values(X_sample)

        if isinstance(shap_values, list):
            # binary: [class_0, class_1]
            shap_trade = np.abs(shap_values[1]).mean(axis=0) if len(shap_values) > 1 else np.abs(shap_values[0]).mean(axis=0)
            shap_pass = np.abs(shap_values[0]).mean(axis=0) if len(shap_values) > 1 else np.zeros(len(features))
        else:
            shap_trade = np.abs(shap_values).mean(axis=0)
            shap_pass = np.zeros(len(features))

        shap_df = pd.DataFrame({
            'feature': features,
            'SHAP_Trade': shap_trade,
            'SHAP_Pass': shap_pass,
        })
        shap_df['SHAP_Total'] = shap_df['SHAP_Trade'] + shap_df['SHAP_Pass']
        shap_df = shap_df.sort_values('SHAP_Total', ascending=False)
        out_csv = os.path.join(out_dir, 'shap_importance.csv')
        shap_df.to_csv(out_csv, index=False)
        print(f'SHAP mentve: {out_csv}')
        print('\nTop 15 SHAP:')
        print(shap_df.head(15)[['feature', 'SHAP_Total', 'SHAP_Trade']].to_string(index=False))
        return shap_df
    except Exception as e:
        print(f'SHAP hiba: {e}')
        return None


def main():
    parser = argparse.ArgumentParser(description='Meta-labeling secondary LGBM')
    parser.add_argument('--version', type=str, default='meta_v1')
    parser.add_argument('--features', type=str, default=None)
    parser.add_argument('--data', type=str, default=None)
    parser.add_argument('--th_trade', type=float, default=0.5, help='Trade küszöb')
    args = parser.parse_args()

    print(f'=== META-LABELING LGBM — Version: {args.version} ===')

    out_dir = os.path.join(BASE, 'models', args.version)
    os.makedirs(out_dir, exist_ok=True)

    data_path = args.data or os.path.join(BASE, 'Master_csv', 'processed', 'labeled_dollar_bars_v8.csv')
    print(f'\nAdat: {data_path}')
    df = pd.read_csv(data_path)
    print(f'   {len(df):,} sor, {df.shape[1]} oszlop')

    # Feature-k
    if args.features:
        features = load_features(args.features)
        print(f'   Feature fájl: {args.features} -> {len(features)} feature')
    else:
        features = get_all_features(df)
        print(f'   Összes feature: {len(features)}')

    missing = [f for f in features if f not in df.columns]
    if missing:
        print(f'Hiányzó: {missing}')
        features = [f for f in features if f in df.columns]

    X = df[features]
    y = df['Target_Meta'].astype(int)  # 0=pass, 1=trade
    sides = df['Side'].values  # -1=Short, +1=Long

    X_train, X_test, y_train, y_test, sides_train, sides_test = train_test_split(
        X, y, sides, test_size=0.2, shuffle=False
    )
    print(f'   Train: {len(X_train):,} | Test: {len(X_test):,}')
    print(f'   Train labels: {dict(y_train.value_counts().sort_index())}')
    print(f'   Test labels:  {dict(y_test.value_counts().sort_index())}')

    print('\nBetanitas (binary)...')
    clf = lgb.LGBMClassifier(
        n_estimators=781, learning_rate=0.0142,
        num_leaves=57, max_depth=6, min_child_samples=24,
        colsample_bytree=0.566,
        class_weight='balanced',
        objective='binary',
        random_state=42, n_jobs=1,
        device='gpu', gpu_platform_id=0, gpu_device_id=0,
        verbose=-1,
    )
    clf.fit(X_train, y_train, eval_set=[(X_test, y_test)],
            callbacks=[lgb.log_evaluation(100)])

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f'\n--- EREDMÉNY ({args.version}) ---')
    print(f'Accuracy: {acc*100:.2f}%')
    print(classification_report(y_test, y_pred, target_names=['Pass', 'Trade'], zero_division=0))

    # AUC
    probs = clf.predict_proba(X_test)
    try:
        auc = roc_auc_score(y_test, probs[:, 1])
        print(f'AUC: {auc:.4f}')
    except:
        auc = 0.0

    # Több küszöb értékelése
    print(f'\n--- THRESHOLD ÉRTÉKELÉS ---')
    best_profit = -999
    best_th = 0.5
    for th in [0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]:
        ev = evaluate_meta(y_test.values, probs, sides_test, th_trade=th)
        print(f'  th={th:.2f}: Trades={ev["n_trades"]:4d} '
              f'Win={ev["win_rate"]:5.1f}% Opp={ev["opposite_rate"]:5.1f}% '
              f'Profit={ev["profit"]:7.1f}$ L:{ev["n_long"]} S:{ev["n_short"]}')
        if ev['profit'] > best_profit:
            best_profit = ev['profit']
            best_th = th
            best_ev = ev

    print(f'\n  >>> LEGJOBB: th={best_th:.2f} Profit={best_profit}$ '
          f'Win={best_ev["win_rate"]}% Opp={best_ev["opposite_rate"]}% '
          f'Trades={best_ev["n_trades"]}')

    # Primary modell nélküli baseline (minden trade)
    all_trades = len(y_test)
    all_wins = (y_test == 1).sum()
    all_opp = (y_test == 0).sum()
    base_profit = all_wins * 2.0 - all_opp * 1.0
    print(f'\n  [BASELINE: all trades] Trades={all_trades} '
          f'Win={all_wins/all_trades*100:.1f}% Profit={base_profit}$')

    # Modell mentés
    model_path = os.path.join(out_dir, 'model.pkl')
    joblib.dump(clf, model_path)
    print(f'\nModell: {model_path}')

    with open(os.path.join(out_dir, 'features.txt'), 'w') as f:
        for feat in features:
            f.write(feat + '\n')

    imp = pd.DataFrame({'feature': features,
                        'importance': clf.feature_importances_
                        }).sort_values('importance', ascending=False)
    imp.to_csv(os.path.join(out_dir, 'feature_importance.csv'), index=False)

    metrics = {
        'version': args.version, 'n_features': len(features),
        'accuracy': round(acc * 100, 2), 'auc': round(auc, 4),
        'n_train': len(X_train), 'n_test': len(X_test),
        'data_path': data_path,
        'best_threshold': best_th,
        'best_eval': best_ev,
        'baseline_profit': round(base_profit, 2),
        'baseline_trades': all_trades,
        'baseline_win_rate': round(all_wins / all_trades * 100, 1),
    }
    with open(os.path.join(out_dir, 'metrics.json'), 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f'Metrics: {os.path.join(out_dir, "metrics.json")}')

    run_shap(clf, X_train, y_train, features, out_dir)
    print(f'\n✅ {args.version} KÉSZ! -> {out_dir}/')
    return clf


if __name__ == '__main__':
    main()
