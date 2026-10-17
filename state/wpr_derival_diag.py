#!/usr/bin/env python3
import sys, os
import pandas as pd
import numpy as np
import ta

base = '/data/dev/projects/z-ai-copilot'
os.chdir(base)

csv_path = os.path.join(base, 'Master_csv', 'processed', 'labeled_dollar_bars_adaptive.csv')
df = pd.read_csv(csv_path)

close = df['Close']
high = df['High']
low = df['Low']

wpr = ta.momentum.WilliamsRIndicator(high=high, low=low, close=close, lbp=14).williams_r()

df['WPR_Change_1'] = wpr.diff(1).shift(1)
df['WPR_Change_3'] = wpr.diff(3).shift(1)
df['WPR_Change_5'] = wpr.diff(5).shift(1)
df['WPR_Slope'] = wpr.diff(1).shift(1)
df['WPR_Extremity'] = (wpr + 50).shift(1)
df['WPR_Bearish_Cross'] = ((wpr.shift(1) > -20) & (wpr < -20)).astype(int).shift(1)
df['WPR_Bullish_Cross'] = ((wpr.shift(1) < -80) & (wpr > -80)).astype(int).shift(1)
df['WPR_Overbought'] = (wpr > -20).astype(int).shift(1)
df['WPR_Oversold'] = (wpr < -80).astype(int).shift(1)
df['WPR_Declining_3'] = ((wpr.diff(1) < 0) & (wpr.diff(2) < 0) & (wpr.diff(3) < 0)).astype(int).shift(1)
df['WPR_Rising_3'] = ((wpr.diff(1) > 0) & (wpr.diff(2) > 0) & (wpr.diff(3) > 0)).astype(int).shift(1)

short = df[df['Target_Label'] == -1]
long_ = df[df['Target_Label'] == 1]

print('=== WPR DERIVALTAK DISZKRIMINACIOJA (Short vs Long) ===')
wpr_features = [
    'WPR_14', 'WPR_Change_1', 'WPR_Change_3', 'WPR_Change_5',
    'WPR_Slope', 'WPR_Extremity',
    'WPR_Bearish_Cross', 'WPR_Bullish_Cross',
    'WPR_Overbought', 'WPR_Oversold',
    'WPR_Declining_3', 'WPR_Rising_3'
]

for ft in wpr_features:
    if ft not in df.columns:
        continue
    s_mean = short[ft].mean()
    l_mean = long_[ft].mean()
    s_std = short[ft].std()
    l_std = long_[ft].std()
    pooled = np.sqrt((s_std**2 + l_std**2) / 2)
    d = (s_mean - l_mean) / (pooled + 1e-9)
    corr = df[[ft, 'Target_Label']].corr().iloc[0, 1]
    print(f'  {ft:25s} Short={s_mean:+.3f} Long={l_mean:+.3f} d={d:+.3f} corr={corr:+.4f}')

print('\n=== WPR BEARISH CROSS ===')
bc = df[df['WPR_Bearish_Cross'] == 1]
nb = df[df['WPR_Bearish_Cross'] == 0]
if len(bc) > 0:
    print(f'  Bearish Cross (n={len(bc)}): Short={bc["Target_Label"].eq(-1).mean()*100:.1f}% Long={bc["Target_Label"].eq(1).mean()*100:.1f}%')
    print(f'  Nincs Cross  (n={len(nb)}): Short={nb["Target_Label"].eq(-1).mean()*100:.1f}% Long={nb["Target_Label"].eq(1).mean()*100:.1f}%')

print('\n=== WPR OVERBOUGHT (>-20) ===')
ob = df[df['WPR_Overbought'] == 1]
no = df[df['WPR_Overbought'] == 0]
if len(ob) > 0:
    print(f'  Overbought (n={len(ob)}): Short={ob["Target_Label"].eq(-1).mean()*100:.1f}% Long={ob["Target_Label"].eq(1).mean()*100:.1f}%')
    print(f'  Nem OB    (n={len(no)}): Short={no["Target_Label"].eq(-1).mean()*100:.1f}% Long={no["Target_Label"].eq(1).mean()*100:.1f}%')

print('\n=== WPR OVERSOLD (<-80) ===')
os_ = df[df['WPR_Oversold'] == 1]
no = df[df['WPR_Oversold'] == 0]
if len(os_) > 0:
    print(f'  Oversold (n={len(os_)}): Short={os_["Target_Label"].eq(-1).mean()*100:.1f}% Long={os_["Target_Label"].eq(1).mean()*100:.1f}%')
    print(f'  Nem OS  (n={len(no)}): Short={no["Target_Label"].eq(-1).mean()*100:.1f}% Long={no["Target_Label"].eq(1).mean()*100:.1f}%')

print('\n=== WPR DECLINING 3 bars ===')
dec = df[df['WPR_Declining_3'] == 1]
nd = df[df['WPR_Declining_3'] == 0]
if len(dec) > 0:
    print(f'  Declining (n={len(dec)}): Short={dec["Target_Label"].eq(-1).mean()*100:.1f}% Long={dec["Target_Label"].eq(1).mean()*100:.1f}%')
    print(f'  Rising    (n={len(nd)}): Short={nd["Target_Label"].eq(-1).mean()*100:.1f}% Long={nd["Target_Label"].eq(1).mean()*100:.1f}%')

print('\n=== KESZ ===')
