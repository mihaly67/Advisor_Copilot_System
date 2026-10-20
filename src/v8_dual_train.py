#!/usr/bin/env python3
"""
V8 Dual-Binary Train — Ket fuggetlen binaris modell (Lopez de Prado)
  Modell_Long:  P(Long TP)  vs (Short+Noise) — binary objective
  Modell_Short: P(Short TP) vs (Long+Noise)  — binary objective

Elony a multiclass-sal szemben:
  - Nincs softmax constraint (sum=1) -> P(L) es P(S) fuggetlenul kalibralhato
  - K kulonbozo threshold allithato -> nincs Long-bias a softmax miatt
  - AUC CV metrika helyes (binaris)
  - Ha mindketto alacsony -> Noise (alapbol tobb signal)
"""
import sys, warnings, time, json
warnings.filterwarnings('ignore')
sys.path.insert(0, '/data/LGBM_copilot/src')
import numpy as np, pandas as pd
import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import roc_auc_score
from pathlib import Path
from scalper_copilot_v6 import load_ticks, make_dollar_bars, DATA_DIR, EXAM_DIR, DOLLAR_THR, SEED
from build_features_v8 import build_features_v8, FEATURES_V8_PRUNED
from v8_labeler import label_strict_wick

MDIR = Path('/data/LGBM_copilot/models/scalper'); MDIR.mkdir(exist_ok=True)
KEEP = [f for f in FEATURES_V8_PRUNED if f not in ('kill_zone', 'ema_d_5')]
HORIZONS = [(60,'1min'),(120,'2min'),(180,'3min'),(240,'4min'),(300,'5min')]
PT_M = 0.5; SL_M = 0.3; BURN_IN = 0.1

t0 = time.time()
print('='*72)
print('V8 DUAL-BINARY TRAIN — Long + Short fuggetlen modell (Jules V5 label)')
print('='*72)
print('Features: %d, PT=%.1fxATR SL=%.1fxATR' % (len(KEEP), PT_M, SL_M))

# 1. LOAD TRAIN
print('\n1. Loading TRAIN...', flush=True)
ticks_tr = load_ticks(str(DATA_DIR / 'BTCUSD_training_tick.csv'))
bars_tr = make_dollar_bars(ticks_tr, DOLLAR_THR)
feat_tr, cols_tr = build_features_v8(bars_tr)
avail = [c for c in KEEP if c in cols_tr]
feat_tr = feat_tr[avail]
bars_tr_al = bars_tr.loc[feat_tr.index]
print('   Train: %d bars, %d features [%.0fs]' % (len(feat_tr), len(avail), time.time()-t0))

# 2. LOAD EXAM
print('\n2. Loading EXAM...', flush=True)
ticks_ex = load_ticks(str(EXAM_DIR / 'BTCUSD_exam_tick.csv'), label='EXAM')
bars_ex = make_dollar_bars(ticks_ex, DOLLAR_THR)
feat_ex, cols_ex = build_features_v8(bars_ex)
feat_ex = feat_ex[[c for c in avail if c in cols_ex]]
bars_ex_al = bars_ex.loc[feat_ex.index]
print('   Exam: %d bars [%.0fs]' % (len(feat_ex), time.time()-t0))

# 3. LIGHTGBM PARAMS (binaris)
LP = {'objective':'binary','metric':'auc',
      'learning_rate':0.05,'num_leaves':31,'feature_fraction':0.7,
      'bagging_fraction':0.8,'bagging_freq':5,'seed':SEED,'verbose':-1,
      'min_data_in_leaf':50,'lambda_l1':1.0,'num_threads':4}

