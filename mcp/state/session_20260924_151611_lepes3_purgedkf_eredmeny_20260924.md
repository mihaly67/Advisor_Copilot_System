# Session: lepes3_purgedkf_eredmeny_20260924
*Időbélyeg: 2026-09-24T15:16:11.953654*

LÉPÉS 3: PURGED K-FOLD + EMBARGO — EREDMÉNYEK (2026-09-24)

=== ÖSSZEHASONLÍTÁS ===
Method              AUC   Brier  BestTh   Profit   Win%  Trades
Baseline(80/20)    0.5333  0.2504    0.30  3257.0$  50.8%    6214
Fold 1             0.5264  0.2503    0.30  2788.0$  51.3%    5183
Fold 2             0.5229  0.2512    0.30  2611.0$  50.1%    5186
Fold 3             0.5309  0.2510    0.30  2876.0$  51.9%    5170
Fold 4             0.5375  0.2501    0.35  2834.0$  51.7%    5131
Fold 5             0.5205  0.2522    0.30  2658.0$  50.4%    5184
OOS Aggregated     0.5272  0.2509    0.30 13765.0$  51.1%   25898
BASELINE(all OOS)     —       —       — 13773.0$  51.0%   25950

=== KULCS MEGÁLLAPÍTÁSOK ===

1. AUC STABIL, DE ALACSONY: mean=0.5276 ± 0.0060 (range 0.5205-0.5375)
   - A baseline 80/20 AUC=0.5333 a legjobb — de ez overfit lehet
   - A 5 fold mindegyike 0.52-0.54 között — nagyon stabil, de alig jobb a randomnál
   - Nincs egyetlen fold sem ahol AUC > 0.54!

2. PROFIT = BASELINE minden fold-ban és aggregated-ben is
   - OOS Agg profit=$13,765 vs baseline $13,773 → meta modell NEM ad hozzá
   - Minden fold-ban profit < baseline (trade-ek kihagyása csak csökkenti a profitot)

3. FOLD VARIANCE ALACSONY: AUC std=0.006, profit std=$102
   - A modell nagyon stabil across time → nem overfitting
   - DE a stabilitás nem jelent prediktív erőt

4. EMBARGO HATÁSA: 0% overlapping label volt, de 1% embargo még hasznos
   a rollback feature-ök miatt. Az eredmények nem változtak jelentősen.

5. LEGÉRDESESEBB FOLD: Fold 4 → AUC=0.5375, win=51.7%, th=0.35
   - Ez az egyetlen fold ahol th=0.35 a legjobb (nem th=0.30)
   - A többi fold-nál th=0.30 a legjobb

=== VERDIKT: LÉPÉS 3 KUDARCOT VALLOTT ===
- PurgedKFold nem javítja az AUC-t (0.5333 → 0.5272 aggregated)
- A validációs módszer pontosabb képet ad: a modell stabilan rossz (0.52-0.54)
- Nincs időbeli régime ahol a modell jobban működne — mindenhol AUC≈0.53

=== MIT TANULTUNK ===
A meta_v1 modell probléma NEM:
- ❌ Nem kalibráció (Lépés 1)
- ❌ Nem loss function (Lépés 2)
- ❌ Nem validáció (Lépés 3)
- ✅ A FEATURE-ÖK NEM HORDOZNAK ELÉG INFORMÁCIÓT A TARGET_META ELŐREJELZÉSÉHEZ

A Target_Meta label (PT/SL binary) alapvetően nehezen predikálható a rendelkezésre
álló 30 feature-ből. AUC≈0.53 azt jelenti, hogy a feature-ök marginális prediktív
erővel bírnak a trade outcome-ra.

=== KÖVETKEZŐ LÉPÉS: Lépés 4 (Erősebb Primary Model) ===
A Slope_Close_14 primary trend-following → 51.6% PT rate (ceiling)
QuantAlgo2 insight: "trend-following HURT by meta filter"
Alternatív primary model-ek:
- EMA crossover (10/30)
- RSI threshold
- Breakout signals
- Vagy: V20 (3-class LGBM) mint primary