#!/usr/bin/env python3
"""
Scalper V3 Optuna — Hyperparameter optimization for V3 Hybrid pipeline
Fixed: TP=$50, horizon=60s, $10M dollar bars
Optimizes: LGBM params (num_leaves, lr, feature_fraction, etc.)
"""
import numpy as np, pandas as pd
from pathlib import Path
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import KFold
import lightgbm as lgb
import optuna

DATA_DIR = Path('/data/dev/LGB_copilot_system/RAW_CSV')
MODEL_DIR = Path('/data/LGBM_copilot/models/scalper')

# Fixed config
TP_DOLLAR = 50
HORIZON_SEC = 60
DOLLAR_THRESHOLD = 10_000_000


def load_and_prepare():
    """Load data, build dollar bars, label, compute MTF features."""
    print("Loading tick data...")
    df = pd.read_csv(DATA_DIR / 'BTCUSD' / 'BTCUSD_külön_vizsga.csv',
                     parse_dates=['Timestamp'], index_col='Timestamp')
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]

    # Dollar bars
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
        if cum_d >= DOLLAR_THRESHOLD:
            bars.append({'timestamp': t0, 'open': o, 'high': h, 'low': l, 'close': c,
                         'volume': cum_d / c, 'dollar_volume': cum_d})
            o = None; cum_d = 0.0
    bars_df = pd.DataFrame(bars)
    bars_df['timestamp'] = pd.to_datetime(bars_df['timestamp'])
    bars_df = bars_df.set_index('timestamp')
    print(f"  {len(bars_df)} dollar bars")

    # Label
    closes = bars_df['close'].values
    highs = bars_df['high'].values
    lows = bars_df['low'].values
    timestamps = bars_df.index
    n = len(closes)
    long_lbl = np.zeros(n, dtype=np.int8)
    short_lbl = np.zeros(n, dtype=np.int8)
    for i in range(n):
        entry = closes[i]
        t_limit = timestamps[i] + pd.Timedelta(seconds=HORIZON_SEC)
        for j in range(i + 1, n):
            if timestamps[j] > t_limit: break
            if highs[j] >= entry + TP_DOLLAR: long_lbl[i] = 1; break
            elif lows[j] <= entry - TP_DOLLAR: short_lbl[i] = 1; break
    print(f"  Labels: Long {long_lbl.sum()/n:.1%}, Short {short_lbl.sum()/n:.1%}")

    # MTF features
    from scalper_v3_hybrid import compute_mtf_features_at_bars
    feat = compute_mtf_features_at_bars(df, bars_df.index)
    feat = feat.select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan).dropna()
    common = bars_df.index.intersection(feat.index)
    feat = feat.loc[common]
    y_long = pd.Series(long_lbl, index=bars_df.index).loc[feat.index]
    y_short = pd.Series(short_lbl, index=bars_df.index).loc[feat.index]
    print(f"  {len(feat)} samples, {len(feat.columns)} features")
    return feat, y_long, y_short


def objective(trial, X, y_long, y_short):
    params = {
        'objective': 'binary', 'metric': 'auc', 'boosting_type': 'gbdt',
        'num_leaves': trial.suggest_int('num_leaves', 15, 63),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
        'feature_fraction': trial.suggest_float('feature_fraction', 0.5, 1.0),
        'bagging_fraction': trial.suggest_float('bagging_fraction', 0.5, 1.0),
        'bagging_freq': 5,
        'min_data_in_leaf': trial.suggest_int('min_data_in_leaf', 50, 500),
        'reg_alpha': trial.suggest_float('reg_alpha', 0.001, 1.0, log=True),
        'reg_lambda': trial.suggest_float('reg_lambda', 0.001, 1.0, log=True),
        'verbose': -1, 'n_jobs': -1, 'is_unbalance': True,
    }

    aucs = []
    for name, y in [('long', y_long), ('short', y_short)]:
        kf = KFold(n_splits=3, shuffle=False)
        fold_aucs = []
        for tri, tei in kf.split(X):
            dtrain = lgb.Dataset(X.iloc[tri], label=y.iloc[tri])
            dvalid = lgb.Dataset(X.iloc[tei], label=y.iloc[tei])
            m = lgb.train(params, dtrain, num_boost_round=300,
                         valid_sets=[dvalid],
                         callbacks=[lgb.early_stopping(30), lgb.log_evaluation(0)])
            pred = m.predict(X.iloc[tei])
            fold_aucs.append(roc_auc_score(y.iloc[tei], pred))
        aucs.append(np.mean(fold_aucs))

    avg_auc = np.mean(aucs)
    print(f"  Trial {trial.number}: avg AUC={avg_auc:.4f} (L={aucs[0]:.3f}, S={aucs[1]:.3f})")
    return avg_auc


def main():
    import argparse, json
    ap = argparse.ArgumentParser()
    ap.add_argument('--trials', type=int, default=30)
    ap.add_argument('--timeout', type=int, default=600)
    args = ap.parse_args()

    X, y_long, y_short = load_and_prepare()

    study = optuna.create_study(direction='maximize',
                                study_name='scalper_v3_hybrid',
                                storage=f'sqlite:///{MODEL_DIR}/v3_optuna.db',
                                load_if_exists=True)
    study.optimize(lambda trial: objective(trial, X, y_long, y_short),
                   n_trials=args.trials, timeout=args.timeout)

    best = study.best_params
    best_auc = study.best_value
    print(f"\n{'='*60}")
    print(f"OPTUNA BEST: avg AUC={best_auc:.4f}")
    print(f"  {best}")

    ts = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    with open(MODEL_DIR / f'BTCUSD_v3_optuna_best_{ts}.json', 'w') as f:
        json.dump({'best_avg_auc': best_auc, 'params': best,
                   'tp_dollar': TP_DOLLAR, 'horizon_sec': HORIZON_SEC,
                   'dollar_threshold': DOLLAR_THRESHOLD}, f, indent=2)
    print(f"{'='*60}")


if __name__ == '__main__':
    main()