results = {}
for hsec, hname in HORIZONS:
    print('\n--- %s (%ds) DUAL-BINARY ---' % (hname, hsec), flush=True)
    # Jules V5 label
    y3 = label_strict_wick(bars_tr_al, pt_m=PT_M, sl_m=SL_M, horizon_sec=hsec)
    # Binaris cimkek
    y_long = (y3 == 2).astype(int)   # P(Long TP) vs (Short+Noise)
    y_short = (y3 == 1).astype(int)  # P(Short TP) vs (Long+Noise)
    nT = len(y3)
    nL = int(y_long.sum()); nS = int(y_short.sum()); nN = nT - nL - nS
    print('   Label: L=%d (%.1f%%) S=%d (%.1f%%) N=%d (%.1f%%)' %
          (nL, 100*nL/nT, nS, 100*nS/nT, nN, 100*nN/nT))
    
    X_all = feat_tr.values; s = int(nT*BURN_IN)
    X_t = X_all[s:]; yl_t = y_long[s:]; ys_t = y_short[s:]
    tscv = TimeSeriesSplit(n_splits=3)
    
    # --- MODELL LONG ---
    print('   [LONG] training...', flush=True)
    cv_auc_l = []; cv_pl = []; all_pL = None; fi_l = None
    for fold, (tr, va) in enumerate(tscv.split(X_t)):
        dtr = lgb.Dataset(X_t[tr], label=yl_t[tr], feature_name=avail)
        dva = lgb.Dataset(X_t[va], label=yl_t[va], feature_name=avail, reference=dtr)
        m = lgb.train(LP, dtr, 200, [dva], callbacks=[lgb.early_stopping(20, verbose=False)])
        pv = m.predict(X_t[va])
        auc = roc_auc_score(yl_t[va], pv)
        cv_auc_l.append(auc); cv_pl.append(pv.mean())
        if all_pL is None: all_pL = pv
        else: all_pL = np.concatenate([all_pL, pv])
        if fi_l is None: fi_l = m.feature_importance('gain')
        else: fi_l = fi_l + m.feature_importance('gain')
        print('     L Fold %d: AUC=%.4f avg_P(L)=%.3f' % (fold+1, auc, pv.mean()))
    # Final model: train on all
    dall_l = lgb.Dataset(X_t, label=yl_t, feature_name=avail)
    bst_l = lgb.train(LP, dall_l, 100)
    bst_l.save_model(str(MDIR/f'v8_long_{hname}.txt'))
    
    # --- MODELL SHORT ---
    print('   [SHORT] training...', flush=True)
    cv_auc_s = []; cv_ps = []; all_pS = None; fi_s = None
    for fold, (tr, va) in enumerate(tscv.split(X_t)):
        dtr = lgb.Dataset(X_t[tr], label=ys_t[tr], feature_name=avail)
        dva = lgb.Dataset(X_t[va], label=ys_t[va], feature_name=avail, reference=dtr)
        m = lgb.train(LP, dtr, 200, [dva], callbacks=[lgb.early_stopping(20, verbose=False)])
        pv = m.predict(X_t[va])
        auc = roc_auc_score(ys_t[va], pv)
        cv_auc_s.append(auc); cv_ps.append(pv.mean())
        if all_pS is None: all_pS = pv
        else: all_pS = np.concatenate([all_pS, pv])
        if fi_s is None: fi_s = m.feature_importance('gain')
        else: fi_s = fi_s + m.feature_importance('gain')
        print('     S Fold %d: AUC=%.4f avg_P(S)=%.3f' % (fold+1, auc, pv.mean()))
    dall_s = lgb.Dataset(X_t, label=ys_t, feature_name=avail)
    bst_s = lgb.train(LP, dall_s, 100)
    bst_s.save_model(str(MDIR/f'v8_short_{hname}.txt'))
    
    # --- DUAL PREDIKCIO EXAM ---
    X_ex = feat_ex[avail].values
    pL_ex = bst_l.predict(X_ex)
    pS_ex = bst_s.predict(X_ex)
    
    # --- LONG-BIAS ELLENORZES ---
    avg_pL = float(pL_ex.mean()); avg_pS = float(pS_ex.mean())
    # Threshold count: mindketto fuggetlen
    th = 0.5
    nL_th = int((pL_ex>=th).sum()); nS_th = int((pS_ex>=th).sum())
    bias_ratio = nL_th / max(1, nS_th)
    bias_status = 'OK' if 0.5 <= bias_ratio <= 2.0 else 'LONG-BIAS!' if bias_ratio > 2 else 'SHORT-BIAS!'
    print('   CV: Long AUC=%.4f +/- %.4f | Short AUC=%.4f +/- %.4f' %
          (np.mean(cv_auc_l), np.std(cv_auc_l), np.mean(cv_auc_s), np.std(cv_auc_s)))
    print('   CV avg: P(L)=%.3f P(S)=%.3f (label base: L=%.3f S=%.3f)' %
          (np.mean(all_pL), np.mean(all_pS), nL/nT, nS/nT))
    print('   OOS avg: P(L)=%.3f P(S)=%.3f | th=0.5: Long=%d Short=%d | L/S=%.2f %s' %
          (avg_pL, avg_pS, nL_th, nS_th, bias_ratio, bias_status))
    
    # Save predictions for chart
    preds = pd.DataFrame({
        'p_long': pL_ex, 'p_short': pS_ex,
        'p_long_calibrated': pL_ex,  # placeholder, calibrated later if needed
        'p_short_calibrated': pS_ex,
    }, index=feat_ex.index)
    preds.to_csv(str(MDIR/f'v8_dual_{hname}_preds.csv'))
    
    results[hname] = {
        'cv_auc_long': float(np.mean(cv_auc_l)),
        'cv_auc_short': float(np.mean(cv_auc_s)),
        'avg_pL': avg_pL, 'avg_pS': avg_pS,
        'nL_th': nL_th, 'nS_th': nS_th,
        'bias_ratio': float(bias_ratio),
        'bias_status': bias_status,
        'nL_label': nL, 'nS_label': nS, 'nN_label': nN,
    }
    print('   [%ds elapsed]' % int(time.time()-t0))

