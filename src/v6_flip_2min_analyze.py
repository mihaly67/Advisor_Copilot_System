#!/usr/bin/env python3
"""V6 2min FLIP elemzs - piros gorbe = P(Long), zold gorbe = P(Short)
A chart megjelenites szerint ertelmezzuk a flip-et: a HTML-ben levo 'P(Long)' trace
zold szinu (eredeti), de a flip logika szerint ez SHORT predikcio.
A HTML-ben levo 'P(Short)' trace piros szinu (eredeti), de flip szerint LONG predikcio.
Tehat: FLIP_P_Long  = eredeti P(Short)  (piros gorbe)
       FLIP_P_Short = eredeti P(Long)  (zold gorbe)
"""
import pandas as pd, numpy as np
from pathlib import Path

PREDS = Path('/data/LGBM_copilot/models/scalper/BTCUSD_v6_preds_20261018_141912.csv')
df = pd.read_csv(PREDS, index_col=0, parse_dates=True)
day = df.loc['2026-09-01'].copy()

# FLIP logika: piros gorbe (eredeti P(Short)) -> P(Long)
#              zold gorbe (eredeti P(Long))  -> P(Short)
flip_pL = day['p_short_2min'].values  # piros gorbe = FLIP Long
flip_pS = day['p_long_2min'].values   # zold gorbe = FLIP Short
pN = day['p_noise_2min'].values
px = day['price'].values
idx = day.index
sig_orig = day['signal_2min'].values  # eredeti signal (-1, 0, 1)

print('='*72)
print('V6 2min FLIP ELEMZES - 2026-09-01 (BTCUSD bear day -1.83%)')
print('='*72)
print(f'Bars: {len(day):,} | Price: {px.min():.0f} -> {px.max():.0f} | ret: {(px[-1]/px[0]-1)*100:.2f}%')
print()
print('--- 1. ATLAGOS PREDIKCIO (FLIP logika) ---')
print(f'  Piros gorbe (FLIP P(Long))  avg={flip_pL.mean():.3f}  max={flip_pL.max():.3f}  P95={np.quantile(flip_pL,0.95):.3f}')
print(f'  Zold gorbe (FLIP P(Short)) avg={flip_pS.mean():.3f}  max={flip_pS.max():.3f}  P95={np.quantile(flip_pS,0.95):.3f}')
print(f'  Narancs (P(Noise))         avg={pN.mean():.3f}  max={pN.max():.3f}')
print()

print('--- 2. DOMINANCIA IDOBEN (melyik gorbe magasabb) ---')
diff = flip_pL - flip_pS  # piros - zold
long_dom = (diff > 0).sum()
short_dom = (diff < 0).sum()
tie = (diff == 0).sum()
print(f'  FLIP Long-dominant (piros>zold):  {long_dom:,} ({100*long_dom/len(day):.1f}%)')
print(f'  FLIP Short-dominant (zold>piros): {short_dom:,} ({100*short_dom/len(day):.1f}%)')
print(f'  Tie: {tie}')
print(f'  Erdekessg: eredeti V6-ban a P(Short) magasabb volt ({(day["p_short_2min"]>day["p_long_2min"]).sum():,} bar), igy FLIP-ben ez Long-dominanss valik')
print()

print('--- 3. SIGNAL GENERACIO (th=0.5 crossing) ---')
flip_long_sig = (flip_pL > 0.5) & (flip_pL > flip_pS)  # piros>0.5 es piros>zold
flip_short_sig = (flip_pS > 0.5) & (flip_pS > flip_pL)  # zold>0.5 es zold>piros
flip_noise = ~flip_long_sig & ~flip_short_sig
nL = flip_long_sig.sum()
nS = flip_short_sig.sum()
nN = flip_noise.sum()
print(f'  FLIP Long signal  (piros>0.5): {nL:,} ({100*nL/len(day):.1f}%)')
print(f'  FLIP Short signal (zold>0.5):  {nS:,} ({100*nS/len(day):.1f}%)')
print(f'  FLIP Noise:                    {nN:,} ({100*nN/len(day):.1f}%)')
print(f'  L/S ratio (FLIP): {nL/max(1,nS):.2f}  -> {"LONG-DOMINANS" if nL>nS else "SHORT-DOMINANS"}')
print(f'  (Eredeti V6 L/S ratio: {int((sig_orig==1).sum())/max(1,int((sig_orig==-1).sum())):.2f} volt)')
print()

print('--- 4. MARKER vs FLIP PREDIKCI KONZISZTENCIA (counter-trend) ---')
# eredeti Long marker (zold haromszog) -- a flip logika szerint SHORT kene legyen (zold=Short)
# eredeti Short marker (piros haromszog) -- a flip logika szerint LONG kene legyen (piros=Long)
long_marker_orig = (sig_orig == 1)   # eredeti zold haromszog
short_marker_orig = (sig_orig == -1) # eredeti piros haromszog

