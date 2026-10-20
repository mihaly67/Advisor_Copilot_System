#!/usr/bin/env python3
"""
Scalper Copilot v6 — Optuna Hiperopt
  - SHAP eredmények alapján fix top-N feature
  - Cél: contra% < 20% minden horizontnál, max EV/Sharpe
  - Paraméterek: PT, SL, CUSUM thr, regime küszöb (H, trend_str),
    L1 lambda, num_leaves, feature_fraction, learning_rate
  - Sampler: TPESampler (Tree-structured Parzen Estimator)
  - Multi-objective: contra% és EV egyszerre

Logikus sorrend: SHAP ✅ → Optuna → OOS exam
"""
import os, sys, time, warnings
import numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime
warnings.filterwarnings('ignore')

import optuna
from optuna.samplers import TPESampler
import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import roc_auc_score
import plotly.graph_objects as go
import plotly.subplots as sp

# ─── IMPORT v6 PIPELINE ───
sys.path.insert(0, str(Path(__file__).parent))
from scalper_copilot_v6 import (
    load_ticks, make_dollar_bars, build_features, label_tbm,
    cusum_filter, regime_filter,
    DATA_DIR, MODEL_DIR, CHART_DIR, DOLLAR_THR, HORIZON_SEC, HORIZON_NAMES,
    SEED
)

# ─── KONFIG ───
N_TRIALS = 40         # Optuna trial szám (csökkentve: TBM labeling lassú)
N_FOLD = 5
CONTRA_TARGET = 0.20  # cél: contra% < 20%
CHART_DIR.mkdir(parents=True, exist_ok=True)

# SHAP alapján top feature-ok (fixálva)
SHAP_TOP_FEATURES = [
    'ema_d_60', 'vol_ma_20', 'vol_ma_5', 'mean_rev', 'ema_cross',
    'ema_d_30', 'ema_s_60', 'rsi_28', 'boll_pos', 'upper_wick',
    'ema_d_5', 'ema_s_30', 'micro_trend', 'mom_persistence', 'ema_d_10',
    'ret_1', 'ret_3', 'rv_10', 'variance_ratio', 'bar_dt_rel',
    'hour_sin', 'hour_cos', 'dir_x_mom', 'price_accel', 'ret_x_atr'
]

# Színek
BG='rgb(17,17,17)'; GC='#283442'; TC='#f2f5fa'
C_LONG='#26a69a'; C_SHORT='#ef5350'; C_CONTRA='#FF6B35'; C_NOISE='#888888'
C_OPT='#00d2ff'; C_PARETO='#FFC107'

optuna.logging.set_verbosity(optuna.logging.WARNING)

print("=" * 72)
print("SCALPER COPILOT v6 — OPTUNA HIPEROPT")
print(f"  N_TRIALS={N_TRIALS} | CONTRA_TARGET={CONTRA_TARGET:.0%}")
print("=" * 72)

def prepare_data(train_path):
    ticks = load_ticks(train_path, 'TRAIN')
    bars = make_dollar_bars(ticks, DOLLAR_THR)
    feat_df, feat_cols = build_features(bars)
    regime = regime_filter(bars, feat_df)
    return bars, feat_df, feat_cols, regime

def cusum_filter_custom(ret, thr_mult=0.5):
    thr = ret.std() * thr_mult
    s_pos=0; s_neg=0; events=[]
    for i, r in enumerate(ret):
        s_pos = max(0, s_pos+r-thr); s_neg = min(0, s_neg+r+thr)
        if s_pos>thr or s_neg<-thr: events.append(i); s_pos=0; s_neg=0
    return events, thr

def regime_filter_custom(bars, feat_df, h_thr=0.50, trend_str_thr=3.0, trend_str_elev=1.5):
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

# ── TBM LABEL CACHE ──
_tbm_cache = {}

def label_tbm_cached(bars, horizon_sec, pt_m, sl_m):
    """TBM labeling with cache — diszkretizált PT/SL (2 tizedes)."""
    key = (horizon_sec, round(pt_m, 2), round(sl_m, 2))
    if key not in _tbm_cache:
        _tbm_cache[key] = label_tbm(bars, horizon_sec, pt_m, sl_m)
    return _tbm_cache[key]

