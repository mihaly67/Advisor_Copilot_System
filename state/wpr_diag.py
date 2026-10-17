#!/usr/bin/env python3
"""WPR_14 vizsgalat — diszkriminacio Short vs Long + SHAP eredmeny"""
import sys, os
import pandas as pd
import numpy as np

base = '/data/dev/projects/z-ai-copilot'
os.chdir(base)

csv_path = os.path.join(base, 'Master_csv', 'processed', 'labeled_dollar_bars_adaptive.csv')
df = pd.read_csv(csv_path)

short = df[df['Target_Label'] == -1]
long_ = df[df['Target_Label'] == 1]
noise = df[df['Target_Label'] == 0]

print('=== WPR_14 STATISZTIKA ===')
print(f'  Osszes: mean={df["WPR_14"].mean():.2f} std={df["WPR_14"].std():.2f}')
print(f'  Short (n={len(short)}): mean={short["WPR_14"].mean():.2f} std={short["WPR_14"].std():.2f}')
print(f'  Long  (n={len(long_)}): mean={long_["WPR_14"].mean():.2f} std={long_["WPR_14"].std():.2f}')
print(f'  Noise (n={len(noise)}): mean={noise["WPR_14"].mean():.2f} std={noise["WPR_14"].std():.2f}')

pooled_std = np.sqrt((short['WPR_14'].std()**2 + long_['WPR_14'].std()**2) / 2)
cohen_d = (short['WPR_14'].mean() - long_['WPR_14'].mean()) / (pooled_std + 1e-9)
print(f'\n  Cohen d (Short vs Long): {cohen_d:+.3f}')
print(f'  (|d|>0.3 = kozepes, |d|>0.5 = eros diszkriminacio)')

# WPR eloszlas Short vs Long
print(f'\n=== WPR ELOSZLAS SHORT vs LONG ===')
for pct in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
    print(f'  p{pct:3d}: Short={short["WPR_14"].quantile(pct/100):+.1f}  Long={long_["WPR_14"].quantile(pct/100):+.1f}')

# WPR tartomanyok es label arany
print(f'\n=== WPR TARTOMANY → LABEL ARANY ===')
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

# Korrelacio WPR es Label
corr = df[['WPR_14', 'Target_Label']].corr().iloc[0, 1]
print(f'\n  Korrelacio WPR ↔ Label: {corr:+.4f}')

# OOS: WPR Short barokon
split = int(len(df) * 0.8)
test = df.iloc[split:].copy()
ts = test[test['Target_Label'] == -1]
tl = test[test['Target_Label'] == 1]
print(f'\n=== OOS WPR (test set) ===')
print(f'  True Short (n={len(ts)}): WPR mean={ts["WPR_14"].mean():.2f}')
print(f'  True Long  (n={len(tl)}): WPR mean={tl["WPR_14"].mean():.2f}')

# V1 SHAP megnezes (ha van)
v1_shap = os.path.join(base, 'models', 'v1', 'shap_importance.csv')
if os.path.exists(v1_shap):
    shap_df = pd.read_csv(v1_shap)
    wpr_row = shap_df[shap_df['feature'] == 'WPR_14']
    if len(wpr_row) > 0:
        print(f'\n=== WPR_14 SHAP (V1, 82 feature) ===')
        print(wpr_row.to_string(index=False))
    else:
        print(f'\n  WPR_14 nincs a V1 SHAP-ban')

# V5 SHAP megnezes (WPR miert nincs benne)
v5_shap = os.path.join(base, 'models', 'v5', 'shap_importance.csv')
if os.path.exists(v5_shap):
    shap_df5 = pd.read_csv(v5_shap)
    wpr_row5 = shap_df5[shap_df5['feature'] == 'WPR_14']
    if len(wpr_row5) > 0:
        print(f'\n=== WPR_14 SHAP (V5) ===')
        print(wpr_row5.to_string(index=False))
    else:
        print(f'\n  WPR_14 nincs a V5 SHAP-ban (ki is estett)')

# Minden SHAP-ban megnezzuk
for ver in ['v1', 'v2', 'v3', 'v4', 'v5', 'v6']:
    p = os.path.join(base, 'models', ver, 'shap_importance.csv')
    if os.path.exists(p):
        sdf = pd.read_csv(p)
        wr = sdf[sdf['feature'] == 'WPR_14']
        if len(wr) > 0:
            row = wr.iloc[0]
            print(f'  {ver}: WPR_14 SHAP_Total={row.get("SHAP_Total", "?")} SHAP_Short={row.get("SHAP_Short", "?")}')

print('\n=== KESZ ===')
