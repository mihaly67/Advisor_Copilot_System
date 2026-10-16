"""
Scalper MTF Pipeline — BTCUSD Scalper data → Trained Model
Uses MTF indicators from EA: ATR, RSI, Micro/Sec/Ter R/S levels
"""
import sys, json, numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/data/LGBM_copilot/knowledge/code_templates')
from labeling_cusum_filter import cusum_filter
from labeling_meta_labeling import triple_barrier_meta
from sample_weights import compute_sample_weights
from instrument_config import get_instrument
from cross_validation_purged import PurgedKFold

DATA_DIR = Path('/data/dev/LGB_copilot_system/RAW_CSV')
MODEL_DIR = Path('/data/LGBM_copilot/models')


def load_scalper_data(instrument='BTCUSD'):
    """Load tick-level scalper data with MTF indicators."""
    if instrument == 'BTCUSD':
        path = DATA_DIR / 'BTCUSD' / 'BTCUSD_külön_vizsga.csv'
    else:
        path = DATA_DIR / 'XAUUSD' / 'Scalper_Copilot_MTF_Data_külön_vizsga.csv'
    
    print(f"Loading {path}...")
    df = pd.read_csv(path, parse_dates=['Timestamp'], index_col='Timestamp')
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]
    print(f"  {len(df)} ticks, {df.index[0]} → {df.index[-1]}")
    print(f"  Columns: {list(df.columns)}")
    return df


def resample_to_bars(df, freq='1min'):
    """Resample tick data to OHLCV bars."""
    mid = (df['bid'] + df['ask']) / 2
    df = df.copy()
    df['mid'] = mid
    
    ohlc = df['mid'].resample(freq).ohlc()
    ohlc.columns = [c.lower() for c in ohlc.columns]
    vol = df['bid_volume'].resample(freq).sum()
    ohlc['volume'] = vol
    ohlc = ohlc.dropna()
    return ohlc


def compute_mtf_features(df):
    """Features from Scalper MTF indicators."""
    feat = pd.DataFrame(index=df.index)
    mid = (df['bid'] + df['ask']) / 2
    
    # Spread
    if 'spread' in df.columns:
        feat['spread'] = df['spread']
        feat['spread_atr_ratio'] = df['spread'] / df.get('atr_m15', df['spread'] * 10)
    
    # MTF close levels (mean reversion features)
    for tf in ['1m_close', '5m_close', '15m_close', '30m_close']:
        if tf in df.columns:
            feat[f'dist_{tf}'] = (mid - df[tf]) / df.get('atr_m15', mid * 0.001)
    
    # ATR
    if 'atr_m15' in df.columns:
        feat['atr_m15_pct'] = df['atr_m15'] / mid
    
    # RSI
    if 'rsi_m15' in df.columns:
        feat['rsi_m15'] = df['rsi_m15']
        feat['rsi_oversold'] = (df['rsi_m15'] < 30).astype(int)
        feat['rsi_overbought'] = (df['rsi_m15'] > 70).astype(int)
        feat['rsi_neutral'] = ((df['rsi_m15'] >= 40) & (df['rsi_m15'] <= 60)).astype(int)
    
    # Support/Resistance distances
    for level in ['micro_r', 'sec_r', 'ter_r', 'micro_s', 'sec_s', 'ter_s']:
        if level in df.columns:
            feat[f'dist_{level}'] = (mid - df[level]) / df.get('atr_m15', mid * 0.001)
    
    # Support/Resistance proximity signals
    if 'micro_r' in df.columns and 'micro_s' in df.columns:
        feat['micro_range'] = (df['micro_r'] - df['micro_s']) / df.get('atr_m15', mid * 0.001)
        feat['micro_pos'] = (mid - df['micro_s']) / (df['micro_r'] - df['micro_s'] + 1e-10)
    if 'sec_r' in df.columns and 'sec_s' in df.columns:
        feat['sec_range'] = (df['sec_r'] - df['sec_s']) / df.get('atr_m15', mid * 0.001)
        feat['sec_pos'] = (mid - df['sec_s']) / (df['sec_r'] - df['sec_s'] + 1e-10)
    
    # Volume imbalance
    if 'bid_volume' in df.columns and 'ask_volume' in df.columns:
        bv, av = df['bid_volume'], df['ask_volume']
        feat['vol_imbalance'] = (bv - av) / (bv + av + 1e-10)
        feat['total_volume'] = bv + av
    
    # Direction features from mid price
    feat['mom_5'] = mid.pct_change(5)
    feat['mom_20'] = mid.pct_change(20)
    feat['vol_20'] = mid.pct_change().rolling(20).std()
    
    return feat.dropna()



