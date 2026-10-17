#!/usr/bin/env python3
"""CFD adatok analízis: train vs vizsga (az 'új' mappából)"""
import pandas as pd, numpy as np

# Vizsga
f = '/data/dev/projects/z-ai-copilot/Master_csv/raw/új/Scalper_Copilot_MTF_Data_külön_vizsga.csv'
df = pd.read_csv(f)
df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%Y.%m.%d %H:%M:%S.%f')
mid = (df['Bid'] + df['Ask']) / 2
total_vol = df['Bid_Volume'] + df['Ask_Volume']
dollar_val = mid * total_vol

print('=== KÜLÖN VIZSGA (CFD, 09.14-18) ===')
print(f'  Rows: {len(df):,}')
print(f'  Time: {df["Timestamp"].min()} -> {df["Timestamp"].max()}')
print(f'  Avg dollar/sec: ${dollar_val.mean():,.0f}')
print(f'  Avg tick_vol/sec: {total_vol.mean():.1f}')
print(f'  Avg mid price: {mid.mean():.1f}')
print(f'  Avg spread: {df["Spread"].mean():.2f}')
print(f'  Non-zero vol: {(total_vol>0).sum():,} ({(total_vol>0).mean()*100:.1f}%)')

# Train (V2, first 500K)
f2 = '/data/dev/projects/z-ai-copilot/Master_csv/raw/új/Scalper_Copilot_MTF_Data_v2.csv'
df2 = pd.read_csv(f2, nrows=500000)
df2['Timestamp'] = pd.to_datetime(df2['Timestamp'], format='%Y.%m.%d %H:%M:%S.%f')
mid2 = (df2['Bid'] + df2['Ask']) / 2
total_vol2 = df2['Bid_Volume'] + df2['Ask_Volume']
dollar_val2 = mid2 * total_vol2

print()
print('=== V2 TANÍTÓ (CFD, 06.16-09.01, első 500K) ===')
print(f'  Avg dollar/sec: ${dollar_val2.mean():,.0f}')
print(f'  Avg tick_vol/sec: {total_vol2.mean():.1f}')
print(f'  Avg mid price: {mid2.mean():.1f}')
print(f'  Avg spread: {df2["Spread"].mean():.2f}')
print(f'  Non-zero vol: {(total_vol2>0).sum():,} ({(total_vol2>0).mean()*100:.1f}%)')

print()
print('=== ARÁNYOK (train / vizsga) ===')
print(f'  Dollar vol: {dollar_val2.mean()/dollar_val.mean():.2f}x')
print(f'  Tick vol:   {total_vol2.mean()/total_vol.mean():.2f}x')
print(f'  Price:      {mid2.mean()/mid.mean():.2f}x')

print()
print('=== THRESHOLD KALIBRÁCIÓ ===')
print(f'  Jules eredeti (futures): $444,000')
print(f'  CFD train ($/sec * 45s): ${dollar_val2.mean()*45:,.0f}')
print(f'  CFD vizsga ($/sec * 45s): ${dollar_val.mean()*45:,.0f}')
print()
print('  FIX DOLLAR ($1,746K):')
print(f'    Train: ~{1746000/dollar_val2.mean():.0f} sec/bar')
print(f'    Vizsga: ~{1746000/dollar_val.mean():.0f} sec/bar')
print()
print('  FIX IDŐ (45 sec/bar, volume-adaptív):')
print(f'    Train threshold: ${dollar_val2.mean()*45:,.0f}')
print(f'    Vizsga threshold: ${dollar_val.mean()*45:,.0f}')

print()
print('=== ZZ + MTF OSZLOPOK A VIZSGÁBAN ===')
zz_cols = ['Micro_R','Micro_S','Sec_R','Sec_S','Ter_R','Ter_S']
mtf_cols = ['1m_Close','5m_Close','15m_Close','30m_Close','ATR_M15','RSI_M15']
for c in zz_cols + mtf_cols:
    if c in df.columns:
        print(f'  {c}: mean={df[c].mean():.2f} ✓')
    else:
        print(f'  {c}: HIÁNYZIK ✗')
