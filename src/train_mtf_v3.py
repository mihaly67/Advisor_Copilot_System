"""
Scalper MTF Pipeline v2 — Full Scalper data → MTF side model + meta-labeling
Key: use MTF indicators (RSI, ATR, S/R) as SIDE model, then meta-label
"""
import sys, json, numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/data/LGBM_copilot/knowledge/code_templates')
from labeling_meta_labeling import triple_barrier_meta
from sample_weights import compute_sample_weights
from cross_validation_purged import PurgedKFold

DATA_DIR = Path('/data/dev/LGB_copilot_system/RAW_CSV')
MODEL_DIR = Path('/data/LGBM_copilot/models')


def load_scalper_m1(instrument='BTCUSD', freq='1min', use_full=False):
    """Load scalper tick data and resample to bars."""
    if instrument == 'BTCUSD':
        if use_full:
            path = DATA_DIR / 'BTCUSD' / 'Scalper_Copilot_MTF_Data_v2_BTCUSD.csv'
        else:
            path = DATA_DIR / 'BTCUSD' / 'BTCUSD_külön_vizsga.csv'
    else:
        if use_full:
            path = DATA_DIR / 'XAUUSD' / 'Scalper_Copilot_MTF_Data_v2.csv'
        else:
            path = DATA_DIR / 'XAUUSD' / 'Scalper_Copilot_MTF_Data_külön_vizsga.csv'
    
    print(f"Loading {path}...")
    
    if use_full:
        # Chunk-based loading for large files
        all_bars = []
        chunksize = 500_000
        for ci, chunk in enumerate(pd.read_csv(path, chunksize=chunksize, parse_dates=['Timestamp'])):
            chunk = chunk.set_index('Timestamp')
            chunk.columns = [c.lower().replace(' ', '_') for c in chunk.columns]
            mid = (chunk['bid'] + chunk['ask']) / 2
            ohlc = mid.resample(freq).ohlc()
            ohlc.columns = [c.lower() for c in ohlc.columns]
            ohlc['volume'] = chunk['bid_volume'].resample(freq).sum()
            ohlc['high'] = chunk['ask'].resample(freq).max()
            ohlc['low'] = chunk['bid'].resample(freq).min()
            mtf_cols = [c for c in chunk.columns if c not in ['bid','ask','bid_volume','ask_volume']]
            for col in mtf_cols:
                ohlc[col] = chunk[col].resample(freq).last()
            ohlc = ohlc.dropna(subset=['open'])
            all_bars.append(ohlc)
            if ci % 5 == 0:
                print(f"  Chunk {ci}: {sum(len(b) for b in all_bars)} bars so far")
        
        bars = pd.concat(all_bars)
        bars = bars[~bars.index.duplicated(keep='last')].sort_index()
    else:
        df = pd.read_csv(path, parse_dates=['Timestamp'], index_col='Timestamp')
        df.columns = [c.lower().replace(' ', '_') for c in df.columns]
        mid = (df['bid'] + df['ask']) / 2
        ohlc = mid.resample(freq).ohlc()
        ohlc.columns = [c.lower() for c in ohlc.columns]
        ohlc['volume'] = df['bid_volume'].resample(freq).sum()
        ohlc['high'] = df['ask'].resample(freq).max()
        ohlc['low'] = df['bid'].resample(freq).min()
        mtf_cols = [c for c in df.columns if c not in ['bid','ask','bid_volume','ask_volume']]
        for col in mtf_cols:
            ohlc[col] = df[col].resample(freq).last()
        bars = ohlc.dropna(subset=['open'])
    
    print(f"  {len(bars)} {freq} bars, {bars.index[0]} → {bars.index[-1]}")
    return bars


