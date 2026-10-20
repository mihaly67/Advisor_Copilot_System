#!/usr/bin/env python3
"""V6 2min FADE backtest - ZOLD P(Long) csucsoknal SHORT-olunk (tukor strategia)
Felhasznalo felismerese: a ZOLD P(Long) gorbe erős csúcsa valójában SHORT signal,
mert az ár 1-2 percen belül lefelé megy.
"""
import pandas as pd, numpy as np
from pathlib import Path

PREDS = Path('/data/LGBM_copilot/models/scalper/BTCUSD_v6_preds_20261018_141912.csv')
df = pd.read_csv(PREDS, index_col=0, parse_dates=True)
day = df.loc['2026-09-01'].copy().reset_index(drop=True)

pL_orig = day['p_long_2min'].values    # ZOLD gorbe (eredeti P(Long)) - ezek a csucsok SHORT-ot jeleznek
pS_orig = day['p_short_2min'].values
pN = day['p_noise_2min'].values
px = day['price'].values
n = len(day)

print('='*76)
print('FADE STRATEGIA: ZOLD P(Long) csucs -> SHORT pozicio')
print('='*76)
print()

# Hold period: 2 perc = 16 bar (7.42s/bar)
HOLD = 16

# Forward return mindig window: px[i+HOLD] / px[i] - 1
fwd = np.full(n, np.nan)
fwd[:-HOLD] = (px[HOLD:] / px[:-HOLD] - 1) * 100

# Short trade: SHORT-ba lépünk amikor P(Long) magas -> nyereseg = -fwd
# (ha az ar lefelé megy, a short nyer)

results = []
for label, mask_fn in [
    ('ZOLD P(Long) > 0.50 (1506 bar)', lambda: pL_orig > 0.50),
    ('ZOLD P(Long) > 0.55 (65 bar)', lambda: pL_orig > 0.55),
    ('ZOLD P(Long) Z>2.0 (93 csucs)', lambda: ((pL_orig - pL_orig.mean())/pL_orig.std()) > 2.0),
    ('ZOLD P(Long) Z>1.5 (~250)', lambda: ((pL_orig - pL_orig.mean())/pL_orig.std()) > 1.5),
    ('ZOLD P(Long) Z>1.0 (~450)', lambda: ((pL_orig - pL_orig.mean())/pL_orig.std()) > 1.0),
]:
    mask = mask_fn()
    cnt = int(mask.sum())
    if cnt == 0:
        continue
    r = fwd[mask]
    r = r[~np.isnan(r)]
    if len(r) == 0:
        continue
    short_ret = -r  # short: -forward return
    win_rate = (short_ret > 0).mean() * 100
    total = short_ret.sum()
    avg = short_ret.mean()
    # Egymást kizáró tradek: ugyanabban az időablakban ne legyen átfedés
    # (rough: vagyunk konzervatív, feltételezzük 1 trade / csúcs, de a 16 bar hold miatt átfedés lehet)
    print(f'  {label}')
    print(f'    Tradek: {len(r)} | Total P&L (short): {total:+.3f}% | avg/trade: {avg:+.4f}% | WR: {win_rate:.1f}%')
    print()
    results.append((label, len(r), total, avg, win_rate))

print('='*76)
print('OSSZEHASONLITAS EREDETI V6 BACKTEST-TEL:')
print('='*76)
print('Eredeti V6 (marker alapu): +9.18% total (1 nap, 4048 trade, WR=56.9%)')
print()

# Most: az eredeti V6 signal_2min == 1 (zold marker Long) -> ezek valójában SHORT-ot kene jelentenek
# Az eloző backtest-ben ezek Long pozícióként voltak szamolva (+2.50%)
# FADE-kent Short pozíciókent: -forward_return
sig = day['signal_2min'].values
long_marker = (sig == 1)   # zold haromszog = eredeti V6 Long
short_marker = (sig == -1) # piros haromszog = eredeti V6 Short

print('--- EREDETI V6 MARKER FADE STRATEGIA ---')
print('Ha a marker-ek is fade-k (tukor):')
print('  ZOLD Long marker (1480 db) -> SHORT pozicio')
r = fwd[long_marker]
r = r[~np.isnan(r)]
print(f'    Total P&L: {-r.sum():+.3f}% | WR: {(-r > 0).mean()*100:.1f}% | avg: {-r.mean():+.4f}%')
print('  PIROS Short marker (2568 db) -> LONG pozicio')
r = fwd[short_marker]
r = r[~np.isnan(r)]
print(f'    Total P&L: {r.sum():+.3f}% | WR: {(r > 0).mean()*100:.1f}% | avg: {r.mean():+.4f}%')
print()
print(f'  FADE Total: {-fwd[long_marker].sum() + fwd[short_marker].sum():+.3f}%')
print(f'  (Eredeti V6 Total: +9.18% volt)')
