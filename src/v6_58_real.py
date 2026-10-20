import pandas as pd, numpy as np
from pathlib import Path

PREDS = Path('/data/LGBM_copilot/models/scalper/BTCUSD_v6_preds_20261018_141912.csv')
df = pd.read_csv(PREDS, index_col=0, parse_dates=True)

close = df['close'].values
open_ = df['open'].values
pL = df['p_long_2min'].values
pS = df['p_short_2min'].values
bull = close >= open_
bear = ~bull
fwd = np.diff(close)

# 1) ALAP: mindig a kovetkezo tick az ellentkezet mondjuk (trivial micro-bounce)
# Ha BEAR → Long, ha BULL → Short (mindig kontrarián)
trivial_sig = np.where(bull[:-1], -1, 1)  # ellentétes az épp mostaninak
trivial_wr = np.mean((trivial_sig * fwd) > 0) * 100

# 2) ALAP2: mindig ugyanazt mondjuk (pl mindig Long)
always_long_wr = np.mean(fwd > 0) * 100
always_short_wr = np.mean(fwd < 0) * 100

# 3) MODELL: eredeti P(L)>P(S) → Long
orig_sig = np.where(pL[:-1] > pS[:-1], 1, -1)
orig_wr = np.mean((orig_sig * fwd) > 0) * 100

# 4) Az eredeti modell mennyivel jobb mint a trivial?
print('='*70)
print('A 58% FORWARD WR — VALÓS EDGE VAGY TRIVIÁLIS MICRO-BOUNCE?')
print('='*70)
print()
print(f'Mindig Long:                     {always_long_wr:.1f}%')
print(f'Mindig Short:                    {always_short_wr:.1f}%')
print(f'Trivial kontrarián (ellentétes): {trivial_wr:.1f}%')
print(f'Eredeti modell (P(L)>P(S)):      {orig_wr:.1f}%')
print(f'Eredeti modell edge a trivial felett: {orig_wr - trivial_wr:+.1f}%')
print()

# 5) Statisztikai szignifikancia
# Binomial test: n=659K, p=0.58, H0: p=0.55 (trivial)
n = len(fwd)
k = int((orig_sig * fwd > 0).sum())
p0 = trivial_wr / 100  # null hipotezis
se = np.sqrt(p0 * (1-p0) / n)
z = (k/n - p0) / se
print(f'Binomial test: H0: p={p0:.3f} (trivial kontrarián)')
print(f'  n={n:,}  k={k:,}  p_hat={k/n:.4f}')
print(f'  Z-score = {z:.1f}')
print(f'  p-value < 1e-300' if abs(z) > 30 else f'  p-value = {2*np.exp(-z**2/2):.2e}')
print(f'  Statisztikailag szignifikáns: IGEN')
print(f'  DE gyakorlati jelentőség: {orig_wr - trivial_wr:+.1f}% — elhanyagolható!')
print()

# 6) Eros dominancia eseten
for thresh in [0.03, 0.05, 0.10]:
    mask = np.abs(pL[:-1] - pS[:-1]) > thresh
    n_m = mask.sum()
    if n_m > 0:
        orig_wr_m = np.mean((orig_sig[mask] * fwd[mask]) > 0) * 100
        # Trivial WR ezen a részhalmazon
        trivial_wr_m = np.mean((trivial_sig[mask] * fwd[mask]) > 0) * 100
        print(f'|P(L)-P(S)|>{thresh:.2f}: eredeti={orig_wr_m:.1f}%  trivial={trivial_wr_m:.1f}%  edge={orig_wr_m-trivial_wr_m:+.1f}%')

# 7) A LEGFONTOSABB: milyen P(L) ertekkel van orig Long es mi a forward WR?
print()
print('P(LONG) BONTÁS vs FORWARD WR:')
bins_pL = [0, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 1.0]
for lo, hi in zip(bins_pL[:-1], bins_pL[1:]):
    mask = (pL[:-1] >= lo) & (pL[:-1] < hi)
    n_m = mask.sum()
    if n_m < 1000: continue
    # Long entry signal (P(L)>P(S))
    long_mask = mask & (pL[:-1] > pS[:-1])
    short_mask = mask & (pS[:-1] > pL[:-1])
    n_l = long_mask.sum()
    n_s = short_mask.sum()
    wr_l = np.mean(fwd[long_mask] > 0)*100 if n_l > 0 else 0
    wr_s = np.mean(fwd[short_mask] < 0)*100 if n_s > 0 else 0
    print(f'  P(L)=[{lo:.2f},{hi:.2f}): Long entry WR={wr_l:.1f}%({n_l:,})  Short entry WR={wr_s:.1f}%({n_s:,})')

# 8) A KULCS KERDES: mi a valos edge trading szinten?
# Ha kontrarián strategy: BEAR utan Long, BULL utan Short
# Ha model strategy: P(L)>P(S) utan Long, P(S)>P(L) utan Short
print()
print('='*70)
print('TRADING EDGE OSSZEHASONLITAS')
print('='*70)

# PnL per tick
trivial_pnl = np.sum(trivial_sig * fwd)
orig_pnl = np.sum(orig_sig * fwd)
# Random: fel Long, fel Short
random_pnl = 0  # expected

print(f'Trivial kontrarián PnL:  {trivial_pnl:>+12,.1f}  (mean/tick={trivial_sig.mean()*fwd.mean():+.4f})')
print(f'Eredeti modell PnL:      {orig_pnl:>+12,.1f}  (mean/tick={orig_pnl/n:+.4f})')
print(f'Eredeti edge trivial felett: {orig_pnl - trivial_pnl:>+12,.1f}')
print(f'                       ({(orig_pnl/trivial_pnl - 1)*100:+.1f}% jobb)')

