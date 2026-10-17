# Session: lepes1_calibration_eredmeny_20260924
*Időbélyeg: 2026-09-24T14:48:49.235141*

LÉPÉS 1: ISOTONIC/PLATT CALIBRATION — EREDMÉNYEK (2026-09-24)

=== ÖSSZEHASONLÍTÁS ===
Method       AUC    Brier   P-range      IQR    BestTh  Profit   Win%  Trades
RAW         0.5333  0.2504  0.234-0.870  0.0784  0.30   3257.0$  50.8%  6214
ISOTONIC    0.5233  0.2494  0.432-0.799  0.0248  0.30   3258.0$  50.8%  6228
PLATT       0.5278  0.2494  0.435-0.633  0.0211  0.30   3258.0$  50.8%  6228
BASELINE       —       —         —          —      —    3258.0$  50.8%  6228

=== KULCS MEGÁLLAPÍTÁSOK ===

1. AUC CSÖKKENT a kalibráció hatására!
   - RAW=0.5333 → ISOTONIC=0.5233 → PLATT=0.5278
   - CalibratedClassifierCV cv=3 ensemble-je rontja a diszkriminációt

2. P(trade) ELOSZLÁS NEM SZÉLESSEDETT — SZŰKÜLETT!
   - RAW: IQR=0.0784, Range=0.6354 (0.234-0.870)
   - ISOTONIC: IQR=0.0248, Range=0.3676 (0.432-0.799) — 3x szűkebb!
   - PLATT: IQR=0.0211, Range=0.1980 (0.435-0.633) — 4x szűkebb!
   - Isotonic regression a base rate-hez (~50.8%) közelíti a probabilitásokat

3. Brier score marginálisan javult (0.2504 → 0.2494) — de ez nem konvertálód profitra

4. Profit = BASELINE minden módszernél — a meta modell NEM ad hozzá értéket

5. RAW kalibrációs görbe:
   - Alacsony P (0.271): Actual=0.357 → UNDER-prediction (több win mint várt)
   - Magas P (0.824): Actual=0.667 → OVER-prediction (kevesebb win mint várt)
   - A modell rosszul kalibrált a széleken, de közel van a base rate-hez

6. Érdeges: RAW th=0.65 → 284 trades, 65.5% win, $274 profit
   - magas küszöbnél valóban javul a win rate, de túl kevés trade

=== VERDIKT: LÉPÉS 1 KUDARCOT VALLOTT ===
- A kalibráció nem segített — a probléma nem kalibrációs, hanem diszkriminációs
- AUC≈0.53 = alig jobb a randomnál
- A P(trade) distribúció szűkülése miatt kevesebb threshold resolution
- A meta modell NEM tud megkülönböztetni jó és rossz trade-eket

=== KÖVETKEZTETÉS ===
A kalibráció nem oldja meg a problémát. A meta_v1 alapvető gyengesége:
- AUC=0.53 → a feature-ök nem hordoznak elég információt a trade minőség előrejelzéséhez
- A primary model (Slope_Close_14) trend-following → QuantAlgo2 insight: "trend-following HURT by meta filter"

KÖVETKEZŐ LÉPÉS: Lépés 2 (Focal loss) — közvetlenül a diszkriminációt javítja