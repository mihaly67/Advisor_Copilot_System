#!/usr/bin/env python3
"""V6 2min FORWARD RETURN elemzs - a gorbek csucsai utan mi tortenik az arral?
Felhasznalo hipotezis: ha a Long gorbe (eredeti P(Long), ZOLD) csucsot er,
az ar 1-2 percen belul LEFELT megy (tehat a predikcio counter-trend/fade).
Ha ez igaz, akkor a V6 eredeti Long/Short cimkek TENYLEGESen tukrok!
"""
import pandas as pd, numpy as np
from pathlib import Path

PREDS = Path('/data/LGBM_copilot/models/scalper/BTCUSD_v6_preds_20261018_141912.csv')
df = pd.read_csv(PREDS, index_col=0, parse_dates=True)
day = df.loc['2026-09-01'].copy().reset_index(drop=True)  # 0-indexelt timeline

pL_orig = day['p_long_2min'].values    # ZOLD gorbe (eredeti P(Long))
pS_orig = day['p_short_2min'].values   # PIROS gorbe (eredeti P(Short))
pN = day['p_noise_2min'].values
px = day['price'].values
n = len(day)

# Bar gyakorisag: 86400 masodperc / 11648 bar = ~7.4s/bar
bar_dt = 86400 / n
print(f'Bars: {n:,} | bar gyakorisag: {bar_dt:.2f} s/bar')
print(f'1 perc = {60/bar_dt:.1f} bar | 2 perc = {120/bar_dt:.1f} bar | 5 perc = {300/bar_dt:.1f} bar')
print()

# Forward return kulonbozo horizontokon (szazalek)
# k=10 ~ 1perc, k=16 ~ 2perc, k=40 ~ 5perc
forwards = {}
for k in [1, 5, 10, 16, 30, 60, 120]:
    ret = np.full(n, np.nan)
    ret[:-k] = (px[k:] / px[:-k] - 1) * 100  # % forward return
    forwards[k] = ret

print('='*76)
print('HIPOTEZIS: Long gorbe (ZOLD) csucs -> ar LEFELT megy (counter-trend)')
print('           Short gorbe (PIROS) csucs -> ar FELFELT megy (counter-trend)')
print('='*76)
print()

# Forward return amikor P(Long) magas (csucs)
print('--- A. P(Long) = ZOLD gorbe magas csucsok utan (forward return) ---')
print('     (Ha counter-trend igaz: negatv kene lenni)')
for thr in [0.50, 0.55, 0.57]:
    mask = pL_orig > thr
    cnt = mask.sum()
    if cnt == 0:
        continue
    print(f'  P(Long) > {thr}: {cnt:,} bar ({100*cnt/n:.1f}%)')
    for k in [10, 16, 30, 60]:
        if cnt > 0:
            r = forwards[k][mask]
            r = r[~np.isnan(r)]
            if len(r) > 0:
                print(f'    +{k} bar (~{k*bar_dt:.0f}s) forward ret: mean={r.mean():+.3f}%  median={np.median(r):+.3f}%  pos%%={(r>0).mean()*100:.1f}%')
    print()

print('--- B. P(Short) = PIROS gorbe magas csucsok utan (forward return) ---')
print('     (Ha counter-trend igaz: pozitv kene lenni)')
for thr in [0.50, 0.55, 0.57]:
    mask = pS_orig > thr
    cnt = mask.sum()
    if cnt == 0:
        continue
    print(f'  P(Short) > {thr}: {cnt:,} bar ({100*cnt/n:.1f}%)')
    for k in [10, 16, 30, 60]:
        if cnt > 0:
            r = forwards[k][mask]
            r = r[~np.isnan(r)]
            if len(r) > 0:
                print(f'    +{k} bar (~{k*bar_dt:.0f}s) forward ret: mean={r.mean():+.3f}%  median={np.median(r):+.3f}%  pos%%={(r>0).mean()*100:.1f}%')
    print()

# Peak detection: lokalis maximumok (pLorig[i] > pLorig[i-1] and pLorig[i] > pLorig[i+1])
def find_peaks(arr, min_val=0.50):
    peaks = []
    for i in range(1, len(arr)-1):
        if arr[i] > arr[i-1] and arr[i] > arr[i+1] and arr[i] >= min_val:
            peaks.append(i)
    return np.array(peaks)

print('--- C. LOKALIS CSUCSOK (peak detection, min_val=0.50) ---')
for name, arr in [('ZOLD P(Long)', pL_orig), ('PIROS P(Short)', pS_orig)]:
    peaks = find_peaks(arr, 0.50)
    if len(peaks) == 0:
        print(f'  {name}: nincs peak 0.50 felett')
        continue
    print(f'  {name}: {len(peaks)} peak (min=0.50)')
    for k in [10, 16, 30, 60]:
        # Minden peak utan k bar forward return
        rets = []
        for p in peaks:
            if p+k < n:
                rets.append((px[p+k]/px[p]-1)*100)
        if rets:
            r = np.array(rets)
            print(f'    +{k} bar (~{k*bar_dt:.0f}s) utan: mean={r.mean():+.3f}%  pos%%={(r>0).mean()*100:.1f}%  n={len(r)}')
    print()

# Kifejezetten: erosen megkulonbozteto csucsok (Z-score > 2)
print('--- D. ERDES CSUCSOK (Z-score > 2.0) ---')
for name, arr in [('ZOLD P(Long)', pL_orig), ('PIROS P(Short)', pS_orig)]:
    z = (arr - arr.mean()) / arr.std()
    mask = z > 2.0
    cnt = mask.sum()
    if cnt == 0:
        print(f'  {name}: nincs Z>2.0 csucs')
        continue
    print(f'  {name} Z>2.0: {cnt} db, P_mean={arr[mask].mean():.3f}')
    for k in [10, 16, 30, 60]:
        r = forwards[k][mask]
        r = r[~np.isnan(r)]
        if len(r) > 0:
            print(f'    +{k} bar (~{k*bar_dt:.0f}s) utan: mean={r.mean():+.3f}%  pos%%={(r>0).mean()*100:.1f}%')
    print()

# Vgs konklzio
print('='*76)
print('KONKLÚZIÓ KÉRDÉS:')
print(' Ha ZOLD P(Long) csucsok utan a forward ret NEGATIV -> counter-trend (tukor igaz)')
print(' Ha ZOLD P(Long) csucsok utan a forward ret POZITIV -> trend-kovetes (eredeti helyes)')
print()
print(' Ha PIROS P(Short) csucsok utan a forward ret POZITIV -> counter-trend (tukor igaz)')
print(' Ha PIROS P(Short) csucsok utan a forward ret NEGATIV -> trend-kovetes (eredeti helyes)')
