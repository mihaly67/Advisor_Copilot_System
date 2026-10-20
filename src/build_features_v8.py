#!/usr/bin/env python3
"""
build_features_v8.py - Scalper Copilot v8 Feature Engineering
46 feature / 5 csoport: IRANY(12) + HOLVAN(15) + ERO(8) + VOL(7) + IDO(4)

Logikai alap: LGBM 5 kerdesre valaszol:
  1. IRANY - Merre megy? (CUSUM + flow + zero-lag + momentum)
  2. HOLVAN - Hol a strukturaban? (pivot dist/break + ICT)
  3. ERO - Milyen eros? (trend + flow + aggression)
  4. VOL - Milyen kornyezet? (rv + atr + hurst + VR)
  5. IDO - Mikor? (session + kill zone)
"""
import numpy as np
import pandas as pd
import math


# ======================================================================
# ZERO-LAG MA IMPLEMENTACIOK (MetaQuotes -> Python port)
# ======================================================================

def absolutely_no_lag_lwma(series, length=11):
    """Zero-lag least weighted moving average. lag ~ 0 bars."""
    n = len(series)
    result = np.full(n, np.nan)
    values = series.values
    weights = np.array([length - k for k in range(length)], dtype=float)
    for i in range(length - 1, n):
        wsum = 0.0; norm = 0.0
        for k in range(length):
            idx = i - k
            if idx < 0: break
            wsum += values[idx] * weights[k]
            norm += weights[k]
        if norm > 0:
            result[i] = wsum / norm
    return pd.Series(result, index=series.index)


def kama(series, period=10, fast_sc=2, slow_sc=30):
    """Kaufman Adaptive Moving Average. Fast in trends, slow in ranges."""
    n = len(series)
    result = np.full(n, np.nan)
    values = series.values
    fsc = 2.0 / (fast_sc + 1)
    ssc = 2.0 / (slow_sc + 1)
    result[period - 1] = values[period - 1]
    for i in range(period, n):
        direction = abs(values[i] - values[i - period])
        volatility = sum(abs(values[i - k + 1] - values[i - k]) for k in range(1, period + 1))
        er = direction / volatility if volatility > 0 else 0.0
        sc = (er * (fsc - ssc) + ssc) ** 2
        result[i] = result[i - 1] + sc * (values[i] - result[i - 1])
    return pd.Series(result, index=series.index)


