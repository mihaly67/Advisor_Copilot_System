#!/usr/bin/env python3
# train_lgbm_v2.py rewrite — clean version with --data support
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import json
import os
import sys
import argparse

BASE = '/data/dev/projects/z-ai-copilot'
DATA_PATH_DEFAULT = os.path.join(BASE, 'Master_csv', 'processed', 'labeled_dollar_bars_adaptive.csv')

EXCLUDE = ['Start_Timestamp', 'End_Timestamp',
           'Open', 'High', 'Low', 'Close', 'Target_Label']


def get_all_features(df):
    return [c for c in df.columns if c not in EXCLUDE]


def load_features(feature_file):
    if not feature_file:
        return None
    with open(feature_file) as f:
        return [line.strip() for line in f if line.strip()]


def run_shap(clf, X_train, y_train, features, out_dir):
    print('\n=== SHAP ANALÍZIS ===')
    try:
        import shap
        sample_size = min(5000, len(X_train))
        X_sample = X_train.sample(n=sample_size, random_state=42)
        explainer = shap.TreeExplainer(clf)
        shap_values = explainer.shap_values(X_sample)
        if isinstance(shap_values, list):
            n_classes = len(shap_values)
            shap_imp = np.zeros((len(features), n_classes))
            for c in range(n_classes):
                shap_imp[:, c] = np.abs(shap_values[c]).mean(axis=0)
        else:
            shap_imp = np.abs(shap_values).mean(axis=0)
        class_names = ['Short', 'Noise', 'Long']
        shap_df = pd.DataFrame({
            'feature': features,
            'SHAP_Short': shap_imp[:, 0],
            'SHAP_Noise': shap_imp[:, 1],
            'SHAP_Long': shap_imp[:, 2],
        })
        shap_df['SHAP_Total'] = shap_df[['SHAP_Short', 'SHAP_Noise', 'SHAP_Long']].sum(axis=1)
        shap_df['Long_minus_Short'] = shap_df['SHAP_Long'] - shap_df['SHAP_Short']
        shap_df = shap_df.sort_values('SHAP_Total', ascending=False)
        out_csv = os.path.join(out_dir, 'shap_importance.csv')
        shap_df.to_csv(out_csv, index=False)
        print(f'SHAP mentve: {out_csv}')
        print('\nTop 15 SHAP:')
        print(shap_df.head(15)[['feature', 'SHAP_Total', 'SHAP_Short', 'SHAP_Long']].to_string(index=False))
        return shap_df
    except Exception as e:
        print(f'SHAP hiba: {e}')
        return None


def evaluate_predictions(y_test, probs, classes, th_long=0.35, th_short=0.564,
                         short_zero=False):
    idx_short = list(classes).index(0)
    idx_noise = list(classes).index(1)
    idx_long = list(classes).index(2)
    p_short = probs[:, idx_short]
    p_long = probs[:, idx_long]
    preds = []
    for i in range(len(p_short)):
        if short_zero:
            if p_long[i] > th_long:
                preds.append(2)
            else:
                preds.append(1)
        else:
            if p_short[i] > th_short:
                preds.append(0)
            elif p_long[i] > th_long:
                preds.append(2)
            else:
                preds.append(1)
    preds = np.array(preds)
    profit = 0.0
    n_trades = 0
    n_wins = 0
    n_opposite = 0
    n_long_trades = 0
    n_short_trades = 0
    for i in range(len(preds)):
        actual = y_test.iloc[i] if hasattr(y_test, 'iloc') else y_test[i]
        pred = preds[i]
        if pred == 1:
            continue
        n_trades += 1
        if pred == 2:
            n_long_trades += 1
            if actual == 2:
                profit += 2.0
                n_wins += 1
            elif actual == 0:
                profit -= 1.0
                n_opposite += 1
            else:
                profit -= 1.0
        elif pred == 0:
            n_short_trades += 1
            if actual == 0:
                profit += 2.0
                n_wins += 1
            elif actual == 2:
                profit -= 1.0
                n_opposite += 1
            else:
                profit -= 1.0
    win_rate = n_wins / n_trades * 100 if n_trades > 0 else 0
    opp_rate = n_opposite / n_trades * 100 if n_trades > 0 else 0
    return {
        'n_trades': n_trades,
        'n_wins': n_wins,
        'n_opposite': n_opposite,
        'n_long': n_long_trades,
        'n_short': n_short_trades,
        'win_rate': round(win_rate, 1),
        'opposite_rate': round(opp_rate, 1),
        'profit': round(profit, 2),
        'avg_per_trade': round(profit / n_trades, 3) if n_trades > 0 else 0,
        'predictions': preds,
    }


