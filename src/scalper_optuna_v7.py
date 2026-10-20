#!/usr/bin/env python3
"""
Scalper Copilot v7 — Optuna CONSTRAINED + PRUNING
  v6 tanulság: multi-obj overfit (IS 13% OOS 33%)
  ÚJ: single-obj (max AUC) + constraint (contra<=20%)
  ÚJ: LightGBMPruningCallback + MedianPruner
  ÚJ: GPSampler (Bayesian) ha elérhető
  PT/SL FIX (0.5/0.3) — csak LGB hyper + regime optimalizálva
"""
import os, sys, time, json, warnings
import numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime
warnings.filterwarnings('ignore')

import optuna
from optuna.samplers import TPESampler
try:
    from optuna.samplers import GPSampler
    HAS_GP = True
except ImportError:
    HAS_GP = False
from optuna.pruners import MedianPruner
from optuna_integration.lightgbm import LightGBMPruningCallback
import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import roc_auc_score
import plotly.graph_objects as go
import plotly.subplots as sp

sys.path.insert(0, str(Path(__file__).parent))
from scalper_copilot_v6 import (
    load_ticks, make_dollar_bars, build_features, label_tbm,
    cusum_filter, regime_filter,
    DATA_DIR, MODEL_DIR, CHART_DIR, DOLLAR_THR, HORIZON_SEC, HORIZON_NAMES,
    PROFIT_MULT, STOP_MULT, SEED
)

N_TRIALS = 80
N_FOLD = 5
CONTRA_TARGET = 0.20
FIX_PT = PROFIT_MULT
FIX_SL = STOP_MULT
CHART_DIR.mkdir(parents=True, exist_ok=True)

SHAP_TOP = [
    'ema_d_60','vol_ma_20','vol_ma_5','mean_rev','ema_cross',
    'ema_d_30','ema_s_60','rsi_28','boll_pos','upper_wick',
    'ema_d_5','ema_s_30','micro_trend','mom_persistence','ema_d_10',
    'ret_1','ret_3','rv_10','variance_ratio','bar_dt_rel',
    'hour_sin','hour_cos','dir_x_mom','price_accel','ret_x_atr'
]

BG='rgb(17,17,17)'; TC='#f2f5fa'
optuna.logging.set_verbosity(optuna.logging.WARNING)

print('='*72)
print(f'SCALPER v7 — OPTUNA CONSTRAINED+PRUNING | N={N_TRIALS} | contra<={CONTRA_TARGET:.0%} | PT={FIX_PT} SL={FIX_SL}')
print(f'  Sampler={"GPSampler" if HAS_GP else "TPESampler"} | Pruner=Median+LGB')
print('='*72)

# ── HELPERS ──
def prepare_data(train_path):
    ticks = load_ticks(train_path, 'TRAIN')
    bars = make_dollar_bars(ticks, DOLLAR_THR)
    feat_df, feat_cols = build_features(bars)
    return bars, feat_df, feat_cols

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

_tbm_cache = {}
def label_cached(bars, hsec, pt_m, sl_m):
    key = (hsec, round(pt_m,2), round(sl_m,2))
    if key not in _tbm_cache: _tbm_cache[key] = label_tbm(bars, hsec, pt_m, sl_m)
    return _tbm_cache[key]

