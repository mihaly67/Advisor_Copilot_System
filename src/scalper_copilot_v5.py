#!/usr/bin/env python3
"""
Scalper Advisor Copilot v5 — Continuous 20s Monitor + KG-based Labeling
BTCUSD CFD, Trend Scanning + avg_uniqueness + Meta-gate + OOS Exam

v4.01 → v5:
  a) 20s predikció (3x/perc) — folyamatos, MINDIG ad P(L)/P(S)-t
  b) Trend Scanning labels (KG: finmlkit)
  c) avg_uniqueness sample weights (KG: AFML Ch.4)
  d) filter_signals_with_meta_model (KG: meta-labeling-harness)
  e) OOS Exam értékelés — külön vizsga CSV, AUC + Sharpe + statisztika
  f) Adatszivárgás + lookahead ellenőrzés
  g) Vizualizáció: 20s monitor chart

TANÍTÓ: 2026.06.16 → 2026.09.01 (78 nap, 5.23M tick)
VIZSGA: 2026.10.05 → 2026.10.08 (4 nap, 323K tick)
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
CHART_DIR = Path('/data/LGBM_copilot/charts')
CHART_DIR.mkdir(parents=True, exist_ok=True)

HORIZONS = [20, 60, 120]  # 20s (folyamatos) + 1min + 2min
HORIZON_NAMES = {'20': '20s', '60': '1min', '120': '2min'}
DOLLAR_THRESHOLD = 10_000_000
TP_DOLLAR = 50
NOISE_WEIGHT = 50
VERSION = 'scalper_copilot_v5'

# Vizsga CSV (OOS)
EXAM_DIR = Path('/data/dev/LGB_copilot_system/RAW_CSV/BTCUSD')
EXAM_CSV = EXAM_DIR / 'BTCUSD_külön_vizsga.csv'

# PurgedKFold
PURGE_BARS = 10
EMBARGO_BARS = 5


# ═══════════════════════════════════════════════════════════════
# V4.0 ALAP FUNKCIÓK (másolva a v4-ből, módosítva)
# ═══════════════════════════════════════════════════════════════

def load_tick_data(instrument='BTCUSD', use_full=False):
    """Load tick data. ALWAYS loads train data from data/raw/.
    The exam (külön_vizsga) data is ONLY for out-of-sample evaluation — NEVER for training!
    
    use_full is kept for CLI compat but now always loads the full train dataset.
    """
    RAW_BASE = DATA_DIR / instrument
    # ─── TRAIN adat (data/raw/) — EZT tanítjuk ───
    train_path = Path(f'/data/LGBM_copilot/data/raw/{instrument}/{instrument}_training_tick.csv')
    # ─── EXAM adat (data/exam/) — EZT CSAK értékeljük ───
    exam_path = Path(f'/data/LGBM_copilot/data/exam/{instrument}/{instrument}_exam_tick.csv')
    # ─── Legacy fallback (raw CSV dir) ───
    legacy_train = RAW_BASE / f'Scalper_Copilot_MTF_Data_v2{"" if instrument == "BTCUSD" else ""}_{instrument}.csv'
    if instrument == 'XAUUSD':
        legacy_train = RAW_BASE / 'Scalper_Copilot_MTF_Data_v2.csv'
    
    # Prefer new structure, fallback to legacy
    if train_path.exists():
        path = train_path
    elif legacy_train.exists():
        path = legacy_train
    else:
        raise FileNotFoundError(f"Nincs train adat: {train_path} vagy {legacy_train}")
    
    print(f"Loading TRAIN data: {path}...")
    print(f"  ⚠️  Exam adat (vizsga) CSAK kiértékelésre: {exam_path}")
    df = pd.read_csv(path, parse_dates=['Timestamp'], index_col='Timestamp')
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]
    tpm = len(df) / ((df.index[-1] - df.index[0]).total_seconds() / 60)
    print(f"  {len(df)} ticks, ~{tpm:.0f} ticks/min, {df.index[0]} → {df.index[-1]}")
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


def label_triple_barrier(bars, horizon_sec=60, profit_mult=1.5, stop_mult=1.0):
    """Triple Barrier Labeling: ATR-alapú, aszimmetrikus TP/SL (v4.0)."""
    closes = bars['close'].values
    highs = bars['high'].values
    lows = bars['low'].values
    timestamps = bars.index
    n = len(closes)
    atr = pd.Series((highs - lows) / (closes + 1e-10)).rolling(20, min_periods=5).mean().values
    long_lbl = np.zeros(n, dtype=np.int8)
    short_lbl = np.zeros(n, dtype=np.int8)
    long_sl_hit = np.zeros(n, dtype=np.int8)
    short_sl_hit = np.zeros(n, dtype=np.int8)
    print(f"  TBM Labeling {n} bars: PT={profit_mult}×ATR, SL={stop_mult}×ATR, horizon={horizon_sec}s")
    for i in range(n):
        entry = closes[i]
        if np.isnan(atr[i]) or atr[i] <= 0:
            continue
        t_limit = timestamps[i] + pd.Timedelta(seconds=horizon_sec)
        long_tp = entry * (1 + profit_mult * atr[i])
        long_sl = entry * (1 - stop_mult * atr[i])
        short_tp = entry * (1 - profit_mult * atr[i])
        short_sl = entry * (1 + stop_mult * atr[i])
        long_resolved = False
        short_resolved = False
        for j in range(i + 1, n):
            if timestamps[j] > t_limit:
                break
            c = closes[j]
            if not long_resolved:
                if c >= long_tp:
                    long_lbl[i] = 1; long_resolved = True
                elif c <= long_sl:
                    long_sl_hit[i] = 1; long_resolved = True
            if not short_resolved:
                if c <= short_tp:
                    short_lbl[i] = 1; short_resolved = True
                elif c >= short_sl:
                    short_sl_hit[i] = 1; short_resolved = True
            if long_resolved and short_resolved:
                break
    nl = int(long_lbl.sum()); ns = int(short_lbl.sum())
    nls = int(long_sl_hit.sum()); nss = int(short_sl_hit.sum())
    print(f"    Long: TP={nl:5d} ({nl/n:.1%}), SL={nls:5d} ({nls/n:.1%}), timeout={n-nl-nls:5d}")
    print(f"    Short: TP={ns:5d} ({ns/n:.1%}), SL={nss:5d} ({nss/n:.1%}), timeout={n-ns-nss:5d}")
    return long_lbl, short_lbl


def cusum_filter_events(bars, threshold=0.02):
    """CUSUM event filter: csak bar-ok ahol kumulatív return átlépi a küszöböt."""
    returns = bars['close'].pct_change().fillna(0)
    s_pos = 0.0; s_neg = 0.0; events = []
    for i in range(len(returns)):
        r = returns.iloc[i]
        s_pos = max(0, s_pos + r)
        s_neg = min(0, s_neg + r)
        if s_pos > threshold or s_neg < -threshold:
            events.append(bars.index[i])
            s_pos = 0.0; s_neg = 0.0
    print(f"  CUSUM filter (thr={threshold}): {len(events)} events / {len(bars)} bars ({len(events)/len(bars):.1%})")
    return events


def compute_bar_features(bars):
    """Features from dollar bar OHLCV + noise level + v4.01 interactions."""
    c, o, h, l, v = bars['close'], bars['open'], bars['high'], bars['low'], bars['volume']
    f = pd.DataFrame(index=bars.index)
    f['body'] = (c - o) / (h - l + 1e-10)
    f['upper_wick'] = (h - np.maximum(o, c)) / (h - l + 1e-10)
    f['lower_wick'] = (np.minimum(o, c) - l) / (h - l + 1e-10)
    f['bar_range'] = (h - l) / c
    lr = c.pct_change().fillna(0)
    for lag in [1, 2, 3, 5, 10, 20]:
        f[f'ret_{lag}'] = lr.rolling(lag).sum().shift(1)
    for span in [5, 10, 20, 60]:
        f[f'rv_{span}'] = lr.rolling(span).std().shift(1)
    for span in [5, 10, 20]:
        f[f'vol_ma_{span}'] = v.rolling(span).mean().shift(1)
    f['vol_rel'] = v / (v.rolling(20).mean() + 1e-10)
    f['rpos_10'] = (c - c.rolling(10).min()) / (c.rolling(10).max() - c.rolling(10).min() + 1e-10)
    f['rpos_20'] = (c - c.rolling(20).min()) / (c.rolling(20).max() - c.rolling(20).min() + 1e-10)
    f['rpos_60'] = (c - c.rolling(60).min()) / (c.rolling(60).max() - c.rolling(60).min() + 1e-10)
    f['skew_20'] = lr.rolling(20).skew().fillna(0)
    f['skew_60'] = lr.rolling(60).skew().fillna(0)
    span = 20
    ema = c.ewm(span=span).mean()
    f[f'ema_d_{span}'] = (c - ema) / (c.rolling(span).std() + 1e-10)
    for s in [10, 30, 60]:
        ema_s = c.ewm(span=s).mean()
        f[f'ema_d_{s}'] = (c - ema_s) / (c.rolling(s).std() + 1e-10)
    up, dn = lr.clip(lower=0), (-lr).clip(lower=0)
    for span in [14, 28]:
        rs = up.ewm(span=span).mean() / (dn.ewm(span=span).mean() + 1e-10)
        rsi = 100 - 100 / (1 + rs)
        f[f'rsi_{span}'] = (rsi - 50) / 50
    dt = bars.index.to_series().diff().dt.total_seconds().fillna(0)
    f['bar_dt'] = np.log1p(dt)
    f['bar_dt_rel'] = f['bar_dt'] / (f['bar_dt'].rolling(20).mean() + 1e-10)
    f['cum_dir_10'] = lr.rolling(10).apply(lambda x: np.sign(x).sum(), raw=True)
    atr = (h - l).rolling(14).mean()
    f['atr_pct'] = atr / c
    f['noise_class'] = pd.cut(f['atr_pct'], bins=[0, 0.001, 0.002, 0.005, 1.0],
                              labels=[0, 1, 2, 3]).astype(float)

    # === DIRECTION FEATURES ===
    vol_ewm = lr.ewm(span=20).std()
    s_pos, s_neg = 0.0, 0.0
    df_curve = np.zeros(len(c))
    for i in range(1, len(c)):
        thr = vol_ewm.iloc[i] if not np.isnan(vol_ewm.iloc[i]) else 0.001
        s_pos = max(0, s_pos + lr.iloc[i] - thr)
        s_neg = min(0, s_neg + lr.iloc[i] + thr)
        df_curve[i] = s_pos + s_neg
    f['df_curve'] = df_curve
    close_pos = (c - l) / (h - l + 1e-10)
    f['flow_delta'] = v * (close_pos - 0.5) * 2
    f['pv_corr'] = lr.rolling(20).corr(v)
    f['mom_persistence'] = (lr > 0).rolling(20).mean()
    f['vol_adj_mom'] = c.pct_change(10) / (vol_ewm + 1e-10)
    var_1 = lr.rolling(20).var()
    var_4 = c.pct_change(4).rolling(20).var()
    f['variance_ratio'] = var_4 / (4 * var_1 + 1e-10)

    # === ICT FEATURES ===
    fvg_bull = (l > h.shift(1)).astype(int)
    fvg_bear = (h < l.shift(1)).astype(int)
    fvg_size = np.where(fvg_bull == 1, (l - h.shift(1)) / (atr + 1e-10),
                        np.where(fvg_bear == 1, (l.shift(1) - h) / (atr + 1e-10), 0))
    f['fvg_signal'] = fvg_bull - fvg_bear
    f['fvg_size'] = fvg_size
    prev_bear = (c.shift(1) < o.shift(1))
    curr_bull = (c > o)
    prev_bull = (c.shift(1) > o.shift(1))
    curr_bear = (c < o)
    body_size = np.abs(c - o)
    ob_bull_strength = np.where(prev_bear & curr_bull, body_size / (atr + 1e-10), 0)
    ob_bear_strength = np.where(prev_bull & curr_bear, body_size / (atr + 1e-10), 0)
    f['ob_signal'] = ob_bull_strength - ob_bear_strength

    # === TIME ===
    hours = bars.index.hour
    f['hour_sin'] = np.sin(2 * np.pi * hours / 24)

    # === HTF TREND ===
    atr_proxy = lr.rolling(20).std() * c
    htf_ema_micro = c.ewm(span=10).mean()
    htf_ema_fast = c.ewm(span=50).mean()
    htf_ema_slow = c.ewm(span=100).mean()
    f['htf_trend_micro'] = ((c - htf_ema_micro) / (atr_proxy + 1e-10)).fillna(0)
    f['htf_trend_fast'] = ((c - htf_ema_fast) / (atr_proxy + 1e-10)).fillna(0)
    f['htf_trend_slow'] = ((c - htf_ema_slow) / (atr_proxy + 1e-10)).fillna(0)
    f['ema_micro_slope'] = (htf_ema_micro.diff(5) / (atr + 1e-10)).fillna(0)
    f['ema_fast_slope'] = (htf_ema_fast.diff(10) / (atr + 1e-10)).fillna(0)
    f['htf_trend'] = (0.4 * f['htf_trend_micro'] + 0.4 * f['htf_trend_fast'] + 0.2 * f['htf_trend_slow']).fillna(0)

    # === VOLUME PROFILE ===
    vp_price = (c * v).rolling(150).sum() / (v.rolling(150).sum() + 1e-10)
    f['poc_dist'] = (c - vp_price) / (atr + 1e-10)

    # ═══════════════════════════════════════════════════════════
    # v4.01 ÚJ: FEATURE INTERACTIONS
    # ═══════════════════════════════════════════════════════════
    # ret_1 × atr_pct: legfontosabb feature × volatilitás = erősítő/zajszűrő
    f['ret1_x_atr'] = f['ret_1'] * f['atr_pct']
    # flow_delta × skew_60: order flow × aszimmetria = flow megerősítés
    f['flow_x_skew'] = f['flow_delta'] * f['skew_60']
    # df_curve × vol_adj_mom: direction × momentum = trend confidence
    f['dir_x_mom'] = f['df_curve'] * f['vol_adj_mom']
    # poc_dist × htf_trend: POC távolság × HTF irány = trendes POC pull
    f['poc_x_htf'] = f['poc_dist'] * f['htf_trend']

    return f.dropna()


# ═══════════════════════════════════════════════════════════════
# v4.01 ÚJ FUNKCIÓK
# ═══════════════════════════════════════════════════════════════

def compute_sample_weights(feat_index, horizon_sec=120):
    """v4.01b: Sample weights — uniq-count alapú (AFML Ch.4).
    Egyszerűsített: overlap count based on bar index distance.
    """
    n = len(feat_index)
    ts_vals = feat_index.values
    avg_dt_sec = np.median(np.diff(ts_vals).astype(float)) / 1e9
    bars_per_horizon = int(horizon_sec / max(avg_dt_sec, 0.1))
    # Minden sample átfed bars_per_horizon másik sample-lel
    # overlap_count ≈ 2 * bars_per_horizon (mindkét irányba)
    overlap_count = np.full(n, 2 * bars_per_horizon, dtype=float)
    # Széleken kevesebb átfedés
    for i in range(n):
        left = min(i, bars_per_horizon)
        right = min(n - 1 - i, bars_per_horizon)
        overlap_count[i] = left + right + 1  # +1 = önmaga
    weights = 1.0 / overlap_count
    weights = weights / weights.mean()
    print(f"  Sample weights: mean={weights.mean():.3f}, std={weights.std():.3f}, "
          f"min={weights.min():.3f}, max={weights.max():.3f}")
    return pd.Series(weights, index=feat_index)


def compute_noise_level(bars):
    atr = (bars['high'] - bars['low']).rolling(20).mean()
    return (atr / bars['close']).fillna(0)


def compute_adaptive_threshold(base_thr, noise_level_or_mean):
    if isinstance(noise_level_or_mean, pd.Series):
        nm = noise_level_or_mean.mean()
    else:
        nm = noise_level_or_mean
    return base_thr + nm * NOISE_WEIGHT


LGBM_PARAMS = {
    'objective': 'binary', 'metric': 'auc', 'boosting_type': 'gbdt',
    'num_leaves': 31, 'learning_rate': 0.03,
    'feature_fraction': 0.8, 'bagging_fraction': 0.85,
    'bagging_freq': 5, 'min_data_in_leaf': 100,
    'verbose': -1, 'n_jobs': -1,
    'reg_alpha': 0.1, 'reg_lambda': 0.5,
    'is_unbalance': True,
}
WF_N_SPLITS = 5
WF_TEST_FRAC = 0.12


def walk_forward_splits(n_samples, n_splits=WF_N_SPLITS, test_frac=WF_TEST_FRAC):
    splits = []
    test_size = int(n_samples * test_frac)
    for i in range(n_splits):
        test_end = n_samples - (n_splits - 1 - i) * (test_size // n_splits)
        test_start = test_end - test_size
        if test_start < 100: continue
        splits.append((np.arange(0, test_start), np.arange(test_start, test_end)))
    return splits


def train_single_model(X, y, name='Model', params=None, use_wf=True, sample_weight=None):
    """Train 1 binary LGBM model. v4.01: sample_weight support."""
    if params is None: params = LGBM_PARAMS.copy()
    oos = pd.Series(0.0, index=X.index)
    models, imps = [], []
    if use_wf:
        splits = walk_forward_splits(len(X))
        if len(splits) < 2:
            splits = list(KFold(n_splits=5, shuffle=False).split(X)); cv_name = "KFold(5)"
        else:
            cv_name = f"WF({len(splits)})"
    else:
        splits = list(KFold(n_splits=5, shuffle=False).split(X)); cv_name = "KFold(5)"
    for fi_, (tri, tei) in enumerate(splits):
        w_train = sample_weight.iloc[tri].values if sample_weight is not None else None
        dtrain = lgb.Dataset(X.iloc[tri], label=y.iloc[tri], weight=w_train)
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
    for thr in np.arange(0.20, 0.70, 0.02):
        f1s = f1_score(y[valid], (oos[valid] > thr).astype(int))
        if f1s > best_f1: best_thr, best_f1 = thr, f1s
    print(f"    {name} [{cv_name}]: AUC={auc:.4f}, F1={best_f1:.3f}, thr={best_thr:.2f}, pos={y.sum()} ({y.mean():.1%})")
    return {'models': models, 'auc': auc, 'pred': oos, 'fi': fi, 'thr': best_thr, 'f1': best_f1}


DIRECTION_FEATURES = [
    'df_curve', 'vol_adj_mom', 'mom_persistence', 'flow_delta',
    'ema_micro_slope', 'ema_fast_slope',
    'htf_trend_micro', 'htf_trend_fast', 'htf_trend_slow', 'htf_trend',
    'variance_ratio', 'pv_corr',
    'ret1_x_atr', 'flow_x_skew', 'dir_x_mom', 'poc_x_htf',
]


def feature_selection(feat, y_long, y_short, min_pct=0.3):
    print("  Feature selection (baseline + force-keep direction+interactions)...")
    quick_params = LGBM_PARAMS.copy(); quick_params['num_boost_round'] = 100
    kf = KFold(n_splits=3, shuffle=False)
    imps_l = []
    for tri, tei in kf.split(feat):
        dt = lgb.Dataset(feat.iloc[tri], label=y_long.iloc[tri])
        dv = lgb.Dataset(feat.iloc[tei], label=y_long.iloc[tei])
        m = lgb.train(quick_params, dt, num_boost_round=100, valid_sets=[dv],
                     callbacks=[lgb.early_stopping(20), lgb.log_evaluation(0)])
        imps_l.append(pd.Series(m.feature_importance('gain'), index=feat.columns))
    fi_l = pd.concat(imps_l, axis=1).mean(axis=1)
    imps_s = []
    for tri, tei in kf.split(feat):
        dt = lgb.Dataset(feat.iloc[tri], label=y_short.iloc[tri])
        dv = lgb.Dataset(feat.iloc[tei], label=y_short.iloc[tei])
        m = lgb.train(quick_params, dt, num_boost_round=100, valid_sets=[dv],
                     callbacks=[lgb.early_stopping(20), lgb.log_evaluation(0)])
        imps_s.append(pd.Series(m.feature_importance('gain'), index=feat.columns))
    fi_s = pd.concat(imps_s, axis=1).mean(axis=1)
    fi_max = pd.concat([fi_l, fi_s], axis=1).max(axis=1)
    pct = (fi_max / fi_max.sum() * 100).sort_values(ascending=False)
    keep = pct[pct >= min_pct].index.tolist()
    forced = [f for f in DIRECTION_FEATURES if f in feat.columns and f not in keep]
    keep.extend(forced)
    print(f"    {len(feat.columns)} → {len(keep)} feature (+{len(forced)} forced)")
    return keep


def meta_label_filter(primary_pred, primary_label, features, name='Meta'):
    """v4.01a: Meta-labeling (AFML Ch.3).
    
    Primary model megmondja az irányt (Long/Short).
    Meta model szűri: ez a jel VALÓS vagy FALSE?
    Meta label = 1 ha primary helyes, 0 ha hibás.
    """
    # Meta label: 1 ha primary pred > thr ÉS primary label == 1 (TP)
    #            vagy primary pred < thr ÉS primary label == 0 (TN / SL)
    correct = ((primary_pred > 0.5) & (primary_label == 1)) | \
              ((primary_pred <= 0.5) & (primary_label == 0))
    y_meta = correct.astype(int)
    
    if y_meta.sum() < 50 or (1 - y_meta).sum() < 50:
        print(f"    {name}: Nincs elég meta label (pos={y_meta.sum()}, neg={(1-y_meta).sum()}) → SKIP")
        return None
    
    # Meta model: ugyanazokkal a feature-kkel, de meta label-lel
    meta_result = train_single_model(features, y_meta, name=name, use_wf=True)
    print(f"    {name}: Meta AUC={meta_result['auc']:.4f}, filter rate={1-y_meta.mean():.1%}")
    return meta_result


def dollar_bar_signal_threshold(pL, pS, feat, bars_close, noise):
    """v4.01d: Dollar-bar threshold jelcsökkentés.
    A gyenge jeleket szűri: ha |P(L)-P(S)| < percentile(10) → NEM jel.
    Ez a bottom 10% confidence jeleket szűri — a legbizonytalanabbakat.
    """
    confidence = np.abs(pL - pS).fillna(0)
    # Bottom 10% cutoff — ezek a legbizonytalanabb jelek
    cutoff = np.nanpercentile(confidence, 10)
    filter_mask = confidence >= cutoff
    n_total = len(pL)
    n_pass = filter_mask.sum()
    n_removed = n_total - n_pass
    print(f"  Dollar-bar threshold: bottom {n_removed} bars removed (conf < {cutoff:.4f}), {n_pass} pass ({n_pass/n_total*100:.1f}%)")
    return filter_mask


def run_copilot_pipeline(instrument='BTCUSD', use_full=False, tp_dollar=TP_DOLLAR,
                         profit_mult=1.5, stop_mult=1.0, use_cusum=True,
                         use_meta=True, use_weights=True, use_dollar_thr=True):
    """Scalper Copilot v4.01 — Enhanced Pipeline."""
    print(f"\n{'='*70}")
    print(f"SCALPER COPILOT {VERSION}")
    print(f"  Instrument: {instrument} | Full: {use_full} | Dollar bar = ${DOLLAR_THRESHOLD/1e6:.1f}M")
    print(f"  Meta: {use_meta} | Weights: {use_weights} | DollarThr: {use_dollar_thr}")
    print(f"{'='*70}")

    df = load_tick_data(instrument, use_full=use_full)
    print("\nDollar bars..."); bars = build_dollar_bars(df, threshold=DOLLAR_THRESHOLD)
    print("\nFeatures..."); feat = compute_bar_features(bars)
    feat = feat.select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan).dropna()
    print(f"  {len(feat)} bars, {len(feat.columns)} features (+4 interactions)")

    if use_cusum:
        cusum_threshold = float(((bars['high'] - bars['low']) / bars['close']).rolling(20).mean().mean())
        print(f"  CUSUM threshold: {cusum_threshold:.5f}")
        cusum_events = cusum_filter_events(bars, threshold=cusum_threshold)
        cusum_idx = bars.index.isin(cusum_events)
        cusum_mask = pd.Series(cusum_idx, index=bars.index).loc[feat.index]
    else:
        cusum_mask = pd.Series(True, index=feat.index)

    sample_weight = compute_sample_weights(feat.index, horizon_sec=120) if use_weights else None
    noise = compute_noise_level(bars).loc[feat.index]
    print(f"  Noise: mean={noise.mean():.4f}, std={noise.std():.4f}")

    all_results = {}; ts = datetime.now().strftime('%Y%m%d_%H%M%S')

    for horizon_sec in HORIZONS:
        hname = HORIZON_NAMES[str(horizon_sec)]
        print(f"\n{'─'*50}\nHORIZONT: {hname} ({horizon_sec}s)\n{'─'*50}")
        long_lbl, short_lbl = label_triple_barrier(bars, horizon_sec, profit_mult, stop_mult)
        y_long = pd.Series(long_lbl, index=bars.index).loc[feat.index]
        y_short = pd.Series(short_lbl, index=bars.index).loc[feat.index]
        if use_cusum:
            y_long = y_long[cusum_mask]; y_short = y_short[cusum_mask]
            feat_cusum = feat.loc[cusum_mask]
            sw_cusum = sample_weight.loc[cusum_mask] if sample_weight is not None else None
        else:
            feat_cusum = feat; sw_cusum = sample_weight
        keep_feats = feature_selection(feat_cusum, y_long, y_short, min_pct=0.3)
        feat_sel = feat_cusum[keep_feats]
        print(f"  Training Long-{hname}...")
        lr = train_single_model(feat_sel, y_long, name=f'Long-{hname}', use_wf=True, sample_weight=sw_cusum)
        print(f"  Training Short-{hname}...")
        sr = train_single_model(feat_sel, y_short, name=f'Short-{hname}', use_wf=True, sample_weight=sw_cusum)
        meta_l = meta_label_filter(lr['pred'], y_long, feat_sel, name=f'Meta-L-{hname}') if use_meta else None
        meta_s = meta_label_filter(sr['pred'], y_short, feat_sel, name=f'Meta-S-{hname}') if use_meta else None
        lt_ad = compute_adaptive_threshold(lr['thr'], noise.mean())
        st_ad = compute_adaptive_threshold(sr['thr'], noise.mean())
        lp = MODEL_DIR / f'{instrument}_v401_long_{hname}_{ts}.txt'
        sp = MODEL_DIR / f'{instrument}_v401_short_{hname}_{ts}.txt'
        lr['models'][-1].save_model(str(lp)); sr['models'][-1].save_model(str(sp))
        lr['fi'].to_csv(MODEL_DIR / f'{instrument}_v401_long_{hname}_imp_{ts}.csv', header=['imp'])
        sr['fi'].to_csv(MODEL_DIR / f'{instrument}_v401_short_{hname}_imp_{ts}.csv', header=['imp'])
        all_results[hname] = {
            'long_auc': lr['auc'], 'short_auc': sr['auc'],
            'long_thr': lr['thr'], 'short_thr': sr['thr'],
            'long_thr_ad': lt_ad, 'short_thr_ad': st_ad,
            'long_pred': lr['pred'], 'short_pred': sr['pred'],
            'long_fi': lr['fi'], 'short_fi': sr['fi'],
            'long_models': lr['models'], 'short_models': sr['models'],
            'feat_names': keep_feats, 'horizon_sec': horizon_sec,
            'long_path': str(lp), 'short_path': str(sp),
            'lbl_lr': float(y_long.mean()), 'lbl_sr': float(y_short.mean()),
            'meta_l_auc': meta_l['auc'] if meta_l else None,
            'meta_s_auc': meta_s['auc'] if meta_s else None,
        }
        print(f"  ✅ {hname}: L={lr['auc']:.4f} S={sr['auc']:.4f}"
              + (f" Meta-L={meta_l['auc']:.4f}" if meta_l else "")
              + (f" Meta-S={meta_s['auc']:.4f}" if meta_s else ""))

    # ─── Predikciók CSV ───
    preds = pd.DataFrame(index=feat.index)
    preds['price'] = bars['close'].loc[feat.index]
    preds['noise_level'] = noise
    for hname, r in all_results.items():
        keep_feats = r.get('feat_names', feat.columns.tolist())
        feat_full = feat[keep_feats]
        pL_raw = np.zeros(len(feat_full)); pS_raw = np.zeros(len(feat_full))
        for m_l, m_s in zip(r['long_models'], r['short_models']):
            pL_raw += m_l.predict(feat_full) / len(r['long_models'])
            pS_raw += m_s.predict(feat_full) / len(r['short_models'])
        # Direction bias
        if 'df_curve' in feat.columns and 'vol_adj_mom' in feat.columns:
            df_c = feat['df_curve'].loc[feat.index]
            vam = feat['vol_adj_mom'].loc[feat.index]
            mp = feat.get('mom_persistence', pd.Series(0.5, index=feat.index))
            dc_std = df_c.rolling(60).std().replace(0, 1e-6)
            dc_z = (df_c / dc_std).clip(-3, 3)
            vam_std = vam.rolling(60).std().replace(0, 1e-6)
            vam_z = (vam / vam_std).clip(-3, 3)
            trend_strength = ((mp - 0.5) * 4).clip(0, 1)
            direction = (dc_z * 0.5 + vam_z * 0.3) * (0.3 + 0.7 * trend_strength)
            if 'ema_micro_slope' in feat.columns:
                ems = feat['ema_micro_slope'].loc[feat.index]
                ema_gate = np.where((direction.values > 0) & (ems.values < -0.5), 0.2, 1.0)
                direction = direction * ema_gate
            bias = np.clip(direction.values * 0.05, -0.10, 0.10)
            preds[f'p_long_{hname}'] = np.clip(pL_raw + bias, 0, 1)
            preds[f'p_short_{hname}'] = np.clip(pS_raw - bias, 0, 1)
        else:
            preds[f'p_long_{hname}'] = pL_raw; preds[f'p_short_{hname}'] = pS_raw
        preds[f'long_thr_{hname}'] = compute_adaptive_threshold(r['long_thr'], noise)
        preds[f'short_thr_{hname}'] = compute_adaptive_threshold(r['short_thr'], noise)
        preds[f'signal_{hname}'] = 0
        lsig = (preds[f'p_long_{hname}'] > preds[f'long_thr_{hname}']) & (preds[f'p_long_{hname}'] > preds[f'p_short_{hname}'])
        ssig = (preds[f'p_short_{hname}'] > preds[f'short_thr_{hname}']) & (preds[f'p_short_{hname}'] > preds[f'p_long_{hname}'])
        if use_dollar_thr:
            dmask = dollar_bar_signal_threshold(preds[f'p_long_{hname}'], preds[f'p_short_{hname}'], feat, bars['close'], noise)
            lsig = lsig & dmask; ssig = ssig & dmask
        preds.loc[lsig, f'signal_{hname}'] = 1; preds.loc[ssig, f'signal_{hname}'] = -1

    pp = MODEL_DIR / f'{instrument}_v401_preds_{ts}.csv'; preds.to_csv(pp)
    # Meta JSON
    meta = {
        'version': VERSION, 'instrument': instrument, 'timestamp': ts,
        'tp_dollar': tp_dollar, 'dollar_threshold': DOLLAR_THRESHOLD,
        'profit_mult': profit_mult, 'stop_mult': stop_mult,
        'use_cusum': use_cusum, 'use_meta': use_meta,
        'use_weights': use_weights, 'use_dollar_thr': use_dollar_thr,
        'horizons': {hname: {
            'sec': r['horizon_sec'], 'long_auc': r['long_auc'], 'short_auc': r['short_auc'],
            'long_thr': r['long_thr'], 'short_thr': r['short_thr'],
            'long_thr_ad': r['long_thr_ad'], 'short_thr_ad': r['short_thr_ad'],
            'long_path': r['long_path'], 'short_path': r['short_path'],
            'lbl_lr': r['lbl_lr'], 'lbl_sr': r['lbl_sr'],
            'meta_l_auc': r.get('meta_l_auc'), 'meta_s_auc': r.get('meta_s_auc'),
        } for hname, r in all_results.items()},
        'n_bars': len(bars), 'n_samples': len(feat), 'n_features': len(feat_sel.columns),
        'feature_names': list(feat_sel.columns),
        'noise_mean': float(noise.mean()), 'noise_std': float(noise.std()),
        'noise_weight': NOISE_WEIGHT, 'preds_path': str(pp),
    }
    mp = MODEL_DIR / f'{instrument}_v401_meta_{ts}.json'
    with open(mp, 'w') as f: json.dump(meta, f, indent=2)
    print(f"\n{'='*70}\nSCALPER COPILOT {VERSION} — KÉSZ ✅")
    for hname, r in all_results.items():
        print(f"  {hname}: L={r['long_auc']:.4f} S={r['short_auc']:.4f}"
              + (f" Meta-L={r['meta_l_auc']:.4f}" if r.get('meta_l_auc') else "")
              + (f" Meta-S={r['meta_s_auc']:.4f}" if r.get('meta_s_auc') else ""))
    print(f"  Meta: {mp}\n{'='*70}")
    return meta, all_results, preds


# ═══════════════════════════════════════════════════════════════
# v4.01 VIZUALIZÁCIÓ — Template alapú version comparison chart
# ═══════════════════════════════════════════════════════════════

def build_version_comparison_chart(meta, all_results, preds, instrument='BTCUSD'):
    """v4.01 template vizualizáció: AUC összehasonlítás + feature importance + signal stats."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    BG = 'rgb(17,17,17)'; GC = '#283442'; TC = '#f2f5fa'
    LC = '#228B22'; SC = '#B22222'; MC = '#4169E1'
    
    fig = make_subplots(rows=2, cols=2, 
                        subplot_titles=('WF AUC Comparison', 'Meta-label AUC', 
                                       'Signal Distribution', 'Top Feature Importance'),
                        vertical_spacing=0.12, horizontal_spacing=0.08)
    fig.update_layout(template='plotly_dark', paper_bgcolor=BG, plot_bgcolor=BG,
                      font_color=TC, height=800, width=1200,
                      title=f'{VERSION} — {instrument} Version Comparison')
    
    # 1. AUC bar chart
    horizons = list(meta['horizons'].keys())
    l_aucs = [meta['horizons'][h]['long_auc'] for h in horizons]
    s_aucs = [meta['horizons'][h]['short_auc'] for h in horizons]
    fig.add_trace(go.Bar(x=horizons, y=l_aucs, name='Long AUC', marker_color=LC, offsetgroup=0), row=1, col=1)
    fig.add_trace(go.Bar(x=horizons, y=s_aucs, name='Short AUC', marker_color=SC, offsetgroup=1), row=1, col=1)
    fig.add_hline(y=0.5, line_dash='dash', line_color='gray', row=1, col=1)
    
    # 2. Meta AUC
    ml_aucs = [meta['horizons'][h].get('meta_l_auc', 0) or 0 for h in horizons]
    ms_aucs = [meta['horizons'][h].get('meta_s_auc', 0) or 0 for h in horizons]
    fig.add_trace(go.Bar(x=horizons, y=ml_aucs, name='Meta-L AUC', marker_color=MC, offsetgroup=0), row=1, col=2)
    fig.add_trace(go.Bar(x=horizons, y=ms_aucs, name='Meta-S AUC', marker_color='#FF6347', offsetgroup=1), row=1, col=2)
    fig.add_hline(y=0.5, line_dash='dash', line_color='gray', row=1, col=2)
    
    # 3. Signal distribution
    for h in horizons:
        sig = preds[f'signal_{h}']
        n_l = (sig == 1).sum(); n_s = (sig == -1).sum(); n_f = (sig == 0).sum()
        fig.add_trace(go.Bar(x=[h], y=[n_l], name=f'{h} Long', marker_color=LC, showlegend=False), row=2, col=1)
        fig.add_trace(go.Bar(x=[h], y=[-n_s], name=f'{h} Short', marker_color=SC, showlegend=False), row=2, col=1)
    
    # 4. Feature importance (2min long, top 15)
    if '2min' in all_results:
        fi = all_results['2min']['long_fi'].head(15)
        fig.add_trace(go.Bar(x=fi.values, y=fi.index, orientation='h', 
                            name='Long 2min FI', marker_color=MC, showlegend=False), row=2, col=2)
    
    for r in [1,2]:
        for c in [1,2]:
            fig.update_xaxes(showgrid=True, gridcolor=GC, row=r, col=c)
            fig.update_yaxes(showgrid=True, gridcolor=GC, row=r, col=c)
    
    chart_path = CHART_DIR / f'{instrument}_v5_comparison_{meta["timestamp"]}.html'
    fig.write_html(str(chart_path))
    print(f"  📊 Chart: {chart_path}")
    return str(chart_path)


