# III. AZ 5 TÉNYEZŐ INTERAKCIÓJA + Financial-Specific Overfitting

## A FONDAMENTÁLIS KÉRDÉS: miért más a financial adat?

### Ok-okozat: Financial adat NEM i.i.d.!

```
ML tankönyvek FELTÉTELEZIK:
  (x_1, y_1), ..., (x_n, y_n) i.i.d. ~ P(X,Y)
  
Financial adat VALÓSÁGA:
  1. NEM independent: ρ(x_t, x_{t+1}) = 0.3-0.8
  2. NEM identical: P(X,Y) VÁLTOZIK az idővel (regime change!)
  3. NEM stationary: trend → range → volatile → crash
  → AZ ÖSSZES tankönyv tétel ÉRVÉNYTELEN!
```

### Következmény 1: A stationarity feltételezés HAMIS

```
HA a piac VÁLTOZIK (regime change):
  → train: bull market (2024.01-2024.06) → P(TP|long) = 60%
  → test:  range market (2024.07-2024.12) → P(TP|long) = 40%
  → a modell a BULL-ra tanult → RANGE-ben overfit!
  
  OK: a train adat NEM reprezentatív a test-re!
  OK: nem overfitting a klasszikus értelemben — REGIME SHIFT!
  OK: a modell JOSSÁG a train regime-ban, de ROSSZ a test regime-ban
  
  Ezt NEVÉLIK: "regime overfitting" vagy "concept drift"
```

### Következmény 2: Az effektív sample szám KISEBB mint gondolnánk

```
NEM csak autocorrelation csökkenti!

Regime change is csökkenti:
  HA 2.5 hónap = 1 regime (pl. range):
    → effektív sample = 42,742 (mind hasonló)
    → de a modell CSAK range-re tanul → trend-ben rossz!
    
  HA 2.5 hónap = 2 regime (pl. trend + range):
    → effektív sample regime-1 = 20,000
    → effektív sample regime-2 = 22,742
    → de a regime HATÁRÁN korreláció = 0 → mint 2 külön adat!
    → → MINDEGYIK regime-ben kevesebb sample!
    
  HA 1 év = 4-6 regime:
    → mindegyik regime 30-90 nap
    → mindegyikben 16,000-50,000 bar
    → → ROBUST modell: minden regime-ben tanult!
```

### Következmény 3: A "signal" MÁS minden regime-ben

```
Trend market:
  → "Long" TP gyakori → P(TP|long) = 60%
  → Feature-ök: trend erő, momentum domináns
  → RSI > 70 → folytatódik (nem overbought!)
  
Range market:
  → "Long" TP ritka → P(TP|long) = 35%
  → Feature-ök: S/R távolság, mean-reversion domináns
  → RSI > 70 → REVERSAL (overbought!)
  
Volatile market:
  → "Long" és "Short" is gyakori → P(TP) = 50% de nagy SL risk
  → Feature-ök: vol_ratio, ATR domináns
  → RSI > 70 → unpredictable!

OK: UGYANAZ a feature MÁS jelentésű más regime-ben!
OK: Egyetlen modell NEM tudja jól megtanulni MINDET!
OK: Ez a "feature non-stationarity" — a feature distribution VÁLTOZIK!
```

---

## INTERAKCIÓ 1: Data/Param × Class Imbalance

```
KÉRDÉS: Ha data/param = 40 (jó), DE class imbalance = 72:1,
        akkor is overfit?

VÁLASZ: IGEN, ha a minoritásos class kevesebb mint 100 sample!

  42,742 bar × 1.4% TP = 598 TP sample
  42,742 bar × 98.6% non-TP = 42,144 non-TP sample
  
  A modell 598 TP-n tanul → ha 598/865 = 0.69 TP/param → KEVÉS!
  
  OK: a data/param ratio CSAK a MAJORITÁSOS class-ra jó!
  OK: a MINORITÁSOS class-ra rossz!
  OK: a modell a majoritást jól tanulja, a minoritást rosszul!
  
MEGOLDÁS:
  1. Focal Loss → a minoritás gradiense megnő
  2. Oversampling → SMOTE vagy random oversampling a TP-ket
  3. Stratified batch → minden batch 50% TP, 50% non-TP
  4. Two-stage: először detector (van-e event?), aztán direction
  
  LEGJOBB: stratified batch + Focal Loss (együtt hat!)
```

### Stratified batch miért jobb mint oversampling?

```
Oversampling (SMOTE):
  → a TP-ket megkettőzzük → a gradiens TÚL nagy a TP-n
  → de a TP-k MÁSOLATOK → nincs új információ!
  → overfitting a megkettőzött TP-kre!

Stratified batch:
  → minden batch: 32 TP + 32 non-TP (balanced)
  → a gradiens kiegyenlített: 50% TP, 50% non-TP
  → NEM duplikálunk — csak a batch ÖSSZETÉTEL-t váltjuk
  → a teljes epoch MÉG MINDIG a teljes adaton megy végig
  → → Nincs extra overfitting!
  
OK: stratified batch = class imbalance megoldás WITHOUT overfitting!
```

