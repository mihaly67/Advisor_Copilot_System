#!/usr/bin/env python3
"""Quick retrain + check prediction distribution with is_unbalance=True"""
import json, numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime
from sklearn.metrics import roc_auc_score, f1_score
from sklearn.model_selection import KFold
import lightgbm as lgb

MODEL_DIR = Path('/data/LGBM_copilot/models/scalper')
DATA_DIR = Path('/data/dev/LGB_copilot_system/RAW_CSV')

# Optuna v2 best: h=6, tp=7, sl=9, sub=7
horizon, tp_bps, sl_bps, subsample = 6, 7, 9, 7

print(f"Loading data...")
df = pd.read_csv(DATA_DIR / 'BTCUSD' / 'BTCUSD_külön_vizsga.csv',
                 parse_dates=['Timestamp'], index_col='Timestamp')
df.columns = [c.lower().replace(' ', '_') for c in df.columns]
df_sub = df.iloc[::subsample].copy()
mid = ((df_sub['bid'] + df_sub['ask']) / 2)
print(f"  {len(df_sub)} subsampled ticks")

# Label
tp_f, sl_f = tp_bps / 10000.0, sl_bps / 10000.0
mid_v = mid.values
n = len(mid_v)
long_lbl = np.zeros(n, dtype=np.int8)
short_lbl = np.zeros(n, dtype=np.int8)
print(f"Labeling: h={horizon}, tp={tp_bps}bps, sl={sl_bps}bps...")
for i in range(n - horizon):
    entry = mid_v[i]
    for j in range(1, horizon + 1):
        if i + j >= n: break
        if mid_v[i+j] >= entry * (1 + tp_f): long_lbl[i] = 1; break
        elif mid_v[i+j] <= entry * (1 - sl_f): short_lbl[i] = 1; break
nl, ns = long_lbl.sum(), short_lbl.sum()
print(f"  Long: {nl} ({nl/n:.1%}), Short: {ns} ({ns/n:.1%}), Skip: {n-nl-ns} ({(n-nl-ns)/n:.1%})")

# Quick features (reuse scalper_continuous logic)
from scalper_continuous import compute_tick_features
features = compute_tick_features(df_sub)
feat = features.select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan).dropna()
lab_long = pd.Series(long_lbl, index=df_sub.index).loc[feat.index]
lab_short = pd.Series(short_lbl, index=df_sub.index).loc[feat.index]
print(f"  {len(feat)} samples, {len(feat.columns)} features")

# Optuna v2 LGBM params with is_unbalance=True
lgbm_params = {
    'objective': 'binary', 'metric': 'auc', 'boosting_type': 'gbdt',
    'num_leaves': 28, 'learning_rate': 0.03,
    'feature_fraction': 0.86, 'bagging_fraction': 0.55,
    'bagging_freq': 5, 'min_data_in_leaf': 278,
    'verbose': -1, 'n_jobs': -1,
    'reg_alpha': 0.024, 'reg_lambda': 0.44,
    'is_unbalance': True,
}

# Train both models
for name, y in [('Long', lab_long), ('Short', lab_short)]:
    print(f"\n=== {name} (5-fold, is_unbalance=True) ===")
    params = lgbm_params.copy()
    kf = KFold(n_splits=5, shuffle=False)
    oos = pd.Series(0.0, index=feat.index)
    models, imps = [], []
    for fi_, (tri, tei) in enumerate(kf.split(feat)):
        dtrain = lgb.Dataset(feat.iloc[tri], label=y.iloc[tri])
        dvalid = lgb.Dataset(feat.iloc[tei], label=y.iloc[tei])
        m = lgb.train(params, dtrain, num_boost_round=500, valid_sets=[dvalid],
                     callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)])
        oos.iloc[tei] = m.predict(feat.iloc[tei])
        models.append(m)
        imps.append(pd.Series(m.feature_importance('gain'), index=feat.columns))
    fi = pd.concat(imps, axis=1).mean(axis=1).sort_values(ascending=False)
    valid = oos > 0
    auc = roc_auc_score(y[valid], oos[valid])
    best_thr, best_f1 = 0.5, 0
    for thr in np.arange(0.3, 0.7, 0.02):
        f1 = f1_score(y[valid], (oos[valid] > thr).astype(int))
        if f1 > best_f1: best_thr, best_f1 = thr, f1
    print(f"  {name}: AUC={auc:.4f}, thr={best_thr:.2f}")
    # Pred distribution
    for lo, hi in [(0,0.05),(0.05,0.1),(0.1,0.2),(0.2,0.3),(0.3,0.4),(0.4,0.5),(0.5,0.6),(0.6,0.7),(0.7,0.8),(0.8,1.0)]:
        cnt = ((oos>=lo) & (oos<hi)).sum()
        print(f"    [{lo:.2f}-{hi:.2f}): {cnt:6d} ({cnt/len(oos):.1%})")
    print(f"  Top 5: {', '.join(fi.head(5).index.tolist())}")

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    sfx = name.lower()
    models[-1].save_model(str(MODEL_DIR / f'BTCUSD_scalper_{sfx}_{ts}.txt'))
    fi.to_csv(MODEL_DIR / f'BTCUSD_scalper_{sfx}_imp_{ts}.csv', header=['imp'])
    if name == 'Long':
        long_auc, long_thr, long_pred = auc, best_thr, oos
        long_model_path = str(MODEL_DIR / f'BTCUSD_scalper_{sfx}_{ts}.txt')
    else:
        short_auc, short_thr, short_pred = auc, best_thr, oos
        short_model_path = str(MODEL_DIR / f'BTCUSD_scalper_{sfx}_{ts}.txt')

# Save preds + meta
ts = datetime.now().strftime('%Y%m%d_%H%M%S')
preds = pd.DataFrame({'p_long': long_pred, 'p_short': short_pred,
                      'long_lbl': lab_long, 'short_lbl': lab_short}, index=feat.index)
pp = MODEL_DIR / f'BTCUSD_scalper_preds_{ts}.csv'
preds.to_csv(pp)
mid.loc[feat.index].to_csv(MODEL_DIR / f'BTCUSD_scalper_price_{ts}.csv')
meta = {
    'instrument': 'BTCUSD', 'timestamp': ts, 'version': 'scalper_optuna_v2',
    'horizon': horizon, 'tp_bps': tp_bps, 'sl_bps': sl_bps,
    'subsample': subsample, 'n_ticks': len(df), 'n_samples': len(feat),
    'n_features': len(feat.columns), 'feature_names': list(feat.columns),
    'long_auc': long_auc, 'short_auc': short_auc,
    'long_thr': long_thr, 'short_thr': short_thr,
    'models': {'long': long_model_path, 'short': short_model_path, 'preds': str(pp)},
    'is_unbalance': True, 'label_long_rate': float(lab_long.mean()),
    'label_short_rate': float(lab_short.mean()),
}
mp = MODEL_DIR / f'BTCUSD_scalper_meta_{ts}.json'
with open(mp, 'w') as f: json.dump(meta, f, indent=2)
print(f"\n{'='*60}")
print(f"RETRAIN COMPLETE ✅ (is_unbalance=True)")
print(f"  Long:  AUC={long_auc:.4f}, thr={long_thr:.2f}")
print(f"  Short: AUC={short_auc:.4f}, thr={short_thr:.2f}")
print(f"  Labels: Long {lab_long.mean():.1%}, Short {lab_short.mean():.1%}")
print(f"  Meta: {mp}")
print(f"{'='*60}")
