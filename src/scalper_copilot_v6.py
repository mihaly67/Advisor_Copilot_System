#!/usr/bin/env python3
"""
Scalper Copilot v6 — Iterative Pipeline
  - $0.5M dollar bars (9s/bar, ATR≈$17, 20s alatt 2.2 bár)
  - TBM labeling: PT=0.5×ATR, SL=0.3×ATR (reális 20s scalping)
  - 3 horizont: 20s, 1min, 2min
  - Zaj mint predikció (noise probability)
  - OOS exam auto-kiértékelés
  - Chart + HTML generálás
  
Iteráció 1: baseline $0.5M + PT=0.5×/SL=0.3×
"""
import os, sys, json, time, warnings
import numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime
warnings.filterwarnings('ignore')

# ─── KONFIG ───
INST = 'BTCUSD'
DATA_DIR = Path('/data/LGBM_copilot/data/raw/BTCUSD')
EXAM_DIR = Path('/data/LGBM_copilot/data/exam/BTCUSD')
MODEL_DIR = Path('/data/LGBM_copilot/models/scalper')
CHART_DIR = Path('/data/LGBM_copilot/charts')
MODEL_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)

# v6 konfig — $0.5M dollár bár
DOLLAR_THR = 500_000        # $0.5M — 9s/bar, ATR≈$17
HORIZON_SEC = [120, 180, 300]  # v6.2: 2min, 3min, 5min (rangsor alapján)
HORIZON_NAMES = {120:'2min', 180:'3min', 300:'5min'}
# HORIZON_SEC = [20, 60, 120, 180, 240, 300] # v6.1: full 6-horizon
PROFIT_MULT = 0.5           # PT = 0.5×ATR (reális 20s scalping)
STOP_MULT = 0.3             # SL = 0.3×ATR (tight stop)
CUSUM_THR = None             # auto
N_FOLD = 5
SEED = 42

# Színek
LC='#228B22'; SC='#B22222'; NC='#888888'; BC='#00d2ff'; CC='#FF6B35'
BG='rgb(17,17,17)'; GC='#283442'; TC='#f2f5fa'

print("="*72)
print(f"SCALPER COPILOT v6 — ${DOLLAR_THR/1e6:.1f}M bars | PT={PROFIT_MULT}×ATR SL={STOP_MULT}×ATR")
print("="*72)

# ─── 1. ADATBETÖLTÉS ───
def load_ticks(path, label='TRAIN'):
    print(f"\n  Loading {label}: {Path(path).name}...")
    df = pd.read_csv(path, parse_dates=['Timestamp'], index_col='Timestamp',
                     usecols=['Timestamp','Bid','Ask'])
    mid = ((df['Bid'] + df['Ask']) / 2).to_frame('price')
    print(f"    {len(mid):,} ticks, {mid.index[0]} → {mid.index[-1]}")
    return mid

# ─── 2. DOLLÁR BÁROK ───
def make_dollar_bars(ticks, dthr):
    print(f"\n  Dollar bars (${dthr/1e6:.1f}M)...")
    prices = ticks['price'].values
    ts = ticks.index.values
    cum = 0.0; bars = []
    o=prices[0]; h=o; l=o; vol=0; t0=ts[0]
    for i in range(len(prices)):
        p = prices[i]; cum += p; vol += 1/2  # est. volume
        if p>h: h=p
        if p<l: l=p
        if cum >= dthr:
            bars.append({'ts':t0, 'open':o, 'high':h, 'low':l, 'close':p,
                         'dollar':cum, 'vol':vol, 'n':i})
            cum=0; o=p; h=p; l=p; vol=0; t0=ts[i]
    df = pd.DataFrame(bars)
    df['ts'] = pd.to_datetime(df['ts'])
    df = df.set_index('ts')
    # ATR
    df['atr'] = df['high'] - df['low']
    df['atr_pct'] = df['atr'] / df['close']
    df['ret'] = df['close'].pct_change()
    print(f"    {len(df):,} bars, ATR: ${df['atr'].median():.1f} (med), bar_time: {df.index.to_series().diff().median().total_seconds():.1f}s")
    return df