def main():
    parser = argparse.ArgumentParser(description='Verziozott LGBM betanitas')
    parser.add_argument('--version', type=str, default='v1')
    parser.add_argument('--features', type=str, default=None)
    parser.add_argument('--short_zero', action='store_true')
    parser.add_argument('--th_long', type=float, default=0.35)
    parser.add_argument('--th_short', type=float, default=0.564)
    parser.add_argument('--class_weight_short', type=float, default=1.5)
    parser.add_argument('--class_weight_noise', type=float, default=0.5)
    parser.add_argument('--class_weight_long', type=float, default=1.3)
    parser.add_argument('--data', type=str, default=None, help='Label CSV path')
    args = parser.parse_args()

    print(f'=== LIGHTGBM V2 — Version: {args.version} ===')
    print(f'   Short zero: {args.short_zero}')

    out_dir = os.path.join(BASE, 'models', args.version)
    os.makedirs(out_dir, exist_ok=True)

    data_path = args.data or DATA_PATH_DEFAULT
    print(f'\nAdat: {data_path}')
    df = pd.read_csv(data_path)
    print(f'   {len(df):,} sor, {df.shape[1]} oszlop')

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
    y = df['Target_Label']
    y_shifted = (y + 1).astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_shifted, test_size=0.2, shuffle=False
    )
    print(f'   Train: {len(X_train):,} | Test: {len(X_test):,}')
    print(f'   Train labels: {dict(y_train.value_counts().sort_index())}')
    print(f'   Test labels:  {dict(y_test.value_counts().sort_index())}')

    print('\nBetanitas...')
    clf = lgb.LGBMClassifier(
        n_estimators=781, learning_rate=0.0142,
        num_leaves=57, max_depth=6, min_child_samples=24,
        colsample_bytree=0.566,
        class_weight={0: args.class_weight_short,
                      1: args.class_weight_noise,
                      2: args.class_weight_long},
        objective='multiclass', num_class=3,
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
    print(classification_report(y_test, y_pred,
                                 target_names=['Short', 'Noise', 'Long'],
                                 zero_division=0))

    probs = clf.predict_proba(X_test)
    classes = clf.classes_
    ev_sz = evaluate_predictions(y_test, probs, classes,
                                 args.th_long, args.th_short, short_zero=args.short_zero)
    ev_n = evaluate_predictions(y_test, probs, classes,
                                args.th_long, args.th_short, short_zero=False)

    mode = 'LONG-ONLY (Short=0)' if args.short_zero else 'NORMAL'
    print(f'\n--- THRESHOLD ÉRTÉKELÉS ({mode}) ---')
    print(f'Trades: {ev_sz["n_trades"]} '
          f'(L:{ev_sz["n_long"]} S:{ev_sz["n_short"]})')
    print(f'Win rate: {ev_sz["win_rate"]}% | Opposite: {ev_sz["opposite_rate"]}%')
    print(f'Profit: {ev_sz["profit"]}$ | Avg/trade: {ev_sz["avg_per_trade"]}$')
    print(f'[NORMAL ref] Trades: {ev_n["n_trades"]} Profit: {ev_n["profit"]}$')

    imp = pd.DataFrame({'feature': features,
                        'importance': clf.feature_importances_
                        }).sort_values('importance', ascending=False)

    model_path = os.path.join(out_dir, 'model.pkl')
    joblib.dump(clf, model_path)
    print(f'\nModell: {model_path}')

    with open(os.path.join(out_dir, 'features.txt'), 'w') as f:
        for feat in features:
            f.write(feat + '\n')
    imp.to_csv(os.path.join(out_dir, 'feature_importance.csv'), index=False)

    metrics = {
        'version': args.version, 'n_features': len(features),
        'short_zero': args.short_zero, 'accuracy': round(acc*100, 2),
        'n_train': len(X_train), 'n_test': len(X_test),
        'data_path': data_path,
        'threshold_eval': {k: v for k, v in ev_sz.items() if k != 'predictions'},
        'normal_eval': {k: v for k, v in ev_n.items() if k != 'predictions'},
    }
    with open(os.path.join(out_dir, 'metrics.json'), 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f'Metrics: {os.path.join(out_dir, "metrics.json")}')

    shap_df = run_shap(clf, X_train, y_train, features, out_dir)
    print(f'\n✅ {args.version} KÉSZ! -> {out_dir}/')
    return clf


if __name__ == '__main__':
    main()