def hull_ma(series, period=10):
    """Hull Moving Average. HMA = WMA(2*WMA(n/2) - WMA(n), sqrt(n))"""
    def wma(s, p):
        n = len(s); res = np.full(n, np.nan); v = s.values
        w = np.arange(1, p + 1, dtype=float); ws = w.sum()
        for i in range(p - 1, n):
            res[i] = (v[i - p + 1:i + 1] * w).sum() / ws
        return pd.Series(res, index=s.index)
    half_n = max(1, period // 2)
    sqrt_n = max(1, int(math.sqrt(period)))
    return wma(2 * wma(series, half_n) - wma(series, period), sqrt_n)


def laguerre_rsi(series, gamma=0.8):
    """Laguerre RSI. Output 0-1 (0.5=neutral, >0.5=bull, <0.5=bear)"""
    n = len(series); result = np.full(n, np.nan); v = series.values
    l0 = l1 = l2 = l3 = 0.0
    for i in range(1, n):
        l0p, l1p, l2p, l3p = l0, l1, l2, l3
        l0 = gamma * l0p + (1 - gamma) * v[i]
        l1 = -gamma * l0 + l0p + gamma * l1p
        l2 = -gamma * l1 + l1p + gamma * l2p
        l3 = -gamma * l2 + l2p + gamma * l3p
        cu = max(l0 - l1, 0) + max(l1 - l2, 0) + max(l2 - l3, 0)
        cd = max(l1 - l0, 0) + max(l2 - l1, 0) + max(l3 - l2, 0)
        result[i] = cu / (cu + cd) if cu + cd > 0 else 0.5
    return pd.Series(result, index=series.index)


# ======================================================================
# PRUNED V8 FEATURE LIST (28 features after SHAP + correlation pruning)
# ======================================================================

FEATURES_V8_PRUNED = [
    # IRANY (13) - Direction
    'df_curve_cont',        # CUSUM continuous (2.0% SHAP)
    'flow_delta',           # Volume flow proxy (2.8%)
    'mfi_14',               # Money Flow Index (3.1%)
    'auto_corr_20',         # Autocorrelation 20-bar (2.7%) — replaces pv_corr_20
    'laguerre_rsi_dir',     # Zero-lag RSI direction (5.8%) - BEST NEW!
    'hull_slope_10',        # Hull MA slope (2.4%)
    'cmo_14',               # Chande Momentum Oscillator (2.5%)
    'vol_adj_mom_10',       # Risk-adjusted momentum (1.8%)
    'mom_persist_20',       # Momentum persistence (2.9%)
    'ret_1',                # 1-bar return (1.9%)
    'ret_3',                # 3-bar return (2.1%)
    'ret_20',               # 20-bar return (10.2%)
    'dir_x_mom',            # Sign(ret) x volatility (2.5%)
    # ERO (5) - Strength
    'delta_force_14',       # Delta Force accumulated (3.5%)
    'vroc_14',              # Volume rate of change (1.2%)
    'obv_slope_14',         # OBV slope (4.2%)
    'vol_ma_20',            # Volume MA 20 (13.7%) - TOP FEATURE
    'trend_str_33',         # Trend strength (1.6%)
    # VOL (5) - Regime
    'atr_pct',              # ATR / close (1.9%)
    'rv_10',                # Rolling vol 10 (2.3%)
    'rv_60',                # Rolling vol 60 (3.2%)
    'variance_ratio_1_4',   # Variance ratio (2.0%)
    'ema_dist_20',          # EMA distance (2.3%)
    # EMA (2) - Trend proxies
    'price_accel',          # Price acceleration (2.2%)
    'ema_d_5',              # EMA slope 5 (1.7%)
    # IDO (3) - Time
    'hour_sin',             # Hour cyclic (3.2%)
    'hour_cos',             # Hour cyclic (2.3%)
    'kill_zone',            # London/NY overlap (0.6%)
]

# DROPPED from 42 -> 28:
# hurst_proxy (redundant with variance_ratio_1_4, corr=0.956)
# micro_trend (redundant with hull_slope_10, corr=0.929)
# ema_d_5 kept over ret_3/ret_5 (they're redundant, keep ema as it's more general)
# ema_d_60 dropped (redundant with ret_20, corr=0.890) -> BUT ret_20 is more useful
# nolag_slope (redundant with ema_dist_20, corr=0.858)
# boll_width (redundant with trend_str_33, corr=0.850)
# poc_dist (redundant with ema_dist_20, corr=0.974)
# vol_ma_5 (SHAP < 0.5%)
# df_curve (SHAP = 0% - binary CUSUM useless, continuous version kept)
# kama_dir (SHAP = 0% - too slow crossover)
# ob_bull_active (SHAP = 0% - too rare events)
# fvg_net (SHAP = 0% - too rare events)
# session_vol_rank (SHAP = 0% - constant vol issue)
# ret_x_atr dropped as borderline (0.9% SHAP, but keep ret_20 which captures same info)




# ═══════════════════════════════════════════════════════════════════════
# MAIN FEATURE BUILDER
# ═══════════════════════════════════════════════════════════════════════

def build_features_v8(bars, pivot_data=None):
    """
    Scalper Copilot v8 Feature Engineering - 46 feature / 5 csoport.
    Args:
        bars: DataFrame with [open, high, low, close, dollar, vol, n, atr, ret]
        pivot_data: dict with pivot levels (Micro_R, Micro_S, Sec_R, Sec_S, Ter_R, Ter_S)
    Returns:
        (df_clean, feat_cols) - clean feature DataFrame and column list
    """
    print(f"\n  Features v8 ({len(bars):,} bars)...")
    df = bars.copy()
    c = df['close']; o = df['open']; h = df['high']; l = df['low']
    # Use tick count 'n' as volume proxy (vol is constant in dollar bars)
    v = df.get('n', df.get('vol', pd.Series(1, index=df.index))).astype(float)
    atr = df['atr']
    returns = c.pct_change()
    
    feat = pd.DataFrame(index=df.index)
    
    # ═══════════════════════════════════════════════════════════════════
    # CSOPORT 1: IRÁNY (Direction) - 12 feature
    # "Merre megy az ár?"
    # ═══════════════════════════════════════════════════════════════════
    
    # --- 1A. CUSUM direction (2) ⭐⭐⭐
    vol_ewm = returns.ewm(span=20).std()
    s_pos = 0.0; s_neg = 0.0
    df_curve = np.zeros(len(df)); df_curve_cont = np.zeros(len(df))
    for i in range(1, len(df)):
        thr = vol_ewm.iloc[i] if not np.isnan(vol_ewm.iloc[i]) else 0.001
        ret_i = returns.iloc[i]
        s_pos = max(0, s_pos + ret_i - thr)
        s_neg = min(0, s_neg + ret_i + thr)
        df_curve_cont[i] = s_pos + s_neg
        df_curve[i] = 1.0 if s_pos > -s_neg else -1.0
    feat['df_curve'] = df_curve
    feat['df_curve_cont'] = df_curve_cont
    
    # --- 1B. Flow direction (3) ⭐⭐
    close_position = (c - l) / (h - l + 1e-10)
    feat['flow_delta'] = v * (close_position - 0.5) * 2
    # MFI-14
    typical_price = (h + l + c) / 3
    money_flow = typical_price * v
    mf_pos = money_flow.where(typical_price > typical_price.shift(1), 0).rolling(14).sum()
    mf_neg = money_flow.where(typical_price < typical_price.shift(1), 0).rolling(14).sum()
    feat['mfi_14'] = 100 - 100 / (1 + mf_pos / (mf_neg + 1e-10))
    # Autocorrelation (replaces pv_corr_20 — n.diff() is near-constant in dollar bars,
    # causing 83.4% NaN. Autocorrelation captures momentum/mean-reversion regime.)
    feat['auto_corr_20'] = returns.rolling(20).corr(returns.shift(1))
    
    # --- 1C. Zero-lag trend direction (4) ⭐⭐
    nolag = absolutely_no_lag_lwma(c, length=11)
    feat['nolag_slope'] = nolag.diff() / atr.replace(0, np.nan)
    kama_fast = kama(c, period=10, fast_sc=2, slow_sc=30)
    kama_slow = kama(c, period=50, fast_sc=2, slow_sc=30)
    feat['kama_dir'] = np.sign(kama_fast - kama_slow)
    lag_rsi = laguerre_rsi(c, gamma=0.8)
    feat['laguerre_rsi_dir'] = lag_rsi * 2 - 1  # scale [-1, +1]
    hull10 = hull_ma(c, period=10)
    feat['hull_slope_10'] = hull10.diff() / atr.replace(0, np.nan)
    
    # --- 1D. Momentum direction (3) ⭐
    up_sum = returns.where(returns > 0, 0).rolling(14).sum()
    dn_sum = (-returns.where(returns < 0, 0)).rolling(14).sum()
    feat['cmo_14'] = 100 * (up_sum - dn_sum) / (up_sum + dn_sum + 1e-10)
    feat['vol_adj_mom_10'] = c.pct_change(10) / (vol_ewm + 1e-10)
    feat['mom_persist_20'] = (np.sign(returns) == np.sign(returns.shift(1))).astype(float).rolling(20).mean()
    
    # --- IRANY: proven micro returns (keep from v6)
    feat['ret_1'] = returns
    feat['ret_3'] = c.pct_change(3)
    feat['ret_5'] = c.pct_change(5)
    feat['ret_20'] = c.pct_change(20)
    rv_10 = returns.rolling(10).std()
    feat['dir_x_mom'] = np.sign(returns) * rv_10
    atr_pct = atr / c
    feat['ret_x_atr'] = returns * atr_pct
    feat['ema_d_5'] = c.ewm(span=5).mean().diff() / c
    feat['ema_d_60'] = c.ewm(span=60).mean().diff() / c
    feat['price_accel'] = returns.diff()
    # micro_trend: 5-bar regression slope
    def _slope(y):
        if len(y) < 5: return 0
        return np.polyfit(np.arange(5), y[-5:], 1)[0]
    feat['micro_trend'] = c.rolling(5).apply(_slope, raw=True) / atr.replace(0, np.nan)
    
    # ═══════════════════════════════════════════════════════════════════
    # CSOPORT 2: HOL VAN (Structure) - 15 feature
    # "Hol van az ár a struktúrában?"
    # ═══════════════════════════════════════════════════════════════════
    
    # --- 2A. Pivot távolság (6) - HA VAN pivot_data
    if pivot_data is not None:
        for lvl in ['Micro', 'Sec', 'Ter']:
            for side in ['R', 'S']:
                col = f'{lvl}_{side}'
                if col in pivot_data:
                    feat[f'{lvl.lower()}_dist_{side.lower()}'] = (c - pivot_data[col]) / atr.replace(0, np.nan)
        # --- 2B. Pivot breakout/bounce (6)
        for lvl in ['Micro', 'Sec']:
            for side in ['R', 'S']:
                col = f'{lvl}_{side}'
                if col in pivot_data:
                    if side == 'R':
                        feat[f'{lvl.lower()}_break_r'] = (c > pivot_data[col]).astype(float)
                    else:
                        feat[f'{lvl.lower()}_break_s'] = (c < pivot_data[col]).astype(float)
        # Wick rejection/bounce at Micro level
        if 'Micro_R' in pivot_data:
            feat['mic_wick_rej_r'] = ((h > pivot_data['Micro_R']) & (c < pivot_data['Micro_R'])).astype(float)
        if 'Micro_S' in pivot_data:
            feat['mic_wick_bnc_s'] = ((l < pivot_data['Micro_S']) & (c > pivot_data['Micro_S'])).astype(float)
        # Pivot velocity
        if 'Micro_R' in pivot_data:
            feat['pivot_vel_r'] = pivot_data['Micro_R'].diff() / atr.replace(0, np.nan)
        if 'Micro_S' in pivot_data:
            feat['pivot_vel_s'] = pivot_data['Micro_S'].diff() / atr.replace(0, np.nan)
    
    # --- 2C. ICT Structure (3) ⭐
    # FVG detection (Fair Value Gap)
    fvg_bull = (l > h.shift(1)).astype(float)
    fvg_bear = (h < l.shift(1)).astype(float)
    fvg_size = np.where(fvg_bull > 0, (l - h.shift(1)) / atr.replace(0, np.nan),
                        np.where(fvg_bear > 0, (l.shift(1) - h) / atr.replace(0, np.nan), 0))
    # Track active FVGs (not filled)
    fvg_bull_active = fvg_bull.copy()
    fvg_bear_active = fvg_bear.copy()
    for i in range(2, len(df)):
        if i >= 2 and fvg_bull.iloc[i-1] == 1 and c.iloc[i] < h.iloc[i-2]:
            fvg_bull_active.iloc[i-1] = 0  # filled
        if i >= 2 and fvg_bear.iloc[i-1] == 1 and c.iloc[i] > l.iloc[i-2]:
            fvg_bear_active.iloc[i-1] = 0
    feat['fvg_net'] = fvg_bull_active.rolling(10).sum() - fvg_bear_active.rolling(10).sum()
    
    # Order Block detection (bullish: bearish[i-1] then bullish[i])
    prev_bearish = (c.shift(1) < o.shift(1)).astype(float)
    curr_bullish = (c > o).astype(float)
    curr_body = (c - o).abs()
    feat['ob_bull_active'] = (prev_bearish * curr_bullish * (curr_body > atr * 1.0)).astype(float).rolling(5).max()
    
    # Volume Profile POC (fast numpy - rolling 20-bar VWAP proxy)
    n_bars_vp = 20
    # Fast POC approximation: volume-weighted rolling median
    # True POC is expensive O(n*lookback), use VWAP proxy instead
    close_v = c.values; vol_v = v.values
    vol_sum = pd.Series(vol_v).rolling(n_bars_vp).sum().values
    cv_sum = pd.Series(close_v * vol_v).rolling(n_bars_vp).sum().values
    vwap = np.where(vol_sum > 0, cv_sum / vol_sum, np.nan)
    feat['poc_dist'] = (c - pd.Series(vwap, index=df.index)) / atr.replace(0, np.nan)
    
    # ═══════════════════════════════════════════════════════════════════
    # CSOPORT 3: ERŐ (Strength) - 8 feature
    # "Milyen erős az irány?"
    # ═══════════════════════════════════════════════════════════════════
    
    # --- 3A. Trend strength (3)
    ret33 = c.pct_change(33)
    feat['trend_str_33'] = (ret33 * c / atr.replace(0, np.nan)).abs().fillna(0)
    # pivot_vel_r/s already added in 2B if pivot_data available
    
    # --- 3B. Flow strength (3)
    # Delta Force: volume x (2*close_position - 1) akkumulált 14 bar
    delta_force = v * (2 * close_position - 1)
    feat['delta_force_14'] = delta_force.rolling(14).sum()
    # VROC-14: Volume Rate of Change (or dollar change if vol constant)
    feat['vroc_14'] = v.pct_change(14) if v.std() > 0 else df.get('dollar', v).pct_change(14)
    # OBV slope
    obv_sign = np.sign(returns).fillna(0)
    obv = (v * obv_sign).cumsum()
    feat['obv_slope_14'] = obv.diff(14) / atr.replace(0, np.nan)
    
    # --- 3C. Volume context (keep from v6)
    feat['vol_ma_5'] = v.rolling(5).mean()
    feat['vol_ma_20'] = v.rolling(20).mean()
    
    # ═══════════════════════════════════════════════════════════════════
    # CSOPORT 4: VOLATILITÁS (Regime) - 7 feature
    # "Milyen a környezet?"
    # ═══════════════════════════════════════════════════════════════════
    
    feat['atr_pct'] = atr_pct
    feat['rv_10'] = rv_10
    feat['rv_60'] = returns.rolling(60).std()
    # Bollinger width
    sma20 = c.rolling(20).mean(); std20 = c.rolling(20).std()
    feat['boll_width'] = (2 * std20) / atr.replace(0, np.nan)
    # Variance ratio 1:4
    var_1 = returns.rolling(20).var()
    var_4 = c.pct_change(4).rolling(20).var()
    feat['variance_ratio_1_4'] = var_4 / (4 * var_1 + 1e-10)
    # Hurst proxy (cheap: via variance ratio)
    vr_hurst = feat['variance_ratio_1_4'].clip(0.25, 4)
    feat['hurst_proxy'] = (0.5 + 0.5 * np.log2(vr_hurst)).clip(0.1, 0.9).fillna(0.5)
    # EMA distance
    ema20 = c.ewm(span=20).mean()
    feat['ema_dist_20'] = (c - ema20) / atr.replace(0, np.nan)
    
    # ═══════════════════════════════════════════════════════════════════
    # CSOPORT 5: IDŐ (Time) - 4 feature
    # "Mikor vagyunk?"
    # ═══════════════════════════════════════════════════════════════════
    
    dt = df.index
    hour_sec = dt.hour * 3600 + dt.minute * 60 + dt.second
    feat['hour_sin'] = np.sin(2 * np.pi * hour_sec / 86400)
    feat['hour_cos'] = np.cos(2 * np.pi * hour_sec / 86400)
    # Kill zone: London (8-9 UTC) + NY overlap (12-16 UTC)
    hours = dt.hour
    feat['kill_zone'] = ((hours >= 12) & (hours < 16)).astype(float)
    # Session vol rank (handle constant vol)
    vol_proxy = v if v.std() > 0 else df.get('dollar', v)
    vol_by_hour = vol_proxy.groupby(hours).transform('median')
    feat['session_vol_rank'] = vol_by_hour.rank(pct=True)
    
    # ═══════════════════════════════════════════════════════════════════
    # CLEANUP: shift by 1 (leakage prevention), drop NaN/inf
    # ═══════════════════════════════════════════════════════════════════
    
    feat = feat.shift(1)  # prevent lookahead bias
    feat = feat.replace([np.inf, -np.inf], np.nan).dropna()
    
    feat_cols = list(feat.columns)
    n_feat = len(feat_cols)
    
    # Print group summary
    groups = {
        'IRÁNY': ['df_curve', 'df_curve_cont', 'flow_delta', 'mfi_14', 'auto_corr_20',
                   'nolag_slope', 'kama_dir', 'laguerre_rsi_dir', 'hull_slope_10',
                   'cmo_14', 'vol_adj_mom_10', 'mom_persist_20',
                   'ret_1', 'ret_3', 'ret_5', 'ret_20', 'dir_x_mom', 'ret_x_atr',
                   'ema_d_5', 'ema_d_60', 'price_accel', 'micro_trend'],
        'HOL VAN': [c for c in feat_cols if any(c.startswith(p) for p in ['mic_', 'sec_', 'ter_', 'fvg_', 'ob_', 'poc_'])],
        'ERŐ': ['trend_str_33', 'delta_force_14', 'vroc_14', 'obv_slope_14',
                 'vol_ma_5', 'vol_ma_20'] + [c for c in feat_cols if c.startswith('pivot_vel_')],
        'VOL': ['atr_pct', 'rv_10', 'rv_60', 'boll_width', 'variance_ratio_1_4', 'hurst_proxy', 'ema_dist_20'],
        'IDŐ': ['hour_sin', 'hour_cos', 'kill_zone', 'session_vol_rank'],
    }
    print(f"    {len(feat):,} bars, {n_feat} features")
    for grp, cols in groups.items():
        actual = [c for c in cols if c in feat_cols]
        print(f"      {grp}: {len(actual)} feat")
    
    return feat, feat_cols

