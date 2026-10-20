#!/usr/bin/env python3
"""
Regime Filter Grid Sweep — Baseline pipeline, csak regime küszöbök variálása
  - Baseline: v6 pipeline (PT=0.5×/SL=0.3×, fix LGBM params, CUSUM auto)
  - Grid: h_thr × ts_thr × ts_elev × elev_amt
  - Minden kombináció: IS + OOS WR/contra/EV
  - Eredmény: CSV tábla, rendezve OOS EV/bar szerint
  - Cél: OOS EV > baseline (0.142/bar) és OOS contra < 20%
"""
import os, sys, time, json, warnings, itertools
import numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime
warnings.filterwarnings('ignore')

import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).parent))
from scalper_copilot_v6 import (
    load_ticks, make_dollar_bars, build_features, label_tbm,
    cusum_filter, regime_filter,
    DATA_DIR, EXAM_DIR, MODEL_DIR, CHART_DIR, DOLLAR_THR,
    HORIZON_SEC, HORIZON_NAMES,
    PROFIT_MULT, STOP_MULT, N_FOLD, SEED
)

# ─── KONFIG ───
PT_M = 0.5; SL_M = 0.3  # fix PT/SL

# Grid — baseline: h_thr=0.50, ts_thr=3.0, ts_elev=1.5, elev_amt=0.08
H_THR_GRID    = [0.42, 0.46, 0.50, 0.54]
TS_THR_GRID   = [1.5, 2.0, 2.5, 3.0, 4.0]
TS_ELEV_GRID  = [0.8, 1.0, 1.5, 2.0, 2.5]
ELEV_AMT_GRID = [0.04, 0.06, 0.08, 0.10, 0.12]
MAX_OOS_EVAL = 30   # top-30 IS EV/bar → OOS

# ─── REGIME CUSTOM ───
def regime_custom(bars, feat_df, h_thr, ts_thr):
    close = bars['close'].loc[feat_df.index]
    ret1 = close.pct_change(1); ret2 = close.pct_change(2)
    var1 = ret1.rolling(100).var(); var2 = ret2.rolling(100).var()
    vr = var2 / (2 * var1.replace(0, np.nan))
    hurst = 0.5 + 0.5 * np.log2(vr.clip(0.25, 4))
    hurst = hurst.clip(0.1, 0.9).fillna(0.5)
    atr = bars['atr'].loc[feat_df.index]
    ret33 = close.pct_change(33)
    trend_str = (ret33 * close / atr.replace(0, np.nan)).abs().fillna(0)
    ema20 = close.ewm(span=20).mean(); ema60 = close.ewm(span=60).mean()
    trend_dir = np.sign(ema20 - ema60).fillna(0)
    regime = np.where((hurst > h_thr) & (trend_str > ts_thr), 'trending',
             np.where(hurst < (h_thr - 0.10), 'mean_rev', 'neutral'))
    return pd.DataFrame({'hurst':hurst,'trend_str':trend_str,'trend_dir':trend_dir,'regime':regime}, index=feat_df.index)

def apply_regime_filter(sig, pL, pS, tL, tS, regime, fa_idx, ts_elev, elev_amt):
    """Vectorized regime filter — 50× faster than loop."""
    sig = sig.copy()
    rv = regime['regime'].loc[fa_idx.index].values
    td = regime['trend_dir'].loc[fa_idx.index].values
    ts_ = regime['trend_str'].loc[fa_idx.index].values
    # Contra mask: signal against trend
    is_contra = ((sig == -1) & (td > 0)) | ((sig == 1) & (td < 0))
    # Rule 1: trending + contra → suppress
    suppress = is_contra & (rv == 'trending') & (sig != 0)
    # Rule 2: moderate contra + elevate threshold
    mod_contra = is_contra & ~suppress & (ts_ > ts_elev) & (sig != 0)
    elevate_long = mod_contra & (sig == 1) & (pL < tL + elev_amt)
    elevate_short = mod_contra & (sig == -1) & (pS < tS + elev_amt)
    sig[suppress | elevate_long | elevate_short] = 0
    n_supp = suppress.sum(); n_elev = (elevate_long | elevate_short).sum()
    return sig, int(n_supp), int(n_elev)

def signal_metrics(sig, y_long, y_short, trend_dir_vals, pt_m, sl_m):
    n_sig = (sig != 0).sum()
    if n_sig == 0:
        return {'wr': 0, 'contra': 0, 'ev_bar': 0, 'n_signal': 0}
    co = np.zeros(len(sig), dtype=bool)
    co[(sig == 1) & (trend_dir_vals < 0)] = True
    co[(sig == -1) & (trend_dir_vals > 0)] = True
    contra_pct = co.sum() / n_sig
    tp = ((sig == 1) & (y_long == 1)).sum() + ((sig == -1) & (y_short == 1)).sum()
    sl = ((sig == 1) & (y_long == -1)).sum() + ((sig == -1) & (y_short == -1)).sum()
    wr = tp / max(1, tp + sl)
    ev_bar = wr * pt_m - (1 - wr) * sl_m
    return {'wr': wr, 'contra': contra_pct, 'ev_bar': ev_bar, 'n_signal': n_sig}