# Ha a marker konzisztens a FLIP predikcioval (gorbe>0.5)
# Long marker (zold) -> flip szerint short, ha zold gorbe > 0.5
marker_long_konzisztens = long_marker_orig & (flip_pS > 0.5)  # zold marker + zold>0.5
marker_short_konzisztens = short_marker_orig & (flip_pL > 0.5)  # piros marker + piros>0.5
print(f'  Eredeti Long marker (zold): {long_marker_orig.sum():,}')
print(f'    -> konzisztens FLIP Short-tal (zold>0.5): {marker_long_konzisztens.sum():,} ({100*marker_long_konzisztens.sum()/max(1,long_marker_orig.sum()):.1f}%)')
print(f'  Eredeti Short marker (piros): {short_marker_orig.sum():,}')
print(f'    -> konzisztens FLIP Long-gal (piros>0.5): {marker_short_konzisztens.sum():,} ({100*marker_short_konzisztens.sum()/max(1,short_marker_orig.sum()):.1f}%)')
print()

print('--- 5. ORANKENTI DOMINANCIA (melyik irany a legerosebb ora-ablakonkent) ---')
hourly = pd.DataFrame({'pL': flip_pL, 'pS': flip_pS, 'pN': pN, 'px': px}, index=idx)
h = hourly.groupby(hourly.index.hour).agg({'pL':'mean','pS':'mean','pN':'mean','px':['first','last']})
h.columns = ['pL','pS','pN','px_f','px_l']
h['ret_pct'] = (h['px_l']/h['px_f']-1)*100
h['dom'] = np.where(h['pL']>h['pS'],'LONG','SHORT')
print('  ora | pL(flip)  pS(flip)  pN     | price_ret% | dom')
print('  ----+-----------------------------------')
for hr, row in h.iterrows():
    print(f'  {hr:02d}:00 | {row.pL:.3f}   {row.pS:.3f}   {row.pN:.3f}  | {row.ret_pct:+.2f}%    | {row.dom}')
print()

print('--- 6. AMPLITUDO ANOMALIAK (Z-score a piros=Long gorben) ---')
flip_L_z = (flip_pL - flip_pL.mean()) / flip_pL.std()
flip_S_z = (flip_pS - flip_pS.mean()) / flip_pS.std()
flip_L_bursts = (flip_L_z > 2.5).sum()
flip_S_bursts = (flip_S_z > 2.5).sum()
print(f'  Piros gorbe (FLIP Long) Z>2.5 burst-ek: {flip_L_bursts}')
print(f'  Zold gorbe (FLIP Short) Z>2.5 burst-ek: {flip_S_bursts}')
top5_L = day.iloc[np.argsort(-flip_L_z)[:5]][['price']].copy()
top5_L['z'] = np.sort(-flip_L_z)[:5] * -1
top5_L['pL_flip'] = flip_pL[np.argsort(-flip_L_z)[:5]]
print('  Top-5 FLIP Long burst idopontok:')
for ts, r in top5_L.iterrows():
    print(f'    {ts} | price={r.price:.0f} | z={r.z:.2f} | piros_gorbe={r.pL_flip:.3f}')
print()

print('--- 7. BACKTEST SIMULATION (FLIP vs EREDETI, long-only/short-only) ---')
# EGY BAR-on 2min horizon = 2 percig tart pozicio
# Eredeti V6: Long marker (sig==1) -> vasarol, 2min mulva elad
# FLIP: eredeti Long marker -> SHORT pozicio (flip), eredeti Short marker -> LONG pozicio
next_ret = np.zeros(len(day))
next_ret[:-1] = (px[1:] / px[:-1] - 1) * 100  # kovetkezo bar return %

orig_long_ret = next_ret[long_marker_orig[:-1]].sum() if long_marker_orig.sum() > 0 else 0
orig_short_ret = -next_ret[short_marker_orig[:-1]].sum() if short_marker_orig.sum() > 0 else 0
flip_long_ret = next_ret[short_marker_orig[:-1]].sum() if short_marker_orig.sum() > 0 else 0  # eredeti short marker -> FLIP long
flip_short_ret = -next_ret[long_marker_orig[:-1]].sum() if long_marker_orig.sum() > 0 else 0  # eredeti long marker -> FLIP short
print(f'  Eredeti V6 Long-only (zold marker): {orig_long_ret:+.2f}% ({long_marker_orig.sum()} trade)')
print(f'  Eredeti V6 Short-only (piros marker): {orig_short_ret:+.2f}% ({short_marker_orig.sum()} trade)')
print(f'  Eredeti V6 Total: {orig_long_ret+orig_short_ret:+.2f}%')
print(f'  FLIP Long-only (piros marker->long): {flip_long_ret:+.2f}% ({short_marker_orig.sum()} trade)')
print(f'  FLIP Short-only (zold marker->short): {flip_short_ret:+.2f}% ({long_marker_orig.sum()} trade)')
print(f'  FLIP Total: {flip_long_ret+flip_short_ret:+.2f}%')
print(f'  Buy & Hold: {(px[-1]/px[0]-1)*100:+.2f}%')
print()

print('--- 8. KONKLUSZIO ---')
if orig_long_ret + orig_short_ret > flip_long_ret + flip_short_ret:
    print(f'  -> EREDETI V6 jobb ({orig_long_ret+orig_short_ret:+.2f}% vs FLIP {flip_long_ret+flip_short_ret:+.2f}%)')
    print('  -> A V6 eredeti Long/Short cimkek helyesek, FLIP-elve rosszabb')
else:
    print(f'  -> FLIP jobb ({flip_long_ret+flip_short_ret:+.2f}% vs EREDETI {orig_long_ret+orig_short_ret:+.2f}%)')
    print('  -> A V6 eredeti cimkek rosszak (tukor problema), FLIP-elve jobb')
