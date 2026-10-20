import pandas as pd, numpy as np
from pathlib import Path

PREDS = Path('/data/LGBM_copilot/models/scalper/BTCUSD_v6_preds_20261018_141912.csv')
df = pd.read_csv(PREDS, index_col=0, parse_dates=True)

# 08.21 11:55-12:15 — a konkret drawdown
sub = df.loc['2026-08-21 11:55':'2026-08-21 12:15']

print('08.21 11:55-12:15 — LEPENGES RESZLET')
print('='*130)
print(f'{"time":<11} | {"price":>8} | {"candle":>5} | {"P(L)":>6} | {"P(S)":>6} | {"eredeti":>7} | {"flip":>7} | {"fwd_ret":>7} | {"orig_pnl":>8} | {"flip_pnl":>8} | {"orig_cum":>8} | {"flip_cum":>8}')
print('-'*130)

close = sub['close'].values
open_ = sub['open'].values
pL = sub['p_long_2min'].values
pS = sub['p_short_2min'].values

orig_sig = np.where(pL > pS, 1, -1)
flip_sig = np.where(pS > pL, 1, -1)

orig_cum = 0; flip_cum = 0
for i in range(len(sub)-1):
    t = sub.index[i].strftime('%H:%M:%S')
    candle = 'BULL' if close[i] >= open_[i] else 'BEAR'
    fwd = close[i+1] - close[i]
    
    orig_s = 'LONG' if orig_sig[i]==1 else 'SHRT'
    flip_s = 'LONG' if flip_sig[i]==1 else 'SHRT'
    
    op = orig_sig[i] * fwd
    fp = flip_sig[i] * fwd
    orig_cum += op
    flip_cum += fp
    
    mark = ''
    # Jeloljuk ha BEAR gyertya de eredeti Long-ot mond
    if candle == 'BEAR' and orig_sig[i] == 1:
        mark = ' ← BEAR+Long=HIBAS'
    elif candle == 'BULL' and orig_sig[i] == -1:
        mark = ' ← BULL+Short=HIBAS'
    
    print(f'{t:<11} | {close[i]:>8.1f} | {candle:>5} | {pL[i]:.3f} | {pS[i]:.3f} | {orig_s:>7} | {flip_s:>7} | {fwd:>+7.1f} | {op:>+8.1f} | {fp:>+8.1f} | {orig_cum:>+8.1f} | {flip_cum:>+8.1f}{mark}')

print()
print(f'VEGSUM: eredeti={orig_cum:+.1f}  flip={flip_cum:+.1f}')
print(f'Arfolyam valtozas: {close[-1]-close[0]:+.1f}')

# A KULCS: ha bear trend van, az eredeti Long pozicioban van
# Es a kovetkezo tick-re 58%-ban helyes (mert micro-bounce van)
# De VIZUALISAN a user latja: BEAR trend + Long predikcio = HIBAS

print()
print('='*80)
print('MAGYARZAT A KETTO KÖZÖTTI ELLENTMONDÁSRA:')
print('='*80)
print('A PnL POZITIV mert:')
print('  - Eredeti Long JELEN (BEAR gyertya) → forward tick 58%-ban BULL (micro-bounce)')
print('  - A micro-bounce-ok osszesen tobbet hoznak mint a trend-veszteseg')
print()
print('DE a user VIZUALISAN latja:')
print('  - Folyamatos BEAR trend → modell folyamatosan Long-ot mond → HIBAS')
print('  - A micro-bounce-ok nem latszanak, csak a trend iranya')
print()
print('A KERDES: melyik a valosag?')
print('  - PnL szint: eredeti nyer (micro-bounce scalping)')
print('  - Trend szint: eredeti veszt (trend-ellenes pozicio)')
print('  - Vizualis: eredeti hibas (görbe ellentétes a trenddel)')