# ─── MAIN ───
print("=" * 72)
ngrid = len(H_THR_GRID)*len(TS_THR_GRID)*len(TS_ELEV_GRID)*len(ELEV_AMT_GRID)
print(f"REGIME GRID SWEEP | PT={PT_M}× SL={SL_M}× | {ngrid} configs")
print("=" * 72)

ts0 = datetime.now()

# ── 1. ADAT ──
print("\n  Loading IS data...")
ticks = load_ticks(DATA_DIR / 'BTCUSD_training_tick.csv', 'TRAIN')
bars = make_dollar_bars(ticks, DOLLAR_THR)
feat_df, feat_cols = build_features(bars)
print(f"  IS: {len(bars):,} bars, {len(feat_cols)} features")

print("\n  Loading OOS data...")
ticks_o = load_ticks(EXAM_DIR / 'BTCUSD_exam_tick.csv', 'EXAM')
bars_o = make_dollar_bars(ticks_o, DOLLAR_THR)
feat_o, feat_cols_o = build_features(bars_o)
print(f"  OOS: {len(bars_o):,} bars, {len(feat_cols_o)} features")

# ── 2. BASELINE MODELS ──
print("\n  Training baseline models...")
is_models = {}
for hsec in HORIZON_SEC:
    hn = HORIZON_NAMES[hsec]
    print(f"\n  {hn} ({hsec}s)...")
    y_long, y_short = label_tbm(bars, hsec, PT_M, SL_M)
    idx = feat_df.index.intersection(bars.index[:len(y_long)])
    fa = feat_df.loc[idx]
    yl = pd.Series(y_long[:len(bars)], index=bars.index[:len(y_long)]).loc[idx]
    ys = pd.Series(y_short[:len(bars)], index=bars.index[:len(y_short)]).loc[idx]
    ev, cthr = cusum_filter(bars['ret'].loc[idx].fillna(0), None)
    fc = fa.iloc[ev]
    ylc = (yl.iloc[ev] == 1).astype(int)
    ysc = (ys.iloc[ev] == 1).astype(int)
    models = {}
    for side, y_c in [('long', ylc), ('short', ysc)]:
        tscv = TimeSeriesSplit(n_splits=N_FOLD)
        aucs = []; ms = []
        for fold, (tr, va) in enumerate(tscv.split(fc)):
            dtr = lgb.Dataset(fc.iloc[tr], label=y_c.iloc[tr])
            dva = lgb.Dataset(fc.iloc[va], label=y_c.iloc[va], reference=dtr)
            p = {'objective': 'binary', 'metric': 'auc',
                 'learning_rate': 0.05, 'num_leaves': 31,
                 'feature_fraction': 0.8, 'lambda_l1': 0, 'lambda_l2': 0,
                 'bagging_fraction': 0.8, 'bagging_freq': 5,
                 'min_data_in_leaf': 50, 'seed': SEED, 'verbose': -1}
            m = lgb.train(p, dtr, 300, [dva], callbacks=[lgb.early_stopping(30, verbose=False)])
            aucs.append(roc_auc_score(y_c.iloc[va], m.predict(fc.iloc[va])))
            ms.append(m)
        models[f'auc_{side}'] = np.mean(aucs); models[f'model_{side}'] = ms[-1]
    pL = models['model_long'].predict(fa); pS = models['model_short'].predict(fa)
    tL = np.mean(pL[ev]) + 0.5 * np.std(pL[ev]); tS = np.mean(pS[ev]) + 0.5 * np.std(pS[ev])
    # OOS
    y_lo, y_so = label_tbm(bars_o, hsec, PT_M, SL_M)
    idx_o = feat_o.index.intersection(bars_o.index[:len(y_lo)])
    fa_o = feat_o.loc[idx_o]
    pL_o = models['model_long'].predict(fa_o); pS_o = models['model_short'].predict(fa_o)
    yl_o = pd.Series(y_lo[:len(bars_o)], index=bars_o.index[:len(y_lo)]).loc[idx_o]
    ys_o = pd.Series(y_so[:len(bars_o)], index=bars_o.index[:len(y_so)]).loc[idx_o]
    is_models[hn] = {
        'fa': fa, 'pL': pL, 'pS': pS, 'tL': tL, 'tS': tS,
        'yl': yl.values, 'ys': ys.values,
        'fa_o': fa_o, 'pL_o': pL_o, 'pS_o': pS_o,
        'yl_o': yl_o.values, 'ys_o': ys_o.values,
        'auc_L': models['auc_long'], 'auc_S': models['auc_short'],
        'is_pos': feat_df.index.get_indexer_for(fa.index),
        'oos_pos': feat_o.index.get_indexer_for(fa_o.index)
    }
    print(f"    L_AUC={models['auc_long']:.4f} S_AUC={models['auc_short']:.4f}")