def train_and_evaluate(bars, feat_df, feat_cols, regime, horizon_sec,
                       pt_m, sl_m, cusum_mult,
                       h_thr, trend_str_thr, trend_str_elev, elev_amt,
                       lr, num_leaves, feat_frac, l1, min_data,
                       use_shap_features=True):
    if use_shap_features:
        available = [f for f in SHAP_TOP_FEATURES if f in feat_cols]
        if len(available) < 10: available = feat_cols
        fa = feat_df[available]
    else:
        fa = feat_df; available = feat_cols
    
    y_long, y_short = label_tbm_cached(bars, horizon_sec, pt_m, sl_m)
    idx = fa.index.intersection(bars.index[:len(y_long)])
    fa_idx = fa.loc[idx]
    yl = pd.Series(y_long[:len(bars)], index=bars.index[:len(y_long)]).loc[idx]
    ys = pd.Series(y_short[:len(bars)], index=bars.index[:len(y_short)]).loc[idx]
    
    ev, cthr = cusum_filter_custom(bars['ret'].loc[idx].fillna(0), cusum_mult)
    if len(ev) < 100: return None
    
    fc = fa_idx.iloc[ev]
    ylc = (yl.iloc[ev] == 1).astype(int)
    ysc = (ys.iloc[ev] == 1).astype(int)
    regime_custom = regime_filter_custom(bars, feat_df, h_thr, trend_str_thr, trend_str_elev)
    
    metrics = {}
    for side, y_c in [('long', ylc), ('short', ysc)]:
        tscv = TimeSeriesSplit(n_splits=N_FOLD)
        aucs = []; models = []
        for fold, (tr, va) in enumerate(tscv.split(fc)):
            dtr = lgb.Dataset(fc.iloc[tr], label=y_c.iloc[tr])
            dva = lgb.Dataset(fc.iloc[va], label=y_c.iloc[va], reference=dtr)
            p = {'objective':'binary','metric':'auc','learning_rate':lr,
                 'num_leaves':num_leaves,'feature_fraction':feat_frac,
                 'bagging_fraction':0.8,'bagging_freq':5,'seed':SEED,'verbose':-1,
                 'min_data_in_leaf':min_data,'lambda_l1':l1}
            m = lgb.train(p, dtr, 300, [dva], callbacks=[lgb.early_stopping(30,verbose=False)])
            auc = roc_auc_score(y_c.iloc[va], m.predict(fc.iloc[va]))
            aucs.append(auc); models.append(m)
        metrics[f'auc_{side}'] = np.mean(aucs)
        metrics[f'model_{side}'] = models[-1]
    
    pL = metrics['model_long'].predict(fa_idx)
    pS = metrics['model_short'].predict(fa_idx)
    tL = np.mean(pL[ev]) + 0.5*np.std(pL[ev])
    tS = np.mean(pS[ev]) + 0.5*np.std(pS[ev])
    
    sig = np.zeros(len(fa_idx))
    sig[pL>tL] = 1; sig[pS>tS] = -1
    both = (pL>tL)&(pS>tS)
    sig[both&(pL>=pS)] = 1; sig[both&(pS>pL)] = -1
    
    regime_vals = regime_custom['regime'].loc[fa_idx.index].values
    trend_dir_vals = regime_custom['trend_dir'].loc[fa_idx.index].values
    trend_str_vals = regime_custom['trend_str'].loc[fa_idx.index].values
    
    for i in range(len(sig)):
        if sig[i]==0: continue
        is_trending = regime_vals[i]=='trending'
        is_contra = False
        if sig[i]==-1 and trend_dir_vals[i]>0: is_contra=True
        if sig[i]==1 and trend_dir_vals[i]<0: is_contra=True
        if is_contra and is_trending: sig[i]=0
        elif is_contra and trend_str_vals[i]>trend_str_elev:
            if sig[i]==1 and pL[i]<tL+elev_amt: sig[i]=0
            elif sig[i]==-1 and pS[i]<tS+elev_amt: sig[i]=0
    
    n_long = (sig==1).sum(); n_short = (sig==-1).sum()
    n_signal = n_long + n_short
    contra_mask = np.zeros(len(sig), dtype=bool)
    contra_mask[(sig==1)&(trend_dir_vals<0)] = True
    contra_mask[(sig==-1)&(trend_dir_vals>0)] = True
    contra_pct = contra_mask.sum() / max(1, n_signal)
    
    yl_arr = yl.values[:len(sig)]; ys_arr = ys.values[:len(sig)]
    long_tp = ((sig==1)&(yl_arr==1)).sum(); long_sl = ((sig==1)&(yl_arr==-1)).sum()
    short_tp = ((sig==-1)&(ys_arr==1)).sum(); short_sl = ((sig==-1)&(ys_arr==-1)).sum()
    total_ev = (long_tp*pt_m - long_sl*sl_m + short_tp*pt_m - short_sl*sl_m) / max(1, n_signal)
    wr = (long_tp+short_tp) / max(1, long_tp+short_sl+short_tp+long_sl)
    
    metrics.update({
        'n_long':n_long, 'n_short':n_short, 'n_signal':n_signal,
        'contra_pct':contra_pct, 'total_ev':total_ev, 'win_rate':wr,
        'pt_m':pt_m, 'sl_m':sl_m,
        'long_tp':long_tp, 'long_sl':long_sl, 'short_tp':short_tp, 'short_sl':short_sl
    })
    return metrics