def train_lgbm(X, y, sample_weight=None, t1=None):
    import lightgbm as lgb
    params = {
        'objective': 'binary', 'metric': 'binary_logloss',
        'boosting_type': 'gbdt', 'num_leaves': 63,
        'learning_rate': 0.1, 'feature_fraction': 0.7,
        'bagging_fraction': 0.7, 'bagging_freq': 5,
        'min_data_in_leaf': 50, 'verbose': -1, 'n_jobs': -1,
    }
    n_pos, n_neg = y.sum(), len(y) - y.sum()
    params['scale_pos_weight'] = n_neg / max(n_pos, 1)
    
    if t1 is not None and len(t1) == len(X):
        pkf = PurgedKFold(n_splits=5, pct_embargo=0.005, t1=t1)
        splits = list(pkf.split(X))
    else:
        from sklearn.model_selection import KFold
        kf = KFold(n_splits=5, shuffle=False)
        splits = list(kf.split(X))
    
    oos = pd.Series(0.0, index=X.index)
    models, imps = [], []
    for fold_idx, (tri, tei) in enumerate(splits):
        Xt, Xte = X.iloc[tri], X.iloc[tei]
        yt, yte = y.iloc[tri], y.iloc[tei]
        w = sample_weight[tri] if sample_weight is not None else None
        dtrain = lgb.Dataset(Xt, label=yt, weight=w)
        dvalid = lgb.Dataset(Xte, label=yte)
        m = lgb.train(params, dtrain, num_boost_round=500, valid_sets=[dvalid],
                     callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)])
        oos.iloc[tei] = m.predict(Xte)
        models.append(m)
        imps.append(pd.Series(m.feature_importance('gain'), index=X.columns))
        print(f"  Fold {fold_idx+1}: best_iter={m.best_iteration}")
    
    fi = pd.concat(imps, axis=1).mean(axis=1).sort_values(ascending=False)
    from sklearn.metrics import roc_auc_score
    valid = oos > 0
    auc = roc_auc_score(y[valid], oos[valid]) if valid.sum() > 50 else 0
    return {'models': models, 'auc': auc, 'predictions': oos, 'feature_importance': fi}


def run_scalper_pipeline(instrument='BTCUSD', bar_freq='1min'):
    print(f"\n{'='*60}\nSCALPER MTF PIPELINE — {instrument}\n{'='*60}")
    config = get_instrument(instrument)
    tick_df = load_scalper_data(instrument)
    
    print(f"\nResampling to {bar_freq} bars...")
    bars = resample_to_bars(tick_df, freq=bar_freq)
    print(f"  {len(bars)} bars")
    
    print("\nCUSUM filter...")
    events = cusum_filter(bars['close'])
    print(f"  {len(events)} events")
    
    print("\nTriple Barrier meta-labeling...")
    bp = config.get_barrier_params()
    labels = triple_barrier_meta(bars['close'], events, **bp)
    tr = (labels['label'] == 1).mean()
    print(f"  {len(labels)} labels, Take rate: {tr:.2%}")
    
    print("\nMTF features...")
    mtf_feat = compute_mtf_features(tick_df)
    mtf_bar = mtf_feat.resample(bar_freq).last().dropna()
    common_idx = labels.index.intersection(mtf_bar.index)
    feat = mtf_bar.loc[common_idx].select_dtypes(include=[np.number]).dropna()
    lab = labels.loc[feat.index]
    print(f"  {len(feat)} samples, {len(feat.columns)} features")
    
    print("\nSample weights...")
    try: w = compute_sample_weights(lab, bars['close'])
    except Exception as e: print(f"  Warning: {e}"); w = np.ones(len(feat))
    
    print("\nTraining LightGBM...")
    t1 = lab.get('t1', lab.index + pd.Timedelta(bar_freq))
    res = train_lgbm(feat, lab['label'], sample_weight=w, t1=t1)
    print(f"\n  OOS AUC: {res['auc']:.4f}")
    print("  Top 10 features:")
    for f, i in res['feature_importance'].head(10).items():
        print(f"    {f}: {i:.1f}")
    
    # Save
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    mp = MODEL_DIR / f'{instrument}_scalper_model_{ts}.txt'
    res['models'][-1].save_model(str(mp))
    
    preds_df = pd.DataFrame({'prob_take': res['predictions'], 'label': lab['label']}, index=feat.index)
    preds_path = MODEL_DIR / f'{instrument}_scalper_preds_{ts}.csv'
    preds_df.to_csv(preds_path)
    
    bar_sub = bars.loc[feat.index]
    bar_path = MODEL_DIR / f'{instrument}_scalper_bars_{ts}.csv'
    bar_sub.to_csv(bar_path)
    
    fi_path = MODEL_DIR / f'{instrument}_scalper_importance_{ts}.csv'
    res['feature_importance'].to_csv(fi_path, header=['importance'])
    
    meta = {
        'instrument': instrument, 'timestamp': ts, 'data_source': 'scalper_mtf',
        'bar_freq': bar_freq, 'n_ticks': len(tick_df), 'n_bars': len(bars),
        'n_events': len(events), 'n_labels': len(lab),
        'take_rate': float(tr), 'n_features': len(feat.columns),
        'auc': float(res['auc']), 'model_path': str(mp),
        'feature_names': list(feat.columns),
        'config': {'profit_mult': config.profit_mult, 'stop_mult': config.stop_mult,
                   'max_bars': config.max_holding_bars}
    }
    meta_path = MODEL_DIR / f'{instrument}_scalper_meta_{ts}.json'
    with open(meta_path, 'w') as f: json.dump(meta, f, indent=2)
    
    print(f"\n{'='*60}\nPIPELINE COMPLETE ✅\n  Model: {mp}\n  AUC: {res['auc']:.4f}\n  Predictions: {preds_path}\n  Meta: {meta_path}\n{'='*60}")
    return meta, res


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--instrument', default='BTCUSD')
    p.add_argument('--freq', default='1min')
    a = p.parse_args()
    run_scalper_pipeline(a.instrument, a.freq)