# 4. FEATURE IMPORTANCE (osszeg)
print('\n' + '='*60)
print('  OSSZEGFOGALO — DUAL-BINARY')
print('='*60)
print('  %s | %s | %s | %s | %s | %s | %s' %
      ('Horizon'.ljust(8), 'AUC_L'.ljust(7), 'AUC_S'.ljust(7),
       'P(L)'.ljust(6), 'P(S)'.ljust(6), 'L_th'.ljust(5), 'S_th'.ljust(5)))
for h, r in results.items():
    print('  %s | %.4f | %.4f | %.3f | %.3f | %d | %d | %s' %
          (h.ljust(8), r['cv_auc_long'], r['cv_auc_short'],
           r['avg_pL'], r['avg_pS'], r['nL_th'], r['nS_th'], r['bias_status']))

# 5. FEATURE IMPORTANCE TOP 10 (utolso horizon)
print('\n=== FEATURE IMPORTANCE TOP 10 (Long model, utolso horizon) ===')
fi_avg = fi_l / 3
order = np.argsort(fi_avg)[::-1]
for i in order[:10]:
    print('  %-30s: %.1f' % (avail[i], fi_avg[i]))
print('\n=== FEATURE IMPORTANCE TOP 10 (Short model, utolso horizon) ===')
fi_avg = fi_s / 3
order = np.argsort(fi_avg)[::-1]
for i in order[:10]:
    print('  %-30s: %.1f' % (avail[i], fi_avg[i]))

# Meta
with open(MDIR/'v8_dual_meta.json','w') as f:
    json.dump({'version':'v8_dual_binary','labeler':'strict_wick_jules',
               'pt_m':PT_M,'sl_m':SL_M,'horizons':results,
               'elapsed':time.time()-t0,'ts':pd.Timestamp.now().isoformat()},
              f, indent=2, default=str)
print('\n[+] Dual-Binary Complete! Elapsed: %.0fs' % (time.time()-t0))