---

## INTERAKCIÓ 2: Feature Skála × Multikollinearitás

```
KÉRDÉS: Ha RankGauss-t alkalmazunk, de a feature-ök korreláltak,
        mi történik?

RankGauss UTÁN:
  → feature_A: N(0,1) → bounded, scaled ✅
  → feature_B: N(0,1) → bounded, scaled ✅
  → DE: ha corr(A,B) = 0.95 → UGYANAZ az információ KÉTSZER!

  A NN két súlyt tanul: w_A × A + w_B × B
  → de A ≈ B → (w_A + w_B) × A → ONE degree of freedom, TWO params!
  → a loss landscape SÍK a (w_A, w_B) irányban
  → a gradiens VÉLETLENSZERŰEN sétál a sikon → instabil!

MIÉRT rosszabb mint a skálázatlan eset?
  Skálázatlan: ha A range = [0,100] és B range = [0,0.01]
    → w_A gradiens >> w_B → a modell A-t preferálja → egyértelmű!
    → (NEM jó, de legalább STABIL rossz döntés)
    
  RankGauss: A és B UGYANAZ a skála → w_A és w_B UGYANAZ a gradiens
    → a síkon随机 sétál → KÜLÖNBÖZŐ eredmény minden futtatáskor!
    → (ROSSZABB: instabil + reprodukálhatatlan!)

MEGOLDÁS:
  1. RankGauss ELŐTT: dobjuk el a korrelált feature-öket (|corr| > 0.8)
  2. VAGY: PCA RankGauss UTÁN → ortogonalizálás
  3. VAGY: Weight Decay (L2) → preferálja kis súlyokat → regularizálja a sikot
  4. LEGJOBB: (1) + (3) együtt!
```

### Konkrétan a V10 feature-ökre:

```
37 feature → mennyi korrelált?

Gyanús párok:
  - consecutive_f vs vol_ratio_f (momentum ↔ volatility)
  - RSI_3_f vs PastRet_2_f (RSI ≈ short-term return)
  - body_sign_f vs tick_imbalance_f (mikrostruktúra)
  - CUSUM_pos_f vs CUSUM_neg_f (anti-correlated by construction!)
  
TEENDŐ: futtatni corr() a 37 feature-ön és azonosítani a |corr| > 0.8 párokat
  → eldobjuk az egyiket (az alacsonyabb SHAP-importance-t)
  → 37 → ~25-30 feature → kisebb input dim → kevesebb param → kevesebb overfit!
```

---

## INTERAKCIÓ 3: Temporális Korreláció × Regime Change

```
KÉRDÉS: Ha blocked CV-t használunk, de a fold HATÁR regime határra esik,
        mi történik?

Fold 1: train = regime_A (trend)   test = regime_B (range)
  → modell trend-re tanult → range-ben rossz → OOS_AUC alacsony
  → DE ez NEM overfitting! Ez regime mismatch!

Fold 2: train = regime_A + regime_B  test = regime_C (volatile)
  → modell trend+range-re tanult → volatile-ben rossz → OOS_AUC alacsony
  → DE ez is regime mismatch, nem overfitting!

HA minden fold OOS_AUC alacsony:
  → NEM overfitting → a modell NEM generalizál regime-ek között!
  → megoldás: regime-aware modell (regime flag feature)
  → VAGY: csak egy regime-ben tanítunk és használunk
  
HA késői fold-ok OOS_AUC JÓ, korai rossz:
  → a korai adat más regime → a modell "felejt" → learning curve normális
  
HA OOS_AUC JÓ DE PnL rossz:
  → AUC jó osztályozás → de a threshold/calibration rossz!
  → AUC ≠ profitability! (AUC csak ranking, nem sizing!)
```

---

## INTERAKCIÓ 4: Normalizáció × Overfitting — a ROLLING vs EXPANDING dilemma

```
KÉRDÉS: RankGauss az EGÉSZ train adaton → lookahead?
  → IGEN, ha a test adat MÁS eloszlás!

Példa:
  Train: 2026.06-2026.08 (range, price 4280-4340)
  Test:  2026.09 (trend, price 4340-4420)
  
  RankGauss train: price 4280 → z=-2.5, price 4340 → z=+2.5
  Test: price 4420 → RANK > train max → z = ∞ !!
  
  → a normalizáció NEM működik OOS!
  → a modell Extrapolál → rossz predikció!

MEGOLDÁSOK:
  1. Rolling RankGauss (csak múlt adat, window = 5000 bar)
     → nem lookahead → de edge effects a window elején
     
  2. Expanding RankGauss (fokozatosan bővül)
     → minél több adat → annál stabilabb → jó!
     → de korai bar-ok kevésbé normalizáltak
     
  3. Clip + RankGauss (rank clamped to [0.001, 0.999])
     → z ∈ [-3.09, +3.09] → bounded → NEM ∞!
     → egyszerű, biztonságos → AJÁNLOTT!
     
  4. Feature scale-free design (decision_features.py elv)
     → minden feature return/ratio/gap → inherently bounded!
     → NEM kell RankGauss! A feature MÁR normalizált!
     → DE: csak ha MINDET scale-free-re tervezzük!
```

