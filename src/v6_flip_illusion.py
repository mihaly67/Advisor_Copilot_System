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

# EREDETI signal: P(L)>P(S)->Long, P(S)>P(L)->Short
orig_sig = np.where(pL > pS, 1, -1)
# FLIP signal: P(S)>P(L)->Long, P(L)>P(S)->Short  
flip_sig = np.where(pS > pL, 1, -1)

fwd1 = np.diff(close)  # 1 tick forward

print('='*80)
print('A FLIP ILLÚZIÓ — MIÉRT LÁTSZIK JÓL DE MIÉRT NEM AZ')
print('='*80)
print()

# 1) BACKWARD: az aktualis gyertya iranya egyezik-e a signallal
print('1) HÁTRANÉZŐ (jelenlegi gyertya irány vs signal):')
orig_back = np.mean(((bull[:-1] & (orig_sig[:-1]==1)) | (bear[:-1] & (orig_sig[:-1]==-1))))*100
flip_back = np.mean(((bull[:-1] & (flip_sig[:-1]==1)) | (bear[:-1] & (flip_sig[:-1]==-1))))*100
print(f'   EREDETI: {orig_back:.1f}% — rosszabb mint véletlen')
print(f'   FLIP:    {flip_back:.1f}% — jónak látszik')
print()

# 2) FORWARD 1 tick: a kovetkezo tick iranya
print('2) ELŐRENÉZŐ 1 tick (következő tick vs signal):')
orig_fwd = np.mean(((fwd1>0) & (orig_sig[:-1]==1)) | ((fwd1<0) & (orig_sig[:-1]==-1)))*100
flip_fwd = np.mean(((fwd1>0) & (flip_sig[:-1]==1)) | ((fwd1<0) & (flip_sig[:-1]==-1)))*100
print(f'   EREDETI: {orig_fwd:.1f}% — jobb mint véletlen')
print(f'   FLIP:    {flip_fwd:.1f}% — rosszabb mint véletlen')
print()

# 3) A KULCS: mi tortenik a kovetkezo tick-en BEAR utan?
bear_idx = np.where(bear[:-1])[0]
bull_idx = np.where(bull[:-1])[0]

print('3) MI TÖRTÉNIK BEAR GYERTYA UTÁN (a következő tick)?')
next_bull_after_bear = np.mean(bull[bear_idx+1])*100
next_bear_after_bear = np.mean(bear[bear_idx+1])*100
print(f'   Következő tick BULL (visszapattan): {next_bull_after_bear:.1f}%')
print(f'   Következő tick BEAR (folytatódik):  {next_bear_after_bear:.1f}%')
print()

print('4) MI TÖRTÉNIK BULL GYERTYA UTÁN (a következő tick)?')
next_bear_after_bull = np.mean(bear[bull_idx+1])*100
next_bull_after_bull = np.mean(bull[bull_idx+1])*100
print(f'   Következő tick BEAR (visszapattan): {next_bear_after_bull:.1f}%')
print(f'   Következő tick BULL (folytatódik):  {next_bull_after_bull:.1f}%')
print()

# 4) A modell megtanulta:
print('='*80)
print('A MODELL TANULÁSA:')
print('='*80)
print()
print('BEAR gyertya → EREDETI Long (P(L)>P(S)) → "ár pattan felfelé"')
print('  Ez 58%-ban igaz a következő tick-re (micro-bounce)!')
print('  A modell HELYESEN tanulta meg a 2 perces mean-reversion-t.')
print()
print('FLIP: BEAR gyertya → Short (P(S)>P(L)) → "ár esik tovább"')
print('  Ez csak 42%-ban igaz a következő tick-re!')
print('  DE vizualisan HELYESNEK látszik, mert az ÉPP MOSTANI irány Short!')
print()

# 5) A FELISMERES
print('='*80)
print('A FELISMERÉS — AMIT TE MONDTÁL:')
print('='*80)
print()
print('A FLIP "látszólag" a trendet követi, de ez ILLÚZIÓ:')
print('  - A modell idöben ELŐREHALADVA tanult (past → future)')
print('  - A modell megtanulta: BEAR → Long TP (visszapattanás)')
print('  - A FLIP csak a kimenetet cseréli fel: BEAR → Short')
print('  - De a belső tudás (súlyok, feature-k) NEM változott!')
print('  - A modell belső tudása azt mondja: "ár pattan felfelé"')
print('  - A FLIP ezt ellentétesre fordítja: "ár esik tovább"')
print('  - A valóság: 58%-ban pattan, 42%-ban esik → FLIP veszt!')
print()
print('A FLIP úgy néz ki mint ha "látná a jövőt", de valójában')
print('a JELENT mutatja helyesen (backward 77%), a JÖVŐT rosszul (forward 42%).')
print()

# 6) Szamoljuk ki: mennyire korrelal az eredeti signal az elozo tick iranyaval
print('5) KORRELÁCIÓ: signal vs ELŐZŐ tick irány (backward) vs KÖVETKEZŐ tick irány (forward):')
prev_dir = np.where(close[:-1] > open_[:-1], 1, -1)  # elozo tick iranya
next_dir = np.where(fwd1 > 0, 1, -1)  # kovetkezo tick iranya

# Korrelacio eredeti signallal
corr_prev_orig = np.mean(orig_sig[:-1] == prev_dir)*100
corr_next_orig = np.mean(orig_sig[:-1] == next_dir)*100
# Korrelacio flip signallal
corr_prev_flip = np.mean(flip_sig[:-1] == prev_dir)*100
corr_next_flip = np.mean(flip_sig[:-1] == next_dir)*100

print(f'   EREDETI vs előző tick: {corr_prev_orig:.1f}% (ellentétes!)')
print(f'   EREDETI vs következő tick: {corr_next_orig:.1f}% (helyes)')
print(f'   FLIP vs előző tick: {corr_prev_flip:.1f}% (helyes — ILLÚZIÓ!)')
print(f'   FLIP vs következő tick: {corr_next_flip:.1f}% (rossz)')

