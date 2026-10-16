# II. OVERFITTING DETEKTÁLÁS — 6+ módszer ok-okozat mélyelemzéssel

## Módszer 1: Train/Val Loss Gap — az ALAPVETŐ diagnózis

### Mit mér?
```
train_loss(t) = (1/N_train) Σ L(y_i, f(x_i; θ_t))    ← IS (in-sample)
val_loss(t)   = (1/N_val)   Σ L(y_j, f(x_j; θ_t))    ← OOS (out-of-sample)
```

### Ok-okozat: MIÉRT nő a val_loss miközben train_loss csökken?

```
Epoch 1-10:  train_loss ↓  val_loss ↓   → tanulás (mindkettő javul)
Epoch 11-20: train_loss ↓  val_loss ~    → Memorizálás kezdete (IS javul, OOS stagnál)
Epoch 21-30: train_loss ↓  val_loss ↑   → OVERFITTING (IS javul, OOS ROMLIK)

MIÉRT?
  A gradiens descent MINIMALIZÁLJA a train_loss-t.
  Ha a modell kapacitás nagy → a gradiens "kiszolgálja" a train adatot
  → a súlyok a train adat SAJÁTSÁGAIHOZ igazodnak
  → de az OOS adat MÁS sajátságokkal bír → rossz predikció
  
ANALÓGIA:
  Ha egy diák (modell) csak a feladatsort (train) memorizálja
  → a vizsgán (test) más feladatok → rossz eredmény
  → de a feladatsoron 100% (train_loss ≈ 0)
```

### Hogyan kvantifikáljuk?

```
Generalizációs gap: G = val_loss - train_loss

G ≈ 0     → jó generalizáció (modell tanult, nem memorizált)
G > 0     → overfitting (memorizálás)
G növekszik → egyre rosszabb overfitting

Optimális epoch: ahol val_loss MINIMÁLIS (nem ahol G minimális!)
Early stopping: ha val_loss 20 epoch-ja nem javul → STOP
```

### CSAPDA! Ami a Financial-Forecasting-MLP repóban HIBÁSAN van:

```python
# ŐK: csak training_loss-t plotolnak (train.py:143-150)
plt.plot(train_losses, label="Training Loss")  # ← NINCS val_loss!
# → NEM látják az overfitting-et!
# → a modell valószínűleg overfit, de nem tudják!

# HELYES: train_loss ÉS val_loss egy ábrán
plt.plot(train_losses, label="Train")
plt.plot(val_losses, label="Val")
plt.axvline(best_epoch, color='r', linestyle='--', label='Early Stop')
```

### Focal Loss hatása a gap-re:

```
Focal Loss → a "könnyű" sample-ök gradiense kicsi
→ a modell NEM tudja könnyen levinni a train_loss-t
→ a tanítás LASSABB → több epoch kell → de kevésbé overfit
→ train_loss nem megy olyan közel 0-hoz
→ val_loss is jobb (mert a modell a NEHEZŐKRE tanul)
→ G kisebb → jobb generalizáció!
```

---

## Módszer 2: Purged Walk-Forward CV — a KÖTELEZŐ érvényesítés

### A BlockedTimeSeriesSplit a repóban:

```python
# blockedcv.py — amit tanulmányoztunk
class BlockedTimeSeriesSplit:
    def split(self, X, y=None, groups=None):
        fold_sizes = np.array_split(np.arange(n_samples), self.n_splits)
        for i in range(1, self.n_splits):
            train_idx = np.concatenate(fold_sizes[:i])  # minden korábbi blokk
            val_idx = fold_sizes[i]                       # a következő blokk
            yield train_idx, val_idx
```

### Ok-okozat: MIÉRT kell purged és MIÉRT kell embargo?

```
PROBLÉMA 1: K-napos label lookahead
  Ha a label = "PT elért-e a következő 10 bar-ban?"
  → az entry bar-nál a label már TUDJA a jövőt!
  → ha a train utolsó bar-ja = entry, és a test első bar-ja = exit
  → a train label TUDJA a test árfolyamot → LEAKAGE!
  
  MEGOLDÁS: Purge — dobjuk el a train VÉGÉRŐL a K-napos ablakot
  → train: [0, ..., T-purge]
  → test:  [T+1, ...]
  → purge = label_horizon (pl. 10 bar)

PROBLÉMA 2: Temporális korreláció (autocorrelation)
  Ha ρ_1 = 0.3 → a bar_T info átszivárog bar_{T+1}-be
  → a test első bar-ja még "emlékszik" a train utolsó bar-jára
  → OOS AUC torzítva felfelé!
  
  MEGOLDÁS: Embargo — gap a train és test között
  → train: [0, ..., T-purge-embargo]
  → gap:  [T-purge-embargo+1, ..., T]  ← ELDOBVA!
  → test:  [T+1, ...]
  → embargo = f(autocorrelation) pl. ~5-20 bar

PROBLÉMA 3: Túl sok fold → túl kevés train
  5 fold × 2642 sample → 529 test/fold
  → de a train NÖVEKSIK: fold 1: 529, fold 2: 1058, ...
  → ez CORRECT — a modell egyre többet tanul
  
  PROBLÉMA: ha n = 2642 → 5 fold → 529 test → kevés!
  → 3 fold → 880 test → jobb, de kevesebb CV
  → KOMPROMISSZUM: 3-5 fold, + embargo
```