# ─── 3. FEATURE-ÖK ───
def build_features(bars):
    print(f"\n  Features ({len(bars):,} bars)...")
    df = bars.copy()
    c = df['close']; o = df['open']; h = df['high']; l = df['low']
    
    # Returns
    for p in [1,3,5,10,20]:
        df[f'ret_{p}'] = c.pct_change(p)
    # Volatility
    for w in [10,20,60]:
        df[f'rv_{w}'] = df['ret'].rolling(w).std()
    df['variance_ratio'] = df['rv_10'] / df['rv_60'].replace(0, np.nan)
    # EMA slopes
    for span in [5,10,30,60]:
        ema = c.ewm(span=span).mean()
        df[f'ema_d_{span}'] = ema.diff() / c
        df[f'ema_s_{span}'] = (ema - ema.shift(span)) / c
    # ATR
    df['atr_pct'] = df['atr'] / c
    # Bar properties
    df['body'] = (c - o) / df['atr'].replace(0, np.nan)
    df['bar_range'] = (h - l) / df['atr'].replace(0, np.nan)
    df['upper_wick'] = (h - np.maximum(c,o)) / df['atr'].replace(0, np.nan)
    df['lower_wick'] = (np.minimum(c,o) - l) / df['atr'].replace(0, np.nan)
    # Volume
    df['vol_ma_5'] = df['vol'].rolling(5).mean()
    df['vol_ma_20'] = df['vol'].rolling(20).mean()
    df['vol_rel'] = df['vol'] / df['vol_ma_20'].replace(0, np.nan)
    # Time
    dt = df.index
    df['bar_dt'] = dt.hour * 3600 + dt.minute * 60 + dt.second
    df['bar_dt_rel'] = df['bar_dt'] / 86400
    df['hour_sin'] = np.sin(2 * np.pi * df['bar_dt'] / 86400)
    df['hour_cos'] = np.cos(2 * np.pi * df['bar_dt'] / 86400)
    # RSI
    delta = c.diff()
    gain = delta.where(delta>0, 0).rolling(14).mean()
    loss = (-delta.where(delta<0, 0)).rolling(14).mean()
    df['rsi_14'] = 100 - 100 / (1 + gain / loss.replace(0, np.nan))
    # Direction × momentum
    df['dir_x_mom'] = np.sign(df['ret_1']) * df['rv_10']
    # Momentum persistence
    df['mom_persistence'] = (np.sign(df['ret_1']) == np.sign(df['ret_1'].shift(1))).astype(float).rolling(5).mean()
    # ── v6.1 ÚJ feature-k ──
    # RSI 28
    gain28 = delta.where(delta>0,0).rolling(28).mean()
    loss28 = (-delta.where(delta<0,0)).rolling(28).mean()
    df['rsi_28'] = 100 - 100 / (1 + gain28 / loss28.replace(0, np.nan))
    # EMA fast/slow crossover
    ema5 = c.ewm(span=5).mean(); ema20 = c.ewm(span=20).mean()
    df['ema_cross'] = (ema5 - ema20) / df['atr'].replace(0, np.nan)
    # Bollinger width
    sma20 = c.rolling(20).mean(); std20 = c.rolling(20).std()
    df['boll_width'] = (2 * std20) / df['atr'].replace(0, np.nan)
    df['boll_pos'] = (c - sma20) / (2 * std20).replace(0, np.nan)
    # Volume imbalance (up vs down bars)
    up_vol = (df['vol'] * (c > o).astype(float)).rolling(20).sum()
    dn_vol = (df['vol'] * (c <= o).astype(float)).rolling(20).sum()
    df['vol_imbalance'] = (up_vol - dn_vol) / (up_vol + dn_vol).replace(0, np.nan)
    # Price acceleration (2nd derivative)
    df['price_accel'] = df['ret_1'].diff() 
    # Mean reversion signal
    df['mean_rev'] = -(c - sma20) / std20.replace(0, np.nan)
    # Micro trend (5-bar regression slope)
    from numpy.polynomial import polynomial as P
    def _slope(y):
        if len(y)<5: return 0
        x = np.arange(5)
        c_ = P.polyfit(x, y[-5:], 1)
        return c_[1]
    df['micro_trend'] = c.rolling(5).apply(_slope, raw=True) / df['atr'].replace(0, np.nan)
    # Return × ATR interaction
    df['ret_x_atr'] = df['ret_1'] * df['atr_pct']
    
    # Drop NaN, select features
    feat_cols = [c for c in df.columns if c not in ['open','high','low','close','dollar','vol','n','atr','ret']]
    df_clean = df[feat_cols].replace([np.inf, -np.inf], np.nan).dropna()
    print(f"    {len(df_clean):,} bars, {len(feat_cols)} features")
    return df_clean, feat_cols

