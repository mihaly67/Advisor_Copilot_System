#!/usr/bin/env python3
"""Test different dollar bar thresholds for TP=$30, horizon=3min"""
import numpy as np, pandas as pd

df = pd.read_csv('/data/dev/LGB_copilot_system/RAW_CSV/BTCUSD/BTCUSD_külön_vizsga.csv',
                 parse_dates=['Timestamp'], index_col='Timestamp')
df.columns = [c.lower().replace(' ', '_') for c in df.columns]
mid = ((df['bid'] + df['ask']) / 2).values
vol = (df['bid_volume'] + df['ask_volume']).values
dollars = mid * vol
ts_arr = df.index.values

print("Dollar bar threshold sweep (TP=$30, horizon=3min):\n")

for threshold in [5_000_000, 10_000_000, 50_000_000, 100_000_000]:
    bars = []
    cum_d = 0.0
    o = h = l = c = None
    t0 = None
    for i in range(len(mid)):
        d = dollars[i]
        if o is None:
            o = h = l = c = mid[i]; cum_d = d; t0 = ts_arr[i]; continue
        h = max(h, mid[i]); l = min(l, mid[i]); c = mid[i]; cum_d += d
        if cum_d >= threshold:
            bars.append({'t': t0, 'c': c})
            o = None; cum_d = 0.0

    nb = len(bars)
    if nb < 10:
        print(f"  ${threshold/1e6:.0f}M: too few bars ({nb})")
        continue

    bt = pd.Series([b['t'] for b in bars])
    avg_sec = bt.diff().dropna().dt.total_seconds().mean()

    # Label $30/3min on first 5000 bars
    closes = np.array([b['c'] for b in bars[:5000]])
    bts = pd.Series([b['t'] for b in bars[:5000]])
    nl = ns = 0
    n_test = len(closes)
    for i in range(n_test):
        entry = closes[i]
        t_lim = bts.iloc[i] + pd.Timedelta(seconds=180)
        for j in range(i + 1, n_test):
            if bts.iloc[j] > t_lim: break
            if closes[j] >= entry + 30: nl += 1; break
            elif closes[j] <= entry - 30: ns += 1; break

    sig = (nl + ns) / n_test
    neutral = 1 - sig
    print(f"  ${threshold/1e6:>5.0f}M: {nb:>6d} bars, avg {avg_sec:>6.1f}s/bar | "
          f"Long={nl/n_test:.1%} Short={ns/n_test:.1%} Neutral={neutral:.1%}")

print("\nCél: 15-30% signal rate, 70-85% neutral (modell tanulhasson!)")
