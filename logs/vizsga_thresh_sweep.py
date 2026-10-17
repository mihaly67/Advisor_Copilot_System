#!/usr/bin/env python3
"""Vizsga eval with calibrated threshold ($654K for ~45 sec/bar)"""
import sys
sys.path.insert(0, '/data/dev/projects/z-ai-copilot/src')
from v110_vizsga_eval import *

# Load model
clf = joblib.load(os.path.join(MOD, 'lgbm_18feat_leakfix.pkl'))
print(f'Model loaded: {MOD}/lgbm_18feat_leakfix.pkl')

# Load vizsga
vizsga_csv = os.path.join(RAW, 'Merkava_MTF_MGCQ26_0720_23_vizsga_Data.csv')
if not os.path.exists(vizsga_csv):
    vizsga_csv = '/data/dev/projects/scalper-copilot/Master_csv/raw/Merkava_MTF_MGCQ26_0720_23_vizsga_Data.csv'
df_viz_tick = pd.read_csv(vizsga_csv)
df_viz_tick['Timestamp'] = pd.to_datetime(df_viz_tick['Timestamp'], format='%Y.%m.%d %H:%M:%S.%f')

# Load ZZ
zz_csv = os.path.join(RAW, 'Master_ZigZag_GCEQ26_M1.csv')
if not os.path.exists(zz_csv):
    zz_csv = '/data/dev/projects/scalper-copilot/Master_csv/raw/Master_ZigZag_GCEQ26_M1.csv'
df_zz = pd.read_csv(zz_csv)
df_zz['Time'] = pd.to_datetime(df_zz['Time'], format='%Y.%m.%d %H:%M:%S')
viz_start = df_viz_tick['Timestamp'].min() - pd.Timedelta(hours=1)
viz_end = df_viz_tick['Timestamp'].max() + pd.Timedelta(hours=1)
df_zz_viz = df_zz[(df_zz['Time']>=viz_start)&(df_zz['Time']<=viz_end)].copy().reset_index(drop=True)

# Test multiple thresholds
for thresh in [654264, 872352, 1308529, 1746000]:
    print(f'\n{"="*60}')
    print(f'  Threshold: ${thresh:,.0f}')
    print(f'{"="*60}')
    db_viz = build_dollar_bars(df_viz_tick, threshold=thresh)
    if len(db_viz) == 0:
        print('  No bars!'); continue
    df_viz_feat = compute_vizsga_features(db_viz, df_zz_viz)
    df_viz_lab = apply_triple_barrier(df_viz_feat)
    df_viz_lab = df_viz_lab.iloc[:-5].reset_index(drop=True)
    
    X_viz = df_viz_lab[FEAT_ALL].replace([np.inf,-np.inf],np.nan).fillna(0).values
    y_viz = (df_viz_lab['Target_Label']+1).astype(int).values
    probs_viz = clf.predict_proba(X_viz)
    sig_t, ps, pn, pl = apply_threshold(probs_viz, clf.classes_)
    sig_f = apply_stability(sig_t)
    r = eval_detailed(sig_f, y_viz, ps, pn, pl)
    print(f'  WR={r["wr"]}%  P=${r["profit"]}  T={r["trades"]}  Opp={r["opposite"]} ({r["swap_pct"]}%)')
    print(f'  Dir_Conviction: {r["mean_conviction"]:.4f}')
