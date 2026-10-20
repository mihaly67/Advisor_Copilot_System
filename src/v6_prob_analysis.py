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

print('='*80)
print('A VALÓDI PROBLÉMA: P(LONG) MAGAS → DE MIÉRT?')
print('='*80)
print()

# P(Long) magas → eredeti Long jelez → de az EREDETI Long entry forward WR:
# P(L)=[0.00,0.35): Long entry WR=0.0%(0)     ← NINCS Long entry (P(L) alacsony)
# P(L)=[0.35,0.40): Long entry WR=48.1%       ← 48%! 50% ALATT!
# P(L)=[0.40,0.45): Long entry WR=52.4%       ← alig 52%
# P(L)=[0.45,0.50): Long entry WR=57.1%       ← ez már jobb
# P(L)=[0.50,0.55): Long entry WR=58.8%
# P(L)=[0.55,0.60): Long entry WR=60.4%
# P(L)=[0.60,1.00): Long entry WR=65.1%

# Tehat: ha P(L) > 0.50, a forward WR 58-65%
# De: P(L)=[0.35,0.40) eseten Long entry WR=48% — 50% ALATT!
# Ha ez VALOSZINUSEG, akkor 48% LEHETETLEN!

print('P(Long) ÉRTÉK vs FORWARD WR (Long entry-k):')
print('Amikor P(Long)>P(Short) és modell Long-ot jelez:')
print()
bins = [(0.30,0.35),(0.35,0.40),(0.40,0.45),(0.45,0.50),(0.50,0.55),(0.55,0.60),(0.60,0.70)]
for lo, hi in bins:
    mask = (pL[:-1] >= lo) & (pL[:-1] < hi) & (pL[:-1] > pS[:-1])
    n_m = mask.sum()
    if n_m < 100: continue
    wr = np.mean(fwd[mask] > 0)*100
    mean_pL = pL[:-1][mask].mean()
    mean_pS = pS[:-1][mask].mean()
    gap = wr - mean_pL*100
    print(f'  P(L)=[{lo:.2f},{hi:.2f}): n={n_m:>7,}  mean_P(L)={mean_pL:.3f}  forward WR={wr:.1f}%  gap={gap:+.1f}%')

print()
print('P(Short) ÉRTÉK vs FORWARD WR (Short entry-k):')
print('Amikor P(Short)>P(Long) és modell Short-ot jelez:')
print()
for lo, hi in bins:
    mask = (pS[:-1] >= lo) & (pS[:-1] < hi) & (pS[:-1] > pL[:-1])
    n_m = mask.sum()
    if n_m < 100: continue
    wr = np.mean(fwd[mask] < 0)*100  # Short WR: forward < 0
    mean_pS = pS[:-1][mask].mean()
    mean_pL = pL[:-1][mask].mean()
    gap = wr - mean_pS*100
    print(f'  P(S)=[{lo:.2f},{hi:.2f}): n={n_m:>7,}  mean_P(S)={mean_pS:.3f}  forward WR={wr:.1f}%  gap={gap:+.1f}%')

print()
print('='*80)
print('HA P(LONG) VALÓS VALÓSZÍNŰSÉG, AKKOR:')
print('  P(L)=0.40 → 40%-ban Long TP → forward WR ≥ 40%')
print('  De ha forward WR=48% > P(L)=40%, az NEM ellentmondás')
print('  Mert P(L) = P(TP hit first), nem P(next tick up)')
print('  A next tick up valószínűség más! (micro-bounce)')
print()
print('A VALÓDI PROBLÉMA:')
print('  P(Long) = P(TP ér el először 2 percen belül)')
print('  De a modell NEM P(next tick up)-ot prediktálja!')
print('  A P(Long) az 1.5×ATR TP elérésének valószínűsége')
print('  Nem a következő tick irányának valószínűsége')
print()

# AMI A LEGFONTOSABB: P(L)+P(S) nem = 1
print(f'P(L)+P(S) atlag = {(pL+pS).mean():.4f}')
print(f'P(L)+P(S) min = {(pL+pS).min():.4f}')
print(f'P(L)+P(S) max = {(pL+pS).max():.4f}')
print()
print('P(L) és P(S) KÜLÖN modellből jönnek (2 LightGBM)')
print('P(L) = P(y_long=1 | features) = P(TP_long hit first)')
print('P(S) = P(y_short=1 | features) = P(TP_short hit first)')
print('Ezek NEM komplementer valószínűségek!')
print('P(L)+P(S) ≠ 1, mert a noise (y=0) semelyik sem')

# A TENY: bear utan P(L) magas, bull utan P(S) magas
# Ez a TBM label struktúrából jon, nem bug
print()
print('='*80)
print('TENY: bear után P(Long) magas, bull után P(Short) magas')
print('OK: P(Long) = P(ar FEL megy 0.5×ATR-t 2 percen belül | BEAR)')
print('    = 37.9% (tényleges a label-ekben)')
print('    P(ar FEL megy 0.5×ATR-t 2 percen belül | BULL) = 30.5%')
print('')
print('A modell ezt tanulta: BEAR → nagyobb P(Long TP)')
print('És EZ HELYES a label-ekre! (mean-reversion a 2 perces TMB-ban)')
print('')
print('DE: a V6 feature-k NEM elégők a forward irány predikciójához')
print('A modell csak a kontrarián label-t tudja, nem a trendet')

