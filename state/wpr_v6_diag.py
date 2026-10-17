#!/usr/bin/env python3
import sys, os
import pandas as pd
import numpy as np
import ta

base = '/data/dev/projects/z-ai-copilot'
os.chdir(base)

csv_path = os.path.join(base, 'Master_csv', 'processed', 'labeled_dollar_bars_v6.csv')
df = pd.read_csv(csv_path)

close = df['Close']
high = df['High']
low = df['Low']

wpr = ta.momentum.WilliamsRIndicator(high=high, low=low, close=close, lbp=14).williams_r()

df['WPR_14'] = wpr.shift(1)
df['WPR_Change_1'] = wpr.diff(1).shift(1)
df['WPR_Change_3'] = wpr.diff(3).shift(1)
df['WPR_Change_5'] = wpr.diff(5).shift(1)
df['WPR_Bearish_Cross'] = ((wpr.shift(1) > -20) & (wpr < -20)).astype(int).shift(1)
df['WPR_Bullish_Cross'] = ((wpr.shift(1) < -80) & (wpr > -80)).astype(int).shift(1)
df['WPR_Overbought'] = (wpr > -20).astype(int).shift(1)
df['WPR_Oversold'] = (wpr < -80).astype(int).shift(1)
df['WPR_Declining_3'] = ((wpr.diff(1) < 0) & (wpr.diff(2) < 0) & (wpr.diff(3) < 0)).astype(int).shift(1)
df['WPR_Rising_3'] = ((wpr.diff(1) > 0) & (wpr.diff(2) > 0) & (wpr.diff(3) > 0)).astype(int).shift(1)

short = df[df['Target_Label'] == -1]
long_ = df[df['Target_Label'] == 1]
noise = df[df['Target_Label'] == 0]

print('=== V6 LABELING: WPR DERIVALTAK DISZKRIMINACIOJA (Short vs Long) ===')
print(f'   Short n={len(short)}  Long n={len(long_)}  Noise n={len(noise)}')
print()

wpr_features = [
    'WPR_14', 'WPR_Change_1', 'WPR_Change_3', 'WPR_Change_5',
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
    marker = ' ***' if abs(d) > 0.3 else (' *' if abs(d) > 0.15 else '')
    print(f'  {ft:25s} Short={s_mean:+.3f} Long={l_mean:+.3f} d={d:+.3f} corr={corr:+.4f}{marker}')

print('\n=== WPR TARTOMANY -> LABEL ARANY (V6) ===')
bins = [-100, -80, -50, -20, 0]
labels_bin = ['[-100,-80)', '[-80,-50)', '[-50,-20)', '[-20,0]']
df['WPR_bin'] = pd.cut(df['WPR_14'], bins=bins, labels=labels_bin, include_lowest=True)
for b in labels_bin:
    sub = df[df['WPR_bin'] == b]
    if len(sub) == 0:
        continue
    n_s = (sub['Target_Label'] == -1).sum()
    n_n = (sub['Target_Label'] == 0).sum()
    n_l = (sub['Target_Label'] == 1).sum()
    print(f'  {b:12s} (n={len(sub):5d}): Short={n_s/len(sub)*100:5.1f}% Noise={n_n/len(sub)*100:5.1f}% Long={n_l/len(sub)*100:5.1f}%')

print('\n=== WPR OVERBOUGHT (>-20) -> LABEL (V6) ===')
ob = df[df['WPR_Overbought'] == 1]
no = df[df['WPR_Overbought'] == 0]
print(f'  Overbought (n={len(ob)}): Short={ob["Target_Label"].eq(-1).mean()*100:.1f}% Long={ob["Target_Label"].eq(1).mean()*100:.1f}%')
print(f'  Nem OB    (n={len(no)}): Short={no["Target_Label"].eq(-1).mean()*100:.1f}% Long={no["Target_Label"].eq(1).mean()*100:.1f}%')

print('\n=== WPR OVERSOLD (<-80) -> LABEL (V6) ===')
os_ = df[df['WPR_Oversold'] == 1]
no = df[df['WPR_Oversold'] == 0]
print(f'  Oversold (n={len(os_)}): Short={os_["Target_Label"].eq(-1).mean()*100:.1f}% Long={os_["Target_Label"].eq(1).mean()*100:.1f}%')
print(f'  Nem OS  (n={len(no)}): Short={no["Target_Label"].eq(-1).mean()*100:.1f}% Long={no["Target_Label"].eq(1).mean()*100:.1f}%')

print('\n=== WPR DECLINING 3 -> LABEL (V6) ===')
dec = df[df['WPR_Declining_3'] == 1]
nd = df[df['WPR_Declining_3'] == 0]
if len(dec) > 0:
    print(f'  Declining (n={len(dec)}): Short={dec["Target_Label"].eq(-1).mean()*100:.1f}% Long={dec["Target_Label"].eq(1).mean()*100:.1f}%')
    print(f'  Rising    (n={len(nd)}): Short={nd["Target_Label"].eq(-1).mean()*100:.1f}% Long={nd["Target_Label"].eq(1).mean()*100:.1f}%')

print('\n=== WPR BEARISH CROSS -> LABEL (V6) ===')
bc = df[df['WPR_Bearish_Cross'] == 1]
nb = df[df['WPR_Bearish_Cross'] == 0]
if len(bc) > 0:
    print(f'  Bearish Cross (n={len(bc)}): Short={bc["Target_Label"].eq(-1).mean()*100:.1f}% Long={bc["Target_Label"].eq(1).mean()*100:.1f}%')
    print(f'  Nincs Cross  (n={len(nb)}): Short={nb["Target_Label"].eq(-1).mean()*100:.1f}% Long={nb["Target_Label"].eq(1).mean()*100:.1f}%')

print('\n=== KESZ ===')
