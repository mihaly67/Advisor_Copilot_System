#!/usr/bin/env bash
cd /data/dev/projects/z-ai-copilot
/home/Jules/jules_venv/bin/python3 -c "
import sys, os
sys.path.insert(0, 'src')
from dom_labeler_v7 import apply_binary_labeling
import pandas as pd, numpy as np

inp = 'Master_csv/processed/features_dollar_bars_adaptive.csv'
out = 'Master_csv/processed/labeled_dollar_bars_v7_15.csv'
df = pd.read_csv(inp)
df['Start_Timestamp'] = pd.to_datetime(df['Start_Timestamp'])
df.sort_values('Start_Timestamp', inplace=True)
df.reset_index(drop=True, inplace=True)

df_l = apply_binary_labeling(df, horizon=15, threshold_pct=0.05)
df_l = df_l.iloc[:-15].copy()
dist = df_l['Target_Label'].value_counts(normalize=True) * 100
print('Label eloszlas:')
for k, v in dist.items():
    print(f'  {int(k):+d}: {v:.1f}%')

short = df_l[df_l['Target_Label']==-1]
long_ = df_l[df_l['Target_Label']==1]
print(f'Short n={len(short)} Long n={len(long_)}')
irany = ['Bar_Direction','Price_Vel_Signed','Mom5_Direction','Mom10_Direction',
         'Wick_Asymmetry','Trade_Flow_Imb','Regime_Slope','Price_Velocity']
for ft in irany:
    if ft not in df_l.columns: continue
    sm, lm = short[ft].mean(), long_[ft].mean()
    p = np.sqrt((short[ft].std()**2 + long_[ft].std()**2)/2)
    d = (sm - lm) / (p + 1e-9)
    m = ' ***' if abs(d) > 0.3 else (' *' if abs(d) > 0.15 else '')
    print(f'  {ft:25s} S={sm:+.3f} L={lm:+.3f} d={d:+.3f}{m}')

df_l.to_csv(out, index=False)
print(f'Mentve: {out}')
" 2>&1