# ─── 4. TBM LABELING ───
def label_tbm(bars, horizon_sec, pt_m=0.5, sl_m=0.3):
    n = len(bars)
    atr = bars['atr'].values; close = bars['close'].values
    bar_sec = max(1, pd.Series(bars.index.values).diff().dropna().median().total_seconds())
    max_bars = int(horizon_sec / bar_sec) + 1
    y_long = np.zeros(n, dtype=int); y_short = np.zeros(n, dtype=int)
    for i in range(n):
        entry = close[i]; a = atr[i] if atr[i]>0 else entry*0.001
        ltp = entry*(1+pt_m*a/entry); lsl = entry*(1-sl_m*a/entry)
        stp = entry*(1-pt_m*a/entry); ssl = entry*(1+sl_m*a/entry)
        end = min(i+max_bars+1, n)
        for j in range(i+1, end):
            if close[j]>=ltp: y_long[i]=1; break
            if close[j]<=lsl: y_long[i]=-1; break
        else: y_long[i]=0
        for j in range(i+1, end):
            if close[j]<=stp: y_short[i]=1; break
            if close[j]>=ssl: y_short[i]=-1; break
        else: y_short[i]=0
    nl=(y_long==1).sum(); nls=(y_long==-1).sum()
    ns=(y_short==1).sum(); nss=(y_short==-1).sum()
    print(f"    TBM {horizon_sec}s PT={pt_m}×SL={sl_m}×: Long TP={nl}({nl/n:.1%}) SL={nls}({nls/n:.1%}) | Short TP={ns}({ns/n:.1%}) SL={nss}({nss/n:.1%})")
    return y_long, y_short

# ─── 5. CUSUM + TRAINING ───
def cusum_filter(ret, thr=None):
    if thr is None: thr = ret.std() * 0.5  # 0.5× = lazább, több event
    s_pos=0; s_neg=0; events=[]
    for i, r in enumerate(ret):
        s_pos = max(0, s_pos+r-thr); s_neg = min(0, s_neg+r+thr)
        if s_pos>thr or s_neg<-thr: events.append(i); s_pos=0; s_neg=0
    return events, thr

def train_lgb(X, y, n_fold=5, lgb_params=None):
    import lightgbm as lgb
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import roc_auc_score
    tscv = TimeSeriesSplit(n_splits=n_fold)
    aucs=[]; models=[]
    # Base params (can be overridden by lgb_params from Optuna)
    p = {'objective':'binary','metric':'auc','learning_rate':0.05,'num_leaves':31,
         'feature_fraction':0.7,'bagging_fraction':0.8,'bagging_freq':5,
         'seed':SEED,'verbose':-1,'min_data_in_leaf':50,'lambda_l1':1.0}
    if lgb_params:
        p['learning_rate'] = lgb_params.get('lr', p['learning_rate'])
        p['num_leaves'] = int(lgb_params.get('num_leaves', p['num_leaves']))
        p['feature_fraction'] = lgb_params.get('feat_frac', p['feature_fraction'])
        p['lambda_l1'] = lgb_params.get('l1', p['lambda_l1'])
        p['min_data_in_leaf'] = int(lgb_params.get('min_data', p['min_data_in_leaf']))
    for fold,(tr,va) in enumerate(tscv.split(X)):
        dtr = lgb.Dataset(X.iloc[tr], label=y.iloc[tr])
        dva = lgb.Dataset(X.iloc[va], label=y.iloc[va], reference=dtr)
        m = lgb.train(p, dtr, 300, [dva], callbacks=[lgb.early_stopping(30,verbose=False)])
        auc = roc_auc_score(y.iloc[va], m.predict(X.iloc[va]))
        aucs.append(auc); models.append(m)
    return models, np.mean(aucs), aucs

