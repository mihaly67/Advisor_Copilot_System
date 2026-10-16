"""
Scalper Optuna Optimizer — find best horizon, TP/SL, thresholds, LGBM params
BTC can move $100/min → need shorter horizon or wider TP/SL to avoid noise
"""
import json, numpy as np, pandas as pd, optuna, warnings
from pathlib import Path
from datetime import datetime
from sklearn.metrics import roc_auc_score, f1_score
from sklearn.model_selection import KFold
warnings.filterwarnings('ignore')

DATA_DIR = Path('/data/dev/LGB_copilot_system/RAW_CSV')
MODEL_DIR = Path('/data/LGBM_copilot/models/scalper')
MODEL_DIR.mkdir(parents=True, exist_ok=True)

print("Loading BTCUSD külön_vizsga data...")
_df_cache = None

def load_data():
    global _df_cache
    if _df_cache is None:
        path = DATA_DIR / 'BTCUSD' / 'BTCUSD_külön_vizsga.csv'
        _df_cache = pd.read_csv(path, parse_dates=['Timestamp'], index_col='Timestamp')
        _df_cache.columns = [c.lower().replace(' ', '_') for c in _df_cache.columns]
        print(f"  {_df_cache.shape[0]} ticks loaded")
    return _df_cache


def label_ticks(mid, horizon, tp_bps, sl_bps):
    """Vectorized labeling."""
    n = len(mid)
    long_lbl = np.zeros(n, dtype=np.int8)
    short_lbl = np.zeros(n, dtype=np.int8)
    tp_f = tp_bps / 10000.0
    sl_f = sl_bps / 10000.0
    for i in range(n - horizon):
        entry = mid[i]
        tp_p, sl_p = entry * (1 + tp_f), entry * (1 - sl_f)
        window = mid[i+1:i+1+horizon]
        hit_tp = np.where(window >= tp_p)[0]
        hit_sl = np.where(window <= sl_p)[0]
        if len(hit_tp) > 0 and (len(hit_sl) == 0 or hit_tp[0] < hit_sl[0]):
            long_lbl[i] = 1
        elif len(hit_sl) > 0 and (len(hit_tp) == 0 or hit_sl[0] < hit_tp[0]):
            short_lbl[i] = 1
    return long_lbl, short_lbl


def compute_features(df, subsample=5):
    """Features from subsampled ticks (same as scalper_continuous)."""
    df_sub = df.iloc[::subsample].copy()
    mid = (df_sub['bid'] + df_sub['ask']) / 2
    atr = df_sub.get('atr_m15', mid.rolling(15).std() * np.sqrt(15))
    f = pd.DataFrame(index=df_sub.index)
    for tf in ['1m_close', '5m_close', '15m_close', '30m_close']:
        if tf in df_sub.columns:
            f[f'd_{tf}'] = (mid - df_sub[tf]) / (atr + 1e-10)
    f['atr_pct'] = atr / mid
    if 'rsi_m15' in df_sub.columns:
        rsi = df_sub['rsi_m15']
        f['rsi_n'] = (rsi - 50) / 50
        f['rsi_os'] = (rsi < 30).astype(int)
        f['rsi_ob'] = (rsi > 70).astype(int)
        f['rsi_mom'] = rsi.diff(5) / 50
    for lv in ['micro_r', 'sec_r', 'ter_r', 'micro_s', 'sec_s', 'ter_s']:
        if lv in df_sub.columns:
            f[f'd_{lv}'] = (mid - df_sub[lv]) / (atr + 1e-10)
    for px in ['micro', 'sec', 'ter']:
        rc, sc = f'{px}_r', f'{px}_s'
        if rc in df_sub.columns and sc in df_sub.columns:
            rng = df_sub[rc] - df_sub[sc]
            f[f'{px}_pos'] = (mid - df_sub[sc]) / (rng + 1e-10)
            f[f'{px}_sqz'] = atr / (rng + 1e-10)
    if 'spread' in df_sub.columns:
        f['sp_atr'] = df_sub['spread'] / (atr + 1e-10)
    if 'bid_volume' in df_sub.columns and 'ask_volume' in df_sub.columns:
        bv, av = df_sub['bid_volume'], df_sub['ask_volume']
        f['vol_imb'] = (bv - av) / (bv + av + 1e-10)
        f['vol_tot'] = np.log1p(bv + av)
    mr = mid.pct_change()
    for lag in [1, 3, 5, 10, 20]:
        f[f'ret_{lag}'] = mid.pct_change(lag)
    for lag in [10, 20, 60]:
        f[f'tv_{lag}'] = mr.rolling(lag).std()
    for lag in [20, 60]:
        f[f'tsk_{lag}'] = mr.rolling(lag).skew()
    for lag in [20, 60]:
        hh, ll = mid.rolling(lag).max(), mid.rolling(lag).min()
        f[f'rpos_{lag}'] = (mid - ll) / (hh - ll + 1e-10)
    if '1m_close' in df_sub.columns and '15m_close' in df_sub.columns:
        f['mtf_al'] = np.sign(df_sub['1m_close'].pct_change(5)) * np.sign(df_sub['15m_close'].pct_change(5))
    return f.dropna(), df_sub


