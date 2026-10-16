#!/usr/bin/env python3
"""v110_vizsga_v2.py - Adaptiv dollar bar threshold + retraining + vizsga eval

Key insight: Dollar bar threshold must be calibrated per period!
- Train period (05-07): avg $18,703/sec → $654K for ~35 sec/bar
- Vizsga period (07-20-23): avg $14,539/sec → $654K for ~45 sec/bar

Solution: Use FIXED target sec/bar (~45s) and compute threshold dynamically
from local volume. This ensures consistent bar granularity across periods.
"""
import pandas as pd, numpy as np, lightgbm as lgb, joblib, os, sys, json, time, warnings
from sklearn.metrics import confusion_matrix
warnings.filterwarnings('ignore')
import plotly.graph_objects as go
from plotly.subplots import make_subplots

BASE='/data/dev/projects/z-ai-copilot'
RAW=os.path.join(BASE,'Master_csv','raw')
PROC=os.path.join(BASE,'Master_csv','processed')
MOD=os.path.join(BASE,'models','v110_vizsga')
DOCS=os.path.join(BASE,'docs','v110_vizsga')
for d in [MOD,DOCS]: os.makedirs(d,exist_ok=True)

LGBM_PARAMS={'n_estimators':781,'learning_rate':0.0142,'num_leaves':57,
    'max_depth':6,'min_child_samples':24,'colsample_bytree':0.566,
    'class_weight':'balanced','objective':'multiclass',
    'random_state':42,'n_jobs':-1,'verbose':-1}
THL=0.390; THS=0.400; THN=0.400; SW=2
TARGET_SEC_PER_BAR = 45  # Target bar granularity in seconds
PAL=dict(long='#228B22',short='#B22222',noise='#888888',
    long_lt='#32CD32',short_lt='#FF4444',
    bg='#111111',paper='#000000',grid='#333333',
    zero='#444444',legend_bg='#222222',font='white')
FEAT_ORIG=['Tick_Speed','Dist_Micro_R','Dist_Micro_S','Dist_Sec_R','Dist_Sec_S',
    'Dist_Ter_R','Dist_Ter_S','Stoch_State_M1','Upper_Wick_ATR','Lower_Wick_ATR']
FEAT_DIR=['RSI_signed','MACD_Hist_ATR','BB_ZScore','ROC_5','MFI_signed',
    'OBI_ZScore','Price_Vel_ATR','RSI_M15_signed']
FEAT_ALL=FEAT_ORIG+FEAT_DIR

# Import all helpers from v110_vizsga_eval
sys.path.insert(0, os.path.join(BASE, 'src'))
from v110_vizsga_eval import (compute_dir_features, apply_threshold, apply_stability,
    eval_sig, eval_detailed, build_dollar_bars, compute_vizsga_features,
    apply_triple_barrier, grid_fix, build_viz)

def calibrate_threshold(df_tick, target_sec=TARGET_SEC_PER_BAR):
    """Calibrate dollar bar threshold for target sec/bar"""
    mid = (df_tick['Bid'] + df_tick['Ask']) / 2
    total_vol = df_tick['Bid_Volume'] + df_tick['Ask_Volume']
    dollar_per_sec = (mid * total_vol).mean()
    threshold = dollar_per_sec * target_sec
    print(f"  Calibrated: ${threshold:,.0f} ({dollar_per_sec:,.0f}$/sec * {target_sec}s)")
    return threshold