# ═══════════════════════════════════════════════════════════════
# CONSTRAINED OBJECTIVE: max AUC + constraint(contra <= 20%)
# ═══════════════════════════════════════════════════════════════
def create_objective(bars, feat_df, feat_cols, horizon_sec, horizon_name):
    def objective(trial):
        # LGB hiperek
        lr = trial.suggest_float('lr', 0.01, 0.10, log=True)
        num_leaves = trial.suggest_int('num_leaves', 15, 63)
        feat_frac = trial.suggest_float('feat_frac', 0.5, 0.9)
        l1 = trial.suggest_float('l1', 0.5, 5.0)
        min_data = trial.suggest_int('min_data', 30, 100)
        bagging_frac = trial.suggest_float('bagging_frac', 0.6, 1.0)
        l2 = trial.suggest_float('l2', 1e-3, 5.0, log=True)
        # Regime küszöbök
        cusum_mult = trial.suggest_float('cusum_mult', 0.3, 1.0)
        h_thr = trial.suggest_float('h_thr', 0.45, 0.60)
        ts_thr = trial.suggest_float('ts_thr', 1.5, 5.0)
        ts_elev = trial.suggest_float('ts_elev', 0.8, 2.5)
        elev_amt = trial.suggest_float('elev_amt', 0.04, 0.15)
        
        # SHAP feature szűrés
        avail = [f for f in SHAP_TOP if f in feat_cols]
        if len(avail) < 10: avail = list(feat_cols)
        fa = feat_df[avail]
        
        # TBM (FIX PT/SL)
        y_long, y_short = label_cached(bars, horizon_sec, FIX_PT, FIX_SL)
        idx = fa.index.intersection(bars.index[:len(y_long)])
        fa_idx = fa.loc[idx]
        yl = pd.Series(y_long[:len(bars)], index=bars.index[:len(y_long)]).loc[idx]
        ys = pd.Series(y_short[:len(bars)], index=bars.index[:len(y_short)]).loc[idx]
        ev, _ = cusum_custom(bars['ret'].loc[idx].fillna(0), cusum_mult)
        if len(ev) < 100: return -1.0  # invalid
        fc = fa_idx.iloc[ev]
        ylc = (yl.iloc[ev]==1).astype(int)
        ysc = (ys.iloc[ev]==1).astype(int)
        
        # Regime custom
        rg = regime_custom(bars, feat_df, h_thr, ts_thr)
        
        # TRAIN with PRUNING
        metrics = {}
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
                prune_cb = LightGBMPruningCallback(trial, 'auc')
                m = lgb.train(p, dtr, 300, [dva],
                    callbacks=[lgb.early_stopping(30,verbose=False), prune_cb])
                auc = roc_auc_score(y_c.iloc[va], m.predict(fc.iloc[va]))
                aucs.append(auc); models.append(m)
            metrics[f'auc_{side}'] = np.mean(aucs)
            metrics[f'model_{side}'] = models[-1]
        
        # Signal + regime filter
        pL = metrics['model_long'].predict(fa_idx)
        pS = metrics['model_short'].predict(fa_idx)
        tL = np.mean(pL[ev])+0.5*np.std(pL[ev])
        tS = np.mean(pS[ev])+0.5*np.std(pS[ev])
        sig = np.zeros(len(fa_idx)); sig[pL>tL]=1; sig[pS>tS]=-1
        b=(pL>tL)&(pS>tS); sig[b&(pL>=pS)]=1; sig[b&(pS>pL)]=-1
        
        rv=rg['regime'].loc[fa_idx.index].values
        td=rg['trend_dir'].loc[fa_idx.index].values
        ts_=rg['trend_str'].loc[fa_idx.index].values
        for i in range(len(sig)):
            if sig[i]==0: continue
            ic=(sig[i]==-1 and td[i]>0) or (sig[i]==1 and td[i]<0)
            if ic and rv[i]=='trending': sig[i]=0
            elif ic and ts_[i]>ts_elev:
                if sig[i]==1 and pL[i]<tL+elev_amt: sig[i]=0
                elif sig[i]==-1 and pS[i]<tS+elev_amt: sig[i]=0
        
        # Contra%
        n_sig = (sig!=0).sum()
        cm = np.zeros(len(sig),dtype=bool)
        cm[(sig==1)&(td<0)]=True; cm[(sig==-1)&(td>0)]=True
        contra_pct = cm.sum()/max(1,n_sig)
        
        # CONSTRAINT: contra% <= CONTRA_TARGET
        trial.set_constraint('contra', contra_pct - CONTRA_TARGET)
        
        # WR
        yla=yl.values[:len(sig)]; ysa=ys.values[:len(sig)]
        tp=((sig==1)&(yla==1)).sum()+((sig==-1)&(ysa==1)).sum()
        sl=((sig==1)&(yla==-1)).sum()+((sig==-1)&(ysa==-1)).sum()
        wr=tp/max(1,tp+sl)
        metrics.update({'contra_pct':contra_pct,'win_rate':wr,'n_signal':n_sig})
        
        # Cél: max mean AUC
        return (metrics['auc_long'] + metrics['auc_short']) / 2
    return objective

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    ts_total = datetime.now()
    train_path = DATA_DIR / 'BTCUSD_training_tick.csv'
    bars, feat_df, feat_cols = prepare_data(train_path)
    
    best_params_all = {}
    
    for hsec in HORIZON_SEC:
        hn = HORIZON_NAMES[hsec]
        print(f"\n{'═'*50}\nOPTUNA v7: {hn} ({hsec}s) — {N_TRIALS} trials\n{'═'*50}")
        
        # Sampler: TPESampler (GPSampler NEM támogat constraint!)
        sampler = TPESampler(seed=SEED)
        
        # Pruner: MedianPruner (early stop rossz trial)
        pruner = MedianPruner(n_startup_trials=5, n_warmup_steps=10, interval_steps=1)
        
        study = optuna.create_study(
            direction='maximize',  # SINGLE objective: max AUC
            sampler=sampler,
            pruner=pruner,
            study_name=f'scalper_v7_{hn}'
        )
        
        objective = create_objective(bars, feat_df, feat_cols, hsec, hn)
        study.optimize(objective, n_trials=N_TRIALS, show_progress_bar=False)
        
        # Best feasible trial (constraint satisfied)
        feasible = [t for t in study.trials 
                    if t.state == optuna.trial.TrialState.COMPLETE
                    and len(t.constraints) > 0
                    and all(v <= 0 for v in t.constraints.values())]
        if feasible:
            best = max(feasible, key=lambda t: t.value)
            print(f"\n  🏆 Best FEASIBLE trial: {best.number}")
            print(f"     AUC: {best.value:.4f}")
            for k, v in best.params.items():
                print(f"     {k}: {v:.4f}" if isinstance(v,float) else f"     {k}: {v}")
            if best.constraints:
                for ck, cv in best.constraints.items():
                    print(f"     constraint {ck}: {cv:.4f} ({'✅ feasible' if cv<=0 else '❌ violated'})")
            best_params_all[hn] = {'params': best.params, 'auc': best.value, 
                                   'constraints': dict(best.constraints)}
        else:
            # Fallback: best infeasible (closest to feasible)
            all_complete = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
            if all_complete:
                best = min(all_complete, key=lambda t: max(t.constraints.values()) if t.constraints else 999)
                print(f"\n  ⚠️ No feasible trial! Best infeasible: {best.number}")
                if best.constraints:
                    for ck, cv in best.constraints.items():
                        print(f"     constraint {ck}: {cv:.4f}")
                best_params_all[hn] = {'params': best.params, 'auc': best.value,
                                       'constraints': dict(best.constraints)}
    
    # Save best params
    bp_path = CHART_DIR / 'optuna_v7_best_params.json'
    bp_path.write_text(json.dumps(best_params_all, indent=2, default=str))
    print(f"\n💾 Best params: {bp_path}")
    
    el = (datetime.now() - ts_total).total_seconds()
    print(f"\n{'='*72}")
    print(f"OPTUNA v7 KÉSZ — {el:.0f}s")
    for hn, bp in best_params_all.items():
        c = bp.get('constraints', {})
        cs = f"contra={c.get('contra',0):.1%}" if c else "?"
        print(f"  {hn}: AUC={bp['auc']:.4f} {cs}")
    print(f"{'='*72}")
