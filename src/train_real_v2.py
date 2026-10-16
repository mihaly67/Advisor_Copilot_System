"""
Real Data Pipeline v2 — M1 History + Rich Features → Trained Model
Key fixes: symmetric barriers, more features, better training params
"""
import sys, json, numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/data/LGBM_copilot/knowledge/code_templates')
from data_dollar_bars import dollar_bars
from labeling_cusum_filter import cusum_filter
from labeling_meta_labeling import triple_barrier_meta
from features_direction import compute_all_direction_features, compute_boolean_features
from sample_weights import compute_sample_weights
from instrument_config import get_instrument
from cross_validation_purged import PurgedKFold

DATA_DIR = Path('/data/dev/LGB_copilot_system/RAW_CSV')
MODEL_DIR = Path('/data/LGBM_copilot/models')


def load_m1(instrument='BTCUSD'):
    path = DATA_DIR / instrument / f'M1_History_{instrument}.csv'
    print(f"Loading {path}...")
    df = pd.read_csv(path, parse_dates=['Timestamp'], index_col='Timestamp')
    df.columns = [c.lower() for c in df.columns]
    if 'tickvolume' in df.columns:
        df = df.rename(columns={'tickvolume': 'volume'})
    print(f"  {len(df)} bars, {df.index[0]} → {df.index[-1]}")
    return df


def compute_rich_features(bars):
    """Extended feature set beyond direction features."""
    # Base direction + boolean
    dir_f = compute_all_direction_features(bars)
    bool_f = compute_boolean_features(bars, dir_f)
    
    c = bars['close']
    h = bars['high']
    l = bars['low']
    v = bars['volume']
    
    extra = pd.DataFrame(index=bars.index)
    
    # Returns at multiple horizons
    for lag in [1, 2, 3, 5, 10, 20, 50]:
        extra[f'ret_{lag}'] = c.pct_change(lag)
    
    # Realized volatility at multiple horizons
    ret = c.pct_change()
    for lag in [5, 10, 20, 50]:
        extra[f'rvol_{lag}'] = ret.rolling(lag).std()
    
    # Price position in N-bar range
    for lag in [10, 20, 50]:
        hh = h.rolling(lag).max()
        ll = l.rolling(lag).min()
        extra[f'pos_{lag}'] = (c - ll) / (hh - ll + 1e-10)
    
    # Volume features
    extra['vol_change'] = v.pct_change().clip(-5, 5)
    extra['vol_ma_ratio'] = v / v.rolling(20).mean()
    
    # Intraday patterns (hour of day)
    if isinstance(bars.index, pd.DatetimeIndex):
        extra['hour'] = bars.index.hour / 23.0
        extra['dow'] = bars.index.dayofweek / 6.0
    
    # RSI-like features
    delta = c.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / (loss + 1e-10)
    extra['rsi_14'] = 100 - 100 / (1 + rs)
    
    # EMA distances
    for span in [10, 20, 50]:
        ema = c.ewm(span=span).mean()
        extra[f'dist_ema{span}'] = (c - ema) / (c.rolling(20).std() + 1e-10)
    
    # Combine all
    all_feat = pd.concat([dir_f, bool_f, extra], axis=1)
    return all_feat.dropna()



def train_lgbm(X, y, sample_weight=None, t1=None):
    import lightgbm as lgb
    params = {
        'objective': 'binary', 'metric': 'auc',
        'boosting_type': 'gbdt', 'num_leaves': 31,
        'learning_rate': 0.02, 'feature_fraction': 0.6,
        'bagging_fraction': 0.8, 'bagging_freq': 5,
        'min_data_in_leaf': 100, 'verbose': -1, 'n_jobs': -1,
        'reg_alpha': 0.1, 'reg_lambda': 0.1,
    }
    n_pos, n_neg = y.sum(), len(y) - y.sum()
    params['scale_pos_weight'] = n_neg / max(n_pos, 1)
    if t1 is not None and len(t1) == len(X):
        try:
            pkf = PurgedKFold(n_splits=5, pct_embargo=0.005, t1=t1)
            splits = list(pkf.split(X))
        except: splits = None
    else: splits = None
    if splits is None:
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
        m = lgb.train(params, dtrain, num_boost_round=1000, valid_sets=[dvalid],
                     callbacks=[lgb.early_stopping(100), lgb.log_evaluation(200)])
        oos.iloc[tei] = m.predict(Xte)
        models.append(m)
        imps.append(pd.Series(m.feature_importance('gain'), index=X.columns))
        print(f"  Fold {fi_+1}: iter={m.best_iteration}, auc={m.best_score['valid_0']['auc']:.4f}")
    fi = pd.concat(imps, axis=1).mean(axis=1).sort_values(ascending=False)
    from sklearn.metrics import roc_auc_score, accuracy_score
    valid = oos > 0
    auc = roc_auc_score(y[valid], oos[valid]) if valid.sum() > 50 else 0
    acc = accuracy_score(y[valid], (oos[valid] > 0.5).astype(int))
    return {'models': models, 'auc': auc, 'accuracy': acc, 'predictions': oos, 'feature_importance': fi}


