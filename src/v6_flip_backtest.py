#!/usr/bin/env python3
"""V6 2min FLIP backtest - 2026-09-01"""
import pandas as pd, numpy as np
from pathlib import Path

PREDS = Path('/data/LGBM_copilot/models/scalper/BTCUSD_v6_preds_20261018_141912.csv')
df = pd.read_csv(PREDS, index_col=0, parse_dates=True)
day = df.loc['2026-09-01'].copy()
flip_pL = day['p_short_2min'].values  # piros gorbe = FLIP Long
flip_pS = day['p_long_2min'].values   # zold gorbe = FLIP Short
px = day['price'].values
sig_orig = day['signal_2min'].values

n = len(day)
next_ret = np.zeros(n)
next_ret[:-1] = (px[1:] / px[:-1] - 1) * 100

long_marker = (sig_orig == 1)    # eredeti zold haromszog (Long)
short_marker = (sig_orig == -1)  # eredeti piros haromszog (Short)

# Eredeti V6: Long marker -> Long pozicio; Short marker -> Short pozicio
orig_long_ret = next_ret[long_marker].sum()
orig_short_ret = -next_ret[short_marker].sum()

# FLIP: eredeti Long marker (zold) -> SHORT pozicio; eredeti Short marker (piros) -> LONG pozicio
flip_long_ret = next_ret[short_marker].sum()
flip_short_ret = -next_ret[long_marker].sum()

n_long = int(long_marker.sum())
n_short = int(short_marker.sum())

print('--- 7. BACKTEST SIMULATION (FLIP vs EREDETI, 2min horizon) ---')
print(f'  Eredeti V6 Long-only  (zold marker->long):   {orig_long_ret:+.2f}% ({n_long} trade) | avg={orig_long_ret/max(1,n_long):.4f}%')
print(f'  Eredeti V6 Short-only (piros marker->short):  {orig_short_ret:+.2f}% ({n_short} trade) | avg={orig_short_ret/max(1,n_short):.4f}%')
print(f'  Eredeti V6 Total:                             {orig_long_ret+orig_short_ret:+.2f}%')
print(f'  FLIP Long-only  (piros marker->long):  {flip_long_ret:+.2f}% ({n_short} trade) | avg={flip_long_ret/max(1,n_short):.4f}%')
print(f'  FLIP Short-only (zold marker->short):   {flip_short_ret:+.2f}% ({n_long} trade) | avg={flip_short_ret/max(1,n_long):.4f}%')
print(f'  FLIP Total:                                  {flip_long_ret+flip_short_ret:+.2f}%')
print(f'  Buy & Hold:                                  {(px[-1]/px[0]-1)*100:+.2f}%')
print()

orig_total = orig_long_ret + orig_short_ret
flip_total = flip_long_ret + flip_short_ret

print('--- 8. KONKLUSZIO ---')
if orig_total > flip_total:
    print(f'  -> EREDETI V6 JOBB ({orig_total:+.2f}% vs FLIP {flip_total:+.2f}%, kulonbseg: {orig_total-flip_total:+.2f}%)')
    print('  -> A V6 eredeti Long/Short cimkek HELYESEK, FLIP-elve rosszabb')
    print('  -> A tukor hipotezis NEM igazolodott')
else:
    print(f'  -> FLIP JOBB ({flip_total:+.2f}% vs EREDETI {orig_total:+.2f}%, kulonbseg: {flip_total-orig_total:+.2f}%)')
    print('  -> A V6 eredeti cimkek ROSSZAK (tukor problema), FLIP-elve jobb')
    print('  -> A tukor hipotezis IGAZ')

print()
print('--- 9. IRANYONKENTI WR ---')
orig_long_wr = (next_ret[long_marker] > 0).sum() / max(1, n_long) * 100
orig_short_wr = ((-next_ret[short_marker]) > 0).sum() / max(1, n_short) * 100
flip_long_wr = (next_ret[short_marker] > 0).sum() / max(1, n_short) * 100
flip_short_wr = ((-next_ret[long_marker]) > 0).sum() / max(1, n_long) * 100
print(f'  Eredeti Long WR  ({n_long} trade): {orig_long_wr:.1f}%')
print(f'  Eredeti Short WR ({n_short} trade): {orig_short_wr:.1f}%')
print(f'  FLIP Long WR  ({n_short} trade): {flip_long_wr:.1f}%')
print(f'  FLIP Short WR ({n_long} trade): {flip_short_wr:.1f}%')
