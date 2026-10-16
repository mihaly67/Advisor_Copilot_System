#!/usr/bin/env python3
"""
Scalper V3 Retrain — Final retrain with Optuna best params
$50 TP, 60s horizon, $10M dollar bars, 5-fold CV
"""
import json, numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime
from sklearn.metrics import roc_auc_score, f1_score
from sklearn.model_selection import KFold
import lightgbm as lgb
import sys
sys.path.insert(0, str(Path(__file__).parent))
from scalper_v3_hybrid import (load_tick_data, build_dollar_bars,
                                label_dollar_bars, compute_mtf_features_at_bars)
MODEL_DIR = Path('/data/LGBM_copilot/models/scalper')
OPTUNA_PARAMS = {
    'objective': 'binary', 'metric': 'auc', 'boosting_type': 'gbdt',
    'num_leaves': 22, 'learning_rate': 0.0101,
    'feature_fraction': 0.583, 'bagging_fraction': 0.509,
    'bagging_freq': 5, 'min_data_in_leaf': 233,
    'reg_alpha': 0.584, 'reg_lambda': 0.0024,
    'verbose': -1, 'n_jobs': -1, 'is_unbalance': True,
}

def retrain(tp_dollar=50, horizon_sec=60, dollar_threshold=10_000_000):
    print(f"\n{'='*60}\nV3 RETRAIN — Optuna Best Params\n  TP=${tp_dollar}, SL=${tp_dollar}, h={horizon_sec}s\n{'='*60}")
    df = load_tick_data()
    bars = build_dollar_bars(df, threshold=dollar_threshold)
    long_lbl, short_lbl = label_dollar_bars(bars, tp_dollar=tp_dollar, horizon_sec=horizon_sec)
    feat = compute_mtf_features_at_bars(df, bars.index)
    feat = feat.select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan).dropna()
    common = bars.index.intersection(feat.index)
    feat = feat.loc[common]
    y_long = pd.Series(long_lbl, index=bars.index).loc[feat.index]
    y_short = pd.Series(short_lbl, index=bars.index).loc[feat.index]
    print(f"  {len(feat)} samples, {len(feat.columns)} features")
    results = {}
    for name, y in [('Long', y_long), ('Short', y_short)]:
        print(f"\n  === {name} (5-fold CV, Optuna params) ===")
        kf = KFold(n_splits=5, shuffle=False)
        oos = pd.Series(0.0, index=feat.index)
        models, imps = [], []
        for fi_, (tri, tei) in enumerate(kf.split(feat)):
            dtrain = lgb.Dataset(feat.iloc[tri], label=y.iloc[tri])
            dvalid = lgb.Dataset(feat.iloc[tei], label=y.iloc[tei])
            m = lgb.train(OPTUNA_PARAMS, dtrain, num_boost_round=1000, valid_sets=[dvalid],
                         callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)])
            oos.iloc[tei] = m.predict(feat.iloc[tei])
            models.append(m); imps.append(pd.Series(m.feature_importance('gain'), index=feat.columns))
        fi = pd.concat(imps, axis=1).mean(axis=1).sort_values(ascending=False)
        valid = oos > 0; auc = roc_auc_score(y[valid], oos[valid])
        best_thr, best_f1 = 0.5, 0
        for thr in np.arange(0.2, 0.8, 0.02):
            f1 = f1_score(y[valid], (oos[valid] > thr).astype(int))
            if f1 > best_f1: best_thr, best_f1 = thr, f1
        print(f"    AUC={auc:.4f}, F1={best_f1:.3f}, thr={best_thr:.2f}")
        for lo, hi in [(0,0.05),(0.05,0.1),(0.1,0.2),(0.2,0.3),(0.3,0.5),(0.5,0.7),(0.7,1.0)]:
            cnt = ((oos>=lo) & (oos<hi)).sum()
            print(f"      [{lo:.2f}-{hi:.2f}): {cnt:5d} ({cnt/len(oos):.1%})")
        results[name.lower()] = {'models': models, 'auc': auc, 'pred': oos, 'fi': fi, 'thr': best_thr, 'f1': best_f1}
    # Save
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    saved = {}
    for sfx, r in results.items():
        mp = MODEL_DIR / f'BTCUSD_v3f_{sfx}_{ts}.txt'
        r['models'][-1].save_model(str(mp)); saved[sfx] = str(mp)
        r['fi'].to_csv(MODEL_DIR / f'BTCUSD_v3f_{sfx}_imp_{ts}.csv', header=['imp'])
        print(f"  Top 5 {sfx}: {', '.join(r['fi'].head(5).index.tolist())}")
    preds = pd.DataFrame({'p_long': results['long']['pred'], 'p_short': results['short']['pred'],
                          'long_lbl': y_long, 'short_lbl': y_short}, index=feat.index)
    preds['net_signal'] = preds['p_long'] - preds['p_short']
    pp = MODEL_DIR / f'BTCUSD_v3f_preds_{ts}.csv'; preds.to_csv(pp)
    bars[['close']].loc[feat.index].to_csv(MODEL_DIR / f'BTCUSD_v3f_price_{ts}.csv')
    both_low = ((preds['p_long'] < 0.05) & (preds['p_short'] < 0.05)).mean()
    meta = {'instrument': 'BTCUSD', 'timestamp': ts, 'version': 'scalper_v3_final',
            'tp_dollar': tp_dollar, 'sl_dollar': tp_dollar, 'horizon_sec': horizon_sec,
            'dollar_threshold': dollar_threshold, 'n_bars': len(bars), 'n_samples': len(feat),
            'n_features': len(feat.columns), 'feature_names': list(feat.columns),
            'long_auc': results['long']['auc'], 'short_auc': results['short']['auc'],
            'long_thr': results['long']['thr'], 'short_thr': results['short']['thr'],
            'models': saved, 'preds': str(pp), 'is_unbalance': True,
            'label_long_rate': float(y_long.mean()), 'label_short_rate': float(y_short.mean()),
            'both_under_005': float(both_low)}
    mp = MODEL_DIR / f'BTCUSD_v3f_meta_{ts}.json'
    with open(mp, 'w') as f: json.dump(meta, f, indent=2)
    print(f"\n{'='*60}\nV3 FINAL ✅ Long AUC={results['long']['auc']:.4f} Short AUC={results['short']['auc']:.4f}\n  Labels: L {y_long.mean():.1%} S {y_short.mean():.1%} Both<0.05: {both_low:.1%}\n{'='*60}")
    return results

if __name__ == '__main__':
    retrain()