### Walk-forward specifikus:

```
Walk-forward = a legrealistább értékelés:

Fold 1: train=[0:528]     test=[529:1057]    (20%→40%)
Fold 2: train=[0:1057]    test=[1058:1585]   (40%→60%)
Fold 3: train=[0:1585]    test=[1586:2113]   (60%→80%)
Fold 4: train=[0:2113]    test=[2114:2641]   (80%→100%)

HA minden fold OOS PnL pozitív → a modell ROBUST
HA csak késői fold-ok PnL pozitív → a modell TANUL (korai adat kevés)
HA csak korai fold-ok PnL pozitív → REGIME VÁLTOZÁS (piac megváltozott!)
```

---

## Módszer 3: Learning Curve — a DIAGNOSZTIKA

### Mitől függ a learning curve alakja?

```
KÉT dimenzió: adat mennyiség × modell kapacitás

            ╔═══════════════════════════════════╗
            ║  Adat KEVÉS, kapacitás NAGY:       ║
            ║  train_AUC = 0.95                  ║
            ║  val_AUC   = 0.55                  ║
            ║  → OVERFITTING (memorizálás)       ║
            ╚═══════════════════════════════════╝
            
            ╔═══════════════════════════════════╗
            ║  Adat SOK, kapacitás KICSINY:      ║
            ║  train_AUC = 0.65                  ║
            ║  val_AUC   = 0.64                  ║
            ║  → UNDERFITTING (nem tanul eléggé) ║
            ╚═══════════════════════════════════╝
            
            ╔═══════════════════════════════════╗
            ║  Adat SOK, kapacitás MEGFELELŐ:    ║
            ║  train_AUC = 0.75                  ║
            ║  val_AUC   = 0.72                  ║
            ║  → OPTIMÁLIS (gap kicsi, AUC jó)  ║
            ╚═══════════════════════════════════╝
```

### A learning curve mint DIAGNOSZTIKA eszköz:

```
X tengely: train adat mennyiség (20%, 40%, 60%, 80%, 100%)
Y tengely: AUC (vagy val_loss)

Ha val_AUC NÖVEKSIK az adattal:
  → a modell TÖBB adattal jobb lenne → UNDERFITTING
  → megoldás: nagyobb kapacitás (H↑, L↑)
  → VAGY: több adat kell!

Ha val_AUC STAGNÁL vagy CSÖKKEN az adattal:
  → a modell ELÉG kapacitásos → de overfit
  → megoldás: regularizáció (dropout↑, weight_decay↑)
  → VAGY: kevesebb feature (PCA)

Ha val_AUC és train_AUC KONVERGÁLNAK:
  → optimális kapacitás!
  → a gap ≈ 0.03-0.05 normális
```

### Konkrét esetünk: 42,742 bar, tiny MLP (H=16, L=2)

```
Elvárt learning curve:
  20% (8,548 bar):  val_AUC ≈ 0.58  (még kevés)
  40% (17,097 bar): val_AUC ≈ 0.63  (javul)
  60% (25,645 bar): val_AUC ≈ 0.66  (tovább javul)
  80% (34,194 bar): val_AUC ≈ 0.68  (lassan telítődik)
  100% (42,742 bar): val_AUC ≈ 0.69  (optimális?)

HA a 100%-os val_AUC jóval alacsonyabb a LGBM 0.732-nél:
  → az MLP kevésbé tanult → OK, csak diszkrepancia-jelző!
  → NEM kell hogy az MLP jobb legyen a LGBM-nél
  → csak annyi: MLP és LGBM KORRELÁLNAK-e, vagy függetlenek?
```

---

## Módszer 4: Random Label Permutation Test — a NULLA HIPOTÉZIS TESZT

### Ok-okozat: MIÉRT kell?