# ─── 6a. REGIME DETECTION (KG: Hurst exponent + trend strength) ───
def compute_hurst(close, window=100):
    """Hurst exponent via R/S method — rolling window.
    H < 0.5 : Mean-Reverting (safe for contra-trend)
    H ≈ 0.5 : Random Walk
    H > 0.5 : Trending (DANGER: contra-trend = huge loss)
    """
    n = len(close)
    H = np.full(n, 0.5)  # default = random walk
    for i in range(window, n):
        chunk = close.iloc[i-window:i].values
        if len(chunk) < 20: continue
        returns = np.diff(np.log(chunk))
        if np.std(returns) < 1e-12: continue
        # R/S across sub-blocks
        max_k = min(20, len(returns)//4)
        if max_k < 4: continue
        ks = np.unique(np.geomspace(4, len(returns), max_k).astype(int))
        rs_vals = []
        for k in ks:
            n_blocks = len(returns) // k
            if n_blocks < 1: continue
            rs_block = []
            for b in range(n_blocks):
                block = returns[b*k:(b+1)*k]
                cumdev = np.cumsum(block - block.mean())
                R = cumdev.max() - cumdev.min()
                S = block.std()
                if S > 0: rs_block.append(R / S)
            if rs_block:
                rs_vals.append((k, np.mean(rs_block)))
        if len(rs_vals) >= 3:
            log_k = np.log([v[0] for v in rs_vals])
            log_rs = np.log([v[1] for v in rs_vals])
            H[i] = np.polyfit(log_k, log_rs, 1)[0]
    return pd.Series(H, index=close.index)

def compute_trend_strength(bars, window=33):
    """Trend strength: |return| / ATR over window bars.
    > 2.0 = strong trend (contra-trend dangerous)
    < 1.0 = weak/noise (mean reversion safe)
    """
    close = bars['close']
    atr = bars['atr']
    ret = close.pct_change(window)
    return (ret * close / atr.replace(0, np.nan)).abs().fillna(0)

def regime_filter(bars, feat_df):
    """Compute regime features for signal filtering.
    Returns DataFrame with:
      - hurst: rolling Hurst exponent
      - trend_str: trend strength (|ret|/ATR)
      - trend_dir: +1 (up), -1 (down), 0 (neutral)
      - regime: 'trending', 'mean_rev', 'neutral'
    """
    print(f"\n  Regime detection...")
    close = bars['close'].loc[feat_df.index]
    # Hurst (expensive — use simpler proxy: variance ratio)
    # VR = var(2-period return) / (2 * var(1-period return))
    # VR < 1 → mean-reverting, VR > 1 → trending
    ret1 = close.pct_change(1)
    ret2 = close.pct_change(2)
    var1 = ret1.rolling(100).var()
    var2 = ret2.rolling(100).var()
    vr = var2 / (2 * var1.replace(0, np.nan))
    # Hurst proxy: H ≈ 0.5 + 0.5 * log2(VR)
    hurst_proxy = 0.5 + 0.5 * np.log2(vr.clip(0.25, 4))
    hurst_proxy = hurst_proxy.clip(0.1, 0.9).fillna(0.5)
    
    # Trend strength
    atr = bars['atr'].loc[feat_df.index]
    ret33 = close.pct_change(33)
    trend_str = (ret33 * close / atr.replace(0, np.nan)).abs().fillna(0)
    
    # Trend direction
    ema20 = close.ewm(span=20).mean()
    ema60 = close.ewm(span=60).mean()
    trend_dir = np.sign(ema20 - ema60).fillna(0)
    
    # Regime classification
    # H < 0.45 → mean-reverting (safe for contra-trend)
    # H > 0.55 → trending (contra-trend = dangerous)  
    # BUT: H mean=0.37 for BTCUSD → most bars are mean-reverting
    # Use H AND trend_str together: only TRENDING if BOTH H>0.50 AND strong trend
    regime = np.where((hurst_proxy > 0.50) & (trend_str > 3.0), 'trending',
             np.where(hurst_proxy < 0.40, 'mean_rev', 'neutral'))
    
    result = pd.DataFrame({
        'hurst': hurst_proxy,
        'trend_str': trend_str,
        'trend_dir': trend_dir,
        'regime': regime
    }, index=feat_df.index)
    
    n_trend = (result['regime'] == 'trending').sum()
    n_mr = (result['regime'] == 'mean_rev').sum()
    n_neut = (result['regime'] == 'neutral').sum()
    print(f"    Trending: {n_trend:,} ({n_trend/len(result):.1%})")
    print(f"    Mean-Rev: {n_mr:,} ({n_mr/len(result):.1%})")
    print(f"    Neutral:  {n_neut:,} ({n_neut/len(result):.1%})")
    print(f"    H mean={hurst_proxy.mean():.3f} trend_str mean={trend_str.mean():.2f}")
    
    return result

# ─── 6. PIPELINE ───
def run_v6(train_path):
    ts0 = datetime.now()
    ticks = load_ticks(train_path, 'TRAIN')
    bars = make_dollar_bars(ticks, DOLLAR_THR)
    feat_df, feat_cols = build_features(bars)
    
    # ── Regime detection (KG: Hurst + trend strength) ──
    regime = regime_filter(bars, feat_df)
    
    all_res = {}; hnames = HORIZON_NAMES
    
    for hsec in HORIZON_SEC:
        hn = hnames[hsec]
        print(f"\n{'─'*50}\nHORIZONT: {hn} ({hsec}s)\n{'─'*50}")
        y_long, y_short = label_tbm(bars, hsec, PROFIT_MULT, STOP_MULT)
        idx = feat_df.index.intersection(bars.index[:len(y_long)])
        fa = feat_df.loc[idx]
        yl = pd.Series(y_long[:len(bars)],index=bars.index[:len(y_long)]).loc[idx]
        ys = pd.Series(y_short[:len(bars)],index=bars.index[:len(y_short)]).loc[idx]
        ev, cthr = cusum_filter(bars['ret'].loc[idx].fillna(0), CUSUM_THR)
        print(f"    CUSUM: {len(ev):,}/{len(idx):,} ({len(ev)/len(idx):.1%}) thr={cthr:.6f}")
        fc = fa.iloc[ev]; ylc = (yl.iloc[ev]==1).astype(int); ysc = (ys.iloc[ev]==1).astype(int)
        mL, aL, _ = train_lgb(fc, ylc, N_FOLD)
        mS, aS, _ = train_lgb(fc, ysc, N_FOLD)
        pL = mL[-1].predict(fa); pS = mS[-1].predict(fa)
        pN = np.minimum(pL, pS)  # noise probability
        tL = np.mean(pL[ev])+0.5*np.std(pL[ev])
        tS = np.mean(pS[ev])+0.5*np.std(pS[ev])
        sig = np.zeros(len(fa))
        sig[pL>tL] = 1; sig[pS>tS] = -1
        both = (pL>tL)&(pS>tS); sig[both&(pL>=pS)]=1; sig[both&(pS>pL)]=-1
        
        # ── RAW (pre-filter) signal mentése ──
        sig_raw = sig.copy()  # szűretlen predikció
        
        # ── REGIME-AWARE SIGNAL FILTER (KG: meta-labeling + Hurst) ──
        # Rule 1: TRENDING regime (H>0.50 AND trend_str>3.0) → suppress contra-trend
        #   - uptrend + Short signal → NO TRADE (huge SL risk)
        #   - downtrend + Long signal → NO TRADE (huge SL risk)
        # Rule 2: Moderate contra-trend (trend_str 1.5-3.0) → elevate threshold
        #   - contra-trend signals need +0.08 higher probability (meta-label)
        regime_vals = regime['regime'].loc[fa.index].values
        trend_dir_vals = regime['trend_dir'].loc[fa.index].values
        trend_str_vals = regime['trend_str'].loc[fa.index].values
        
        n_suppressed = 0; n_elevated = 0
        for i in range(len(sig)):
            if sig[i] == 0: continue
            is_trending = regime_vals[i] == 'trending'
            is_contra = False
            if sig[i] == -1 and trend_dir_vals[i] > 0: is_contra = True
            if sig[i] == 1 and trend_dir_vals[i] < 0: is_contra = True
            
            if is_contra and is_trending:
                sig[i] = 0; n_suppressed += 1
            elif is_contra and trend_str_vals[i] > 1.5:
                if sig[i] == 1 and pL[i] < tL + 0.08:
                    sig[i] = 0; n_elevated += 1
                elif sig[i] == -1 and pS[i] < tS + 0.08:
                    sig[i] = 0; n_elevated += 1
        
        all_res[hn] = {'auc_L':aL,'auc_S':aS,'thr_L':tL,'thr_S':tS,
                       'p_long':pL,'p_short':pS,'p_noise':pN,'signal':sig,'signal_raw':sig_raw}
        nL=(sig==1).sum(); nS=(sig==-1).sum()
        print(f"    ✅ {hn}: L={aL:.4f} S={aS:.4f} Long={nL:,} Short={nS:,} L/S={nL/max(1,nS):.1f}x")
        print(f"    🛡️ Regime: suppressed={n_suppressed:,} elevated={n_elevated:,}")
    
    # Save predictions
    ts_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    preds = pd.DataFrame(index=feat_df.index)
    preds['price'] = bars['close'].loc[feat_df.index]
    preds['open'] = bars['open'].loc[feat_df.index]
    preds['high'] = bars['high'].loc[feat_df.index]
    preds['low'] = bars['low'].loc[feat_df.index]
    preds['close'] = bars['close'].loc[feat_df.index]
    preds['noise_level'] = bars['atr_pct'].loc[feat_df.index]
    preds['hurst'] = regime['hurst'].loc[feat_df.index]
    preds['trend_str'] = regime['trend_str'].loc[feat_df.index]
    preds['trend_dir'] = regime['trend_dir'].loc[feat_df.index]
    preds['regime'] = regime['regime'].loc[feat_df.index]
    for hn in list(HORIZON_NAMES.values()):
        r=all_res[hn]
        for k in ['p_long','p_short','p_noise','signal','signal_raw']:
            preds[f'{k}_{hn}'] = r[k]
        preds[f'long_thr_{hn}'] = r['thr_L']; preds[f'short_thr_{hn}'] = r['thr_S']
    pp = MODEL_DIR / f'BTCUSD_v6_preds_{ts_str}.csv'
    preds.to_csv(pp)
    
    # Summary
    el = (datetime.now()-ts0).total_seconds()
    print(f"\n{'='*72}\nSCALPER COPILOT v6.2 — KÉSZ ({el:.0f}s)")
    print(f"  ${DOLLAR_THR/1e6:.1f}M bars | PT={PROFIT_MULT}×ATR SL={STOP_MULT}×ATR")
    print(f"  Horizontok: {list(HORIZON_NAMES.values())}")
    for hn in list(HORIZON_NAMES.values()):
        r=all_res[hn]; nL=(r['signal']==1).sum(); nS=(r['signal']==-1).sum()
        nLr=(r['signal_raw']==1).sum(); nSr=(r['signal_raw']==-1).sum()
        print(f"  {hn}: L_AUC={r['auc_L']:.4f} S_AUC={r['auc_S']:.4f} Filt: L={nL:,} S={nS:,} | Raw: L={nLr:,} S={nSr:,}")
    print(f"  Predikciók: {pp.name}\n{'='*72}")
    return all_res, preds, pp

if __name__ == '__main__':
    train_path = DATA_DIR / 'BTCUSD_training_tick.csv'
    run_v6(train_path)