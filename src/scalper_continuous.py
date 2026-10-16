"""
Scalper Continuous Pipeline — P(Long), P(Short) every tick
NOT event-based. Continuous directional probability for scalping.
"""
import json, numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime

DATA_DIR = Path('/data/dev/LGB_copilot_system/RAW_CSV')
MODEL_DIR = Path('/data/LGBM_copilot/models/scalper')
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def load_tick_data(instrument='BTCUSD', use_full=False):
    if instrument == 'BTCUSD':
        path = DATA_DIR / 'BTCUSD' / ('Scalper_Copilot_MTF_Data_v2_BTCUSD.csv' if use_full else 'BTCUSD_külön_vizsga.csv')
    else:
        path = DATA_DIR / 'XAUUSD' / ('Scalper_Copilot_MTF_Data_v2.csv' if use_full else 'Scalper_Copilot_MTF_Data_külön_vizsga.csv')
    print(f"Loading {path}...")
    df = pd.read_csv(path, parse_dates=['Timestamp'], index_col='Timestamp')
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]
    tpm = len(df) / ((df.index[-1] - df.index[0]).total_seconds() / 60)
    print(f"  {len(df)} ticks, ~{tpm:.0f} ticks/min")
    return df


def label_tick_direction(df, horizon=20, tp_bps=5, sl_bps=5):
    """Label each tick: did price go up (Long=1) or down (Short=1) within horizon?"""
    mid = ((df['bid'] + df['ask']) / 2).values
    n = len(mid)
    long_lbl = np.zeros(n, dtype=np.int8)
    short_lbl = np.zeros(n, dtype=np.int8)
    tp_f = tp_bps / 10000.0
    sl_f = sl_bps / 10000.0
    print(f"  Labeling {n} ticks (horizon={horizon}, TP={tp_bps}bps, SL={sl_bps}bps)...")
    for i in range(n - horizon):
        entry = mid[i]
        for j in range(1, horizon + 1):
            if i + j >= n: break
            if mid[i+j] >= entry * (1 + tp_f):
                long_lbl[i] = 1; break
            elif mid[i+j] <= entry * (1 - sl_f):
                short_lbl[i] = 1; break
    labels = pd.DataFrame({'long': long_lbl, 'short': short_lbl}, index=df.index)
    nl, ns = long_lbl.sum(), short_lbl.sum()
    print(f"  Long: {nl} ({nl/n:.1%}), Short: {ns} ({ns/n:.1%}), Skip: {n-nl-ns} ({(n-nl-ns)/n:.1%})")
    return labels


def compute_tick_features(df):
    """MTF features at every tick — same features EA provides in real-time."""
    mid = (df['bid'] + df['ask']) / 2
    atr = df.get('atr_m15', mid.rolling(15).std() * np.sqrt(15))
    f = pd.DataFrame(index=df.index)
    # MTF distances
    for tf in ['1m_close', '5m_close', '15m_close', '30m_close']:
        if tf in df.columns: f[f'd_{tf}'] = (mid - df[tf]) / (atr + 1e-10)
    f['atr_pct'] = atr / mid
    # RSI
    if 'rsi_m15' in df.columns:
        rsi = df['rsi_m15']
        f['rsi_n'] = (rsi - 50) / 50
        f['rsi_os'] = (rsi < 30).astype(int)
        f['rsi_ob'] = (rsi > 70).astype(int)
        f['rsi_mom'] = rsi.diff(5) / 50
    # S/R distances
    for lv in ['micro_r', 'sec_r', 'ter_r', 'micro_s', 'sec_s', 'ter_s']:
        if lv in df.columns: f[f'd_{lv}'] = (mid - df[lv]) / (atr + 1e-10)
    # S/R position
    for px in ['micro', 'sec', 'ter']:
        rc, sc = f'{px}_r', f'{px}_s'
        if rc in df.columns and sc in df.columns:
            rng = df[rc] - df[sc]
            f[f'{px}_pos'] = (mid - df[sc]) / (rng + 1e-10)
            f[f'{px}_sqz'] = atr / (rng + 1e-10)
    # Spread
    if 'spread' in df.columns: f['sp_atr'] = df['spread'] / (atr + 1e-10)
    # Volume
    if 'bid_volume' in df.columns and 'ask_volume' in df.columns:
        bv, av = df['bid_volume'], df['ask_volume']
        f['vol_imb'] = (bv - av) / (bv + av + 1e-10)
        f['vol_tot'] = np.log1p(bv + av)
    # Returns
    mr = mid.pct_change()
    for lag in [1, 3, 5, 10, 20]: f[f'ret_{lag}'] = mid.pct_change(lag)
    for lag in [10, 20, 60]: f[f'tv_{lag}'] = mr.rolling(lag).std()
    for lag in [20, 60]: f[f'tsk_{lag}'] = mr.rolling(lag).skew()
    for lag in [20, 60]:
        hh, ll = mid.rolling(lag).max(), mid.rolling(lag).min()
        f[f'rpos_{lag}'] = (mid - ll) / (hh - ll + 1e-10)
    # MTF alignment
    if '1m_close' in df.columns and '15m_close' in df.columns:
        f['mtf_al'] = np.sign(df['1m_close'].pct_change(5)) * np.sign(df['15m_close'].pct_change(5))
    return f.dropna()