### A scale-free elv mélyebben:

```
decision_features.py elv:
  "All features are deliberately scale-free (returns, ratios, gaps, 
   centred oscillators) so the model generalises across symbols 
   and price levels."

MIÉRT működik?
  Return: (p_2 - p_1) / p_1 → ∈ [-1, ∞) → bounded for small changes
  Ratio: p / SMA(p, 20) - 1 → ∈ [-0.1, +0.1] typically → bounded
  Centred oscillator: (RSI - 50) / 50 → ∈ [-1, +1] → bounded!
  Distance/ATR: (p - S) / ATR → ∈ [-3, +3] typically → bounded!
  
  → NINCS outlier! NINCS scale dominancia! NINCS normalizáció probléma!
  
MIÉRT nem használjuk ezt a V10-ben?
  Mert a V10 feature-ök MIXED:
  - vol_ratio_f: scale-free ✅
  - consecutive_f: COUNT → nem scale-free ❌ (range: 0-50)
  - ticks_inv_f: COUNT → nem scale-free ❌
  - RSI_3_f: [0, 100] → nem centred ❌
  - CUSUM_pos_f: CUMULATIVE → nem bounded ❌

  → A V10 feature-ök NEM mind scale-free!
  → → RankGauss (vagy rolling z-score) KELL!
```

---

## INTERAKCIÓ 5: Modell Kapacitás × Adat Mennyiség — a DOUBLE DESCENT

```
KÉT klasszikus nézet:
  1. "Több param → overfit" (classical ML)
  2. "Több param → BETTER" (deep learning paradox!)

A VALÓSÁG: double descent!

  AUC
   ↑        ╱‾‾‾‾‾‾‾‾ BETTER (overparameterized)
   │       ╱
   │      ╱
   │     ╱         ← interpolációs küszöb (train_loss = 0)
   │    ╲╱
   │   ╱
   │  ╱ WORST (interpolation küszöb körül)
   │ ╱
   │╱ BETTER (underparameterized)
   └──────────────→ Params

OK-okozat:
  KEVÉS param: underfitting → nem tanul eléggé → AUC alacsony
  KÖZEPES param: overfitting → memorizál → AUC ROSSZABB!
  SOK param: overparameterized → a gradiens "lazy" → SIMPLE megoldást talál!
  
  MIÉRT "lazy" a sok param?
  → Neural Tangent Kernel (NTK) limit: ha params → ∞
  → a gradiens linearizálódik → kernel regression!
  → a legegyszerűbb (minimum norm) megoldást találja
  → → KEVÉSB overfit mint a közepes kapacitás!
  
DE: double descent ONLY ha:
  - label noise KEVÉS (clean data)
  - n >> d (sok adat, kevés feature)
  - SGD training (nem analytic solution)
  
Financial adat: label noise NAGY → double descent KEVÉSBÉ jelentkezik
→ → klasszikus U-alak valószínűbb!
→ → KEVESEBB param → KEVESEBB overfit → jobb!
```

### Következmény a V11-re:

```
2.5 hónap, 42,742 bar:
  → NE próbáljuk meg a double descent jobb oldalát!
  → az TÖBB adatot kíván (100K+)
  → maradjunk a klasszikus U-alak bal oldalán: KEVESEBB param!
  
  Optimális: ahol val_AUC maximális a U-alakon
  → tiny MLP (H=16, L=2, 865 param) → valószínűleg itt!
  → medium MLP (H=32, L=2, 2561 param) → talán jobb, talán overfit
  → nagy MLP (H=64, L=3, 12K+ param) → biztosan overfit!
  
  TESZT: learning curve + dropout sensitivity → megtaláljuk az optimum-ot!
```

---

## VÉGSŐ SZINTÉZIS: az interakciók HIERARCHIÁJA

```
Legfontosabb (MINDIG kezelni):
  1. Temporális korreláció → blocked CV + embargo (KÖTELEZŐ)
  2. Class imbalance → Focal Loss + stratified batch (KÖTELEZŐ)
  3. Train/Val gap → early stopping (KÖTELEZŐ)

Fontos (JAVULÁS):
  4. Feature normalizáció → RankGauss + clip (AJÁNLOTT)
  5. Feature redundancia → corr filter + PCA (AJÁNLOTT)
  6. Data/Param ratio → tiny MLP (AJÁNLOTT)

Hasznos (DIAGNOSZTIKA):
  7. Learning curve → kapacitás döntés
  8. Label permutation → signal validáció
  9. Dropout sensitivity → regularizáció tuning
  10. Bootstrap CI → bizonytalanság

Financial-specifikus:
  11. Regime awareness → regime flag feature
  12. Scale-free design → returns/ratios/gaps
  13. Non-stationarity → expanding window normalizáció
  14. AUC ≠ profitability → threshold calibration
```