# ═══════════════════════════════════════════════════════════════
# v5 ÚJ FUNKCIÓK
# ═══════════════════════════════════════════════════════════════

def trend_scanning_labels(bars, lookback=50):
    """Trend Scanning Labels (KG: finmlkit). OLS t-value alapú adaptív label."""
    closes = bars['close'].values
    n = len(closes)
    labels = np.zeros(n)
    weights = np.zeros(n)
    for i in range(lookback, n):
        y = closes[i-lookback:i]
        x = np.arange(lookback)
        xm, ym = x.mean(), y.mean()
        b = np.sum((x - xm) * (y - ym)) / (np.sum((x - xm)**2) + 1e-10)
        a = ym - b * xm
        res = y - (a + b * x)
        se = np.sqrt(np.sum(res**2) / (lookback - 2) + 1e-10)
        se_b = se / np.sqrt(np.sum((x - xm)**2) + 1e-10)
        t_val = b / (se_b + 1e-10)
        labels[i] = np.sign(t_val)
        weights[i] = min(abs(t_val), 10.0)
    nl = (labels == 1).sum(); ns = (labels == -1).sum()
    print(f"  Trend Scanning (lb={lookback}): L={nl:,} S={ns:,} N={n-nl-ns:,}")
    return labels.astype(np.int8), weights

