#!/usr/bin/env python3
"""
Scalper Copilot v6 — OOS Exam (Out-of-Sample)
  - Vizsga adat: 2026.10.05–10.08 (EXAM_DIR)
  - Betanított modellek a training adaton (v6.2 vagy Optuna best)
  - Walk-forward: utolsó fold modell + regime filter
  - Kimenet: OOS AUC, WR, contra%, Sharpe vs IS (in-sample)

Logikus sorrend: SHAP ✅ → Optuna ✅ → OOS exam
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

# ─── IMPORT v6 PIPELINE ───
sys.path.insert(0, str(Path(__file__).parent))
from scalper_copilot_v6 import (
    load_ticks, make_dollar_bars, build_features, label_tbm,
    cusum_filter, train_lgb, regime_filter,
    DATA_DIR, EXAM_DIR, MODEL_DIR, CHART_DIR, DOLLAR_THR,
    HORIZON_SEC, HORIZON_NAMES,
    PROFIT_MULT, STOP_MULT, CUSUM_THR, N_FOLD, SEED
)

# SHAP top feature-ök — ugyanaz mint Optuna-ban
SHAP_TOP_FEATURES = [
    'ema_d_60', 'vol_ma_20', 'vol_ma_5', 'mean_rev', 'ema_cross',
    'ema_d_30', 'ema_s_60', 'rsi_28', 'boll_pos', 'upper_wick',
    'ema_d_5', 'ema_s_30', 'micro_trend', 'mom_persistence', 'ema_d_10',
    'ret_1', 'ret_3', 'rv_10', 'variance_ratio', 'bar_dt_rel',
    'hour_sin', 'hour_cos', 'dir_x_mom', 'price_accel', 'ret_x_atr'
]

def cusum_filter_custom(ret, thr_mult=0.5):
    """Ugyanaz mint Optuna-ban — CUSUM egyéni küszöb szorzóval."""
    thr = ret.std() * thr_mult
    s_pos=0; s_neg=0; events=[]
    for i, r in enumerate(ret):
        s_pos = max(0, s_pos+r-thr); s_neg = min(0, s_neg+r+thr)
        if s_pos>thr or s_neg<-thr: events.append(i); s_pos=0; s_neg=0
    return events, thr

def regime_filter_custom(bars, feat_df, h_thr=0.50, trend_str_thr=3.0, trend_str_elev=1.5):
    """Ugyanaz mint Optuna-ban — regime filter egyéni küszöbökkel."""
    close = bars['close'].loc[feat_df.index]
    ret1 = close.pct_change(1); ret2 = close.pct_change(2)
    var1 = ret1.rolling(100).var(); var2 = ret2.rolling(100).var()
    vr = var2 / (2 * var1.replace(0, np.nan))
    hurst_proxy = 0.5 + 0.5 * np.log2(vr.clip(0.25, 4))
    hurst_proxy = hurst_proxy.clip(0.1, 0.9).fillna(0.5)
    atr = bars['atr'].loc[feat_df.index]
    ret33 = close.pct_change(33)
    trend_str = (ret33 * close / atr.replace(0, np.nan)).abs().fillna(0)
    ema20 = close.ewm(span=20).mean(); ema60 = close.ewm(span=60).mean()
    trend_dir = np.sign(ema20 - ema60).fillna(0)
    regime = np.where((hurst_proxy > h_thr) & (trend_str > trend_str_thr), 'trending',
             np.where(hurst_proxy < (h_thr - 0.10), 'mean_rev', 'neutral'))
    return pd.DataFrame({
        'hurst': hurst_proxy, 'trend_str': trend_str,
        'trend_dir': trend_dir, 'regime': regime
    }, index=feat_df.index)

CHART_DIR.mkdir(parents=True, exist_ok=True)

# Színek
BG='rgb(17,17,17)'; GC='#283442'; TC='#f2f5fa'
C_LONG='#26a69a'; C_SHORT='#ef5350'; C_CONTRA='#FF6B35'; C_NOISE='#888888'; C_OPT='#00d2ff'

print("=" * 72)
print("SCALPER COPILOT v6 — OOS EXAM")
print("=" * 72)

def run_oos_exam(train_path, exam_path, horizon_sec, horizon_name,
                 pt_m=PROFIT_MULT, sl_m=STOP_MULT,
                 optuna_params=None):
    """OOS exam — PONTOSAN ugyanaz a pipeline mint Optuna."""
    # ─── Paraméterek (Optuna vagy baseline) ───
    if optuna_params:
        pt_m = optuna_params.get('pt_m', pt_m)
        sl_m = optuna_params.get('sl_m', sl_m)
    cusum_mult = optuna_params.get('cusum_mult', 0.5) if optuna_params else 0.5
    h_thr = optuna_params.get('h_thr', 0.50) if optuna_params else 0.50
    trend_str_thr = optuna_params.get('trend_str_thr', 3.0) if optuna_params else 3.0
    trend_str_elev = optuna_params.get('trend_str_elev', 1.5) if optuna_params else 1.5
    elev_amt = optuna_params.get('elev_amt', 0.08) if optuna_params else 0.08
    use_shap = optuna_params is not None
    print(f"\n{'─'*50}\nOOS EXAM: {horizon_name} ({horizon_sec}s) | PT={pt_m:.2f}× SL={sl_m:.2f}× | CUSUM={cusum_mult:.2f} H={h_thr:.2f} TS_thr={trend_str_thr:.1f}{' [SHAP]' if use_shap else ''}\n{'─'*50}")
    
    # IS
    print("  IS (training) adat betöltése...")
    ticks_train = load_ticks(train_path, 'TRAIN')
    bars_train = make_dollar_bars(ticks_train, DOLLAR_THR)
    feat_train, feat_cols = build_features(bars_train)
    
    # SHAP feature szűrés — ugyanaz mint Optuna
    if use_shap:
        available = [f for f in SHAP_TOP_FEATURES if f in feat_cols]
        if len(available) < 10: available = list(feat_cols)
        feat_train = feat_train[available]
        print(f"    SHAP top features: {len(available)}")
    
    regime_train = regime_filter_custom(bars_train, feat_train, h_thr, trend_str_thr, trend_str_elev)
    
    y_long, y_short = label_tbm(bars_train, horizon_sec, pt_m, sl_m)
    idx = feat_train.index.intersection(bars_train.index[:len(y_long)])
    fa = feat_train.loc[idx]
    yl = pd.Series(y_long[:len(bars_train)], index=bars_train.index[:len(y_long)]).loc[idx]
    ys = pd.Series(y_short[:len(bars_train)], index=bars_train.index[:len(y_short)]).loc[idx]
    # CUSUM custom — ugyanaz mint Optuna
    ev, cthr = cusum_filter_custom(bars_train['ret'].loc[idx].fillna(0), cusum_mult)
    fc = fa.iloc[ev]
    ylc = (yl.iloc[ev]==1).astype(int); ysc = (ys.iloc[ev]==1).astype(int)
    
    is_m = {}
    for side, y_c in [('long', ylc), ('short', ysc)]:
        models, auc_mean, _ = train_lgb(fc, y_c, N_FOLD, lgb_params=optuna_params)
        is_m[f'auc_{side}'] = auc_mean; is_m[f'model_{side}'] = models[-1]
    
    pL = is_m['model_long'].predict(fa); pS = is_m['model_short'].predict(fa)
    tL = np.mean(pL[ev])+0.5*np.std(pL[ev]); tS = np.mean(pS[ev])+0.5*np.std(pS[ev])
    
    # IS signal + regime filter
    sig_is = np.zeros(len(fa)); sig_is[pL>tL]=1; sig_is[pS>tS]=-1
    b=(pL>tL)&(pS>tS); sig_is[b&(pL>=pS)]=1; sig_is[b&(pS>pL)]=-1
    rv=regime_train['regime'].loc[fa.index].values; td=regime_train['trend_dir'].loc[fa.index].values
    ts_=regime_train['trend_str'].loc[fa.index].values
    for i in range(len(sig_is)):
        if sig_is[i]==0: continue
        ic=(sig_is[i]==-1 and td[i]>0) or (sig_is[i]==1 and td[i]<0)
        if ic and rv[i]=='trending': sig_is[i]=0
        elif ic and ts_[i]>trend_str_thr:
            if sig_is[i]==1 and pL[i]<tL+elev_amt: sig_is[i]=0
            elif sig_is[i]==-1 and pS[i]<tS+elev_amt: sig_is[i]=0
    ci=np.zeros(len(sig_is),dtype=bool); ci[(sig_is==1)&(td<0)]=True; ci[(sig_is==-1)&(td>0)]=True
    is_cp=ci.sum()/max(1,(sig_is!=0).sum())
    yla=yl.values[:len(sig_is)]; ysa=ys.values[:len(sig_is)]
    tp_i=((sig_is==1)&(yla==1)).sum()+((sig_is==-1)&(ysa==1)).sum()
    sl_i=((sig_is==1)&(yla==-1)).sum()+((sig_is==-1)&(ysa==-1)).sum()
    wr_i=tp_i/max(1,tp_i+sl_i)
    print(f"  IS: L_AUC={is_m['auc_long']:.4f} S_AUC={is_m['auc_short']:.4f} WR={wr_i:.1%} contra={is_cp:.1%}")
    
    # OOS
    print("  OOS (exam) adat betöltése...")
    ticks_exam = load_ticks(exam_path, 'EXAM')
    bars_exam = make_dollar_bars(ticks_exam, DOLLAR_THR)
    feat_exam, feat_cols_exam = build_features(bars_exam)
    # SHAP feature szűrés OOS-on is
    if use_shap:
        available_o = [f for f in SHAP_TOP_FEATURES if f in feat_cols_exam]
        if len(available_o) < 10: available_o = list(feat_cols_exam)
        feat_exam = feat_exam[available_o]
    regime_exam = regime_filter_custom(bars_exam, feat_exam, h_thr, trend_str_thr, trend_str_elev)
    
    y_lo, y_so = label_tbm(bars_exam, horizon_sec, pt_m, sl_m)
    idx_o = feat_exam.index.intersection(bars_exam.index[:len(y_lo)])
    fa_o = feat_exam.loc[idx_o]
    yl_o = pd.Series(y_lo[:len(bars_exam)],index=bars_exam.index[:len(y_lo)]).loc[idx_o]
    ys_o = pd.Series(y_so[:len(bars_exam)],index=bars_exam.index[:len(y_so)]).loc[idx_o]
    
    pL_o = is_m['model_long'].predict(fa_o); pS_o = is_m['model_short'].predict(fa_o)
    auc_L_o = roc_auc_score((yl_o==1).astype(int), pL_o)
    auc_S_o = roc_auc_score((ys_o==1).astype(int), pS_o)
    
    sig_o = np.zeros(len(fa_o)); sig_o[pL_o>tL]=1; sig_o[pS_o>tS]=-1
    b_o=(pL_o>tL)&(pS_o>tS); sig_o[b_o&(pL_o>=pS_o)]=1; sig_o[b_o&(pS_o>pL_o)]=-1
    rv_o=regime_exam['regime'].loc[fa_o.index].values; td_o=regime_exam['trend_dir'].loc[fa_o.index].values
    ts_o=regime_exam['trend_str'].loc[fa_o.index].values
    for i in range(len(sig_o)):
        if sig_o[i]==0: continue
        ic=(sig_o[i]==-1 and td_o[i]>0) or (sig_o[i]==1 and td_o[i]<0)
        if ic and rv_o[i]=='trending': sig_o[i]=0
        elif ic and ts_o[i]>trend_str_thr:
            if sig_o[i]==1 and pL_o[i]<tL+elev_amt: sig_o[i]=0
            elif sig_o[i]==-1 and pS_o[i]<tS+elev_amt: sig_o[i]=0
    
    co=np.zeros(len(sig_o),dtype=bool); co[(sig_o==1)&(td_o<0)]=True; co[(sig_o==-1)&(td_o>0)]=True
    oos_cp=co.sum()/max(1,(sig_o!=0).sum())
    yla_o=yl_o.values; ysa_o=ys_o.values
    tp_o=((sig_o==1)&(yla_o==1)).sum()+((sig_o==-1)&(ysa_o==1)).sum()
    sl_o=((sig_o==1)&(yla_o==-1)).sum()+((sig_o==-1)&(ysa_o==-1)).sum()
    wr_o=tp_o/max(1,tp_o+sl_o)
    nL_o=(sig_o==1).sum(); nS_o=(sig_o==-1).sum()
    
    print(f"  OOS: L_AUC={auc_L_o:.4f} S_AUC={auc_S_o:.4f} WR={wr_o:.1%} contra={oos_cp:.1%} Long={nL_o:,} Short={nS_o:,}")
    print(f"  📉 Degradáció: AUC_L={auc_L_o-is_m['auc_long']:+.4f} AUC_S={auc_S_o-is_m['auc_short']:+.4f} WR={wr_o-wr_i:+.1%} contra={oos_cp-is_cp:+.1%}")
    
    return {
        'horizon':horizon_name,
        'is_auc_L':is_m['auc_long'],'is_auc_S':is_m['auc_short'],'is_wr':wr_i,'is_contra':is_cp,
        'oos_auc_L':auc_L_o,'oos_auc_S':auc_S_o,'oos_wr':wr_o,'oos_contra':oos_cp,
        'oos_n_long':nL_o,'oos_n_short':nS_o,'oos_tp':tp_o,'oos_sl':sl_o
    }

def make_oos_chart(results, output_dir):
    fig = sp.make_subplots(rows=2, cols=2,
        subplot_titles=['AUC (IS vs OOS)', 'Win Rate (IS vs OOS)',
                        'Contra% (IS vs OOS)', 'OOS Trades'],
        vertical_spacing=0.15, horizontal_spacing=0.15)
    horizons = [r['horizon'] for r in results]
    
    for col_attr, row, col in [('auc_L',1,1),('auc_S',1,1)]:
        pass
    
    # AUC comparison
    fig.add_trace(go.Bar(name='IS L', x=horizons,
        y=[r['is_auc_L'] for r in results], marker_color=C_LONG, offsetgroup='IS'), row=1, col=1)
    fig.add_trace(go.Bar(name='OOS L', x=horizons,
        y=[r['oos_auc_L'] for r in results], marker_color=C_LONG, opacity=0.6, offsetgroup='OOS'), row=1, col=1)
    fig.add_trace(go.Bar(name='IS S', x=horizons,
        y=[r['is_auc_S'] for r in results], marker_color=C_SHORT, offsetgroup='IS'), row=1, col=1)
    fig.add_trace(go.Bar(name='OOS S', x=horizons,
        y=[r['oos_auc_S'] for r in results], marker_color=C_SHORT, opacity=0.6, offsetgroup='OOS'), row=1, col=1)
    
    # WR
    fig.add_trace(go.Bar(name='IS', x=horizons,
        y=[r['is_wr'] for r in results], marker_color=C_LONG), row=1, col=2)
    fig.add_trace(go.Bar(name='OOS', x=horizons,
        y=[r['oos_wr'] for r in results], marker_color=C_OPT), row=1, col=2)
    
    # Contra%
    fig.add_trace(go.Bar(name='IS', x=horizons,
        y=[r['is_contra'] for r in results], marker_color=C_CONTRA), row=2, col=1)
    fig.add_trace(go.Bar(name='OOS', x=horizons,
        y=[r['oos_contra'] for r in results], marker_color=C_OPT), row=2, col=1)
    
    # OOS trades
    fig.add_trace(go.Bar(name='Long', x=horizons,
        y=[r['oos_n_long'] for r in results], marker_color=C_LONG), row=2, col=2)
    fig.add_trace(go.Bar(name='Short', x=horizons,
        y=[r['oos_n_short'] for r in results], marker_color=C_SHORT), row=2, col=2)
    
    fig.update_layout(barmode='group', template='plotly_dark', height=800,
        title_text='OOS Exam — Scalper Copilot v6.2',
        paper_bgcolor=BG, plot_bgcolor=BG, font=dict(color=TC))
    p = output_dir / 'oos_exam_dashboard.html'
    fig.write_html(str(p))
    print(f"📊 Chart: {p.name}")

if __name__ == '__main__':
    ts_total = datetime.now()
    train_path = DATA_DIR / 'BTCUSD_training_tick.csv'
    exam_path = EXAM_DIR / 'BTCUSD_exam_tick.csv'
    
    # Optuna best params betöltése (ha van)
    optuna_file = CHART_DIR / 'optuna_best_params.json'
    optuna_all = {}
    if optuna_file.exists():
        optuna_all = json.loads(optuna_file.read_text())
        print(f"  🏆 Optuna best params betöltve: {list(optuna_all.keys())}")
    else:
        print("  ⚠️ Nincs Optuna best params — baseline paraméterek")
    
    all_results = []
    for hsec in HORIZON_SEC:
        hn = HORIZON_NAMES[hsec]
        op = optuna_all.get(hn, {}).get('params') if optuna_all else None
        r = run_oos_exam(train_path, exam_path, hsec, hn, optuna_params=op)
        all_results.append(r)
    
    make_oos_chart(all_results, CHART_DIR)
    
    el = (datetime.now() - ts_total).total_seconds()
    print(f"\n{'='*72}")
    print(f"OOS EXAM KÉSZ — {el:.0f}s")
    for r in all_results:
        print(f"  {r['horizon']}: OOS WR={r['oos_wr']:.1%} contra={r['oos_contra']:.1%} "
              f"(IS WR={r['is_wr']:.1%} contra={r['is_contra']:.1%})")
    print(f"{'='*72}")