def train_direction_model(X, y, name='long'):
    import lightgbm as lgb
    from sklearn.model_selection import KFold
    from sklearn.metrics import roc_auc_score, f1_score
    params = {
        'objective': 'binary', 'metric': 'auc', 'boosting_type': 'gbdt',
        'num_leaves': 63, 'learning_rate': 0.05, 'feature_fraction': 0.5,
        'bagging_fraction': 0.7, 'bagging_freq': 5, 'min_data_in_leaf': 200,
        'verbose': -1, 'n_jobs': -1, 'reg_alpha': 0.1, 'reg_lambda': 0.1,
    }
    n_pos = y.sum()
    n_neg = len(y) - n_pos
    if n_pos < 100: print(f"  {name}: too few pos ({n_pos})"); return None
    params['scale_pos_weight'] = n_neg / max(n_pos, 1)
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
    auc = roc_auc_score(y[valid], oos[valid]) if valid.sum() > 50 else 0
    best_thr, best_f1 = 0.5, 0
    for thr in np.arange(0.3, 0.7, 0.02):
        f1 = f1_score(y[valid], (oos[valid] > thr).astype(int))
        if f1 > best_f1: best_thr, best_f1 = thr, f1
    print(f"  {name}: AUC={auc:.4f}, thr={best_thr:.2f}, pos={n_pos} ({n_pos/len(y):.1%})")
    return {'models': models, 'auc': auc, 'pred': oos, 'fi': fi, 'thr': best_thr}


def run_scalper_pipeline(instrument='BTCUSD', horizon=20, tp_bps=5, sl_bps=5, use_full=False, subsample=5):
    print(f"\n{'='*60}\nSCALPER CONTINUOUS — {instrument}\n{'='*60}")
    df = load_tick_data(instrument, use_full=use_full)
    df_sub = df.iloc[::subsample].copy() if subsample > 1 else df
    print(f"\nSubsampled: {len(df_sub)} (every {subsample}th)")
    print("\nLabeling...")
    labels = label_tick_direction(df_sub, horizon=horizon, tp_bps=tp_bps, sl_bps=sl_bps)
    print("\nFeatures...")
    features = compute_tick_features(df_sub)
    common = labels.index.intersection(features.index)
    feat = features.loc[common].select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan).dropna()
    lab = labels.loc[feat.index]
    print(f"  {len(feat)} samples, {len(feat.columns)} features")
    print("\n=== LONG MODEL ===")
    lr = train_direction_model(feat, lab['long'], name='Long')
    print("\n=== SHORT MODEL ===")
    sr = train_direction_model(feat, lab['short'], name='Short')
    # Save
    import lightgbm as lgb
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    saved = {}
    for result, sfx in [(lr, 'long'), (sr, 'short')]:
        if result is None: continue
        mp = MODEL_DIR / f'{instrument}_scalper_{sfx}_{ts}.txt'
        result['models'][-1].save_model(str(mp))
        saved[sfx] = str(mp)
        result['fi'].to_csv(MODEL_DIR / f'{instrument}_scalper_{sfx}_imp_{ts}.csv', header=['imp'])
        print(f"  Top 5 {sfx}: {', '.join(result['fi'].head(5).index.tolist())}")
    if lr and sr:
        preds = pd.DataFrame({'p_long': lr['pred'], 'p_short': sr['pred'],
                              'long_lbl': lab['long'], 'short_lbl': lab['short']}, index=feat.index)
        pp = MODEL_DIR / f'{instrument}_scalper_preds_{ts}.csv'
        preds.to_csv(pp); saved['preds'] = str(pp)
    mid = ((df_sub['bid'] + df_sub['ask']) / 2).loc[feat.index]
    mid.to_csv(MODEL_DIR / f'{instrument}_scalper_price_{ts}.csv')
    meta = {
        'instrument': instrument, 'timestamp': ts, 'version': 'scalper_continuous',
        'horizon': horizon, 'tp_bps': tp_bps, 'sl_bps': sl_bps,
        'subsample': subsample, 'n_ticks': len(df), 'n_samples': len(feat),
        'n_features': len(feat.columns), 'feature_names': list(feat.columns),
        'long_auc': lr['auc'] if lr else 0, 'short_auc': sr['auc'] if sr else 0,
        'long_thr': lr['thr'] if lr else 0.5, 'short_thr': sr['thr'] if sr else 0.5,
        'models': saved,
    }
    mp = MODEL_DIR / f'{instrument}_scalper_meta_{ts}.json'
    with open(mp, 'w') as f: json.dump(meta, f, indent=2)
    print(f"\n{'='*60}\nSCALPER COMPLETE ✅")
    if lr: print(f"  Long:  AUC={lr['auc']:.4f}, thr={lr['thr']:.2f}")
    if sr: print(f"  Short: AUC={sr['auc']:.4f}, thr={sr['thr']:.2f}")
    print(f"  ~{60/subsample:.0f} pred/min | Meta: {mp}\n{'='*60}")
    return meta, lr, sr


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--instrument', default='BTCUSD')
    p.add_argument('--horizon', type=int, default=20)
    p.add_argument('--tp', type=int, default=5)
    p.add_argument('--sl', type=int, default=5)
    p.add_argument('--subsample', type=int, default=5)
    p.add_argument('--full', action='store_true')
    a = p.parse_args()
    run_scalper_pipeline(a.instrument, a.horizon, a.tp, a.sl, a.full, a.subsample)