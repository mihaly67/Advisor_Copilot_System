#!/usr/bin/env python3
"""CFD raw CSV-k végleges auditja"""
import pandas as pd, numpy as np, os

BASE = '/data/dev/projects/z-ai-copilot/Master_csv/raw/új'

# TANITO
print('='*70)
print('  TANITO: Scalper_Copilot_MTF_Data_v2.csv')
print('='*70)
f = os.path.join(BASE, 'Scalper_Copilot_MTF_Data_v2.csv')
df = pd.read_csv(f, nrows=50000)
df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%Y.%m.%d %H:%M:%S.%f')
mid = (df['Bid'] + df['Ask'])/2
tv = df['Bid_Volume'] + df['Ask_Volume']
dv = mid * tv
print(f'  Size: {os.path.getsize(f)/1024/1024:.0f} MB')
print(f'  First 50K rows time: {df["Timestamp"].min()} -> {df["Timestamp"].max()}')
print(f'  Avg dollar_vol/sec: ${dv.mean():,.0f}')
print(f'  Avg tick_vol/sec: {tv.mean():.1f}')
print(f'  Non-zero vol: {(tv>0).sum()}/{len(tv)} ({(tv>0).mean()*100:.1f}%)')
print(f'  Spread: mean={df["Spread"].mean():.3f}')
# Volatility
dt = df['Timestamp'].diff().dt.total_seconds().dropna()
pdiff = mid.diff().abs()
print(f'  Avg |price_diff|/sec: {pdiff.mean():.4f}')
print(f'  Avg sec between rows: {dt.mean():.2f}')

# VIZSGA
print()
print('='*70)
print('  VIZSGA: Scalper_Copilot_MTF_Data_külön_vizsga.csv')
print('='*70)
f2 = os.path.join(BASE, 'Scalper_Copilot_MTF_Data_külön_vizsga.csv')
df2 = pd.read_csv(f2)
df2['Timestamp'] = pd.to_datetime(df2['Timestamp'], format='%Y.%m.%d %H:%M:%S.%f')
mid2 = (df2['Bid'] + df2['Ask'])/2
tv2 = df2['Bid_Volume'] + df2['Ask_Volume']
print(f'  Size: {os.path.getsize(f2)/1024/1024:.0f} MB')
print(f'  Rows: {len(df2):,}')
print(f'  Time: {df2["Timestamp"].min()} -> {df2["Timestamp"].max()}')
print(f'  Avg tick_vol/sec: {tv2.mean():.1f}')
print(f'  Non-zero vol: {(tv2>0).sum()}/{len(tv2)} ({(tv2>0).mean()*100:.1f}%)')
print(f'  Spread: mean={df2["Spread"].mean():.3f}')

# Volatility
dt2 = df2['Timestamp'].diff().dt.total_seconds().dropna()
pdiff2 = mid2.diff().abs()
print(f'  Avg |price_diff|/sec: {pdiff2.mean():.4f}')
print(f'  Avg sec between rows: {dt2.mean():.2f}')

# Compare volatilities
print()
print('='*70)
print('  VOLATILITÁS ÖSSZEHASONLÍTÁS')
print('='*70)
# Group by hour, compute hourly volatility
df['hour'] = df['Timestamp'].dt.floor('1h')
hourly_vol_train = df.groupby('hour').apply(lambda x: x['Bid'].diff().abs().sum())
df2['hour'] = df2['Timestamp'].dt.floor('1h')
hourly_vol_vizsga = df2.groupby('hour').apply(lambda x: x['Bid'].diff().abs().sum())

print(f'  Train hourly |price| movement: mean=${hourly_vol_train.mean():.2f}, std=${hourly_vol_train.std():.2f}')
print(f'  Vizsga hourly |price| movement: mean=${hourly_vol_vizsga.mean():.2f}, std=${hourly_vol_vizsga.std():.2f}')
print(f'  Arány (train/vizsga): {hourly_vol_train.mean()/hourly_vol_vizsga.mean():.2f}x')

print()
print('  VOLATILITY BAR KALIBRÁCIÓ:')
for target_atr in [1.0, 2.0, 3.0, 5.0]:
    # Hány bar jön ki ~4 nap vizsgán?
    total_movement = pdiff2.sum()
    n_bars = total_movement / target_atr
    print(f'    ATR_target=${target_atr:.1f} -> ~{n_bars:,.0f} bars a vizsgán ({len(df2)/n_bars:.1f} tick/bar)')

# V2 full time range
print()
print('='*70)
print('  V2 TELJES IDŐTARTAM (csak Timestamp)')
print('='*70)
df_ts = pd.read_csv(f, usecols=['Timestamp'])
print(f'  Rows: {len(df_ts):,}')
print(f'  First: {df_ts.iloc[0,0]}')
print(f'  Last:  {df_ts.iloc[-1,0]}')