# ═══════════════════════════════════════════════════════════════
# 5. OPTUNA OBJECTIVE
# ═══════════════════════════════════════════════════════════════
def create_objective(bars, feat_df, feat_cols, regime, horizon_sec, horizon_name):
    def objective(trial):
        # TBM paraméterek (diszkretizálva 2 tizedesre a cache-hez)
        pt_m = round(trial.suggest_float('pt_m', 0.3, 1.0), 2)
        sl_m = round(trial.suggest_float('sl_m', 0.2, 0.6), 2)
        cusum_mult = trial.suggest_float('cusum_mult', 0.3, 1.0)
        
        # Regime küszöbök
        h_thr = trial.suggest_float('h_thr', 0.45, 0.60)
        trend_str_thr = trial.suggest_float('trend_str_thr', 1.5, 5.0)
        trend_str_elev = trial.suggest_float('trend_str_elev', 0.8, 2.5)
        elev_amt = trial.suggest_float('elev_amt', 0.04, 0.15)
        
        # LightGBM hypererek
        lr = trial.suggest_float('lr', 0.01, 0.10, log=True)
        num_leaves = trial.suggest_int('num_leaves', 15, 63)
        feat_frac = trial.suggest_float('feat_frac', 0.5, 0.9)
        l1 = trial.suggest_float('l1', 0.5, 3.0)
        min_data = trial.suggest_int('min_data', 30, 100)
        
        m = train_and_evaluate(
            bars, feat_df, feat_cols, regime, horizon_sec,
            pt_m, sl_m, cusum_mult,
            h_thr, trend_str_thr, trend_str_elev, elev_amt,
            lr, num_leaves, feat_frac, l1, min_data,
            use_shap_features=True
        )
        
        if m is None:
            return -1.0, 1.0  # invalid trial
        
        # Multi-objective: max EV, min contra%
        # Penalizáljuk a contra%-ot ha > target
        contra_penalty = max(0, m['contra_pct'] - CONTRA_TARGET) * 10
        ev_score = m['total_ev'] - contra_penalty
        
        return ev_score, m['contra_pct']
    
    return objective