def train_quick_lgbm(X, y, params, n_splits=3):
    """Quick 3-fold LGBM for Optuna. Uses is_unbalance instead of scale_pos_weight."""
    import lightgbm as lgb
    n_pos = y.sum()
    if n_pos < 50 or n_pos < 0.02 * len(y):  # need at least 2% positive rate
        return 0, 0.5
    # is_unbalance=True already in params — don't override with scale_pos_weight
    kf = KFold(n_splits=n_splits, shuffle=False)
    oos = pd.Series(0.0, index=X.index)
    for tri, tei in kf.split(X):
        dtrain = lgb.Dataset(X.iloc[tri], label=y.iloc[tri])
        dvalid = lgb.Dataset(X.iloc[tei], label=y.iloc[tei])
        m = lgb.train(params, dtrain, num_boost_round=300, valid_sets=[dvalid],
                     callbacks=[lgb.early_stopping(30), lgb.log_evaluation(0)])
        oos.iloc[tei] = m.predict(X.iloc[tei])
    valid = oos > 0
    if valid.sum() < 50:
        return 0, 0.5
    auc = roc_auc_score(y[valid], oos[valid])
    best_thr, best_f1 = 0.5, 0
    for thr in np.arange(0.3, 0.7, 0.02):
        f1 = f1_score(y[valid], (oos[valid] > thr).astype(int))
        if f1 > best_f1:
            best_thr, best_f1 = thr, f1
    return auc, best_thr


# Feature cache to avoid recomputation
_feat_cache = {}

