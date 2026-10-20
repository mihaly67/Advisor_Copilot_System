#!/usr/bin/env python3
"""Keresünk olyan regime config-ot ami MINDHÁROM horizon-ra javít vagy tart"""
import pandas as pd
import numpy as np

df = pd.read_csv('/data/LGBM_copilot/charts/regime_grid_sweep_results.csv')

bl = {
    '2min': {'wr': 0.554, 'contra': 0.207, 'ev': 0.142},
    '3min': {'wr': 0.558, 'contra': 0.197, 'ev': 0.140},
    '5min': {'wr': 0.559, 'contra': 0.204, 'ev': 0.142}
}

# Pivot: minden (h_thr, ts_thr, ts_elev, elev_amt) kombináció → 3 horizon eredmény
configs = df.groupby(['h_thr', 'ts_thr', 'ts_elev', 'elev_amt'])

results = []
for key, group in configs:
    if len(group) != 3:  # kell mind3 horizon
        continue
    h_t, ts_t, ts_e, e_a = key
    score = 0
    min_wr_delta = 999
    sum_wr_delta = 0
    sum_contra_delta = 0
    sum_ev_delta = 0
    for _, row in group.iterrows():
        hn = row['horizon']
        b = bl[hn]
        wr_d = row['oos_wr'] - b['wr']
        c_d = row['oos_contra'] - b['contra']
        ev_d = row['oos_ev_bar'] - b['ev']
        sum_wr_delta += wr_d
        sum_contra_delta += c_d
        sum_ev_delta += ev_d
        min_wr_delta = min(min_wr_delta, wr_d)
    results.append({
        'h_thr': h_t, 'ts_thr': ts_t, 'ts_elev': ts_e, 'elev_amt': e_a,
        'sum_wr_delta': sum_wr_delta,
        'sum_contra_delta': sum_contra_delta,
        'sum_ev_delta': sum_ev_delta,
        'min_wr_delta': min_wr_delta,
    })

rdf = pd.DataFrame(results)
print(f'  {len(rdf)} config with all 3 horizons')
print(f'  Columns: {list(rdf.columns)}')
if len(rdf) == 0:
    print('  ❌ Nincs config mind3 horizon-ra!')
    exit()

print('KERESÉS: Config ami MINDHÁROM horizon-ra JAVÍT vagy TART')
print('=' * 70)

# 1. Legalább nem rontja a WR-t sehol (min_wr_delta >= -0.5%)
good = rdf[rdf['min_wr_delta'] >= -0.005].sort_values('sum_contra_delta', ascending=True)
print(f'\nConfig-ok ahol min_WR_delta >= -0.5%: {len(good)}')
for i, (_, r) in enumerate(good.head(10).iterrows()):
    print(f'  {i+1}. h={r.h_thr:.2f} ts={r.ts_thr:.1f} elev_thr={r.ts_elev:.1f} elev={r.elev_amt:.2f}')
    print(f'     ΣWR={r.sum_wr_delta:+.1%} Σcontra={r.sum_contra_delta:+.1%} ΣEV={r.sum_ev_delta:+.3f} min_WR={r.min_wr_delta:+.1%}')

# 2. Szumma EV javulás + min_WR nem ront
print(f'\n\nTop-10 by ΣEV (min_WR >= -1%):')
good2 = rdf[rdf['min_wr_delta'] >= -0.01].sort_values('sum_ev_delta', ascending=False)
for i, (_, r) in enumerate(good2.head(10).iterrows()):
    print(f'  {i+1}. h={r.h_thr:.2f} ts={r.ts_thr:.1f} elev_thr={r.ts_elev:.1f} elev={r.elev_amt:.2f}')
    print(f'     ΣWR={r.sum_wr_delta:+.1%} Σcontra={r.sum_contra_delta:+.1%} ΣEV={r.sum_ev_delta:+.3f} min_WR={r.min_wr_delta:+.1%}')

# 3. Minden detail a legjobb összes config-hoz
print(f'\n\nDETAIL a legjobb config-hoz (by Σcontra, min_WR>=-0.5%):')
if len(good) > 0:
    best_key = good.iloc[0]
    detail = df[(df.h_thr == best_key.h_thr) & (df.ts_thr == best_key.ts_thr) &
                (df.ts_elev == best_key.ts_elev) & (df.elev_amt == best_key.elev_amt)]
    for _, r in detail.iterrows():
        b = bl[r['horizon']]
        print(f'  {r["horizon"]}: WR={r.oos_wr:.1%}({r.oos_wr-b["wr"]:+.1%}) contra={r.oos_contra:.1%}({r.oos_contra-b["contra"]:+.1%}) EV={r.oos_ev_bar:.3f}({r.oos_ev_bar-b["ev"]:+.3f})')