def run_v2(instrument='BTCUSD', profit_mult=1.0, stop_mult=1.0):
    print(f"\n{'='*60}\nREAL PIPELINE v2 — {instrument}\n{'='*60}")
    config = get_instrument(instrument)
    config.profit_mult = profit_mult
    config.stop_mult = stop_mult
    m1 = load_m1(instrument)
    print(f"\nDollar bars (threshold=${config.dollar_bar_threshold:,.0f})...")
    dbars = dollar_bars(m1, threshold=config.dollar_bar_threshold)
    dbars = dbars.set_index('timestamp')
    print(f"  {len(dbars)} bars ({len(m1)/len(dbars):.0f}x compression)")
    print("\nCUSUM filter...")
    events = cusum_filter(dbars['close'])
    print(f"  {len(events)} events")
    print(f"\nTriple Barrier (PT={profit_mult}σ, SL={stop_mult}σ)...")
    bp = config.get_barrier_params()
    labels = triple_barrier_meta(dbars['close'], events, **bp)
    tr = (labels['label'] == 1).mean()
    print(f"  {len(labels)} labels, Take rate: {tr:.2%}")
    print("\nRich features...")
    all_feat = compute_rich_features(dbars)
    common = labels.index.intersection(all_feat.index)
    feat = all_feat.loc[common].select_dtypes(include=[np.number])
    lab = labels.loc[feat.index]
    feat = feat.replace([np.inf, -np.inf], np.nan).dropna()
    lab = lab.loc[feat.index]
    print(f"  {len(feat)} samples, {len(feat.columns)} features")
    print("\nSample weights...")
    try: w = compute_sample_weights(lab, dbars['close'])
    except Exception as e: print(f"  Warning: {e}"); w = np.ones(len(feat))
    print("\nTraining LightGBM...")
    t1 = lab.get('t1', None)
    res = train_lgbm(feat, lab['label'], sample_weight=w, t1=t1)
    print(f"\n  OOS AUC: {res['auc']:.4f}, Accuracy: {res['accuracy']:.4f}")
    print("  Top 10 features:")
    for f, i in res['feature_importance'].head(10).items():
        print(f"    {f}: {i:.1f}")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    mp = MODEL_DIR / f'{instrument}_v2_model_{ts}.txt'
    res['models'][-1].save_model(str(mp))
    preds_df = pd.DataFrame({'prob_take': res['predictions'], 'label': lab['label']}, index=feat.index)
    preds_path = MODEL_DIR / f'{instrument}_v2_preds_{ts}.csv'
    preds_df.to_csv(preds_path)
    bar_sub = dbars.loc[feat.index]
    bar_path = MODEL_DIR / f'{instrument}_v2_bars_{ts}.csv'
    bar_sub.to_csv(bar_path)
    fi_path = MODEL_DIR / f'{instrument}_v2_importance_{ts}.csv'
    res['feature_importance'].to_csv(fi_path, header=['importance'])
    meta = {
        'instrument': instrument, 'timestamp': ts, 'version': 'v2',
        'n_m1_bars': len(m1), 'n_dollar_bars': len(dbars),
        'n_events': len(events), 'n_labels': len(lab),
        'take_rate': float(tr), 'n_features': len(feat.columns),
        'auc': float(res['auc']), 'accuracy': float(res['accuracy']),
        'model_path': str(mp), 'feature_names': list(feat.columns),
        'config': {'profit_mult': profit_mult, 'stop_mult': stop_mult,
                   'max_bars': config.max_holding_bars, 'threshold': config.dollar_bar_threshold}
    }
    meta_path = MODEL_DIR / f'{instrument}_v2_meta_{ts}.json'
    with open(meta_path, 'w') as f: json.dump(meta, f, indent=2)
    print(f"\n{'='*60}\nPIPELINE COMPLETE ✅\n  Model: {mp}\n  AUC: {res['auc']:.4f}, Acc: {res['accuracy']:.4f}\n  Preds: {preds_path}\n  Bars: {bar_path}\n{'='*60}")
    return meta, res


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--instrument', default='BTCUSD')
    p.add_argument('--pt', type=float, default=1.0, help='Profit mult')
    p.add_argument('--sl', type=float, default=1.0, help='Stop mult')
    a = p.parse_args()
    run_v2(a.instrument, a.pt, a.sl)