#!/usr/bin/env python3
"""
Scalper V3 — Dollar Bar Pipeline
- Dollar bár gyertyák (nem tick)
- TP = $30 abszolút (nem bps!)
- SL = TP szimmetrikus (nem kell külön megadni)
- Horizont = 3 perc (időalapú, nem tick)
- EGY modell: 3-os osztály (Long/Neutral/Short)
"""
import json, numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime
from sklearn.metrics import roc_auc_score, f1_score
from sklearn.model_selection import KFold
import lightgbm as lgb

DATA_DIR = Path('/data/dev/LGB_copilot_system/RAW_CSV')
MODEL_DIR = Path('/data/LGBM_copilot/models/scalper')
MODEL_DIR.mkdir(parents=True, exist_ok=True)

TP_DOLLAR = 30
HORIZON_SEC = 180
DOLLAR_THRESHOLD = 500_000


def load_tick_data(instrument='BTCUSD'):
    path = DATA_DIR / 'BTCUSD' / 'BTCUSD_külön_vizsga.csv'
    print(f"Loading {path}...")
    df = pd.read_csv(path, parse_dates=['Timestamp'], index_col='Timestamp')
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]
    print(f"  {len(df)} ticks, {df.index[0]} → {df.index[-1]}")
    return df


def build_dollar_bars(df, threshold=DOLLAR_THRESHOLD):
    """Dollar bars: Σ(price × volume) ≥ threshold → new bar."""
    mid = ((df['bid'] + df['ask']) / 2).values
    vol = (df['bid_volume'] + df['ask_volume']).values
    dollars = mid * vol
    timestamps = df.index.values
    bars, cum_d = [], 0.0
    o = h = l = c = None
    t0 = None
    for i in range(len(mid)):
        d = dollars[i]
        if o is None:
            o = h = l = c = mid[i]; cum_d = d; t0 = timestamps[i]; continue
        h = max(h, mid[i]); l = min(l, mid[i]); c = mid[i]; cum_d += d
        if cum_d >= threshold:
            bars.append({'timestamp': t0, 'open': o, 'high': h, 'low': l, 'close': c,
                         'volume': cum_d / c, 'dollar_volume': cum_d})
            o = None; cum_d = 0.0
    result = pd.DataFrame(bars)
    result['timestamp'] = pd.to_datetime(result['timestamp'])
    result = result.set_index('timestamp')
    print(f"  Dollar bars: {len(result)} (from {len(df)} ticks, ${threshold/1e6:.1f}M)")
    return result


def label_dollar_bars(bars, tp_dollar=TP_DOLLAR, horizon_sec=HORIZON_SEC):
    """
    Label each dollar bar: did price move +$tp (Long) or -$tp (Short) within horizon?
    SL = TP (szimmetrikus). Horizont in seconds.
    """
    closes = bars['close'].values
    timestamps = bars.index
    n = len(closes)
    long_lbl = np.zeros(n, dtype=np.int8)
    short_lbl = np.zeros(n, dtype=np.int8)
    print(f"  Labeling {n} bars: TP=${tp_dollar}, SL=${tp_dollar}, horizon={horizon_sec}s")
    for i in range(n):
        entry = closes[i]
        t_limit = timestamps[i] + pd.Timedelta(seconds=horizon_sec)
        for j in range(i + 1, n):
            if timestamps[j] > t_limit: break
            if closes[j] >= entry + tp_dollar: long_lbl[i] = 1; break
            elif closes[j] <= entry - tp_dollar: short_lbl[i] = 1; break
    nl, ns = long_lbl.sum(), short_lbl.sum()
    nn = n - nl - ns
    print(f"  Long: {nl:6d} ({nl/n:.1%}), Short: {ns:6d} ({ns/n:.1%}), Neutral: {nn:6d} ({nn/n:.1%})")
    print(f"  Signal rate: {(nl+ns)/n:.1%} (cél >10%)")
    return long_lbl, short_lbl


