#!/usr/bin/env python3
"""
Scalper V3 — Hybrid Pipeline
- Címkézés: dollar bár gyertyákon (TP=$30 abszolút, SL=TP, 3 perc)
- Feature-k: MTF tick feature-k a bár időpontjában (S/R, RSI, micro/sec/ter)
- 2 modell: Long + Short, is_unbalance=True
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
DOLLAR_THRESHOLD = 10_000_000  # $10M → ~2-3s bars, good granularity


def load_tick_data():
    path = DATA_DIR / 'BTCUSD' / 'BTCUSD_külön_vizsga.csv'
    print(f"Loading {path}...")
    df = pd.read_csv(path, parse_dates=['Timestamp'], index_col='Timestamp')
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]
    print(f"  {len(df)} ticks")
    return df


def build_dollar_bars(df, threshold=DOLLAR_THRESHOLD):
    """Dollar bars from tick data."""
    mid = ((df['bid'] + df['ask']) / 2).values
    vol = (df['bid_volume'] + df['ask_volume']).values
    dollars = mid * vol
    ts = df.index.values
    bars, cum_d = [], 0.0
    o = h = l = c = None; t0 = None
    for i in range(len(mid)):
        d = dollars[i]
        if o is None:
            o = h = l = c = mid[i]; cum_d = d; t0 = ts[i]; continue
        h = max(h, mid[i]); l = min(l, mid[i]); c = mid[i]; cum_d += d
        if cum_d >= threshold:
            bars.append({'timestamp': t0, 'open': o, 'high': h, 'low': l, 'close': c,
                         'volume': cum_d / c, 'dollar_volume': cum_d})
            o = None; cum_d = 0.0
    result = pd.DataFrame(bars)
    result['timestamp'] = pd.to_datetime(result['timestamp'])
    result = result.set_index('timestamp')
    avg_sec = result.index.to_series().diff().dt.total_seconds().mean()
    print(f"  {len(result)} dollar bars (avg {avg_sec:.1f}s/bar, ${threshold/1e6:.0f}M)")
    return result


def label_dollar_bars(bars, tp_dollar=TP_DOLLAR, horizon_sec=HORIZON_SEC):
    """Label each bar: +$tp = Long, -$tp = Short, within horizon seconds."""
    closes = bars['close'].values
    highs = bars['high'].values
    lows = bars['low'].values
    timestamps = bars.index
    n = len(closes)
    long_lbl = np.zeros(n, dtype=np.int8)
    short_lbl = np.zeros(n, dtype=np.int8)
    print(f"  Labeling: TP=${tp_dollar}, SL=${tp_dollar}, horizon={horizon_sec}s")
    for i in range(n):
        entry = closes[i]
        t_limit = timestamps[i] + pd.Timedelta(seconds=horizon_sec)
        for j in range(i + 1, n):
            if timestamps[j] > t_limit: break
            # Use high/low for more accurate labeling
            if highs[j] >= entry + tp_dollar: long_lbl[i] = 1; break
            elif lows[j] <= entry - tp_dollar: short_lbl[i] = 1; break
    nl, ns = long_lbl.sum(), short_lbl.sum()
    nn = n - nl - ns
    print(f"  Long: {nl:6d} ({nl/n:.1%}), Short: {ns:6d} ({ns/n:.1%}), Neutral: {nn:6d} ({nn/n:.1%})")
    return long_lbl, short_lbl


def compute_mtf_features_at_bars(df_ticks, bar_timestamps):
    """MTF tick features sampled at dollar bar timestamps."""
    mid = (df_ticks['bid'] + df_ticks['ask']) / 2
    atr = df_ticks.get('atr_m15', mid.rolling(15).std() * np.sqrt(15))
    f = pd.DataFrame(index=df_ticks.index)
    for tf in ['1m_close', '5m_close', '15m_close', '30m_close']:
        if tf in df_ticks.columns: f[f'd_{tf}'] = (mid - df_ticks[tf]) / (atr + 1e-10)
    f['atr_pct'] = atr / mid
    if 'rsi_m15' in df_ticks.columns:
        rsi = df_ticks['rsi_m15']
        f['rsi_n'] = (rsi - 50) / 50
        f['rsi_os'] = (rsi < 30).astype(int)
        f['rsi_ob'] = (rsi > 70).astype(int)
        f['rsi_mom'] = rsi.diff(5) / 50
    for lv in ['micro_r', 'sec_r', 'ter_r', 'micro_s', 'sec_s', 'ter_s']:
        if lv in df_ticks.columns: f[f'd_{lv}'] = (mid - df_ticks[lv]) / (atr + 1e-10)
    for px in ['micro', 'sec', 'ter']:
        rc, sc = f'{px}_r', f'{px}_s'
        if rc in df_ticks.columns and sc in df_ticks.columns:
            rng = df_ticks[rc] - df_ticks[sc]
            f[f'{px}_pos'] = (mid - df_ticks[sc]) / (rng + 1e-10)
            f[f'{px}_sqz'] = atr / (rng + 1e-10)
    if 'spread' in df_ticks.columns: f['sp_atr'] = df_ticks['spread'] / (atr + 1e-10)
    if 'bid_volume' in df_ticks.columns and 'ask_volume' in df_ticks.columns:
        bv, av = df_ticks['bid_volume'], df_ticks['ask_volume']
        f['vol_imb'] = (bv - av) / (bv + av + 1e-10)
        f['vol_tot'] = np.log1p(bv + av)
    mr = mid.pct_change()
    for lag in [1, 3, 5, 10, 20]: f[f'ret_{lag}'] = mid.pct_change(lag)
    for lag in [10, 20, 60]: f[f'tv_{lag}'] = mr.rolling(lag).std()
    for lag in [20, 60]: f[f'tsk_{lag}'] = mr.rolling(lag).skew()
    for lag in [20, 60]:
        hh, ll = mid.rolling(lag).max(), mid.rolling(lag).min()
        f[f'rpos_{lag}'] = (mid - ll) / (hh - ll + 1e-10)
    if '1m_close' in df_ticks.columns and '15m_close' in df_ticks.columns:
        f['mtf_al'] = np.sign(df_ticks['1m_close'].pct_change(5)) * np.sign(df_ticks['15m_close'].pct_change(5))
    f = f.dropna()
    bar_ts = pd.DatetimeIndex(bar_timestamps)
    idx_matches = f.index.get_indexer(bar_ts, method='nearest')
    valid = idx_matches >= 0
    feat_at_bars = f.iloc[idx_matches[valid]].copy()
    feat_at_bars.index = bar_ts[valid]
    return feat_at_bars


def train_models(X, y_long, y_short):
    params = {
        'objective': 'binary', 'metric': 'auc', 'boosting_type': 'gbdt',
        'num_leaves': 31, 'learning_rate': 0.03,
        'feature_fraction': 0.8, 'bagging_fraction': 0.7,
        'bagging_freq': 5, 'min_data_in_leaf': 200,
        'verbose': -1, 'n_jobs': -1,
        'reg_alpha': 0.05, 'reg_lambda': 0.3,
        'is_unbalance': True,
    }
    results = {}
    for name, y in [('Long', y_long), ('Short', y_short)]:
        print(f"\n  === {name} (5-fold CV) ===")
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
        print(f"    AUC={auc:.4f}, F1={best_f1:.3f}, thr={best_thr:.2f}")
        for lo, hi in [(0,0.05),(0.05,0.1),(0.1,0.2),(0.2,0.3),(0.3,0.5),(0.5,0.7),(0.7,1.0)]:
            cnt = ((oos>=lo) & (oos<hi)).sum()
            print(f"      [{lo:.2f}-{hi:.2f}): {cnt:5d} ({cnt/len(oos):.1%})")
        results[name.lower()] = {'models': models, 'auc': auc, 'pred': oos, 'fi': fi, 'thr': best_thr, 'f1': best_f1}
    return results


def run_pipeline(tp_dollar=TP_DOLLAR, horizon_sec=HORIZON_SEC):
    print(f"\n{'='*60}")
    print(f"SCALPER V3 HYBRID — Dollar Bar Labels + MTF Features")
    print(f"  TP = ${tp_dollar}, SL = ${tp_dollar}, horizon = {horizon_sec}s")
    print(f"{'='*60}")

    df = load_tick_data()
    print("\nDollar bars...")
    bars = build_dollar_bars(df)

    print("\nLabeling...")
    long_lbl, short_lbl = label_dollar_bars(bars, tp_dollar=tp_dollar, horizon_sec=horizon_sec)

    print("\nMTF features at bar timestamps...")
    feat = compute_mtf_features_at_bars(df, bars.index)
    feat = feat.select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan).dropna()
    common = bars.index.intersection(feat.index)
    feat = feat.loc[common]
    y_long = pd.Series(long_lbl, index=bars.index).loc[feat.index]
    y_short = pd.Series(short_lbl, index=bars.index).loc[feat.index]
    print(f"  {len(feat)} bars, {len(feat.columns)} features")

    print("\nTraining...")
    results = train_models(feat, y_long, y_short)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    saved = {}
    for sfx, r in results.items():
        mp = MODEL_DIR / f'BTCUSD_v3h_{sfx}_{ts}.txt'
        r['models'][-1].save_model(str(mp))
        saved[sfx] = str(mp)
        r['fi'].to_csv(MODEL_DIR / f'BTCUSD_v3h_{sfx}_imp_{ts}.csv', header=['imp'])
        print(f"  Top 5 {sfx}: {', '.join(r['fi'].head(5).index.tolist())}")

    preds = pd.DataFrame({'p_long': results['long']['pred'], 'p_short': results['short']['pred'],
                          'long_lbl': y_long, 'short_lbl': y_short}, index=feat.index)
    preds['net_signal'] = preds['p_long'] - preds['p_short']
    pp = MODEL_DIR / f'BTCUSD_v3h_preds_{ts}.csv'
    preds.to_csv(pp)
    bars[['close']].loc[feat.index].to_csv(MODEL_DIR / f'BTCUSD_v3h_price_{ts}.csv')

    both_low = ((preds['p_long'] < 0.05) & (preds['p_short'] < 0.05)).mean()
    print(f"\n  Both<0.05: {both_low:.1%}")
    print(f"  Net: mean={preds['net_signal'].mean():.3f}, std={preds['net_signal'].std():.3f}")

    meta = {
        'instrument': 'BTCUSD', 'timestamp': ts, 'version': 'scalper_v3_hybrid',
        'tp_dollar': tp_dollar, 'sl_dollar': tp_dollar, 'horizon_sec': horizon_sec,
        'dollar_threshold': DOLLAR_THRESHOLD,
        'n_ticks': len(df), 'n_bars': len(bars), 'n_samples': len(feat),
        'n_features': len(feat.columns), 'feature_names': list(feat.columns),
        'long_auc': results['long']['auc'], 'short_auc': results['short']['auc'],
        'long_thr': results['long']['thr'], 'short_thr': results['short']['thr'],
        'models': saved, 'preds': str(pp), 'is_unbalance': True,
        'label_long_rate': float(y_long.mean()), 'label_short_rate': float(y_short.mean()),
        'both_under_005': float(both_low),
    }
    mp = MODEL_DIR / f'BTCUSD_v3h_meta_{ts}.json'
    with open(mp, 'w') as fout: json.dump(meta, fout, indent=2)

    print(f"\n{'='*60}")
    print(f"V3 HYBRID COMPLETE ✅")
    print(f"  TP=${tp_dollar}, h={horizon_sec}s, bars=${DOLLAR_THRESHOLD/1e6:.0f}M")
    print(f"  Long:  AUC={results['long']['auc']:.4f}, thr={results['long']['thr']:.2f}")
    print(f"  Short: AUC={results['short']['auc']:.4f}, thr={results['short']['thr']:.2f}")
    print(f"  Labels: Long {y_long.mean():.1%}, Short {y_short.mean():.1%}")
    print(f"  Both<0.05: {both_low:.1%}")
    print(f"{'='*60}")


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--tp', type=float, default=TP_DOLLAR)
    ap.add_argument('--horizon', type=int, default=HORIZON_SEC)
    args = ap.parse_args()
    run_pipeline(tp_dollar=args.tp, horizon_sec=args.horizon)