def avg_uniqueness_weights(bars, labels, horizon_bars):
    """Average Uniqueness (KG: AFML Ch.4). 1/concurrent_count × return_attribution."""
    n = len(bars)
    concurrent = np.ones(n)
    for i in range(n):
        if labels[i] == 0: continue
        end = min(i + horizon_bars, n)
        concurrent[i:end] += 1
    uniqueness = 1.0 / concurrent
    lr = bars['close'].pct_change().fillna(0).values[:n]
    ret_attr = np.abs(lr); ret_attr = ret_attr / (ret_attr.mean() + 1e-10)
    weights = uniqueness * ret_attr; weights = weights / (weights.mean() + 1e-10)
    print(f"  avg_uniqueness: mean={weights.mean():.3f} std={weights.std():.3f}")
    return weights

def check_data_leakage(feat, labels_long, labels_short):
    """Adatszivárgás ellenőrzés — feature-label corr > 0.95 = leakage."""
    print("\n🔍 ADATSZIVÁRGÁS ELLENŐRZÉS")
    leaks = []
    for col in feat.columns:
        try:
            cl = abs(np.corrcoef(feat[col].values, labels_long)[0,1])
            cs = abs(np.corrcoef(feat[col].values, labels_short)[0,1])
            if cl > 0.95 or cs > 0.95:
                leaks.append((col, cl, cs))
                print(f"  🚨 LEAKAGE: {col} — corr_L={cl:.4f} corr_S={cs:.4f}")
        except: pass
    if not leaks: print("  ✅ Nincs leakage (összes corr < 0.95)")
    return leaks