# ═══════════════════════════════════════════════════════════════
# 6. CHARTOK
# ═══════════════════════════════════════════════════════════════
def make_optuna_charts(study, horizon_name, output_dir):
    trials = study.trials
    df = study.trials_dataframe()
    if len(df) == 0: return
    
    # 1. Optimization history
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=list(range(len(df))), y=df['values_0'],
        mode='lines+markers', name='EV score',
        line=dict(color=C_OPT)
    ))
    fig1.update_layout(
        title_text=f'Optuna History — {horizon_name}',
        template='plotly_dark', height=400,
        paper_bgcolor=BG, plot_bgcolor=BG, font=dict(color=TC))
    fig1.write_html(str(output_dir / f'optuna_history_{horizon_name}.html'))
    
    # 2. Param importance
    try:
        importance = optuna.importance.get_param_importances(study, target=lambda t: t.values[0])
        fig2 = go.Figure(go.Bar(
            x=list(importance.values()), y=list(importance.keys()),
            orientation='h', marker_color=C_PARETO
        ))
        fig2.update_layout(
            title_text=f'Param Importance — {horizon_name}',
            template='plotly_dark', height=500,
            paper_bgcolor=BG, plot_bgcolor=BG, font=dict(color=TC))
        fig2.write_html(str(output_dir / f'optuna_importance_{horizon_name}.html'))
    except Exception:
        pass
    
    # 3. Pareto front (EV vs contra%)
    fig3 = go.Figure()
    ev_vals = df['values_0'].values
    contra_vals = df['values_1'].values
    colors = [C_LONG if c < CONTRA_TARGET else C_CONTRA for c in contra_vals]
    fig3.add_trace(go.Scatter(
        x=contra_vals, y=ev_vals, mode='markers',
        marker=dict(color=colors, size=8, opacity=0.7),
        text=[f'Trial {i}' for i in range(len(df))],
        name='Trials'
    ))
    fig3.add_vline(x=CONTRA_TARGET, line_dash='dash', line_color=C_PARETO,
                   annotation_text=f'target {CONTRA_TARGET:.0%}')
    fig3.update_layout(
        title_text=f'Pareto Front: EV vs Contra% — {horizon_name}',
        template='plotly_dark', height=500,
        xaxis_title='Contra %', yaxis_title='EV Score',
        paper_bgcolor=BG, plot_bgcolor=BG, font=dict(color=TC))
    fig3.write_html(str(output_dir / f'optuna_pareto_{horizon_name}.html'))
    print(f"    Charts saved: optuna_{{history,importance,pareto}}_{horizon_name}.html")

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    ts_total = datetime.now()
    
    # 1. Adat
    train_path = DATA_DIR / 'BTCUSD_training_tick.csv'
    bars, feat_df, feat_cols, regime = prepare_data(train_path)
    
    # 2. Optuna per horizon
    best_params_all = {}
    
    for hsec in HORIZON_SEC:
        hn = HORIZON_NAMES[hsec]
        print(f"\n{'═'*50}\nOPTUNA: {hn} ({hsec}s) — {N_TRIALS} trials\n{'═'*50}")
        
        sampler = TPESampler(seed=SEED)
        study = optuna.create_study(
            directions=['maximize', 'minimize'],  # max EV, min contra%
            sampler=sampler,
            study_name=f'scalper_v6_{hn}'
        )
        
        objective = create_objective(bars, feat_df, feat_cols, regime, hsec, hn)
        study.optimize(objective, n_trials=N_TRIALS, show_progress_bar=False)
        
        # Best trial (legnagyobb EV score)
        best = study.best_trials[0] if study.best_trials else None
        if best:
            print(f"\n  🏆 Best trial: {best.number}")
            print(f"     EV score: {best.values[0]:.4f}")
            print(f"     Contra%: {best.values[1]:.1%}")
            for k, v in best.params.items():
                print(f"     {k}: {v:.4f}" if isinstance(v, float) else f"     {k}: {v}")
            best_params_all[hn] = {'params': best.params, 'ev': best.values[0], 'contra': best.values[1]}
        
        # Charts
        make_optuna_charts(study, hn, CHART_DIR)
    
    # 3. Összesítő
    el = (datetime.now() - ts_total).total_seconds()
    print(f"\n{'='*72}")
    print(f"OPTUNA HIPEROPT KÉSZ — {el:.0f}s")
    for hn, bp in best_params_all.items():
        print(f"  {hn}: EV={bp['ev']:.4f} contra={bp['contra']:.1%}")
    
    # Best params mentés
    import json
    params_path = CHART_DIR / 'optuna_best_params.json'
    with open(params_path, 'w') as f:
        json.dump(best_params_all, f, indent=2, default=str)
    print(f"  Best params: {params_path.name}")
    print(f"{'='*72}")
    print(f"\n➡️ KÖVETKEZŐ: OOS exam (scalper_oos_v6.py)")