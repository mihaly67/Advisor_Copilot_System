#!/usr/bin/env python3
"""Regime Grid Sweep — eredmények elemzése per horizon"""
import pandas as pd

df = pd.read_csv('/data/LGBM_copilot/charts/regime_grid_sweep_results.csv')

# Baseline from earlier OOS exam
bl = {
    '2min': {'wr': 0.554, 'contra': 0.207, 'ev': 0.142},
    '3min': {'wr': 0.558, 'contra': 0.197, 'ev': 0.140},
    '5min': {'wr': 0.559, 'contra': 0.204, 'ev': 0.142}
}

print('REGIME GRID SWEEP — BEST vs BASELINE per HORIZON')
print('=' * 70)

for hn in ['2min', '3min', '5min']:
    best = df[df.horizon == hn].sort_values('oos_ev_bar', ascending=False).iloc[0]
    b = bl[hn]
    wr_d = best.oos_wr - b['wr']
    c_d = best.oos_contra - b['contra']
    ev_d = best.oos_ev_bar - b['ev']
    print(f'\n{hn}:')
    print(f'  Baseline:  WR={b["wr"]:.1%}  contra={b["contra"]:.1%}  EV={b["ev"]:.3f}')
    print(f'  Optimized: WR={best.oos_wr:.1%}  contra={best.oos_contra:.1%}  EV={best.oos_ev_bar:.3f}')
    print(f'  Delta:     WR={wr_d:+.1%}  contra={c_d:+.1%}  EV={ev_d:+.3f}')
    print(f'  Params:    h={best.h_thr:.2f} ts={best.ts_thr:.1f} elev_thr={best.ts_elev:.1f} elev={best.elev_amt:.2f}')

print('\n\nBEST OOS WR per horizon (nem EV!):')
print('=' * 70)
for hn in ['2min', '3min', '5min']:
    best_wr = df[df.horizon == hn].sort_values('oos_wr', ascending=False).iloc[0]
    b = bl[hn]
    wr_d = best_wr.oos_wr - b['wr']
    print(f'{hn}: WR={best_wr.oos_wr:.1%}({wr_d:+.1%}) contra={best_wr.oos_contra:.1%} EV={best_wr.oos_ev_bar:.3f}')
    print(f'  Params: h={best_wr.h_thr:.2f} ts={best_wr.ts_thr:.1f} elev_thr={best_wr.ts_elev:.1f} elev={best_wr.elev_amt:.2f}')

print('\n\nBEST OOS CONTRA (legalacsonyabb) per horizon:')
print('=' * 70)
for hn in ['2min', '3min', '5min']:
    best_c = df[df.horizon == hn].sort_values('oos_contra', ascending=True).iloc[0]
    print(f'{hn}: WR={best_c.oos_wr:.1%} contra={best_c.oos_contra:.1%} EV={best_c.oos_ev_bar:.3f}')
    print(f'  Params: h={best_c.h_thr:.2f} ts={best_c.ts_thr:.1f} elev_thr={best_c.ts_elev:.1f} elev={best_c.elev_amt:.2f}')