```
KÉRDÉS: Honnan tudjuk hogy a modell IGAZI SIGNAL-t tanult,
        és nem csak zajt memorizált?

HA a label-ök VÉLETLENSZERŰEK (nincs signal):
  → AUC ≈ 0.50 (random)
  → a modell NEM tud tanulni → helyes!

HA a label-ök IGAZI signal-t tartalmaznak:
  → AUC ≈ 0.70 (a modell tanult!)
  → de mi van ha a modell a ZAJ-t tanulta, nem a signal-t?

A PERMUTATION TEST megválaszolja:
  1. Keverjük meg a label-öket véletlenszerűen (y_shuffled)
  2. Tanítsunk modellt (x, y_shuffled) → AUC_random
  3. Tanítsunk modellt (x, y_original) → AUC_real
  4. HA AUC_real >> AUC_random → IGAZI signal!
  5. HA AUC_real ≈ AUC_random → NEM signal, csak zaj!
```

### Statisztikai alap:

```
Permutation test p-érték:
  p = (1/B) × Σ_{b=1}^{B} I(AUC_b ≥ AUC_real)
  
  ahol B = permutációk száma (pl. 100-1000)
  
Ha p < 0.05 → a modell szignifikánsan jobb mint random
Ha p > 0.05 → a modell NEM tanult semmi érdemlegeset

KONKRÉTAN:
  Ha AUC_real = 0.72 és AUC_random_mean = 0.50, std = 0.03:
  z = (0.72 - 0.50) / 0.03 = 7.33 → p < 10^{-12}
  → IGAZI signal! A modell tanult!
  
  Ha AUC_real = 0.55 és AUC_random_mean = 0.50, std = 0.03:
  z = (0.55 - 0.50) / 0.03 = 1.67 → p = 0.047
  → marginális! Lehet zaj, lehet gyenge signal.
```

### VESZÉLY: temporális label permutáció

```
HA random shuffle a label-öket:
  → a temporális struktúra MEGSEMMISÜL!
  → a modell nem tudja kihasználni a sorrendet
  → de a feature-k MÉG MINDIG korreláltak!
  → → AUC_random alacsony → hamis pozitív!

HELYES megközelítés:
  CIRCULAR shift: y_shifted[i] = y[(i + k) mod n]
  → a sorrend MEGMARAD, csak eltolódik
  → a feature-label kapcsolat MEGSZAKAD
  → de a temporális korreláció megmarad
  → → AUC_random reálisabb
```

---

## Módszer 5: Bootstrap Predikció CI — a BIZONYTALANSÁG kvantifikálása

### Ok-okozat: MIÉRT ingadozik a predikció?

```
A modell tanítás STOCHASZTIKUS:
  → random seed → más initializáció → más súlyok → más predikció
  → mini-batch SGD → más batch sorrend → más gradiens → más súlyok
  → dropout → más neuronok kikapcsolva → más hálózat → más predikció

Bootstrap = ezeket a forrásokat KVANTIFIKÁLJA:
  1. Tanítunk B modellt (B=100) különböző seed-del
  2. Predikálunk mind B modellel
  3. p_mean = mean(p_1, ..., p_B)
  4. p_std = std(p_1, ..., p_B)
  5. CI_95% = [p_mean - 1.96×p_std, p_mean + 1.96×p_std]
```

### KÉT féle bizonytalanság:

```
1. ALEATORIC (adat zaj):
   → a piac maga bizonytalan → a label nem determinisztikus
   → pl. ugyanazok a feature-ek → egyszer TP, máskor SL
   → ez NEM csökkenthető több adattal!
   
2. EPISTEMIC (modell bizonytalanság):
   → a modell NEM TUDJA melyik súly a jó → több megoldás létezik
   → több adat → kisebb epistemic → konvergál
   → bootstrap CI méri ezt!

HA CI széles (pl. p = 0.5 ± 0.3):
  → epistemic nagy → a modell BIZONYTALAN
  → NE trade-elj! Várj amíg a CI keskenyedik!
  
HA CI keskeny DE rossz (pl. p = 0.8 ± 0.02 de label = SL):
  → epistemic kicsi (a modell biztos) de systematikus hiba
  → a modell TÉVED és magabiztosan → VESZÉLYES!
  → → calibration curve kell!
```

### Kalibráció:

```
Kalibráció = a prediktált valószínűség EGYEZIK-e a valós frekvenciával?

Ha p = 0.7 → a valóságban 70%-ban TP? (kalibrált)
Vagy csak 50%-ban? (nem kalibrált → túl magabiztos)

Kalibrációs görbe:
  X tengely: prediktált p (bin-ek: [0.0-0.1], [0.1-0.2], ...)
  Y tengely: tényleges TP% a bin-ben
  
Ha a görbe az átlón van → KALIBRÁLT (jó!)
Ha a görbe az átló FELETT → túl óvatos (p alulbecsli)
Ha a görbe az átló ALATT → túl magabiztos (p túlbecsli) → VESZÉLYES!
```

---

## Módszer 6: Dropout Sensitivity — a REGULARIZÁCIÓ TESZT

### Ok-okozat: MIÉRT működik a dropout?