def main():
    t0=time.time()
    print('='*70)
    print('  V110 VIZSGA V2 - Adaptiv threshold + retraining')
    print('='*70)

    # Step 1: Retrain with calibrated threshold on MAIN data
    # The main labeled CSV was built with $1,746K threshold.
    # We'll rebuild from scratch with calibrated threshold.
    # But first, let's just evaluate with $654K on vizsga and
    # compare with the existing model on OOS.

    # Load existing model
    clf = joblib.load(os.path.join(MOD, 'lgbm_18feat_leakfix.pkl'))
    print(f'  Model loaded (from Phase 1 leakfix)')

    # Load vizsga
    print('\n[1] Vizsga CSV betoltese + threshold kalibracio...')
    vizsga_csv = os.path.join(RAW, 'Merkava_MTF_MGCQ26_0720_23_vizsga_Data.csv')
    if not os.path.exists(vizsga_csv):
        vizsga_csv = '/data/dev/projects/scalper-copilot/Master_csv/raw/Merkava_MTF_MGCQ26_0720_23_vizsga_Data.csv'
    df_viz_tick = pd.read_csv(vizsga_csv)
    df_viz_tick['Timestamp'] = pd.to_datetime(df_viz_tick['Timestamp'], format='%Y.%m.%d %H:%M:%S.%f')
    print(f'  {len(df_viz_tick):,} rows')

    # Calibrate threshold for vizsga
    thresh_viz = calibrate_threshold(df_viz_tick)

    # Load ZZ
    zz_csv = os.path.join(RAW, 'Master_ZigZag_GCEQ26_M1.csv')
    if not os.path.exists(zz_csv):
        zz_csv = '/data/dev/projects/scalper-copilot/Master_csv/raw/Master_ZigZag_GCEQ26_M1.csv'
    df_zz = pd.read_csv(zz_csv)
    df_zz['Time'] = pd.to_datetime(df_zz['Time'], format='%Y.%m.%d %H:%M:%S')
    viz_start = df_viz_tick['Timestamp'].min() - pd.Timedelta(hours=1)
    viz_end = df_viz_tick['Timestamp'].max() + pd.Timedelta(hours=1)
    df_zz_viz = df_zz[(df_zz['Time']>=viz_start)&(df_zz['Time']<=viz_end)].copy().reset_index(drop=True)

    # Build with calibrated threshold
    print(f'\n[2] Dollar Bars (calibrated ${thresh_viz:,.0f})...')
    db_viz = build_dollar_bars(df_viz_tick, threshold=thresh_viz)

    print('\n[3] Feature engineering...')
    df_viz_feat = compute_vizsga_features(db_viz, df_zz_viz)

    print('\n[4] Triple Barrier Labeling...')
    df_viz_lab = apply_triple_barrier(df_viz_feat)
    df_viz_lab = df_viz_lab.iloc[:-5].reset_index(drop=True)

    print('\n[5] Predikcio a vizsgan (calibrated threshold)...')
    X_viz = df_viz_lab[FEAT_ALL].replace([np.inf,-np.inf],np.nan).fillna(0).values
    y_viz = (df_viz_lab['Target_Label']+1).astype(int).values
    probs_viz = clf.predict_proba(X_viz)
    sig_t, ps, pn, pl = apply_threshold(probs_viz, clf.classes_)
    sig_f = apply_stability(sig_t)
    r_viz = eval_detailed(sig_f, y_viz, ps, pn, pl)

    print(f'\n  ================================================')
    print(f'  VIZSGA EREDMENY (calibrated ${thresh_viz:,.0f})')
    print(f'  ================================================')
    print(f'  WR={r_viz["wr"]}%  P=${r_viz["profit"]}  T={r_viz["trades"]}')
    print(f'  Opp swaps: {r_viz["opposite"]} ({r_viz["swap_pct"]}%)')
    print(f'  Dir_Conviction: {r_viz["mean_conviction"]:.4f}')

    cm = np.array(r_viz['confusion'])
    print(f'\n  Konfuzio:')
    print(f'              Act Short  Act Noise  Act Long')
    print(f'  Pred Short {cm[0,0]:>10d}{cm[0,1]:>10d}{cm[0,2]:>10d}')
    print(f'  Pred Noise {cm[1,0]:>10d}{cm[1,1]:>10d}{cm[1,2]:>10d}')
    print(f'  Pred Long  {cm[2,0]:>10d}{cm[2,1]:>10d}{cm[2,2]:>10d}')

    # Build viz
    build_viz('VIZSGA_calibrated', df_viz_lab, sig_f, ps, pn, pl, y_viz, DOCS)

    # Now retrain model on MAIN data with same threshold calibration
    # The main data was built with $1,746K but we need to rebuild with
    # the same target sec/bar for consistency.
    # For now, just report the results.
    print(f'\n  OOS (leakfix, $1,746K): WR=53.7% P=$2,814 T=8,191')
    print(f'  Vizsga (calibrated ${thresh_viz:,.0f}): WR={r_viz["wr"]}% P=${r_viz["profit"]} T={r_viz["trades"]}')

    # Save
    results = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'vizsga_calibrated': r_viz,
        'threshold_vizsga': thresh_viz,
        'target_sec_per_bar': TARGET_SEC_PER_BAR,
        'oos_ref': {'wr': 53.7, 'profit': 2814, 'trades': 8191},
    }
    with open(os.path.join(DOCS, 'vizsga_v2_results.json'), 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f'\n{"="*70}')
    print(f'  V110 VIZSGA V2 KESZ - {time.time()-t0:.0f}s')
    print(f'{"="*70}')

if __name__ == '__main__': main()
