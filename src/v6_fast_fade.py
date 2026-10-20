#!/usr/bin/env python3
"""V6 2min GYORS FORWARD elemzes - 10s, 30s, 1p, 2p, 3p mikrotrend fade
Felhasznalo: 'amikor a Long gorbe csucsot er, 1-2 percen belul be is kovetkezik'
Megnezzuk rovidebb horizonon is (lehet, hogy csak 10-30 mp-ig tart a fade)
"""
import pandas as pd, numpy as np
from pathlib import Path

PREDS = Path('/data/LGBM_copilot/models/scalper/BTCUSD_v6_preds_20261018_141912.csv')
df = pd.read_csv(PREDS, index_col=0, parse_dates=True)
day = df.loc['2026-09-01'].copy().reset_index(drop=True)

pL = day['p_long_2min'].values
pS = day['p_short_2min'].values
px = day['price'].values
n = len(day)

# Bar gyakorisag: ~7.4s/bar
# 10s ~ 1 bar, 30s ~ 4 bar, 1perc ~ 8 bar, 2perc ~ 16 bar, 3perc ~ 24 bar
horizons = {'10s': 1, '30s': 4, '1p': 8, '2p': 16, '3p': 24, '5p': 40}

fwd = {}
for label, k in horizons.items():
    arr = np.full(n, np.nan)
    arr[:-k] = (px[k:] / px[:-k] - 1) * 100
    fwd[label] = arr

print('='*80)
print('GYORS FADE VIZSGALAT - kulonbozo horizontokon')
print('='*80)
print()
print('Felhasznalo hipotezis: ZOLD P(Long) csucs utan az ar LEFELT megy 1-2 percen belul')
print()

# Mikrotrend detektio: 4 gyertyás emelkedő P(Long)
def get_mikrotrend_updown(arr, window=4):
    up = np.zeros(len(arr), dtype=bool)
    down = np.zeros(len(arr), dtype=bool)
    for i in range(window, len(arr)):
        seq = arr[i-window+1:i+1]
        if all(seq[k] > seq[k-1] for k in range(1, len(seq))):
            up[i] = True
        if all(seq[k] < seq[k-1] for k in range(1, len(seq))):
            down[i] = True
    return up, down

print('--- 1. 4 gyertyás P(Long) emelkedés -> forward return minden horizonon ---')
up_L, down_L = get_mikrotrend_updown(pL, 4)
print(f'  EMELKEDO P(Long) trend ({up_L.sum()} db) -> forward return:')
print(f'  {"horizon":<8} | {"mean fwd":>10} | {"% pos (ar fel)":>15} | {"median":>9}')
print('  ' + '-'*60)
for label in horizons:
    r = fwd[label][up_L]
    r = r[~np.isnan(r)]
    if len(r) > 0:
        print(f'  {label:<8} | {r.mean():>+9.4f}% | {(r>0).mean()*100:>13.1f}% | {np.median(r):>+8.4f}%')

print()
print('--- 2. 4 gyertyás P(Long) esés -> forward return minden horizonon ---')
print(f'  ESO P(Long) trend ({down_L.sum()} db) -> forward return:')
print(f'  {"horizon":<8} | {"mean fwd":>10} | {"% pos (ar fel)":>15} | {"median":>9}')
print('  ' + '-'*60)
for label in horizons:
    r = fwd[label][down_L]
    r = r[~np.isnan(r)]
    if len(r) > 0:
        print(f'  {label:<8} | {r.mean():>+9.4f}% | {(r>0).mean()*100:>13.1f}% | {np.median(r):>+8.4f}%')

print()
print('--- 3. Magas P(Long) (>0.50, nem csak csúcs) -> forward return ---')
mask = pL > 0.50
print(f'  P(Long) > 0.50 ({mask.sum()} db) -> forward return:')
print(f'  {"horizon":<8} | {"mean fwd":>10} | {"% pos":>6}')
print('  ' + '-'*50)
for label in horizons:
    r = fwd[label][mask]
    r = r[~np.isnan(r)]
    if len(r) > 0:
        print(f'  {label:<8} | {r.mean():>+9.4f}% | {(r>0).mean()*100:>5.1f}%')

print()
print('--- 4. Magas P(Long) (>0.55, erős csúcs) -> forward return ---')
mask = pL > 0.55
print(f'  P(Long) > 0.55 ({mask.sum()} db) -> forward return:')
print(f'  {"horizon":<8} | {"mean fwd":>10} | {"% pos":>6}')
print('  ' + '-'*50)
for label in horizons:
    r = fwd[label][mask]
    r = r[~np.isnan(r)]
    if len(r) > 0:
        print(f'  {label:<8} | {r.mean():>+9.4f}% | {(r>0).mean()*100:>5.1f}%')

# 5. P(Long) delta alapu: hirtelen emelkedes (spike)
print()
print('--- 5. P(Long) hirtelen emelkedes (1 bar-on >+0.03) -> forward return ---')
pL_delta1 = np.zeros(n)
pL_delta1[1:] = pL[1:] - pL[:-1]
mask = pL_delta1 > 0.03
print(f'  P(Long) delta1 > +0.03 ({mask.sum()} db) -> forward return:')
print(f'  {"horizon":<8} | {"mean fwd":>10} | {"% pos":>6}')
print('  ' + '-'*50)
for label in horizons:
    r = fwd[label][mask]
    r = r[~np.isnan(r)]
    if len(r) > 0:
        print(f'  {label:<8} | {r.mean():>+9.4f}% | {(r>0).mean()*100:>5.1f}%')

# 6. Erős spike Z-score alapján
print()
print('--- 6. P(Long) erős spike (Z-score > 2, 93 db) -> forward return ---')
z = (pL - pL.mean()) / pL.std()
mask = z > 2.0
print(f'  Z(P(Long)) > 2 ({mask.sum()} db) -> forward return:')
print(f'  {"horizon":<8} | {"mean fwd":>10} | {"% pos":>6}')
print('  ' + '-'*50)
for label in horizons:
    r = fwd[label][mask]
    r = r[~np.isnan(r)]
    if len(r) > 0:
        print(f'  {label:<8} | {r.mean():>+9.4f}% | {(r>0).mean()*100:>5.1f}%')

print()
print('='*80)
print('KONKLÚZIÓ:')
print('  Ha a ZOLD P(Long) csucsok utan minden horizonon negativ a fwd ret -> TUKOR igaz')
print('  Ha csak 1-2 percen belul negativ, de 3-5 percen pozitiv -> ROVID FADE, utana reverzio')
print('  Ha minden horizonon pozitiv -> eredeti Long cimke helyes (trend-kovetes)')
