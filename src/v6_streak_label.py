import pandas as pd, numpy as np
from pathlib import Path

PREDS = Path('/data/LGBM_copilot/models/scalper/BTCUSD_v6_preds_20261018_141912.csv')
df = pd.read_csv(PREDS, index_col=0, parse_dates=True)

pL = df['p_long_2min'].values
pS = df['p_short_2min'].values
close = df['close'].values
open_ = df['open'].values
bull = close >= open_
bear = ~bull

# 1) Bear streak hossz vs. predikcio
# Szamoljuk: ha egymas utan N bear gyertya van, 
# az N-ediknel milyen a P(Long) vs P(Short)?

bear_streak = np.zeros(len(df), dtype=int)
for i in range(1, len(df)):
    if bear[i]:
        bear_streak[i] = bear_streak[i-1] + 1
    else:
        bear_streak[i] = 0

bull_streak = np.zeros(len(df), dtype=int)
for i in range(1, len(df)):
    if bull[i]:
        bull_streak[i] = bull_streak[i-1] + 1
    else:
        bull_streak[i] = 0

print('BEAR STREAK vs PREDIKCIO')
print('='*70)
print(f'{"streak_hossz":>12} | {"darab":>8} | {"P(Long)":>8} | {"P(Short)":>8} | {"P(L)>P(S)%":>8} | {"flip P(S)>P(L)%":>15}')
print('-'*70)
for k in range(0, 11):
    mask = bear_streak == k
    n_k = mask.sum()
    if n_k < 100:
        continue
    mean_pL = pL[mask].mean()
    mean_pS = pS[mask].mean()
    pct_orig_long = np.mean(pL[mask] > pS[mask]) * 100
    pct_flip_long = np.mean(pS[mask] > pL[mask]) * 100  # flip: P(S) erteket longnak
    print(f'{k:>12} | {n_k:>8,} | {mean_pL:>8.4f} | {mean_pS:>8.4f} | {pct_orig_long:>7.1f}% | {pct_flip_long:>14.1f}%')

print()
print('BULL STREAK vs PREDIKCIO')
print('='*70)
print(f'{"streak_hossz":>12} | {"darab":>8} | {"P(Long)":>8} | {"P(Short)":>8} | {"P(L)>P(S)%":>8} | {"flip P(S)>P(L)%":>15}')
print('-'*70)
for k in range(0, 11):
    mask = bull_streak == k
    n_k = mask.sum()
    if n_k < 100:
        continue
    mean_pL = pL[mask].mean()
    mean_pS = pS[mask].mean()
    pct_orig_long = np.mean(pL[mask] > pS[mask]) * 100
    pct_flip_long = np.mean(pS[mask] > pL[mask]) * 100
    print(f'{k:>12} | {n_k:>8,} | {mean_pL:>8.4f} | {mean_pS:>8.4f} | {pct_orig_long:>7.1f}% | {pct_flip_long:>14.1f}%')

# 2) Cumulative return bear streak kozben
print()
print('CUMULATIVE RETURN BEAR STREAK KÖZBEN')
print('='*70)
# Ha bear streak >= 3, szamoljuk a cumulative return-t az egesz streak-re
# Eredeti: Long pozicio (P(L)>P(S)) -> vesztunk egy downtrend-ben
# Flip: Short pozicio (P(S)>P(L)) -> nyerunk egy downtrend-ben

# Vegyunk konkret peldat: 08.21 12:00 kornyek
sub = df.loc['2026-08-21 11:55':'2026-08-21 12:15']
sub_bear = sub[sub['close'] < sub['open']]
sub_bull = sub[sub['close'] >= sub['open']]
print(f'08.21 11:55-12:15: {len(sub)} tick, {len(sub_bear)} BEAR, {len(sub_bull)} BULL')

# Bear streak-ek az idoszakban
prices = sub['close'].values
is_bear = (sub['close'] < sub['open']).values

streaks = []
curr_streak = []
for i in range(len(is_bear)):
    if is_bear[i]:
        curr_streak.append(i)
    else:
        if len(curr_streak) >= 3:
            streaks.append(curr_streak[:])
        curr_streak = []
if len(curr_streak) >= 3:
    streaks.append(curr_streak[:])

print(f'  3+ hosszu bear streak-ek: {len(streaks)}')
for s in streaks[:5]:
    start_i, end_i = s[0], s[-1]
    ret = prices[end_i] - prices[start_i]
    mean_pL_streak = sub.iloc[s]['p_long_2min'].mean()
    mean_pS_streak = sub.iloc[s]['p_short_2min'].mean()
    t0 = sub.index[s[0]].strftime('%H:%M:%S')
    t1 = sub.index[s[-1]].strftime('%H:%M:%S')
    print(f'    {t0}-{t1} ({len(s)} tick) ret={ret:+.1f} P(L)={mean_pL_streak:.3f} P(S)={mean_pS_streak:.3f} eredeti=Long FLIP=Short')

