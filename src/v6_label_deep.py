import pandas as pd, numpy as np
from pathlib import Path

PREDS = Path('/data/LGBM_copilot/models/scalper/BTCUSD_v6_preds_20261018_141912.csv')
df = pd.read_csv(PREDS, index_col=0, parse_dates=True)
close = df['close'].values
open_ = df['open'].values

# Regenerljuk a TBM label-t es hasonltsuk ossze a predikcioval
# 2000 tick minta
tick_sec = 7  # ~7s per tick
horizon_sec = 120  # 2min
horizon = int(horizon_sec / tick_sec) + 1  # ~18 ticks
pt_m = 0.5; sl_m = 0.3

# ATR
atr = pd.Series(close).rolling(20).apply(lambda x: x.max()-x.min()).bfill().values

# TBM labeling 5000 tick
N = 5000; start = 100
y_long = np.zeros(N, dtype=int)
y_short = np.zeros(N, dtype=int)

for i in range(start, start+N):
    entry = close[i]; a = atr[i] if atr[i]>0 else entry*0.001
    ltp = entry + pt_m*a; lsl = entry - sl_m*a
    stp = entry - pt_m*a; ssl = entry + sl_m*a
    end = min(i + horizon + 1, len(close))
    for j in range(i+1, end):
        if close[j]>=ltp: y_long[i-start]=1; break
        if close[j]<=lsl: y_long[i-start]=-1; break
    else: y_long[i-start]=0
    for j in range(i+1, end):
        if close[j]<=stp: y_short[i-start]=1; break
        if close[j]>=ssl: y_short[i-start]=-1; break
    else: y_short[i-start]=0

bull = close[start:start+N] >= open_[start:start+N]
bear = ~bull

# A KULCS KERDES: milyen a label ELosZLAS BEAR gyertyanal?
# y_long=1 (TP hit) ha az ar FEL megy a kovetkezo 2 percben
# Ha BEAR utan gyakran y_long=1, az az mean-reversion a LABEL-ben

print('TBM LABEL vs JELENLEGI GYERTYA IRANY')
print('='*70)
print()
print('LONG LABEL (y_long) — TP=FEL, SL=LE:')
for val, name in [(1,'TP (ar FEL)'), (-1,'SL (ar LE)'), (0,'Noise')]:
    mask = y_long == val
    n = mask.sum()
    if n > 0:
        b = np.mean(bull[mask])*100
        be = np.mean(bear[mask])*100
        print(f'  y_long={val:+d} ({name:>12}): {n:>5}  BULL={b:.1f}%  BEAR={be:.1f}%')

print()
print('SHORT LABEL (y_short) — TP=LE, SL=FEL:')
for val, name in [(1,'TP (ar LE)'), (-1,'SL (ar FEL)'), (0,'Noise')]:
    mask = y_short == val
    n = mask.sum()
    if n > 0:
        b = np.mean(bull[mask])*100
        be = np.mean(bear[mask])*100
        print(f'  y_short={val:+d} ({name:>12}): {n:>5}  BULL={b:.1f}%  BEAR={be:.1f}%')

# MOST A KULCS: a tanitas label
# ylc = (y_long == 1).astype(int)
# ylc=1 ha y_long=1 (Long TP hit = ar FEL megy)
# ylc=0 ha y_long=-1 (Long SL = ar LE megy) VAGY y_long=0 (noise)

print()
print('TANITASI LABEL (ylc) vs GYERTYA IRANY:')
print('  ylc=1 → Long TP (ar FEL a kovetkezo 2 percben):')
lt = y_long == 1
print(f'    BULL gyertya: {np.mean(bull[lt])*100:.1f}%')
print(f'    BEAR gyertya: {np.mean(bear[lt])*100:.1f}%')
print('  ylc=0 → Long SL vagy noise (ar LE vagy semmi):')
l0 = y_long != 1
print(f'    BULL gyertya: {np.mean(bull[l0])*100:.1f}%')
print(f'    BEAR gyertya: {np.mean(bear[l0])*100:.1f}%')

print()
print('='*70)
print('FELISMERES:')
print('Ha Long TP (ylc=1) tobbnyire BEAR utan jon,')
print('a modell BEAR-t tanul Long TP-hez asszocialni.')
print('=> BEAR utan P(Long) magas => KONTRARIAN a label!')
print()
print('DE: ez NEM jelenti azt, hogy a modell rossz!')
print('A model PELDÁUL azt tanulta: "BEAR utan 32%-ban Long TP,')
print('BULL utan csak X%-ban" => BEAR utan nagyobb P(Long).')
print('Ez PONTOS a label-ekre, de VIZUALISAN ellentetes!')

# Szamoljuk ki: milyen gyakran Long TP BULL utan vs BEAR utan?
bull_tp = np.sum(bull & (y_long==1))
bull_all = np.sum(bull)
bear_tp = np.sum(bear & (y_long==1))
bear_all = np.sum(bear)

print()
print(f'Long TP gyakorisag:')
print(f'  BULL utan: {bull_tp}/{bull_all} = {bull_tp/bull_all*100:.1f}%')
print(f'  BEAR utan: {bear_tp}/{bear_all} = {bear_tp/bear_all*100:.1f}%')
print()
if bear_tp/bear_all > bull_tp/bull_all:
    print('  => BEAR utan TOBB a Long TP! (mean-reversion a label-ben)')
    print('  => A model helyesen tanulja: BEAR utan nagyobb P(Long TP)')
    print('  => De vizualisan ez LOOKS LIKE ellentetes predikcio!')