def compute_bar_features(bars):
    """Features from dollar bar OHLCV — clean, bar-native."""
    c, o, h, l, v = bars['close'], bars['open'], bars['high'], bars['low'], bars['volume']
    f = pd.DataFrame(index=bars.index)
    f['body'] = (c - o) / (h - l + 1e-10)
    f['upper_wick'] = (h - np.maximum(o, c)) / (h - l + 1e-10)
    f['lower_wick'] = (np.minimum(o, c) - l) / (h - l + 1e-10)
    f['bar_range'] = (h - l) / (c + 1e-10)
    lr = np.log(c / c.shift(1))
    for lag in [1, 2, 3, 5, 10, 20]: f[f'ret_{lag}'] = lr.rolling(lag).sum()
    for lag in [5, 10, 20, 60]: f[f'rv_{lag}'] = lr.rolling(lag).std()
    for lag in [20, 60]: f[f'skew_{lag}'] = lr.rolling(lag).skew()
    for lag in [10, 20, 60]:
        hh, ll = c.rolling(lag).max(), c.rolling(lag).min()
        f[f'rpos_{lag}'] = (c - ll) / (hh - ll + 1e-10)
    lv = np.log1p(v)
    f['vol_rel'] = lv / lv.rolling(20).mean()
    for lag in [5, 10, 20]: f[f'vol_ma_{lag}'] = lv.rolling(lag).mean() / (lv.rolling(60).mean() + 1e-10)
    f['vol_ret_5'] = f['ret_5'] * f['vol_rel']
    for span in [10, 30, 60]:
        ema = c.ewm(span=span).mean()
        f[f'ema_d_{span}'] = (c - ema) / (c.rolling(span).std() + 1e-10)
    up, dn = lr.clip(lower=0), (-lr).clip(lower=0)
    for span in [14, 28]:
        rs = up.ewm(span=span).mean() / (dn.ewm(span=span).mean() + 1e-10)
        rsi = 100 - 100 / (1 + rs)
        f[f'rsi_{span}'] = (rsi - 50) / 50
    dt = bars.index.to_series().diff().dt.total_seconds().fillna(0)
    f['bar_dt'] = np.log1p(dt)
    f['bar_dt_rel'] = f['bar_dt'] / (f['bar_dt'].rolling(20).mean() + 1e-10)
    f['cum_dir_5'] = lr.rolling(5).apply(lambda x: np.sign(x).sum(), raw=True)
    f['cum_dir_10'] = lr.rolling(10).apply(lambda x: np.sign(x).sum(), raw=True)
    return f.dropna()


def train_models(X, y_long, y_short, params=None):
    """Train 2 binary LGBM models with is_unbalance=True, 5-fold CV."""
    if params is None:
        params = {
            'objective': 'binary', 'metric': 'auc', 'boosting_type': 'gbdt',
            'num_leaves': 31, 'learning_rate': 0.03,
            'feature_fraction': 0.8, 'bagging_fraction': 0.7,
            'bagging_freq': 5, 'min_data_in_leaf': 100,
            'verbose': -1, 'n_jobs': -1,
            'reg_alpha': 0.05, 'reg_lambda': 0.3,
            'is_unbalance': True,
        }
    results = {}
    for name, y in [('Long', y_long), ('Short', y_short)]:
        print(f"\n  === {name} (5-fold CV, is_unbalance=True) ===")
        kf = KFold(n_splits=5, shuffle=False)
        oos = pd.Series(0.0, index=X.index)
        models, imps = [], []
        for fi_, (tri, tei) in enumerate(kf.split(X)):
            dtrain = lgb.Dataset(X.iloc[tri], label=y.iloc[tri])
            dvalid = lgb.Dataset(X.iloc[tei], label=y.iloc[tei])
            m = lgb.train(params, dtrain, num_boost_round=500, valid_sets=[dvalid],
                         callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)])
            oos.iloc[tei] = m.predict(X.iloc[tei])
            models.append(m)
            imps.append(pd.Series(m.feature_importance('gain'), index=X.columns))
        fi = pd.concat(imps, axis=1).mean(axis=1).sort_values(ascending=False)
        valid = oos > 0
        auc = roc_auc_score(y[valid], oos[valid])
        best_thr, best_f1 = 0.5, 0
        for thr in np.arange(0.3, 0.7, 0.02):
            f1 = f1_score(y[valid], (oos[valid] > thr).astype(int))
            if f1 > best_f1: best_thr, best_f1 = thr, f1
        print(f"    {name}: AUC={auc:.4f}, F1={best_f1:.3f}, thr={best_thr:.2f}")
        for lo, hi in [(0,0.05),(0.05,0.1),(0.1,0.2),(0.2,0.3),(0.3,0.5),(0.5,0.7),(0.7,1.0)]:
            cnt = ((oos>=lo) & (oos<hi)).sum()
            print(f"      [{lo:.2f}-{hi:.2f}): {cnt:5d} ({cnt/len(oos):.1%})")
        results[name.lower()] = {'models': models, 'auc': auc, 'pred': oos, 'fi': fi, 'thr': best_thr, 'f1': best_f1}
    return results