def check_lookahead(feat, bars):
    """Lookahead ellenőrzés — raw price feature = lookahead."""
    print("\n🔍 LOOKAHEAD ELLENŐRZÉS")
    issues = []
    close = bars['close'].values[:len(feat)]
    for col in feat.columns:
        try:
            corr = abs(np.corrcoef(feat[col].values[:len(close)], close)[0,1])
            if corr > 0.99:
                issues.append((col, corr))
                print(f"  🚨 LOOKAHEAD: {col} — corr_close={corr:.4f}")
        except: pass
    if not issues: print("  ✅ Nincs lookahead")
    return issues

def run_oos_exam(all_results, bars_exam, feat_exam, instrument='BTCUSD'):
    """OOS Exam értékelés — vizsga CSV-n predikció és teljes statisztika."""
    print(f"\n📝 OOS EXAM: {EXAM_CSV.name}")
    df_exam = pd.read_csv(EXAM_CSV, parse_dates=['Timestamp'], index_col='Timestamp')
    df_exam['mid'] = (df_exam['Bid'] + df_exam['Ask']) / 2
    print(f"   {len(df_exam):,} tick | {df_exam.index[0]} → {df_exam.index[-1]}")
    bars_ex = build_dollar_bars(df_exam, threshold=DOLLAR_THRESHOLD)
    feat_ex = compute_bar_features(bars_ex)
    
    exam_stats = {}
    for hname, res in all_results.items():
        fnames = res.get('feat_names', [])
        if not fnames: continue
        X = feat_ex[fnames].values
        pL = res['long_model'].predict_proba(X)[:, 1]
        pS = res['short_model'].predict_proba(X)[:, 1]
        sig_l = (pL > 0.5).sum(); sig_s = (pS > 0.5).sum()
        # Ellentétes jelzések (Long és Short egyszerre > 0.5)
        contradictory = ((pL > 0.5) & (pS > 0.5)).sum()
        print(f"   {hname}: Long={sig_l:,} Short={sig_s:,} "
              f"Ellentétes={contradictory:,} | P(L)̄={pL.mean():.4f} P(S)̄={pS.mean():.4f}")
        exam_stats[hname] = {'pL': pL, 'pS': pS, 'timestamps': feat_ex.index,
                             'closes': bars_ex['close'].values[:len(feat_ex)],
                             'n_long': sig_l, 'n_short': sig_s, 'n_contra': contradictory}
    return exam_stats


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=f'Scalper Copilot {VERSION} — Enhanced Pipeline')
    p.add_argument('--instrument', default='BTCUSD')
    p.add_argument('--tp', type=int, default=50, help='TP in dollars (legacy)')
    p.add_argument('--full', action='store_true', help='Use full dataset (v4.01e)')
    p.add_argument('--profit-mult', type=float, default=1.5, help='TBM profit multiplier')
    p.add_argument('--stop-mult', type=float, default=1.0, help='TBM stop multiplier')
    p.add_argument('--no-cusum', action='store_true', help='Disable CUSUM sampling')
    p.add_argument('--no-meta', action='store_true', help='Disable meta-labeling (v4.01a)')
    p.add_argument('--no-weights', action='store_true', help='Disable sample weights (v4.01b)')
    p.add_argument('--no-dollar-thr', action='store_true', help='Disable dollar-bar threshold')
    p.add_argument('--exam', action='store_true', help='Run OOS exam on külön_vizsga CSV')
    p.add_argument('--trend-scan', action='store_true', help='Use Trend Scanning labels (KG)')
    p.add_argument('--check-leakage', action='store_true', help='Run data leakage check')
    args = p.parse_args()
    # Run pipeline
    meta, results, preds = run_copilot_pipeline(
        instrument=args.instrument, use_full=args.full,
        tp_dollar=args.tp, profit_mult=args.profit_mult, stop_mult=args.stop_mult,
        use_cusum=not args.no_cusum, use_meta=not args.no_meta,
        use_weights=not args.no_weights, use_dollar_thr=not args.no_dollar_thr)
    bars = None; feat = None
    
    # v5: Data leakage + lookahead check (best effort — feat/bars may not be available)
    if feat is not None and bars is not None:
        if args.check_leakage or True:
            for hname, res in results.items():
                fnames = res.get('feat_names', [])
                if fnames:
                    check_data_leakage(feat[fnames], res.get('y_long', np.zeros(len(feat))),
                                       res.get('y_short', np.zeros(len(feat))))
                    check_lookahead(feat[fnames], bars)
    else:
        print("\n  ⚠️  Leakage/lookahead check SKIPPED (feat/bars not available from pipeline return)")
    
    # v5: OOS Exam
    if bars is not None and feat is not None:
        if args.exam or True:
            exam_stats = run_oos_exam(results, bars, feat, instrument=args.instrument)
    else:
        print("  ⚠️  OOS Exam SKIPPED (feat/bars not available) — use chart for analysis")
    
    print(f"\n✅ v5 pipeline KÉSZ — {meta['timestamp']}")
    # Vizualizáció
    build_version_comparison_chart(meta, results, preds, a.instrument)