def compute_mtf_features(bars):
    """Features from MTF indicators in bar data."""
    feat = pd.DataFrame(index=bars.index)
    c = bars['close']
    mid = c  # already resampled
    
    # MTF close distances (mean reversion signals)
    atr = bars.get('atr_m15', c.rolling(15).std() * np.sqrt(15))
    for tf in ['1m_close', '5m_close', '15m_close', '30m_close']:
        if tf in bars.columns:
            feat[f'dist_{tf}'] = (mid - bars[tf]) / (atr + 1e-10)
    
    # ATR
    if 'atr_m15' in bars.columns:
        feat['atr_pct'] = bars['atr_m15'] / mid
    
    # RSI
    if 'rsi_m15' in bars.columns:
        rsi = bars['rsi_m15']
        feat['rsi'] = rsi / 100.0  # normalized
        feat['rsi_oversold'] = (rsi < 30).astype(int)
        feat['rsi_overbought'] = (rsi > 70).astype(int)
        feat['rsi_mid_signal'] = ((rsi > 40) & (rsi < 60)).astype(int)
    
    # Support/Resistance distances
    for level in ['micro_r', 'sec_r', 'ter_r', 'micro_s', 'sec_s', 'ter_s']:
        if level in bars.columns:
            feat[f'dist_{level}'] = (mid - bars[level]) / (atr + 1e-10)
    
    # Position between S/R
    if 'micro_r' in bars.columns and 'micro_s' in bars.columns:
        rng = bars['micro_r'] - bars['micro_s']
        feat['micro_pos'] = (mid - bars['micro_s']) / (rng + 1e-10)
        feat['micro_width'] = rng / (atr + 1e-10)
    if 'sec_r' in bars.columns and 'sec_s' in bars.columns:
        rng = bars['sec_r'] - bars['sec_s']
        feat['sec_pos'] = (mid - bars['sec_s']) / (rng + 1e-10)
        feat['sec_width'] = rng / (atr + 1e-10)
    if 'ter_r' in bars.columns and 'ter_s' in bars.columns:
        rng = bars['ter_r'] - bars['ter_s']
        feat['ter_pos'] = (mid - bars['ter_s']) / (rng + 1e-10)
    
    # Spread
    if 'spread' in bars.columns:
        feat['spread_atr'] = bars['spread'] / (atr + 1e-10)
    
    # Direction features
    for lag in [1, 2, 3, 5, 10, 20]:
        feat[f'ret_{lag}'] = c.pct_change(lag)
    
    # Volatility
    ret = c.pct_change()
    for lag in [5, 10, 20]:
        feat[f'rvol_{lag}'] = ret.rolling(lag).std()
    
    # Position in range
    for lag in [10, 20]:
        hh = bars['high'].rolling(lag).max()
        ll = bars['low'].rolling(lag).min()
        feat[f'pos_{lag}'] = (c - ll) / (hh - ll + 1e-10)
    
    # Volume
    v = bars.get('volume', pd.Series(1, index=bars.index))
    feat['vol_ratio'] = v / v.rolling(20).mean().clip(lower=1)
    
    return feat.dropna()


def side_model_from_rsi(bars):
    """Side model: RSI momentum + level.
    RSI crossing below 40 from above → Long
    RSI crossing above 60 from below → Short
    """
    if 'rsi_m15' not in bars.columns:
        return None
    rsi = bars['rsi_m15']
    rsi_prev = rsi.shift(1)
    
    direction = pd.Series(0, index=bars.index, dtype=float)
    
    # RSI crossover signals (momentum)
    # RSI drops below 40 → oversold → Long
    direction[(rsi < 40) & (rsi_prev >= 40)] = -1  # DOWN → Long
    # RSI rises above 60 → overbought → Short
    direction[(rsi > 60) & (rsi_prev <= 60)] = +1  # UP → Short
    
    # Also: RSI < 30 (extreme) → Long
    direction[rsi < 30] = -1
    # RSI > 70 (extreme) → Short
    direction[rsi > 70] = +1
    
    active = direction[direction != 0]
    events = pd.DataFrame({'direction': active}, index=active.index)
    return events


def train_lgbm(X, y, sample_weight=None, t1=None):
    import lightgbm as lgb
    params = {
        'objective': 'binary', 'metric': 'auc',
        'boosting_type': 'gbdt', 'num_leaves': 63,
        'learning_rate': 0.05, 'feature_fraction': 0.5,
        'bagging_fraction': 0.7, 'bagging_freq': 5,
        'min_data_in_leaf': 50, 'verbose': -1, 'n_jobs': -1,
        'reg_alpha': 0.05, 'reg_lambda': 0.05,
    }
    n_pos, n_neg = y.sum(), len(y) - y.sum()
    params['scale_pos_weight'] = n_neg / max(n_pos, 1)
    
    from sklearn.model_selection import KFold
    splits = list(KFold(n_splits=5, shuffle=False).split(X))
    
    oos = pd.Series(0.0, index=X.index)
    models, imps = [], []
    for fi_, (tri, tei) in enumerate(splits):
        Xt, Xte = X.iloc[tri], X.iloc[tei]
        yt, yte = y.iloc[tri], y.iloc[tei]
        w = sample_weight[tri] if sample_weight is not None else None
        dtrain = lgb.Dataset(Xt, label=yt, weight=w)
        dvalid = lgb.Dataset(Xte, label=yte)
        m = lgb.train(params, dtrain, num_boost_round=500, valid_sets=[dvalid],
                     callbacks=[lgb.early_stopping(50), lgb.log_evaluation(100)])
        oos.iloc[tei] = m.predict(Xte)
        models.append(m)
        imps.append(pd.Series(m.feature_importance('gain'), index=X.columns))
        bs = m.best_score['valid_0']['auc'] if isinstance(m.best_score, dict) else 0
        print(f"  Fold {fi_+1}: iter={m.best_iteration}, val_auc={bs:.4f}")
    
    fi = pd.concat(imps, axis=1).mean(axis=1).sort_values(ascending=False)
    from sklearn.metrics import roc_auc_score, accuracy_score
    valid = oos > 0
    auc = roc_auc_score(y[valid], oos[valid]) if valid.sum() > 50 else 0
    acc = accuracy_score(y[valid], (oos[valid] > 0.5).astype(int))
    return {'models': models, 'auc': auc, 'accuracy': acc, 'predictions': oos, 'feature_importance': fi}


