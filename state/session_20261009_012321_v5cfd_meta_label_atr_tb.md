# Session: v5cfd_meta_label_atr_tb
*Időbélyeg: 2026-10-09T01:23:21.503220*

# V5 CFD Meta-labeling + ATR-normalizált TB (2026-10-09)

## Változtatások
1. **ATR-normalizált Triple Barrier**: PT=2.0×ATR, SL=2.0×ATR, MAX_BARS=15
   - Régi: PT=SL=$1.0 fix dollar → 0.4 ATR → az 1. bar mindig aktiválta → label = véletlen
   - Új: PT=SL=2×ATR14(bar) → $5 medián → valódi mozgásokat label-el
2. **Meta-labeling implementálva**:
   - Primary model: Fade CUSUM (UP→Short, DOWN→Long)
   - Secondary model (ML): eldönti take/skip
   - Meta-label: 1 ha primary signal profitál, 0 ha nem
3. **CUSUM_x_Bar interakció feature** = CUSUM_Direction × Bar_Direction

## Tréning eredmények (meta-label, 2×ATR barrier)
- Noise: 4,637 (30.6%) — jó, a barrier szűri az 1-bar zajt
- Take: 4,222 (50.3%) Skip: 4,178 (49.7%) — kiegyensúlyozott
- OOS AUC: 0.4973 (még ~0.50)
- Fade CUSUM + ML Conf filter: OOS WR=52.9%, Vizsga WR=52.7%

## Modell diagnózis
- AUC < 0.50 minden modellnél → a feature-k fundamentally nem prediktívek
- A momentum, S/R, trend feature-k MÚLTBELI információt kódolnak
- A jövőbeli 1-2 ATR mozgás iránya lényegében véletlenszerű ezek alapján
- P(Long) és P(Short) tükörképek 0.5-nél = a modell nem diszkriminatív

## Live XAUUSD
- Copilot fut 17 feature-rel, CUSUM_x_Bar interakcióval
- Signálok: LONG (CUSUM:↓ Fade:L ML:L | ML=CUSUM) — CUSUM és ML egyetért
- HUD subchart: index hiba (nem kritikus, a fő chart OK)

## Következő lépések
1. **Feature engineering**: RSI overbought/oversold, S/R proximity flags
2. **Hosszabb horizont**: 3×ATR barrier vagy fixed N-bar ahead labels
3. **Order flow feature-k**: ha elérhető (bid/ask volume, spread)
4. **Ensemble**: több modell kombinációja (LGBM + RF + NN)