```
Dropout(p) training közben:
  → minden forward pass: véletlenszerűen kikapcsol p% neuron-t
  → a hálózat minden forward pass-ban MÁS!
  → → implicit ensemble: ~2^H modell (de csak 1-et tanítunk!)
  
MIÉRT segít?
  Ha neuron_A mindig feature_1-et használ:
    → dropout → néha neuron_A kikapcsol → feature_1 NEM használva
    → a hálózat MÁS feature-ket is tanul → diverzifikáció!
    → nem függenek egy neuron-tól → robusztusabb!
    
ANALÓGIA: ensemble of trees
  LGBM: 47 fa → mindegyik más feature subset → diverzifikáció
  Dropout: ~2^H "fa" → mindegyik más neuron subset → diverzifikáció
  → HASONLÓ hatás, de NN-ben!
```

### A sensitivity teszt:

```
Tanítsunk 3 modellt: dropout = {0.0, 0.3, 0.5}

HA dropout=0.0:  train_AUC=0.95, val_AUC=0.55 → ERŐS overfit
HA dropout=0.3:  train_AUC=0.80, val_AUC=0.68 → JOBB! (regularizáció működik)
HA dropout=0.5:  train_AUC=0.70, val_AUC=0.65 → túl sok (underfitting)

KÖVETKEZMÉNY:
  HA dropout=0.3 JAVÍT → AZ eredeti modell overfit volt!
  HA dropout=0.5 ROMLIK → túl sok regularizáció → underfitting
  → optimális dropout: ahol val_AUC maximális
  
HA dropout=0.0 már jó (val≈train):
  → a modell NEM overfit → dropout nem kell
  → vagy: az adat elég sok → kapacitás megfelelő
```

### BatchNorm mint regularizátor:

```
BatchNorm: normalizálja a hidden layer kimenetét batch-enként
  → a batch statisztika (mean, std) STOCHASZTIKUS
  → ez zajt ad a kimenethez → regularizáció!
  
DE: BatchNorm + small batch → TÚL sok zaj → instabil gradiens
    BatchNorm + large batch → KEVÉS zaj → kevésbé regularizál
    
VESZÉLY: train/eval mód különbség
  train: batch statisztikát használ
  eval:  running statisztikát használ (exponential moving average)
  → HA a train és eval kimenet NAGYON különbözik → instabil!
  → ellenőrzés: model.eval(); check output vs model.train() output
```

---

## + Módszer 7: Gradient Noise Scale — az OPTIMÁLIS batch size

```
Gradient noise scale (GNS):
  G = tr(Σ) / ||g||²
  
  ahol Σ = gradiens kovariancia, g = átlag gradiens

HA G nagy → sok zaj a gradiensben → kicsi batch elég
HA G kicsi → kevés zaj → nagy batch kell (párhuzamos tanítás)

Financial adat → tipikusan NAGY G (sok zaj) → kicsi batch (32-64) optimális
Image adat → tipikusan KICSINY G → nagy batch (256-1024) optimális

KÖVETKEZMÉNY: MLP financial-ra → batch_size = 32-64, NE 256!
```

---

## + Módszer 8: Activation Statistics — a DYING RELU detektálása

```
HA ReLU → a gradiens 0 ha input < 0
  → ha túl sok neuron input < 0 → "dying ReLU"
  → a neuron NEM tanul (gradiens = 0)
  → effektív kapacitás CSÖKKEN → underfitting!

Detektálás: logoljuk a % aktív neuron-t minden layer-ben
  HA < 30% aktív → dying ReLU → LeakyReLU vagy ELU kell!
  HA > 90% aktív → túl kevés regularizáció → dropout kell!
  
KÖVETKEZMÉNY: LeakyReLU(0.01) biztonságosabb mint ReLU
  → mindig van kis gradiens → nem "hal meg" a neuron
```

---

## SZINTÉZIS: Melyik módszer MIKOR használható?

| Módszer | Mikor | Költség | Prioritás |
|---|---|---|---|
| Train/Val gap | MINDIG (tanítás közben) | Ingyenes | 🔴 KÖTELEZŐ |
| Purged CV | Modell értékelés | 3-5× tanítás | 🔴 KÖTELEZŐ |
| Learning curve | Kapacitás döntés | 5× tanítás | 🟡 AJÁNLOTT |
| Label permutation | Signal validáció | 100× tanítás | 🟡 AJÁNLOTT |
| Bootstrap CI | Éles predikció | 100× tanítás | 🟢 HASZNOS |
| Dropout sensitivity | Regularizáció tuning | 3× tanítás | 🟡 AJÁNLOTT |
| Gradient noise scale | Batch size tuning | 1× tanítás | 🟢 HASZNOS |
| Activation stats | Architektúra debug | Ingyenes | 🟢 HASZNOS |
