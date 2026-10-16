#!/usr/bin/env python3
"""
Scalper Copilot v4.0 — Multi-Horizon Advisory Pipeline
BTCUSD 1min bars, 3 horizont (60s, 120s, 180s)

NEM robot — tanácsadó. Folyamatosan vizsgálja az áralakulást és
valószínűséget ad: ha most belépek [LONG/SHORT], mekkora az esély,
hogy N perc alatt profitos kilépés lehetséges?

Horizontok:
  1min: P(Long)/P(Short) — 60s alatt eléri a TP-t?
  2min: P(Long)/P(Short) — 120s alatt eléri a TP-t?
  3min: P(Long)/P(Short) — 180s alatt eléri a TP-t?

TP dinamikus: max(spread * 2, ATR_pct * price * tp_mult)
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

HORIZONS = [60, 120, 180]
HORIZON_NAMES = {'60': '1min', '120': '2min', '180': '3min'}
DOLLAR_THRESHOLD = 10_000_000
TP_DOLLAR = 50
NOISE_WEIGHT = 50


def load_tick_data(instrument='BTCUSD', use_full=False):
    """Load tick data. ALWAYS loads train data from data/raw/.
    The exam (külön_vizsga) data is ONLY for out-of-sample evaluation — NEVER for training!
    """
    train_path = Path(f'/data/LGBM_copilot/data/raw/{instrument}/training_tick_{instrument}.csv')
    exam_path = Path(f'/data/LGBM_copilot/data/exam/{instrument}/exam_tick_{instrument}.csv')
    legacy_train = DATA_DIR / instrument / (
        'Scalper_Copilot_MTF_Data_v2_BTCUSD.csv' if instrument == 'BTCUSD'
        else 'Scalper_Copilot_MTF_Data_v2.csv')
    
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


def label_bars_direction(bars, horizon_sec=60, tp_dollar=TP_DOLLAR):
    """Label each bar: did close move +TP (Long=1) or -TP (Short=1) within horizon?
    [RÉGI — szimmetrikus fix dollár. Új pipeline: label_triple_barrier()]"""
    closes = bars['close'].values
    timestamps = bars.index
    n = len(closes)
    long_lbl = np.zeros(n, dtype=np.int8)
    short_lbl = np.zeros(n, dtype=np.int8)
    print(f"  Labeling {n} bars: TP=${tp_dollar}, horizon={horizon_sec}s ({horizon_sec//60}min)")
    for i in range(n):
        entry = closes[i]
        t_limit = timestamps[i] + pd.Timedelta(seconds=horizon_sec)
        for j in range(i + 1, n):
            if timestamps[j] > t_limit: break
            if closes[j] >= entry + tp_dollar: long_lbl[i] = 1; break
            elif closes[j] <= entry - tp_dollar: short_lbl[i] = 1; break
    nl, ns = long_lbl.sum(), short_lbl.sum()
    nn = n - nl - ns
    print(f"    Long: {nl:5d} ({nl/n:.1%}), Short: {ns:5d} ({ns/n:.1%}), Neutral: {nn:5d} ({nn/n:.1%})")
    return long_lbl, short_lbl


def label_triple_barrier(bars, horizon_sec=60, profit_mult=1.5, stop_mult=1.0):
    """Triple Barrier Labeling: ATR-alapú, aszimmetrikus TP/SL.

    Advisor copilot: független Long és Short kérdés minden bar-on.
      Long:  eléri-e +PT mielőtt -SL-t? (PT=profit_mult×ATR, SL=stop_mult×ATR)
      Short: eléri-e -PT mielőtt +SL-t?

    profit_mult > stop_mult → trend-following:
      - Trend folytatás → TP messzebb → ha eléri = erős signál
      - Mean-reversion bounce → SL közelebb → SL hit = NEM signál
      - Ez SZŰRI a false reversion jeleket!

    Forrás: pt_sl_asymmetry_experiment.md, ml_knowledge_base (§1.1 TBM)
    """
    closes = bars['close'].values
    highs = bars['high'].values
    lows = bars['low'].values
    timestamps = bars.index
    n = len(closes)

    # ATR: rolling 20-bar high-low range / close (százalékban)
    atr = pd.Series((highs - lows) / (closes + 1e-10)).rolling(20, min_periods=5).mean().values

    long_lbl = np.zeros(n, dtype=np.int8)
    short_lbl = np.zeros(n, dtype=np.int8)
    long_sl_hit = np.zeros(n, dtype=np.int8)  # statisztika
    short_sl_hit = np.zeros(n, dtype=np.int8)

    print(f"  TBM Labeling {n} bars: PT={profit_mult}×ATR, SL={stop_mult}×ATR, horizon={horizon_sec}s ({horizon_sec//60}min)")

    for i in range(n):
        entry = closes[i]
        if np.isnan(atr[i]) or atr[i] <= 0:
            continue
        t_limit = timestamps[i] + pd.Timedelta(seconds=horizon_sec)

        # Long barriers
        long_tp = entry * (1 + profit_mult * atr[i])   # fenti TP
        long_sl = entry * (1 - stop_mult * atr[i])     # lenti SL
        # Short barriers
        short_tp = entry * (1 - profit_mult * atr[i])  # lenti TP
        short_sl = entry * (1 + stop_mult * atr[i])    # fenti SL

        long_resolved = False
        short_resolved = False

        for j in range(i + 1, n):
            if timestamps[j] > t_limit:
                break
            c = closes[j]

            # Long barrier check
            if not long_resolved:
                if c >= long_tp:
                    long_lbl[i] = 1; long_resolved = True
                elif c <= long_sl:
                    long_sl_hit[i] = 1; long_resolved = True

            # Short barrier check
            if not short_resolved:
                if c <= short_tp:
                    short_lbl[i] = 1; short_resolved = True
                elif c >= short_sl:
                    short_sl_hit[i] = 1; short_resolved = True

            if long_resolved and short_resolved:
                break

    nl = int(long_lbl.sum())
    ns = int(short_lbl.sum())
    nls = int(long_sl_hit.sum())
    nss = int(short_sl_hit.sum())
    nn = n - nl - nls  # Long szempont: TP + SL + timeout
    print(f"    Long: TP={nl:5d} ({nl/n:.1%}), SL={nls:5d} ({nls/n:.1%}), timeout={n-nl-nls:5d}")
    print(f"    Short: TP={ns:5d} ({ns/n:.1%}), SL={nss:5d} ({nss/n:.1%}), timeout={n-ns-nss:5d}")
    return long_lbl, short_lbl


def cusum_filter_events(bars, threshold=0.02):
    """CUSUM event filter: csak bar-ok ahol kumulatív return átlépi a küszöböt.

    Forrás: ml_knowledge_base §1.2, labelling_study §K3
    CUSUM event-ek NEM folytatásjelzések — REVERSION jelek!
    De event-eken tanítani = fókusz az irányváltozásokon, nem a zajszintű neutral bar-okon.
    """
    returns = bars['close'].pct_change().fillna(0)
    s_pos = 0.0
    s_neg = 0.0
    events = []
    s_pos_arr = np.zeros(len(bars))
    s_neg_arr = np.zeros(len(bars))
    for i in range(len(returns)):
        r = returns.iloc[i]
        s_pos = max(0, s_pos + r)
        s_neg = min(0, s_neg + r)
        s_pos_arr[i] = s_pos
        s_neg_arr[i] = s_neg
        if s_pos > threshold or s_neg < -threshold:
            events.append(bars.index[i])
            s_pos = 0.0
            s_neg = 0.0
    print(f"  CUSUM filter (thr={threshold}): {len(events)} events / {len(bars)} bars ({len(events)/len(bars):.1%})")
    return events


def compute_bar_features(bars):
    """Features from dollar bar OHLCV + noise level."""
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
    # Zaj szint (ATR/Price)
    atr = (h - l).rolling(14).mean()
    f['atr_pct'] = atr / c
    f['noise_class'] = pd.cut(f['atr_pct'], bins=[0, 0.001, 0.002, 0.005, 1.0],
                              labels=[0, 1, 2, 3]).astype(float)

    # === DIRECTION FEATURES (6) — trend direction carrying ===
    # 1. DF_Curve: CUSUM net value (continuous, not binary)
    vol_ewm = lr.ewm(span=20).std()
    s_pos, s_neg = 0.0, 0.0
    df_curve = np.zeros(len(c))
    for i in range(1, len(c)):
        thr = vol_ewm.iloc[i] if not np.isnan(vol_ewm.iloc[i]) else 0.001
        s_pos = max(0, s_pos + lr.iloc[i] - thr)
        s_neg = min(0, s_neg + lr.iloc[i] + thr)
        df_curve[i] = s_pos + s_neg  # NET CUSUM = continuous direction
    f['df_curve'] = df_curve

    # 2. Flow_Delta: volume × (close_position - 0.5) × 2
    close_pos = (c - l) / (h - l + 1e-10)
    f['flow_delta'] = v * (close_pos - 0.5) * 2

    # 3. Price-Volume Correlation: rolling corr(return, volume)
    f['pv_corr'] = lr.rolling(20).corr(v)

    # 4. Momentum Persistence: fraction of positive returns
    f['mom_persistence'] = (lr > 0).rolling(20).mean()

    # 5. Vol-Adjusted Momentum: momentum / vol
    f['vol_adj_mom'] = c.pct_change(10) / (vol_ewm + 1e-10)

    # 6. Variance Ratio 1:4: trending vs mean-reversion
    var_1 = lr.rolling(20).var()
    var_4 = c.pct_change(4).rolling(20).var()
    f['variance_ratio'] = var_4 / (4 * var_1 + 1e-10)

    # === ICT FEATURES (8) — structural S/R ===
    # FVG: Fair Value Gap
    fvg_bull = (l > h.shift(1)).astype(int)
    fvg_bear = (h < l.shift(1)).astype(int)
    fvg_size = np.where(fvg_bull == 1, (l - h.shift(1)) / (atr + 1e-10),
                        np.where(fvg_bear == 1, (l.shift(1) - h) / (atr + 1e-10), 0))
    f['fvg_signal'] = fvg_bull - fvg_bear  # +1=bullish FVG, -1=bearish FVG
    f['fvg_size'] = fvg_size

    # Order Block: bearish→bullish or bullish→bearish transition
    # Continuous: net OB strength (bull - bear) weighted by body size
    prev_bear = (c.shift(1) < o.shift(1))
    curr_bull = (c > o)
    prev_bull = (c.shift(1) > o.shift(1))
    curr_bear = (c < o)
    body_size = np.abs(c - o)
    ob_bull_strength = np.where(prev_bear & curr_bull, body_size / (atr + 1e-10), 0)
    ob_bear_strength = np.where(prev_bull & curr_bear, body_size / (atr + 1e-10), 0)
    f['ob_signal'] = ob_bull_strength - ob_bear_strength  # continuous OB direction

    # Liquidity Sweep: rolling count of recent sweeps (continuous, not binary)
    sw_hi = (h > h.shift(1)) & (h > h.shift(-1))
    sw_lo = (l < l.shift(1)) & (l < l.shift(-1))
    sweep_hi = (h.shift(1) > h.shift(2)) & (c < h.shift(1)) & sw_hi.shift(1)
    sweep_lo = (l.shift(1) < l.shift(2)) & (c > l.shift(1)) & sw_lo.shift(1)
    # Rolling sum over last 5 bars → frequency
    f['liq_sweep_net'] = (sweep_lo.astype(int) - sweep_hi.astype(int)).rolling(5).sum()

    # === TIME FEATURE (1) — ciklikus óra, ennyi elég ===
    hours = bars.index.hour
    f['hour_sin'] = np.sin(2 * np.pi * hours / 24)

    # HTF Trend Filter: HÁROM EMA (10 micro + 50 fast + 100 slow) + SLOPE-ok
    atr_proxy = lr.rolling(20).std() * c
    htf_ema_micro = c.ewm(span=10).mean()
    htf_ema_fast = c.ewm(span=50).mean()
    htf_ema_slow = c.ewm(span=100).mean()
    # Ár-EMA távolság (normalized)
    f['htf_trend_micro'] = ((c - htf_ema_micro) / (atr_proxy + 1e-10)).fillna(0)
    f['htf_trend_fast'] = ((c - htf_ema_fast) / (atr_proxy + 1e-10)).fillna(0)
    f['htf_trend_slow'] = ((c - htf_ema_slow) / (atr_proxy + 1e-10)).fillna(0)
    # EMA SLOPE — a kulcs feature: ha EMA még esik, NEM fordulat!
    # Normalizálva: slope / ATR → ha < -1 = erősen esik, > +1 = erősen emelkedik
    ema_micro_slope = htf_ema_micro.diff(5) / (atr + 1e-10)
    ema_fast_slope = htf_ema_fast.diff(10) / (atr + 1e-10)
    f['ema_micro_slope'] = ema_micro_slope.fillna(0)
    f['ema_fast_slope'] = ema_fast_slope.fillna(0)
    # Konfluencia: 40% micro + 40% fast + 20% slow
    # Ha micro és fast ellentmond: micro slope dönti el
    f['htf_trend'] = (0.4 * f['htf_trend_micro'] + 0.4 * f['htf_trend_fast'] + 0.2 * f['htf_trend_slow']).fillna(0)

    # === VOLUME PROFILE FEATURES (2) — POC magnetic level ===
    # Simplified POC: rolling volume-weighted price
    vp_price = (c * v).rolling(150).sum() / (v.rolling(150).sum() + 1e-10)
    f['poc_dist'] = (c - vp_price) / (atr + 1e-10)  # continuous distance to POC in ATR

    return f.dropna()


LGBM_PARAMS = {
    'objective': 'binary', 'metric': 'auc', 'boosting_type': 'gbdt',
    'num_leaves': 31, 'learning_rate': 0.03,
    'feature_fraction': 0.8, 'bagging_fraction': 0.85,
    'bagging_freq': 5, 'min_data_in_leaf': 100,
    'verbose': -1, 'n_jobs': -1,
    'reg_alpha': 0.1, 'reg_lambda': 0.5,
    'is_unbalance': True,
}

# Walk-forward: 5 expandáló ablak
WF_N_SPLITS = 5
WF_TEST_FRAC = 0.12  # 12% test ablak


def walk_forward_splits(n_samples, n_splits=WF_N_SPLITS, test_frac=WF_TEST_FRAC):
    """Idő-alapú walk-forward split: train növekszik, test mindig utána."""
    splits = []
    test_size = int(n_samples * test_frac)
    # Az első test a test_size-tól kezdődik, az utolsó a végén
    for i in range(n_splits):
        test_end = n_samples - (n_splits - 1 - i) * (test_size // n_splits)
        test_start = test_end - test_size
        if test_start < 100: continue
        train_idx = np.arange(0, test_start)
        test_idx = np.arange(test_start, test_end)
        splits.append((train_idx, test_idx))
    return splits


def train_single_model(X, y, name='Model', params=None, use_wf=True):
    """Train 1 binary LGBM model. use_wf=True → walk-forward, False → KFold."""
    if params is None:
        params = LGBM_PARAMS.copy()
    oos = pd.Series(0.0, index=X.index)
    models, imps = [], []

    if use_wf:
        splits = walk_forward_splits(len(X))
        if len(splits) < 2:
            print(f"    ⚠️  WF csak {len(splits)} split → fallback KFold(5)")
            splits = list(KFold(n_splits=5, shuffle=False).split(X))
            cv_name = "KFold(5)"
        else:
            cv_name = f"WF({len(splits)})"
    else:
        splits = list(KFold(n_splits=5, shuffle=False).split(X))
        cv_name = "KFold(5)"

    for fi_, (tri, tei) in enumerate(splits):
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
    for thr in np.arange(0.20, 0.70, 0.02):
        f1s = f1_score(y[valid], (oos[valid] > thr).astype(int))
        if f1s > best_f1: best_thr, best_f1 = thr, f1s
    print(f"    {name} [{cv_name}]: AUC={auc:.4f}, F1={best_f1:.3f}, thr={best_thr:.2f}, pos={y.sum()} ({y.mean():.1%})")
    return {'models': models, 'auc': auc, 'pred': oos, 'fi': fi, 'thr': best_thr, 'f1': best_f1}


# Direction feature-k: MINDIG bent kell maradniuk (force-keep)
DIRECTION_FEATURES = [
    'df_curve', 'vol_adj_mom', 'mom_persistence', 'flow_delta',
    'ema_micro_slope', 'ema_fast_slope',
    'htf_trend_micro', 'htf_trend_fast', 'htf_trend_slow', 'htf_trend',
    'variance_ratio', 'pv_corr',
]


def feature_selection(feat, y_long, y_short, min_pct=0.3):
    """Feature selection: baseline importance + force-keep direction feature-k."""
    print("  Feature selection (baseline + force-keep direction)...")
    # Gyors baseline: kevesebb round, egyszerűbb
    quick_params = LGBM_PARAMS.copy()
    quick_params['num_boost_round'] = 100
    # Long baseline
    kf = KFold(n_splits=3, shuffle=False)
    imps_l = []
    for tri, tei in kf.split(feat):
        dt = lgb.Dataset(feat.iloc[tri], label=y_long.iloc[tri])
        dv = lgb.Dataset(feat.iloc[tei], label=y_long.iloc[tei])
        m = lgb.train(quick_params, dt, num_boost_round=100, valid_sets=[dv],
                     callbacks=[lgb.early_stopping(20), lgb.log_evaluation(0)])
        imps_l.append(pd.Series(m.feature_importance('gain'), index=feat.columns))
    fi_l = pd.concat(imps_l, axis=1).mean(axis=1)
    # Short baseline
    imps_s = []
    for tri, tei in kf.split(feat):
        dt = lgb.Dataset(feat.iloc[tri], label=y_short.iloc[tri])
        dv = lgb.Dataset(feat.iloc[tei], label=y_short.iloc[tei])
        m = lgb.train(quick_params, dt, num_boost_round=100, valid_sets=[dv],
                     callbacks=[lgb.early_stopping(20), lgb.log_evaluation(0)])
        imps_s.append(pd.Series(m.feature_importance('gain'), index=feat.columns))
    fi_s = pd.concat(imps_s, axis=1).mean(axis=1)
    # Egyesített importance: mindkét irány maximuma
    fi_max = pd.concat([fi_l, fi_s], axis=1).max(axis=1)
    total = fi_max.sum()
    pct = (fi_max / total * 100).sort_values(ascending=False)
    keep = pct[pct >= min_pct].index.tolist()
    # Force-keep direction feature-k (ha léteznek a feat-ban)
    forced = [f for f in DIRECTION_FEATURES if f in feat.columns and f not in keep]
    keep.extend(forced)
    dropped = [f for f in feat.columns if f not in keep]
    forced_str = f" (+{len(forced)} forced)" if forced else ""
    print(f"    {len(feat.columns)} → {len(keep)} features{forced_str} (dropped {len(dropped)}: {', '.join(dropped[:8])}{'...' if len(dropped)>8 else ''})")
    return keep


def compute_adaptive_threshold(base_thr, noise_level, noise_weight=NOISE_WEIGHT):
    """Adaptív küszöb: zajosabb piacon magasabb küszöb."""
    return base_thr * (1 + noise_level * noise_weight)


def compute_noise_level(bars):
    """Zaj szint = realized volatility = rolling std of log returns."""
    lr = np.log(bars['close'] / bars['close'].shift(1))
    # 60-bar rolling realized vol (≈ 1 óra dollár bar-okban)
    rv = lr.rolling(60).std() * np.sqrt(60)  # annualizált ≈ hourly vol
    # Ha túl kicsi (dollar bar), használj fallback ATR/Close
    atr_pct = ((bars['high'] - bars['low']).rolling(14).mean() / bars['close']).fillna(0.003)
    # Vegyük a nagyobbat — a realized vol tipikusan nagyobb
    noise = pd.concat([rv, atr_pct], axis=1).max(axis=1)
    # Fill NaN
    noise = noise.fillna(0.003)
    # Cap: max 0.02 (2% — extrém volatilitás)
    noise = noise.clip(upper=0.02)
    return noise


def run_copilot_pipeline(instrument='BTCUSD', use_full=False, tp_dollar=TP_DOLLAR,
                         profit_mult=1.5, stop_mult=1.0, use_cusum=True):
    """Fő pipeline: TBM címkézés + CUSUM sampling + WF CV + force-keep direction features."""
    print(f"\n{'='*70}")
    print(f"SCALPER COPILOT v4.0 — Triple Barrier Pipeline")
    print(f"  Instrument: {instrument}")
    print(f"  Horizons: {', '.join(f'{h}s ({h//60}min)' for h in HORIZONS)}")
    print(f"  TBM: PT={profit_mult}×ATR, SL={stop_mult}×ATR  CUSUM={'ON' if use_cusum else 'OFF'}")
    print(f"  Dollar bar = ${DOLLAR_THRESHOLD/1e6:.1f}M")
    print(f"{'='*70}")

    df = load_tick_data(instrument, use_full=use_full)
    print("\nDollar bars...")
    bars = build_dollar_bars(df, threshold=DOLLAR_THRESHOLD)

    print("\nFeatures...")
    feat = compute_bar_features(bars)
    feat = feat.select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan).dropna()
    print(f"  {len(feat)} bars, {len(feat.columns)} features")

    # CUSUM event sampling — threshold dinamikus: ATR mean
    if use_cusum:
        cusum_threshold = float(((bars['high'] - bars['low']) / bars['close']).rolling(20).mean().mean())
        print(f"  CUSUM threshold (ATR mean): {cusum_threshold:.5f}")
        cusum_events = cusum_filter_events(bars, threshold=cusum_threshold)
        cusum_idx = bars.index.isin(cusum_events)
        cusum_mask = pd.Series(cusum_idx, index=bars.index).loc[feat.index]
        print(f"  CUSUM bars in feat: {cusum_mask.sum()} / {len(feat)} ({cusum_mask.mean():.1%})")
    else:
        cusum_mask = pd.Series(True, index=feat.index)

    noise = compute_noise_level(bars).loc[feat.index]
    print(f"  Noise: mean={noise.mean():.4f}, std={noise.std():.4f}")

    all_results = {}
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')

    for horizon_sec in HORIZONS:
        hname = HORIZON_NAMES[str(horizon_sec)]
        print(f"\n{'─'*50}\nHORIZONT: {hname} ({horizon_sec}s)\n{'─'*50}")

        # Triple Barrier címkézés (ATR-alapú, aszimmetrikus)
        long_lbl, short_lbl = label_triple_barrier(
            bars, horizon_sec=horizon_sec, profit_mult=profit_mult, stop_mult=stop_mult)
        y_long = pd.Series(long_lbl, index=bars.index).loc[feat.index]
        y_short = pd.Series(short_lbl, index=bars.index).loc[feat.index]

        # CUSUM sampling: csak event bar-okon tanítunk
        if use_cusum:
            y_long = y_long[cusum_mask]
            y_short = y_short[cusum_mask]
            feat_cusum = feat.loc[cusum_mask]
            print(f"  CUSUM training set: {len(feat_cusum)} bars")
        else:
            feat_cusum = feat

        # Feature selection ezen a horizonon (force-keep direction)
        keep_feats = feature_selection(feat_cusum, y_long, y_short, min_pct=0.3)
        feat_sel = feat_cusum[keep_feats]

        print(f"  Training Long-{hname}...")
        lr = train_single_model(feat_sel, y_long, name=f'Long-{hname}', use_wf=True)
        print(f"  Training Short-{hname}...")
        sr = train_single_model(feat_sel, y_short, name=f'Short-{hname}', use_wf=True)

        lt_ad = compute_adaptive_threshold(lr['thr'], noise.mean())
        st_ad = compute_adaptive_threshold(sr['thr'], noise.mean())
        print(f"  Adaptive thr: L={lt_ad:.3f}, S={st_ad:.3f}")

        lp = MODEL_DIR / f'{instrument}_v4_long_{hname}_{ts}.txt'
        sp = MODEL_DIR / f'{instrument}_v4_short_{hname}_{ts}.txt'
        lr['models'][-1].save_model(str(lp))
        sr['models'][-1].save_model(str(sp))
        lr['fi'].to_csv(MODEL_DIR / f'{instrument}_v4_long_{hname}_imp_{ts}.csv', header=['imp'])
        sr['fi'].to_csv(MODEL_DIR / f'{instrument}_v4_short_{hname}_imp_{ts}.csv', header=['imp'])

        all_results[hname] = {
            'long_auc': lr['auc'], 'short_auc': sr['auc'],
            'long_thr': lr['thr'], 'short_thr': sr['thr'],
            'long_thr_ad': lt_ad, 'short_thr_ad': st_ad,
            'long_pred': lr['pred'], 'short_pred': sr['pred'],
            'long_fi': lr['fi'], 'short_fi': sr['fi'],
            'long_models': lr['models'], 'short_models': sr['models'],
            'feat_names': keep_feats,
            'horizon_sec': horizon_sec,
            'long_path': str(lp), 'short_path': str(sp),
            'lbl_lr': float(y_long.mean()), 'lbl_sr': float(y_short.mean()),
        }
        print(f"  ✅ {hname}: L AUC={lr['auc']:.4f}, S AUC={sr['auc']:.4f}")
        print(f"     Top5 L: {', '.join(lr['fi'].head(5).index.tolist())}")
        print(f"     Top5 S: {', '.join(sr['fi'].head(5).index.tolist())}")

    # Predikciók CSV — Direction Bias: CUSUM+momentum+persistence
    preds = pd.DataFrame(index=feat.index)
    preds['price'] = bars['close'].loc[feat.index]
    preds['noise_level'] = noise
    for hname, r in all_results.items():
        # FULL inference: CUSUM-trained model predikál a TELJES feature-ökön
        keep_feats = r.get('feat_names', feat.columns.tolist())
        feat_full = feat[keep_feats]
        # Ensemble prediction (összes fold model átlaga)
        pL_raw = np.zeros(len(feat_full))
        pS_raw = np.zeros(len(feat_full))
        for m_l, m_s in zip(r['long_models'], r['short_models']):
            pL_raw += m_l.predict(feat_full) / len(r['long_models'])
            pS_raw += m_s.predict(feat_full) / len(r['short_models'])
        # DIRECTION BIAS: CUSUM + vol_adj_mom + persistence → session-gated!
        # df_curve: CUSUM — auto-reset, early detection, nem EMA lag
        # vol_adj_mom: momentum/vol — sebesség normalizálva
        # mom_persistence: trend tartósság (0.5=random, >0.6=trending)
        # Ha CUSUM mond irányt + momentum erősíti + tartós → bias
        # FINOM SZABÁLYOZÁS: max 10% shift (volt 25%), session-gated
        if 'df_curve' in feat.columns and 'vol_adj_mom' in feat.columns:
            df_c = feat['df_curve'].loc[feat.index]
            vam = feat['vol_adj_mom'].loc[feat.index]
            mp = feat['mom_persistence'].loc[feat.index] if 'mom_persistence' in feat.columns else pd.Series(0.5, index=feat.index)
            # Normalizáljuk a CUSUM-ot (z-score a rolling ablakban)
            dc_std = df_c.rolling(60).std().replace(0, 1e-6)
            dc_z = (df_c / dc_std).clip(-3, 3)
            # vol_adj_mom z-score
            vam_std = vam.rolling(60).std().replace(0, 1e-6)
            vam_z = (vam / vam_std).clip(-3, 3)
            # persistence: >0.55 = trending, <0.45 = choppy
            # Ha trending → nagy bias; ha choppy → kicsi bias
            trend_strength = ((mp - 0.5) * 4).clip(0, 1)  # 0=choppy, 1=strong trend
            # Kombinált direction signal: CUSUM (50%) + momentum (30%) + persistence gate
            direction = (dc_z * 0.5 + vam_z * 0.3) * (0.3 + 0.7 * trend_strength)
            # EMA SLOPE GATE: ha EMA még esik, NEM fordulat — csökkentjük a long bias-t!
            # EMA micro slope: ha < -0.5, az EMA még esik → crash/ongoing bear
            # EMA fast slope: ha < -0.3, a közép távú trend is esik
            if 'ema_micro_slope' in feat.columns and 'ema_fast_slope' in feat.columns:
                ems = feat['ema_micro_slope'].loc[feat.index]
                efs = feat['ema_fast_slope'].loc[feat.index]
                # Ha direction pozitív (bull bias) DE EMA slope negatív (EMA esik) → gate le!
                # "Ar > EMA de EMA esik" = hamis fordulat, csak slowdown
                ema_gate = np.ones(len(direction))
                # Ha direction > 0 (long bias) de micro slope < -0.5: gate = 0.2
                ema_gate = np.where((direction.values > 0) & (ems.values < -0.5), 0.2, ema_gate)
                # Ha direction > 0 (long bias) de fast slope < -0.3: gate = 0.4
                ema_gate = np.where((direction.values > 0) & (efs.values < -0.3), 0.4, ema_gate)
                # Ha direction < 0 (short bias) de micro slope > +0.5: hamis bear fordulat
                ema_gate = np.where((direction.values < 0) & (ems.values > 0.5), 0.3, ema_gate)
                ema_gate = np.where((direction.values < 0) & (efs.values > 0.3), 0.5, ema_gate)
            else:
                ema_gate = np.ones(len(direction))
            # Bias: csak EMA slope gate, NINCS session gate
            bias = np.clip(direction.values * 0.06 * ema_gate, -0.10, 0.10)
            pL_adj = np.clip(pL_raw + bias, 0, 1)
            pS_adj = np.clip(pS_raw - bias, 0, 1)
            preds[f'p_long_{hname}'] = pL_adj
            preds[f'p_short_{hname}'] = pS_adj
        elif 'df_curve' in feat.columns:
            df_c = feat['df_curve'].loc[feat.index]
            dc_std = df_c.rolling(60).std().replace(0, 1e-6)
            # Fallback bias: csak CUSUM direction, NINCS session gate
            bias = np.clip((df_c / dc_std).clip(-3, 3).values * 0.05, -0.10, 0.10)
            pL_adj = np.clip(pL_raw + bias, 0, 1)
            pS_adj = np.clip(pS_raw - bias, 0, 1)
            preds[f'p_long_{hname}'] = pL_adj
            preds[f'p_short_{hname}'] = pS_adj
        else:
            preds[f'p_long_{hname}'] = pL_raw
            preds[f'p_short_{hname}'] = pS_raw
        preds[f'long_thr_{hname}'] = compute_adaptive_threshold(r['long_thr'], noise)
        preds[f'short_thr_{hname}'] = compute_adaptive_threshold(r['short_thr'], noise)
        preds[f'signal_{hname}'] = 0
        lsig = (preds[f'p_long_{hname}'] > preds[f'long_thr_{hname}']) & (preds[f'p_long_{hname}'] > preds[f'p_short_{hname}'])
        ssig = (preds[f'p_short_{hname}'] > preds[f'short_thr_{hname}']) & (preds[f'p_short_{hname}'] > preds[f'p_long_{hname}'])
        preds.loc[lsig, f'signal_{hname}'] = 1
        preds.loc[ssig, f'signal_{hname}'] = -1
    pp = MODEL_DIR / f'{instrument}_v4_preds_{ts}.csv'
    preds.to_csv(pp)

    # Meta JSON
    meta = {
        'version': 'scalper_copilot_v4.0_TBM', 'instrument': instrument, 'timestamp': ts,
        'tp_dollar': tp_dollar, 'dollar_threshold': DOLLAR_THRESHOLD,
        'profit_mult': profit_mult, 'stop_mult': stop_mult,
        'use_cusum': use_cusum,
        'horizons': {hname: {
            'sec': r['horizon_sec'], 'long_auc': r['long_auc'], 'short_auc': r['short_auc'],
            'long_thr': r['long_thr'], 'short_thr': r['short_thr'],
            'long_thr_ad': r['long_thr_ad'], 'short_thr_ad': r['short_thr_ad'],
            'long_path': r['long_path'], 'short_path': r['short_path'],
            'lbl_lr': r['lbl_lr'], 'lbl_sr': r['lbl_sr'],
        } for hname, r in all_results.items()},
        'n_bars': len(bars), 'n_samples': len(feat), 'n_features': len(feat_sel.columns),
        'feature_names': list(feat_sel.columns),
        'noise_mean': float(noise.mean()), 'noise_std': float(noise.std()),
        'noise_weight': NOISE_WEIGHT, 'preds_path': str(pp),
    }
    mp = MODEL_DIR / f'{instrument}_v4_meta_{ts}.json'
    with open(mp, 'w') as f: json.dump(meta, f, indent=2)

    print(f"\n{'='*70}")
    print(f"SCALPER COPILOT v4.0 — KÉSZ ✅")
    for hname, r in all_results.items():
        print(f"  {hname}: L AUC={r['long_auc']:.4f} (thr={r['long_thr_ad']:.3f}), "
              f"S AUC={r['short_auc']:.4f} (thr={r['short_thr_ad']:.3f})")
    print(f"  Noise: mean={noise.mean():.4f} | Meta: {mp}")
    print(f"{'='*70}")
    return meta, all_results, preds


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Scalper Copilot v4.0 — Triple Barrier Pipeline')
    p.add_argument('--instrument', default='BTCUSD')
    p.add_argument('--tp', type=int, default=50, help='TP in dollars (legacy)')
    p.add_argument('--full', action='store_true', help='Use full dataset')
    p.add_argument('--profit-mult', type=float, default=1.5, help='TBM profit multiplier (×ATR)')
    p.add_argument('--stop-mult', type=float, default=1.0, help='TBM stop multiplier (×ATR)')
    p.add_argument('--no-cusum', action='store_true', help='Disable CUSUM event sampling')
    a = p.parse_args()
    run_copilot_pipeline(a.instrument, a.full, a.tp,
                         profit_mult=a.profit_mult, stop_mult=a.stop_mult,
                         use_cusum=not a.no_cusum)