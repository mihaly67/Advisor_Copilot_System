#!/usr/bin/env python3
"""
Scalper Copilot v7 — OOS Exam (CONSTRAINED Optuna params)
  PONTOSAN ugyanaz pipeline mint scalper_optuna_v7.py
"""
import os, sys, time, json, warnings
import numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime
warnings.filterwarnings('ignore')

import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import roc_auc_score
import plotly.graph_objects as go
import plotly.subplots as sp

sys.path.insert(0, str(Path(__file__).parent))
from scalper_copilot_v6 import (
    load_ticks, make_dollar_bars, build_features, label_tbm,
    cusum_filter, regime_filter,
    DATA_DIR, EXAM_DIR, MODEL_DIR, CHART_DIR, DOLLAR_THR,
    HORIZON_SEC, HORIZON_NAMES,
    PROFIT_MULT, STOP_MULT, N_FOLD, SEED
)

# Inline helpers (same as optuna_v7)
SHAP_TOP = [
    'ema_d_60','vol_ma_20','vol_ma_5','mean_rev','ema_cross',
    'ema_d_30','ema_s_60','rsi_28','boll_pos','upper_wick',
    'ema_d_5','ema_s_30','micro_trend','mom_persistence','ema_d_10',
    'ret_1','ret_3','rv_10','variance_ratio','bar_dt_rel',
    'hour_sin','hour_cos','dir_x_mom','price_accel','ret_x_atr'
]

def cusum_custom(ret, thr_mult=0.5):
    thr = ret.std() * thr_mult
    s_p=0; s_n=0; ev=[]
    for i, r in enumerate(ret):
        s_p = max(0, s_p+r-thr); s_n = min(0, s_n+r+thr)
        if s_p>thr or s_n<-thr: ev.append(i); s_p=0; s_n=0
    return ev, thr

def regime_custom(bars, feat_df, h_thr=0.50, ts_thr=3.0):
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

BG='rgb(17,17,17)'; TC='#f2f5fa'
C_LONG='#26a69a'; C_SHORT='#ef5350'; C_CONTRA='#FF6B35'; C_OPT='#00d2ff'
CHART_DIR.mkdir(parents=True, exist_ok=True)

print('='*72)
print('SCALPER v7 — OOS EXAM (constrained Optuna)')
print('='*72)