def run_pipeline(tp_dollar=TP_DOLLAR, horizon_sec=HORIZON_SEC):
    print(f"\n{'='*60}")
    print(f"SCALPER V3 — Dollar Bar Pipeline")
    print(f"  TP = ${tp_dollar}, SL = ${tp_dollar} (szimmetrikus)")
    print(f"  Horizont = {horizon_sec}s ({horizon_sec//60} perc)")
    print(f"  Dollar bár küszöb = ${DOLLAR_THRESHOLD/1e6:.1f}M")
    print(f"{'='*60}")

    df = load_tick_data('BTCUSD')
    print("\nDollar bars...")
    bars = build_dollar_bars(df, threshold=DOLLAR_THRESHOLD)

    print("\nLabeling...")
    long_lbl, short_lbl = label_dollar_bars(bars, tp_dollar=tp_dollar, horizon_sec=horizon_sec)
    pos_rate = (long_lbl.sum() + short_lbl.sum()) / len(bars)
    if pos_rate < 0.05:
        print(f"\n  ⚠️  Signal rate {pos_rate:.1%} < 5% → trying $20 TP...")
        tp_dollar = 20
        long_lbl, short_lbl = label_dollar_bars(bars, tp_dollar=tp_dollar, horizon_sec=horizon_sec)

    print("\nFeatures...")
    feat = compute_bar_features(bars)
    feat = feat.select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan).dropna()
    y_long = pd.Series(long_lbl, index=bars.index).loc[feat.index]
    y_short = pd.Series(short_lbl, index=bars.index).loc[feat.index]
    print(f"  {len(feat)} bars, {len(feat.columns)} features")

    print("\nTraining...")
    results = train_models(feat, y_long, y_short)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    saved = {}
    for sfx, r in results.items():
        mp = MODEL_DIR / f'BTCUSD_v3_{sfx}_{ts}.txt'
        r['models'][-1].save_model(str(mp))
        saved[sfx] = str(mp)
        r['fi'].to_csv(MODEL_DIR / f'BTCUSD_v3_{sfx}_imp_{ts}.csv', header=['imp'])
        print(f"  Top 5 {sfx}: {', '.join(r['fi'].head(5).index.tolist())}")

    preds = pd.DataFrame({'p_long': results['long']['pred'], 'p_short': results['short']['pred'],
                          'long_lbl': y_long, 'short_lbl': y_short}, index=feat.index)
    preds['net_signal'] = preds['p_long'] - preds['p_short']
    pp = MODEL_DIR / f'BTCUSD_v3_preds_{ts}.csv'
    preds.to_csv(pp)
    bars[['close']].loc[feat.index].to_csv(MODEL_DIR / f'BTCUSD_v3_price_{ts}.csv')

    both_low = ((preds['p_long'] < 0.05) & (preds['p_short'] < 0.05)).mean()
    print(f"\n  Both<0.05: {both_low:.1%}")
    print(f"  Net signal: mean={preds['net_signal'].mean():.3f}, std={preds['net_signal'].std():.3f}")

    meta = {
        'instrument': 'BTCUSD', 'timestamp': ts, 'version': 'scalper_v3_dollar',
        'tp_dollar': tp_dollar, 'sl_dollar': tp_dollar,
        'horizon_sec': horizon_sec, 'dollar_threshold': DOLLAR_THRESHOLD,
        'n_ticks': len(df), 'n_bars': len(bars), 'n_samples': len(feat),
        'n_features': len(feat.columns), 'feature_names': list(feat.columns),
        'long_auc': results['long']['auc'], 'short_auc': results['short']['auc'],
        'long_thr': results['long']['thr'], 'short_thr': results['short']['thr'],
        'models': saved, 'preds': str(pp), 'is_unbalance': True,
        'label_long_rate': float(y_long.mean()), 'label_short_rate': float(y_short.mean()),
        'both_under_005': float(both_low),
    }
    mp = MODEL_DIR / f'BTCUSD_v3_meta_{ts}.json'
    with open(mp, 'w') as f: json.dump(meta, f, indent=2)

    print(f"\n{'='*60}")
    print(f"V3 COMPLETE ✅  TP=${tp_dollar}, h={horizon_sec}s")
    print(f"  Long:  AUC={results['long']['auc']:.4f}, thr={results['long']['thr']:.2f}")
    print(f"  Short: AUC={results['short']['auc']:.4f}, thr={results['short']['thr']:.2f}")
    print(f"  Labels: Long {y_long.mean():.1%}, Short {y_short.mean():.1%}")
    print(f"  Both<0.05: {both_low:.1%}")
    print(f"{'='*60}")
    return results


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--tp', type=float, default=TP_DOLLAR, help='TP in dollars')
    ap.add_argument('--horizon', type=int, default=HORIZON_SEC, help='Horizon in seconds')
    args = ap.parse_args()
    run_pipeline(tp_dollar=args.tp, horizon_sec=args.horizon)