def run_mtf_pipeline(instrument='BTCUSD', profit_mult=1.0, stop_mult=1.0, max_bars=20, use_full=False):
    print(f"\n{'='*60}\nMTF PIPELINE v3 — {instrument}\n{'='*60}")
    
    # 1. Load scalper data resampled to M1
    bars = load_scalper_m1(instrument, freq='1min', use_full=use_full)
    
    # 2. Side model from RSI (primary model)
    print("\nSide model (RSI-based)...")
    events = side_model_from_rsi(bars)
    if events is None:
        print("  No RSI available, using CUSUM filter")
        from labeling_cusum_filter import cusum_filter
        cusum_events = cusum_filter(bars['close'])
        events = pd.DataFrame({'direction': cusum_events}, index=cusum_events.index)
    else:
        n_long = (events['direction'] == -1).sum()
        n_short = (events['direction'] == +1).sum()
        print(f"  {len(events)} side signals (Long={n_long}, Short={n_short})")
    
    # 3. Triple barrier meta-labeling
    print(f"\nTriple Barrier (PT={profit_mult}σ, SL={stop_mult}σ, max={max_bars})...")
    labels = triple_barrier_meta(bars['close'], events, 
                                 profit_mult=profit_mult, stop_mult=stop_mult,
                                 max_bars=max_bars)
    tr = (labels['label'] == 1).mean()
    print(f"  {len(labels)} labels, Take rate: {tr:.2%}")
    
    # 4. Features
    print("\nMTF features...")
    feat_all = compute_mtf_features(bars)
    common = labels.index.intersection(feat_all.index)
    feat = feat_all.loc[common].select_dtypes(include=[np.number])
    feat = feat.replace([np.inf, -np.inf], np.nan).dropna()
    lab = labels.loc[feat.index]
    print(f"  {len(feat)} samples, {len(feat.columns)} features")
    
    # 5. Sample weights
    print("\nSample weights...")
    try: w = compute_sample_weights(lab, bars['close'])
    except Exception as e: print(f"  Warning: {e}"); w = np.ones(len(feat))
    
    # 6. Train
    print("\nTraining LightGBM...")
    res = train_lgbm(feat, lab['label'], sample_weight=w)
    print(f"\n  OOS AUC: {res['auc']:.4f}, Accuracy: {res['accuracy']:.4f}")
    print("  Top 10 features:")
    for f, i in res['feature_importance'].head(10).items():
        print(f"    {f}: {i:.1f}")
    
    # 7. Save
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    mp = MODEL_DIR / f'{instrument}_mtf_model_{ts}.txt'
    res['models'][-1].save_model(str(mp))
    
    preds_df = pd.DataFrame({'prob_take': res['predictions'], 'label': lab['label']}, index=feat.index)
    preds_path = MODEL_DIR / f'{instrument}_mtf_preds_{ts}.csv'
    preds_df.to_csv(preds_path)
    
    bar_sub = bars.loc[feat.index]
    bar_path = MODEL_DIR / f'{instrument}_mtf_bars_{ts}.csv'
    bar_sub.to_csv(bar_path)
    
    meta = {
        'instrument': instrument, 'timestamp': ts, 'version': 'mtf_v3',
        'n_bars': len(bars), 'n_labels': len(lab),
        'take_rate': float(tr), 'n_features': len(feat.columns),
        'auc': float(res['auc']), 'accuracy': float(res['accuracy']),
        'model_path': str(mp), 'feature_names': list(feat.columns),
        'config': {'profit_mult': profit_mult, 'stop_mult': stop_mult, 'max_bars': max_bars}
    }
    meta_path = MODEL_DIR / f'{instrument}_mtf_meta_{ts}.json'
    with open(meta_path, 'w') as f: json.dump(meta, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETE ✅")
    print(f"  Model: {mp}")
    print(f"  AUC: {res['auc']:.4f}, Acc: {res['accuracy']:.4f}")
    print(f"  Preds: {preds_path}")
    print(f"{'='*60}")
    return meta, res


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--instrument', default='BTCUSD')
    p.add_argument('--pt', type=float, default=1.0)
    p.add_argument('--sl', type=float, default=1.0)
    p.add_argument('--max-bars', type=int, default=20)
    p.add_argument('--full', action='store_true', help='Use full 5.2M tick data')
    a = p.parse_args()
    run_mtf_pipeline(a.instrument, a.pt, a.sl, a.max_bars, a.full)