# ── 3. GRID SWEEP (IS) ──
grid = list(itertools.product(H_THR_GRID, TS_THR_GRID, TS_ELEV_GRID, ELEV_AMT_GRID))
print(f"\n  Grid: {len(grid)} configs × {len(HORIZON_SEC)} horizons")

# Pre-compute hurst/trend_str/trend_dir (independent of h_thr/ts_thr)
# Only regime classification depends on them
print("  Pre-computing regime features...")
def precompute_regime(bars, feat_df):
    close = bars['close'].loc[feat_df.index]
    ret1 = close.pct_change(1); ret2 = close.pct_change(2)
    var1 = ret1.rolling(100).var(); var2 = ret2.rolling(100).var()
    vr = var2 / (2 * var1.replace(0, np.nan))
    hurst = (0.5 + 0.5 * np.log2(vr.clip(0.25, 4))).clip(0.1, 0.9).fillna(0.5)
    atr = bars['atr'].loc[feat_df.index]
    ret33 = close.pct_change(33)
    trend_str = (ret33 * close / atr.replace(0, np.nan)).abs().fillna(0)
    ema20 = close.ewm(span=20).mean(); ema60 = close.ewm(span=60).mean()
    trend_dir = np.sign(ema20 - ema60).fillna(0)
    return hurst.values, trend_str.values, trend_dir.values

h_is, ts_is, td_is = precompute_regime(bars, feat_df)
h_oos, ts_oos_raw, td_oos = precompute_regime(bars_o, feat_o)
print(f"  Regime features cached: IS={len(h_is):,} OOS={len(h_oos):,}")

# Fast regime classification (just numpy)
def classify_regime(hurst_arr, ts_arr, h_thr, ts_thr, h_mean_rev_offset=0.10):
    regime = np.where((hurst_arr > h_thr) & (ts_arr > ts_thr), 2,  # 2=trending
             np.where(hurst_arr < (h_thr - h_mean_rev_offset), 0, 1))  # 0=mean_rev, 1=neutral
    return regime

is_results = []
for gi, (h_thr, ts_thr, ts_elev, elev_amt) in enumerate(grid):
    for hsec in HORIZON_SEC:
        hn = HORIZON_NAMES[hsec]; d = is_models[hn]
        # Fast regime (no pandas, pure numpy) — use positions
        pos = d['is_pos']
        h_vals = h_is[pos]; ts_vals = ts_is[pos]; td_vals = td_is[pos]
        regime_arr = classify_regime(h_vals, ts_vals, h_thr, ts_thr)
        
        sig = np.zeros(len(d['fa']))
        sig[d['pL'] > d['tL']] = 1; sig[d['pS'] > d['tS']] = -1
        b = (d['pL'] > d['tL']) & (d['pS'] > d['tS'])
        sig[b & (d['pL'] >= d['pS'])] = 1; sig[b & (d['pS'] > d['pL'])] = -1
        
        # Vectorized regime filter (inline for speed)
        is_contra = ((sig == -1) & (td_vals > 0)) | ((sig == 1) & (td_vals < 0))
        suppress = is_contra & (regime_arr == 2) & (sig != 0)  # 2=trending
        mod_contra = is_contra & ~suppress & (ts_vals > ts_elev) & (sig != 0)
        elev_l = mod_contra & (sig == 1) & (d['pL'] < d['tL'] + elev_amt)
        elev_s = mod_contra & (sig == -1) & (d['pS'] < d['tS'] + elev_amt)
        sig[suppress | elev_l | elev_s] = 0
        
        met = signal_metrics(sig, d['yl'], d['ys'], td_vals, PT_M, SL_M)
        is_results.append({
            'h_thr': h_thr, 'ts_thr': ts_thr, 'ts_elev': ts_elev, 'elev_amt': elev_amt,
            'horizon': hn, 'is_wr': met['wr'], 'is_contra': met['contra'],
            'is_ev_bar': met['ev_bar'], 'is_n_signal': met['n_signal']
        })
    if (gi + 1) % 100 == 0:
        print(f"    IS: {gi+1}/{len(grid)} ({(gi+1)/len(grid):.0%})")
print(f"  IS: {len(is_results)} evaluations done")

