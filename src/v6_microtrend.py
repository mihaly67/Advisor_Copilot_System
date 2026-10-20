#!/usr/bin/env python3
"""V6 2min MIKROTREND ELEMZÉS - tukor/fade minden 3-4 gyertyás trendnél?"""
import pandas as pd, numpy as np
from pathlib import Path

PREDS = Path('/data/LGBM_copilot/models/scalper/BTCUSD_v6_preds_20261018_141912.csv')
df = pd.read_csv(PREDS, index_col=0, parse_dates=True)
day = df.loc['2026-09-01'].copy().reset_index(drop=True)

pL = day['p_long_2min'].values
pS = day['p_short_2min'].values
pN = day['p_noise_2min'].values
px = day['price'].values
n = len(day)

HOLD = 16  # 2 perc = 16 bar
fwd = np.full(n, np.nan)
fwd[:-HOLD] = (px[HOLD:] / px[:-HOLD] - 1) * 100

print('='*80)
print('MIKROTREND FADE VIZSGALAT - V6 2min, 2026-09-01')
print('='*80)
print()

# 1. BIN-ELEMZÉS P(Long) szerint
print('--- 1. BIN-ELEMZES: P(Long) (ZOLD gorbe) ertek -> forward ret 2 perc ---')
print(f'  {"P(Long) range":<18} | {"n":>6} | {"mean fwd":>10} | {"median":>9} | {"%pos":>5}')
print('  ' + '-'*68)
bins = [0.20, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 1.0]
for i in range(len(bins)-1):
    lo, hi = bins[i], bins[i+1]
    mask = (pL >= lo) & (pL < hi)
    cnt = mask.sum()
    if cnt == 0: continue
    r = fwd[mask]; r = r[~np.isnan(r)]
    if len(r) == 0: continue
    print(f'  [{lo:.2f}, {hi:.2f})       | {cnt:>6,} | {r.mean():>+9.4f}% | {np.median(r):>+8.4f}% | {(r>0).mean()*100:>4.1f}%')

print()
print('--- 2. BIN-ELEMZES: P(Short) (PIROS gorbe) ertek -> forward ret 2 perc ---')
print(f'  {"P(Short) range":<18} | {"n":>6} | {"mean fwd":>10} | {"median":>9} | {"%pos":>5}')
print('  ' + '-'*68)
for i in range(len(bins)-1):
    lo, hi = bins[i], bins[i+1]
    mask = (pS >= lo) & (pS < hi)
    cnt = mask.sum()
    if cnt == 0: continue
    r = fwd[mask]; r = r[~np.isnan(r)]
    if len(r) == 0: continue
    print(f'  [{lo:.2f}, {hi:.2f})       | {cnt:>6,} | {r.mean():>+9.4f}% | {np.median(r):>+8.4f}% | {(r>0).mean()*100:>4.1f}%')


# 2. MIKROTREND: 3-4 gyertyas trendek P(Long)-ban
print()
print('='*80)
print('--- 3. MIKROTREND: P(Long) 3-4 gyertyas emelkedes/eses ---')
print('     Ha tukor igaz: P(Long) fel -> ar LEFELT; P(Long) le -> ar FELFELT')
print()

for window in [3, 4, 5]:
    up_mask = np.zeros(n, dtype=bool)
    down_mask = np.zeros(n, dtype=bool)
    for i in range(window, n):
        seq = pL[i-window+1:i+1]
        if all(seq[k] > seq[k-1] for k in range(1, len(seq))):
            up_mask[i] = True
        if all(seq[k] < seq[k-1] for k in range(1, len(seq))):
            down_mask[i] = True
    cnt_up = up_mask.sum(); cnt_dn = down_mask.sum()
    r_up = fwd[up_mask]; r_up = r_up[~np.isnan(r_up)]
    r_dn = fwd[down_mask]; r_dn = r_dn[~np.isnan(r_dn)]
    print(f'  {window} gyertyas mikrotrend P(Long)-on:')
    if len(r_up) > 0:
        print(f'    EMELKEDO P(Long) ({cnt_up} db) -> fwd 2p: mean={r_up.mean():+.4f}% | %pos={(r_up>0).mean()*100:.1f}% | median={np.median(r_up):+.4f}%')
    if len(r_dn) > 0:
        print(f'    ESO P(Long)      ({cnt_dn} db) -> fwd 2p: mean={r_dn.mean():+.4f}% | %pos={(r_dn>0).mean()*100:.1f}% | median={np.median(r_dn):+.4f}%')
    if len(r_up) > 0 and len(r_dn) > 0:
        diff = r_dn.mean() - r_up.mean()
        tag = 'TUKOR IGAZ' if diff > 0 else 'TREND-KOVETES'
        print(f'    Kulonbseg (le - fel): {diff:+.4f}% -> {tag}')
    print()

# 3. P(Long) delta alapu mikrotrend
print('='*80)
print('--- 4. P(Long) DELTA (3 bar-on) -> forward ret ---')
print('     Ha tukor igaz: pozitv delta (P(Long) fel) -> negatv fwd ret')
print()
pL_delta3 = np.zeros(n)
pL_delta3[3:] = pL[3:] - pL[:-3]

delta_bins = [(-1.0, -0.10), (-0.10, -0.05), (-0.05, -0.02), (-0.02, -0.005),
              (-0.005, 0.005), (0.005, 0.02), (0.02, 0.05), (0.05, 0.10), (0.10, 1.0)]
print(f'  {"delta3 range":<20} | {"n":>6} | {"mean fwd":>10} | {"median":>9} | {"%pos":>5}')
print('  ' + '-'*70)
for lo, hi in delta_bins:
    mask = (pL_delta3 >= lo) & (pL_delta3 < hi)
    cnt = mask.sum()
    if cnt == 0: continue
    r = fwd[mask]; r = r[~np.isnan(r)]
    if len(r) == 0: continue
    print(f'  [{lo:+.3f}, {hi:+.3f})      | {cnt:>6,} | {r.mean():>+9.4f}% | {np.median(r):>+8.4f}% | {(r>0).mean()*100:>4.1f}%')

# 4. Korrelacio
print()
print('='*80)
print('--- 5. KORRELACIO ---')
valid = ~np.isnan(fwd)
corr_pl = np.corrcoef(pL[valid], fwd[valid])[0,1]
corr_delta3 = np.corrcoef(pL_delta3[valid], fwd[valid])[0,1]
tag_pl = 'TUKOR/FADE' if corr_delta3 < 0 else 'eredeti helyes'
print(f'  Corr(P(Long),         fwd_2min) = {corr_pl:+.4f}')
print(f'  Corr(delta3 P(Long), fwd_2min) = {corr_delta3:+.4f}  <- {tag_pl}')

pS_delta3 = np.zeros(n)
pS_delta3[3:] = pS[3:] - pS[:-3]
corr_ps = np.corrcoef(pS[valid], fwd[valid])[0,1]
corr_delta3_s = np.corrcoef(pS_delta3[valid], fwd[valid])[0,1]
tag_ps = 'TUKOR/FADE' if corr_delta3_s > 0 else 'eredeti helyes'
print(f'  Corr(P(Short),         fwd_2min) = {corr_ps:+.4f}')
print(f'  Corr(delta3 P(Short), fwd_2min) = {corr_delta3_s:+.4f}  <- {tag_ps}')
