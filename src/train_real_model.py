"""
Real Data Pipeline — BTCUSD M1 History → Trained Model
"""
import sys, os, json, numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/data/LGBM_copilot/knowledge/code_templates')
from data_dollar_bars import dollar_bars, THRESHOLDS
from labeling_cusum_filter import cusum_filter
from labeling_meta_labeling import triple_barrier_meta
from features_direction import compute_all_direction_features, compute_boolean_features
from sample_weights import compute_sample_weights
from instrument_config import get_instrument
from cross_validation_purged import PurgedKFold

DATA_DIR = Path('/data/dev/LGB_copilot_system/RAW_CSV')
OUTPUT_DIR = Path('/data/LGBM_copilot/data')
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


def train_lgbm(X, y, sample_weight=None, t1=None):
    import lightgbm as lgb
    params = {
        'objective': 'binary', 'metric': 'binary_logloss',
        'boosting_type': 'gbdt', 'num_leaves': 31,
        'learning_rate': 0.05, 'feature_fraction': 0.8,
        'bagging_fraction': 0.8, 'bagging_freq': 5,
        'verbose': -1, 'n_jobs': -1,
    }
    n_pos, n_neg = y.sum(), len(y) - y.sum()
    params['scale_pos_weight'] = n_neg / max(n_pos, 1)
    
    pkf = PurgedKFold(n_splits=5, pct_embargo=0.01, t1=t1)
    oos = pd.Series(0.0, index=X.index)
    models, imps = [], []
    
    for _, (tri, tei) in enumerate(pkf.split(X)):
        Xt, Xte = X.iloc[tri], X.iloc[tei]
        yt, yte = y.iloc[tri], y.iloc[tei]
        w = sample_weight[tri] if sample_weight is not None else None
        dtrain = lgb.Dataset(Xt, label=yt, weight=w)
        dvalid = lgb.Dataset(Xte, label=yte)
        m = lgb.train(params, dtrain, num_boost_round=300, valid_sets=[dvalid],
                     callbacks=[lgb.early_stopping(30), lgb.log_evaluation(0)])
        oos.iloc[tei] = m.predict(Xte)
        models.append(m)
        imps.append(pd.Series(m.feature_importance('gain'), index=X.columns))
    
    fi = pd.concat(imps, axis=1).mean(axis=1).sort_values(ascending=False)
    from sklearn.metrics import roc_auc_score
    auc = roc_auc_score(y[oos>0], oos[oos>0]) if (oos>0).sum() > 50 else 0
    return {'models': models, 'auc': auc, 'predictions': oos, 'feature_importance': fi}



def run_real_pipeline(instrument='BTCUSD'):
    print(f"\n{'='*60}\nREAL DATA PIPELINE — {instrument}\n{'='*60}")
    config = get_instrument(instrument)
    m1 = load_m1(instrument)
    
    print(f"\nDollar bars (threshold=${config.dollar_bar_threshold:,.0f})...")
    dbars = dollar_bars(m1, threshold=config.dollar_bar_threshold)
    dbars = dbars.set_index('timestamp')
    print(f"  {len(dbars)} bars ({len(m1)/len(dbars):.0f}x compression)")
    
    print("\nCUSUM filter...")
    events = cusum_filter(dbars['close'])
    print(f"  {len(events)} events")
    
    print("\nTriple Barrier meta-labeling...")
    bp = config.get_barrier_params()
    labels = triple_barrier_meta(dbars['close'], events, **bp)
    tr = (labels['label'] == 1).mean()
    print(f"  {len(labels)} labels, Take rate: {tr:.2%}")
    
    print("\nFeatures...")
    df_ = compute_all_direction_features(dbars)
    bf_ = compute_boolean_features(dbars, df_)
    af_ = pd.concat([df_, bf_], axis=1)
    ef_ = af_.loc[labels.index].dropna().select_dtypes(include=[np.number])
    el_ = labels.loc[ef_.index]
    print(f"  {len(ef_)} samples, {len(ef_.columns)} features")
    
    print("\nSample weights...")
    try: w = compute_sample_weights(el_, dbars['close'])
    except: w = np.ones(len(ef_))
    
    print("\nTraining LightGBM...")
    res = train_lgbm(ef_, el_['label'], sample_weight=w)
    print(f"  OOS AUC: {res['auc']:.4f}")
    print("  Top 5 features:")
    for f, i in res['feature_importance'].head(5).items():
        print(f"    {f}: {i:.1f}")
    
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    mp = MODEL_DIR / f'{instrument}_meta_model_{ts}.txt'
    res['models'][-1].save_model(str(mp))
    
    fi_path = MODEL_DIR / f'{instrument}_feature_importance_{ts}.csv'
    res['feature_importance'].to_csv(fi_path, header=['importance'])
    
    meta = {
        'instrument': instrument, 'timestamp': ts,
        'n_m1_bars': len(m1), 'n_dollar_bars': len(dbars),
        'n_events': len(events), 'n_labels': len(el_),
        'take_rate': float(tr), 'n_features': len(ef_.columns),
        'auc': float(res['auc']), 'model_path': str(mp),
        'feature_names': list(ef_.columns),
        'config': {'profit_mult': config.profit_mult, 'stop_mult': config.stop_mult,
                   'max_bars': config.max_holding_bars, 'threshold': config.dollar_bar_threshold}
    }
    meta_path = MODEL_DIR / f'{instrument}_pipeline_meta_{ts}.json'
    with open(meta_path, 'w') as f: json.dump(meta, f, indent=2)
    
    print(f"\n{'='*60}\nPIPELINE COMPLETE ✅\n  Model: {mp}\n  AUC: {res['auc']:.4f}\n  Meta: {meta_path}\n{'='*60}")
    return meta, res


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--instrument', default='BTCUSD')
    a = p.parse_args()
    run_real_pipeline(a.instrument)