# ── 4. OOS for top-K ──
is_df = pd.DataFrame(is_results)
oos_results = []
for hn in list(HORIZON_NAMES.values()):
    hn_df = is_df[is_df['horizon'] == hn].sort_values('is_ev_bar', ascending=False).head(MAX_OOS_EVAL)
    print(f"\n  OOS top-{len(hn_df)} for {hn}...")
    for _, row in hn_df.iterrows():
        h_thr=row['h_thr']; ts_thr=row['ts_thr']; ts_elev=row['ts_elev']; elev_amt=row['elev_amt']
        d = is_models[hn]
        # Fast OOS regime (pre-computed)
        oos_pos = d['oos_pos']
        h_o = h_oos[oos_pos]; ts_o = ts_oos_raw[oos_pos]; td_o = td_oos[oos_pos]
        regime_o = classify_regime(h_o, ts_o, h_thr, ts_thr)
        
        sig_o = np.zeros(len(d['fa_o']))
        sig_o[d['pL_o'] > d['tL']] = 1; sig_o[d['pS_o'] > d['tS']] = -1
        b_o = (d['pL_o'] > d['tL']) & (d['pS_o'] > d['tS'])
        sig_o[b_o & (d['pL_o'] >= d['pS_o'])] = 1; sig_o[b_o & (d['pS_o'] > d['pL_o'])] = -1
        
        # Vectorized OOS regime filter
        is_contra_o = ((sig_o == -1) & (td_o > 0)) | ((sig_o == 1) & (td_o < 0))
        suppress_o = is_contra_o & (regime_o == 2) & (sig_o != 0)
        mod_contra_o = is_contra_o & ~suppress_o & (ts_o > ts_elev) & (sig_o != 0)
        elev_lo = mod_contra_o & (sig_o == 1) & (d['pL_o'] < d['tL'] + elev_amt)
        elev_so = mod_contra_o & (sig_o == -1) & (d['pS_o'] < d['tS'] + elev_amt)
        sig_o[suppress_o | elev_lo | elev_so] = 0
        
        met_o = signal_metrics(sig_o, d['yl_o'], d['ys_o'], td_o, PT_M, SL_M)
        oos_results.append({
            'h_thr': h_thr, 'ts_thr': ts_thr, 'ts_elev': ts_elev, 'elev_amt': elev_amt,
            'horizon': hn,
            'is_wr': row['is_wr'], 'is_contra': row['is_contra'], 'is_ev_bar': row['is_ev_bar'],
            'oos_wr': met_o['wr'], 'oos_contra': met_o['contra'],
            'oos_ev_bar': met_o['ev_bar'], 'oos_n_signal': met_o['n_signal']
        })

# ── 5. EREDMÉNY ──
oos_df = pd.DataFrame(oos_results)
out_path = CHART_DIR / 'regime_grid_sweep_results.csv'
oos_df.to_csv(out_path, index=False)
oos_df = oos_df.sort_values('oos_ev_bar', ascending=False)

print(f"\n{'='*72}")
print(f"REGIME GRID SWEEP — TOP 10 (OOS EV/bar)")
print(f"{'='*72}")
for i, (_, r) in enumerate(oos_df.head(10).iterrows()):
    print(f"  {i+1}. {r['horizon']} | h={r['h_thr']:.2f} ts={r['ts_thr']:.1f} elev_thr={r['ts_elev']:.1f} elev={r['elev_amt']:.2f}")
    print(f"     IS: WR={r['is_wr']:.1%} contra={r['is_contra']:.1%} EV={r['is_ev_bar']:.3f}")
    print(f"     OOS: WR={r['oos_wr']:.1%} contra={r['oos_contra']:.1%} EV={r['oos_ev_bar']:.3f} n={r['oos_n_signal']:,}")

# Baseline
print(f"\n{'='*72}")
print("BASELINE (h=0.50 ts=3.0 elev_thr=1.5 elev=0.08)")
bl = oos_df[(oos_df['h_thr']==0.50)&(oos_df['ts_thr']==3.0)&(oos_df['ts_elev']==1.5)&(oos_df['elev_amt']==0.08)]
for _, r in bl.iterrows():
    print(f"  {r['horizon']}: OOS_WR={r['oos_wr']:.1%} OOS_contra={r['oos_contra']:.1%} OOS_EV={r['oos_ev_bar']:.3f}")

# Best per horizon
print(f"\nBEST per horizon (OOS EV/bar)")
for hn in list(HORIZON_NAMES.values()):
    hb = oos_df[oos_df['horizon']==hn].iloc[0]
    print(f"  {hn}: h={hb['h_thr']:.2f} ts={hb['ts_thr']:.1f} elev_thr={hb['ts_elev']:.1f} elev={hb['elev_amt']:.2f} → OOS_WR={hb['oos_wr']:.1%} contra={hb['oos_contra']:.1%} EV={hb['oos_ev_bar']:.3f}")

el = (datetime.now() - ts0).total_seconds()
print(f"\n  KÉSZ — {el:.0f}s")
