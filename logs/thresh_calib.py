#!/usr/bin/env python3
"""Threshold calibration analysis"""
import pandas as pd
import numpy as np

# Vizsga
df = pd.read_csv('/data/dev/projects/scalper-copilot/Master_csv/raw/Merkava_MTF_MGCQ26_0720_23_vizsga_Data.csv')
df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%Y.%m.%d %H:%M:%S.%f')
mid = (df['Bid'] + df['Ask']) / 2
total_vol = df['Bid_Volume'] + df['Ask_Volume']
dollar_val = mid * total_vol
print(f'Vizsga tick stats:')
print(f'  Rows: {len(df):,}')
print(f'  Avg total_vol/sec: {total_vol.mean():.1f}')
print(f'  Avg dollar_val/sec: ${dollar_val.mean():,.0f}')
print(f'  Avg mid price: {mid.mean():.1f}')

# Train first 100K
df2 = pd.read_csv('/data/dev/projects/scalper-copilot/Master_csv/raw/Merkava_MTF_GCE_0527_0717_Data.csv', nrows=100000)
df2['Timestamp'] = pd.to_datetime(df2['Timestamp'], format='%Y.%m.%d %H:%M:%S.%f')
mid2 = (df2['Bid'] + df2['Ask']) / 2
total_vol2 = df2['Bid_Volume'] + df2['Ask_Volume']
dollar_val2 = mid2 * total_vol2
print(f'\nTrain tick stats (first 100K):')
print(f'  Avg total_vol/sec: {total_vol2.mean():.1f}')
print(f'  Avg dollar_val/sec: ${dollar_val2.mean():,.0f}')
print(f'  Avg mid price: {mid2.mean():.1f}')

ratio = dollar_val2.mean() / dollar_val.mean()
print(f'\nVolume ratio (train/vizsga): {ratio:.2f}x')
print(f'\nThreshold kalibracio:')
for target_sec in [30, 45, 60, 90]:
    thresh_viz = dollar_val.mean() * target_sec
    print(f'  {target_sec} sec/bar -> vizsga threshold=${thresh_viz:,.0f}')