def objective(trial):
    """Optuna objective — maximize (long_auc + short_auc) / 2."""
    df = load_data()
    horizon = trial.suggest_int('horizon', 6, 20)           # not too long
    tp_bps = trial.suggest_int('tp_bps', 5, 18)
    sl_bps = trial.suggest_int('sl_bps', 5, 14)             # cap SL to avoid sparse labels
    subsample = trial.suggest_int('subsample', 3, 7)
    num_leaves = trial.suggest_int('num_leaves', 15, 127)
    learning_rate = trial.suggest_float('learning_rate', 0.01, 0.15, log=True)
    feature_fraction = trial.suggest_float('feature_fraction', 0.3, 0.9)
    bagging_fraction = trial.suggest_float('bagging_fraction', 0.5, 0.95)
    min_data_in_leaf = trial.suggest_int('min_data_in_leaf', 50, 500)
    reg_alpha = trial.suggest_float('reg_alpha', 0.01, 1.0, log=True)
    reg_lambda = trial.suggest_float('reg_lambda', 0.01, 1.0, log=True)
    lgbm_params = {
        'objective': 'binary', 'metric': 'auc', 'boosting_type': 'gbdt',
        'num_leaves': num_leaves, 'learning_rate': learning_rate,
        'feature_fraction': feature_fraction, 'bagging_fraction': bagging_fraction,
        'bagging_freq': 5, 'min_data_in_leaf': min_data_in_leaf,
        'verbose': -1, 'n_jobs': -1, 'reg_alpha': reg_alpha, 'reg_lambda': reg_lambda,
        'is_unbalance': True,  # replaces extreme scale_pos_weight
    }
    # Cache features by subsample
    if subsample not in _feat_cache:
        features, df_sub = compute_features(df, subsample)
        _feat_cache[subsample] = (features, df_sub)
    features, df_sub = _feat_cache[subsample]
    mid = ((df_sub['bid'] + df_sub['ask']) / 2).loc[features.index].values
    long_lbl, short_lbl = label_ticks(mid, horizon, tp_bps, sl_bps)
    lab_long = pd.Series(long_lbl, index=features.index)
    lab_short = pd.Series(short_lbl, index=features.index)
    feat = features.select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan).dropna()
    y_long, y_short = lab_long.loc[feat.index], lab_short.loc[feat.index]
    # Label density check — penalize if too sparse (<5% positive)
    long_rate = y_long.mean()
    short_rate = y_short.mean()
    min_rate = min(long_rate, short_rate)
    if min_rate < 0.03:  # less than 3% positive → predictions will be near-zero
        penalty = min_rate / 0.03  # 0..1 multiplier
        print(f"  Trial {trial.number}: h={horizon} tp={tp_bps} sl={sl_bps} sub={subsample} | "
              f"SPARSE L={long_rate:.1%} S={short_rate:.1%} → penalty={penalty:.2f}")
        return penalty * 0.5  # low value to discourage sparse labels
    long_auc, long_thr = train_quick_lgbm(feat, y_long, lgbm_params.copy())
    short_auc, short_thr = train_quick_lgbm(feat, y_short, lgbm_params.copy())
    avg_auc = (long_auc + short_auc) / 2
    trial.set_user_attr('long_auc', long_auc)
    trial.set_user_attr('short_auc', short_auc)
    trial.set_user_attr('long_thr', long_thr)
    trial.set_user_attr('short_thr', short_thr)
    trial.set_user_attr('long_rate', long_rate)
    trial.set_user_attr('short_rate', short_rate)
    print(f"  Trial {trial.number}: h={horizon} tp={tp_bps} sl={sl_bps} sub={subsample} | "
          f"L={long_auc:.4f}({long_rate:.1%}) S={short_auc:.4f}({short_rate:.1%}) avg={avg_auc:.4f}")
    return avg_auc


def run_optuna(n_trials=60, timeout=1800):
    study = optuna.create_study(direction='maximize',
                                study_name='scalper_btc_optuna',
                                sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objective, n_trials=n_trials, timeout=timeout)
    best = study.best_trial
    print(f"\n{'='*60}")
    print(f"BEST TRIAL #{best.number}")
    print(f"  Avg AUC = {best.value:.4f}")
    print(f"  Long  AUC = {best.user_attrs['long_auc']:.4f} (thr={best.user_attrs['long_thr']:.2f})")
    print(f"  Short AUC = {best.user_attrs['short_auc']:.4f} (thr={best.user_attrs['short_thr']:.2f})")
    print(f"  Params:")
    for k, v in best.params.items():
        print(f"    {k} = {v}")
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    result = {
        'best_avg_auc': best.value,
        'long_auc': best.user_attrs['long_auc'],
        'short_auc': best.user_attrs['short_auc'],
        'long_thr': best.user_attrs['long_thr'],
        'short_thr': best.user_attrs['short_thr'],
        'params': best.params, 'n_trials': len(study.trials),
    }
    out = MODEL_DIR / f'BTCUSD_optuna_best_{ts}.json'
    with open(out, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"  Saved: {out}")
    print(f"\n  Top 5 trials:")
    df_s = study.trials_dataframe().sort_values('value', ascending=False).head(5)
    for _, row in df_s.iterrows():
        print(f"    #{int(row['number']):3d} avg={row['value']:.4f} "
              f"h={int(row['params_horizon'])} tp={int(row['params_tp_bps'])} sl={int(row['params_sl_bps'])}")
    print(f"{'='*60}")
    return result


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--trials', type=int, default=60)
    p.add_argument('--timeout', type=int, default=1800)
    a = p.parse_args()
    run_optuna(a.trials, a.timeout)

