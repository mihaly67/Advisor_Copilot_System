#!/usr/bin/env python3
"""
v8_rolling_pivot.py — Rolling Pivot Rendszer
- N-ablakos gördülő retrain (pl. 5000 bar ablak, 1000 lépés)
- Pivot detektálás: swing high/low, S/R szintek
- Adaptív küszöb: P(Long) küszöb = f(volatility, regime)
"""
import sys, warnings, numpy as np, pandas as pd
warnings.filterwarnings('ignore')
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from scalper_copilot_v6 import load_ticks, make_dollar_bars, label_tbm, DATA_DIR, DOLLAR_THR, SEED
from build_features_v8 import build_features_v8, FEATURES_V8_PRUNED
import lightgbm as lgb
from sklearn.metrics import roc_auc_score


def detect_swing_points(bars, order=5):
    """Swing high/low detektálás. order: hány bar balra/jobbra"""
    h = bars['high'].values; l = bars['low'].values; n = len(bars); swings = []
    for i in range(order, n - order):
        is_high = all(h[i] >= h[i-k] for k in range(1, order+1)) and \
                  all(h[i] >= h[i+k] for k in range(1, order+1))
        if is_high: swings.append({'type': 'high', 'price': h[i], 'idx': i})
        is_low = all(l[i] <= l[i-k] for k in range(1, order+1)) and \
                 all(l[i] <= l[i+k] for k in range(1, order+1))
        if is_low: swings.append({'type': 'low', 'price': l[i], 'idx': i})
    return pd.DataFrame(swings) if swings else pd.DataFrame(columns=['type', 'price', 'idx'])


def cluster_pivot_levels(swings, tolerance_pct=0.003):
    """Közeli pivot pontok clusterelése S/R szintekké."""
    if len(swings) == 0: return []
    levels = []
    def _cluster(prices, label):
        if len(prices) == 0: return
        clusters = [[prices[0]]]
        for p in prices[1:]:
            if abs(p - np.mean(clusters[-1])) / np.mean(clusters[-1]) < tolerance_pct:
                clusters[-1].append(p)
            else: clusters.append([p])
        for c in clusters: levels.append({'level': np.mean(c), 'strength': len(c), 'type': label})
    _cluster(swings[swings['type']=='high']['price'].sort_values().values, 'resistance')
    _cluster(swings[swings['type']=='low']['price'].sort_values().values, 'support')
    levels.sort(key=lambda x: -x['strength'])
    return levels




def rolling_retrain(bars, feat_df, avail, horizon_sec=120,
                    window=5000, step=1000, min_train=3000, lgb_params=None):
    """Gördülő ablak retrain. Returns: dict of {end_idx: model} + AUC history"""
    if lgb_params is None:
        lgb_params = {'objective':'binary','metric':'auc','learning_rate':0.05,'num_leaves':31,
                      'feature_fraction':0.7,'bagging_fraction':0.8,'bagging_freq':5,
                      'seed':SEED,'verbose':-1,'min_data_in_leaf':50,'lambda_l1':1.0}
    n = len(feat_df); models = {}; auc_history = []
    for end in range(window, n, step):
        start = end - window
        feat_w = feat_df.iloc[start:end]; bars_w = bars.iloc[start:end]
        y, _ = label_tbm(bars_w, horizon_sec, pt_m=0.5, sl_m=0.3)
        valid = (y != 0)
        if valid.sum() < min_train: continue
        X = feat_w[valid].values; y_arr = y[valid]
        sp = int(len(X)*0.8); X_tr,X_va = X[:sp],X[sp:]; y_tr,y_va = y_arr[:sp],y_arr[sp:]
        dtr = lgb.Dataset(X_tr,label=y_tr,feature_name=avail)
        dva = lgb.Dataset(X_va,label=y_va,feature_name=avail,reference=dtr)
        m = lgb.train(lgb_params,dtr,200,[dva],callbacks=[lgb.early_stopping(20,verbose=False)])
        va_auc = roc_auc_score(y_va,m.predict(X_va))
        models[end] = m; auc_history.append({'end_idx':end,'auc':va_auc,'n_train':len(X_tr)})
        print(f'  [{start}:{end}] AUC={va_auc:.4f} n={len(X_tr):,}')
    return models, auc_history


if __name__ == '__main__':
    print('='*60); print('V8 ROLLING PIVOT SYSTEM'); print('='*60)
    ticks = load_ticks(str(DATA_DIR / 'BTCUSD_training_tick.csv'))
    bars = make_dollar_bars(ticks, DOLLAR_THR)
    feat, cols = build_features_v8(bars)
    avail = [c for c in FEATURES_V8_PRUNED if c in cols and c not in ('kill_zone','ema_d_5')]
    # 1. Swings
    print('\n1. Swing Detection (last 1000 bars)...')
    swings = detect_swing_points(bars.iloc[-1000:], order=5)
    print(f'   {len(swings)} swings: {(swings["type"]=="high").sum()} highs, {(swings["type"]=="low").sum()} lows')
    # 2. S/R Levels
    print('\n2. S/R Levels...')
    levels = cluster_pivot_levels(swings)
    for lvl in levels[:5]: print(f'   ${lvl["level"]:,.0f} ({lvl["type"]}, str={lvl["strength"]})')
    # 3. Adaptive threshold
    print('\n3. Adaptive Threshold...')
    for vol_pct in [0.001, 0.003, 0.005]:
        for regime in [-0.5, 0.0, 0.5]:
            lt, st = adaptive_threshold(vol_pct, regime)
            print(f'   vol={vol_pct:.3f} reg={regime:+.1f} -> L>{lt:.3f} S<{st:.3f}')
    print('\n✅ Rolling Pivot System ready!')
def adaptive_threshold(vol_pct, regime_score):
    """Adaptív küszöb: P(Long) threshold = f(vol, regime). Returns (long_thr, short_thr)"""
    base_long = 0.55; base_short = 0.45
    vol_adj = np.clip(vol_pct * 10, -0.05, 0.05)
    regime_adj = -0.03 * regime_score if abs(regime_score) > 0.3 else 0
    long_thr = np.clip(base_long - vol_adj + regime_adj, 0.50, 0.65)
    short_thr = np.clip(base_short + vol_adj - regime_adj, 0.35, 0.50)
    return long_thr, short_thr