def run_oos_v7(train_path, exam_path, hsec, hn, params):
    """OOS exam PONTOSAN az optuna_v7 pipeline-el."""
    # Unpack params
    lr = params['lr']
    num_leaves = params['num_leaves']
    feat_frac = params['feat_frac']
    l1 = params['l1']
    min_data = params['min_data']
    bagging_frac = params['bagging_frac']
    l2 = params['l2']
    cusum_mult = params['cusum_mult']
    h_thr = params['h_thr']
    ts_thr = params['trend_str_thr']  # converted name
    ts_elev = params['trend_str_elev']  # converted name
    elev_amt = params['elev_amt']
    pt_m = params.get('pt_m', 0.5)
    sl_m = params.get('sl_m', 0.3)
    
    print(f"\n{'─'*50}\nOOS v7: {hn} ({hsec}s) | PT={pt_m}× SL={sl_m}× CUSUM={cusum_mult:.2f} H={h_thr:.2f} TS={ts_thr:.1f} elev={ts_elev:.1f}\n{'─'*50}")
    
    # IS data
    print("  IS adat...")
    ticks = load_ticks(train_path, 'TRAIN')
    bars = make_dollar_bars(ticks, DOLLAR_THR)
    feat_df, feat_cols = build_features(bars)
    
    avail = [f for f in SHAP_TOP if f in feat_cols]
    if len(avail) < 10: avail = list(feat_cols)
    fa = feat_df[avail]
    
    y_long, y_short = label_tbm(bars, hsec, pt_m, sl_m)
    idx = fa.index.intersection(bars.index[:len(y_long)])
    fa_idx = fa.loc[idx]
    yl = pd.Series(y_long[:len(bars)], index=bars.index[:len(y_long)]).loc[idx]
    ys = pd.Series(y_short[:len(bars)], index=bars.index[:len(y_short)]).loc[idx]
    
    ev, _ = cusum_custom(bars['ret'].loc[idx].fillna(0), cusum_mult)
    fc = fa_idx.iloc[ev]
    ylc = (yl.iloc[ev]==1).astype(int)
    ysc = (ys.iloc[ev]==1).astype(int)
    
    rg = regime_custom(bars, feat_df, h_thr, ts_thr)
    
    # IS train (same as optuna objective)
    is_m = {}
    for side, y_c in [('long', ylc), ('short', ysc)]:
        tscv = TimeSeriesSplit(n_splits=N_FOLD)
        aucs = []; models = []
        for fold, (tr, va) in enumerate(tscv.split(fc)):
            dtr = lgb.Dataset(fc.iloc[tr], label=y_c.iloc[tr])
            dva = lgb.Dataset(fc.iloc[va], label=y_c.iloc[va], reference=dtr)
            p = {'objective':'binary','metric':'auc','learning_rate':lr,
                 'num_leaves':num_leaves,'feature_fraction':feat_frac,
                 'lambda_l1':l1,'lambda_l2':l2,'bagging_fraction':bagging_frac,
                 'bagging_freq':5,'min_data_in_leaf':min_data,
                 'seed':SEED,'verbose':-1}
            m = lgb.train(p, dtr, 300, [dva], callbacks=[lgb.early_stopping(30,verbose=False)])
            auc = roc_auc_score(y_c.iloc[va], m.predict(fc.iloc[va]))
            aucs.append(auc); models.append(m)
        is_m[f'auc_{side}'] = np.mean(aucs); is_m[f'model_{side}'] = models[-1]
    
    # IS signals
    pL = is_m['model_long'].predict(fa_idx); pS = is_m['model_short'].predict(fa_idx)
    tL = np.mean(pL[ev])+0.5*np.std(pL[ev]); tS = np.mean(pS[ev])+0.5*np.std(pS[ev])
    sig = np.zeros(len(fa_idx)); sig[pL>tL]=1; sig[pS>tS]=-1
    b=(pL>tL)&(pS>tS); sig[b&(pL>=pS)]=1; sig[b&(pS>pL)]=-1
    
    rv=rg['regime'].loc[fa_idx.index].values; td=rg['trend_dir'].loc[fa_idx.index].values; ts_=rg['trend_str'].loc[fa_idx.index].values
    for i in range(len(sig)):
        if sig[i]==0: continue
        ic=(sig[i]==-1 and td[i]>0) or (sig[i]==1 and td[i]<0)
        if ic and rv[i]=='trending': sig[i]=0
        elif ic and ts_[i]>ts_elev:
            if sig[i]==1 and pL[i]<tL+elev_amt: sig[i]=0
            elif sig[i]==-1 and pS[i]<tS+elev_amt: sig[i]=0
    
    ci=np.zeros(len(sig),dtype=bool); ci[(sig==1)&(td<0)]=True; ci[(sig==-1)&(td>0)]=True
    is_cp=ci.sum()/max(1,(sig!=0).sum())
    yla=yl.values[:len(sig)]; ysa=ys.values[:len(sig)]
    tp_i=((sig==1)&(yla==1)).sum()+((sig==-1)&(ysa==1)).sum()
    sl_i=((sig==1)&(yla==-1)).sum()+((sig==-1)&(ysa==-1)).sum()
    wr_i=tp_i/max(1,tp_i+sl_i)
    print(f"  IS: L_AUC={is_m['auc_long']:.4f} S_AUC={is_m['auc_short']:.4f} WR={wr_i:.1%} contra={is_cp:.1%}")
    
    # OOS data
    print("  OOS adat...")
    ticks_o = load_ticks(exam_path, 'EXAM')
    bars_o = make_dollar_bars(ticks_o, DOLLAR_THR)
    feat_o, feat_cols_o = build_features(bars_o)
    
    avail_o = [f for f in SHAP_TOP if f in feat_cols_o]
    if len(avail_o) < 10: avail_o = list(feat_cols_o)
    fa_o = feat_o[avail_o]
    
    y_lo, y_so = label_tbm(bars_o, hsec, pt_m, sl_m)
    idx_o = fa_o.index.intersection(bars_o.index[:len(y_lo)])
    fa_idx_o = fa_o.loc[idx_o]
    yl_o = pd.Series(y_lo[:len(bars_o)],index=bars_o.index[:len(y_lo)]).loc[idx_o]
    ys_o = pd.Series(y_so[:len(bars_o)],index=bars_o.index[:len(y_so)]).loc[idx_o]
    
    rg_o = regime_custom(bars_o, feat_o, h_thr, ts_thr)
    
    pL_o = is_m['model_long'].predict(fa_idx_o); pS_o = is_m['model_short'].predict(fa_idx_o)
    auc_L_o = roc_auc_score((yl_o==1).astype(int), pL_o)
    auc_S_o = roc_auc_score((ys_o==1).astype(int), pS_o)
    
    sig_o = np.zeros(len(fa_idx_o)); sig_o[pL_o>tL]=1; sig_o[pS_o>tS]=-1
    b_o=(pL_o>tL)&(pS_o>tS); sig_o[b_o&(pL_o>=pS_o)]=1; sig_o[b_o&(pS_o>pL_o)]=-1
    
    rv_o=rg_o['regime'].loc[fa_idx_o.index].values; td_o=rg_o['trend_dir'].loc[fa_idx_o.index].values; ts_o=rg_o['trend_str'].loc[fa_idx_o.index].values
    for i in range(len(sig_o)):
        if sig_o[i]==0: continue
        ic=(sig_o[i]==-1 and td_o[i]>0) or (sig_o[i]==1 and td_o[i]<0)
        if ic and rv_o[i]=='trending': sig_o[i]=0
        elif ic and ts_o[i]>ts_elev:
            if sig_o[i]==1 and pL_o[i]<tL+elev_amt: sig_o[i]=0
            elif sig_o[i]==-1 and pS_o[i]<tS+elev_amt: sig_o[i]=0
    
    co=np.zeros(len(sig_o),dtype=bool); co[(sig_o==1)&(td_o<0)]=True; co[(sig_o==-1)&(td_o>0)]=True
    oos_cp=co.sum()/max(1,(sig_o!=0).sum())
    yla_o=yl_o.values; ysa_o=ys_o.values
    tp_o=((sig_o==1)&(yla_o==1)).sum()+((sig_o==-1)&(ysa_o==1)).sum()
    sl_o=((sig_o==1)&(yla_o==-1)).sum()+((sig_o==-1)&(ysa_o==-1)).sum()
    wr_o=tp_o/max(1,tp_o+sl_o)
    nL=(sig_o==1).sum(); nS=(sig_o==-1).sum()
    
    print(f"  OOS: L_AUC={auc_L_o:.4f} S_AUC={auc_S_o:.4f} WR={wr_o:.1%} contra={oos_cp:.1%} Long={nL:,} Short={nS:,}")
    print(f"  📉 Degradáció: AUC_L={auc_L_o-is_m['auc_long']:+.4f} AUC_S={auc_S_o-is_m['auc_short']:+.4f} WR={wr_o-wr_i:+.1%} contra={oos_cp-is_cp:+.1%}")
    
    return {'horizon':hn,'is_auc_L':is_m['auc_long'],'is_auc_S':is_m['auc_short'],'is_wr':wr_i,'is_contra':is_cp,
            'oos_auc_L':auc_L_o,'oos_auc_S':auc_S_o,'oos_wr':wr_o,'oos_contra':oos_cp,
            'oos_n_long':nL,'oos_n_short':nS}

if __name__ == '__main__':
    ts0 = datetime.now()
    train_path = DATA_DIR / 'BTCUSD_training_tick.csv'
    exam_path = EXAM_DIR / 'BTCUSD_exam_tick.csv'
    
    optuna_file = CHART_DIR / 'optuna_v7_best_params.json'
    optuna_all = json.loads(optuna_file.read_text())
    print(f"  🏆 Optuna v7 params: {list(optuna_all.keys())}")
    
    results = []
    for hsec in HORIZON_SEC:
        hn = HORIZON_NAMES[hsec]
        bp = optuna_all.get(hn, {}).get('params')
        if bp: results.append(run_oos_v7(train_path, exam_path, hsec, hn, bp))
    
    el = (datetime.now() - ts0).total_seconds()
    print(f"\n{'='*72}")
    print(f"OOS v7 EXAM KÉSZ — {el:.0f}s")
    for r in results:
        print(f"  {r['horizon']}: IS_contra={r['is_contra']:.1%} OOS_contra={r['oos_contra']:.1%} IS_WR={r['is_wr']:.1%} OOS_WR={r['oos_wr']:.1%}")
    print(f"{'='*72}")
