# I. MIÉRT OVERFIT A NN ÉS MIÉRT NEM A TREE? — Ok-okozat mélyelemzés

## A kérdés ami mindent megalapoz

LGBM: 2,642 event, 47 fa × 61 levél ≈ 2,867 "paraméter" → AUC 0.732 ✅
MLP:  2,642 event, H=16 L=2 = 865 paraméter → garantált overfit ❌

**Hogy lehet hogy KEVESEBB paraméterrel a NN overfit, de a tree NEM?**

Ez nem paradoxon — a "paraméterszám" más dolgot jelent a két modellnél.

---

## Ok-okozat lánc 1: A tanulás MÓDSZERE határozza meg az overfittinget

```
Tree model (LGBM)                    Neural Network (MLP)
─────────────────                    ────────────────────
Tanulás: greedy boosting             Tanulás: gradient descent
  → minden fa a RESIDUUM-ra tanul      → minden súly egyszerre módosul
  → sorrendben, egyik a másik után     → párhuzamosan, kölcsönhatásban
  → korai stopping = fa szám           → korai stopping = epoch szám
  
Regularizáció: implicit               Regularizáció: explicit kell!
  → fa mélység limit                   → Dropout, BatchNorm, Weight Decay
  → leaf szám limit                    → de MINDEGYIKET be kell állítani!
  → feature subsampling               → learning rate scheduling
  → min_data_in_leaf                  → gradient clipping
  
Kapacitás: lokális                    Kapacitás: globális
  → minden levél LOKÁLIS döntés       → minden neuron GLOBÁLIS hatás
  → egy levél csak a saját régióját   → egy súly megváltoztatása az
    látja                               EGÉSZ hálzat kimenetét megváltoztatja
```

### MIÉRT globális a NN? — A gradiens terjedés

Amikor `w_23` (a 2. layer 3. neuronjának súlya) megváltozik `Δw`-vel:
- Ez megváltoztatja `h_2[3]`-at (2. layer 3. neuron kimenete)
- Ami megváltoztatja `h_3[0], h_3[1], ..., h_3[H]`-at (3. layer ÖSSZES neuronja)
- Ami megváltoztatja a VÉGSŐ kimenetet
- **Egyetlen súly → az egész hálózat kimenete változik!**

Ezzel szemben egy tree levél:
- Csak a saját régiójában lévő sample-öket érinti
- Más levelek KIZÁRÓLAG nem változnak
- **Egyetlen levél → csak lokális hatás!**

### Következmény: a NN "paraméter" NEM független!

```
LGBM: 2,867 "paraméter" → mindegyik LOKÁLIS → effektív szabadságfok ≈ 2,867
MLP:    865 "paraméter" → mindegyik GLOBÁLIS → effektív szabadságfok >> 865
```

A NN effektív kapacitása NAGYOBB mint a paraméterszám!
- 865 globális paraméter ≈ 5,000-10,000 lokális "egyenértékű" döntés
- Ezért kell data/param > 10 a NN-nez, de data/param > 1 is elég a tree-nek

---

## Ok-okozat lánc 2: A gradiens descent IRÁNYA határozza meg a memorizálást

```
Gradient descent memória:
  w_{t+1} = w_t - η * ∂L/∂w

Ha a tanító adat "ritka" (22% TP, 78% SL):
  → a gradiens 78%-ban az SL felé mutat
  → a modell "megtanulja" hogy a default válasz SL
  → a TP sample-ök csak 22%-ban "húzzák" a gradienst
  → erős class imbalance → a modell a többséget memorizálja
  → a kisebbséget (TP) alulreprezentálja → rossz TP predikció
```

LGBM-ben ez NEM történik:
- A boosting SORRENDEN tanul — először a legnagyobb hibákon
- A `scale_pos_weight` automatikusan kompenzál
- A fa struktúra TERMÉSZETESEN szelektál — egy levél vagy TP vagy SL

### Következmény: Focal Loss miért kritikus?

```
Standard BCE loss:  L = -[y·log(p) + (1-y)·log(1-p)]
  → 72:1 class imbalance → gradiens 72× inkább SL felé

Focal Loss:  L = -[α·(1-p)^γ·y·log(p) + (1-α)·p^γ·(1-y)·log(1-p)]
  → (1-p)^γ: ha a modell már biztos (p≈1 vagy p≈0) → kicsi gradiens
  → p^γ: ha a modell bizonytalan → NAGY gradiens
  → γ=2: a "könnyű" sample-ök (SL 72×) gradiense 1/9-re csökken
  → A "nehéz" TP sample-ök gradiense RELATÍVAN megnő!
  
OK: Focal Loss = class imbalance + hard example mining EGYSZERRE
OK: A modell a NEHEZŐKRE fókuszál, nem a többségre
OK: Ez kompenzálja a gradiens aszimmetriát
```

---

## Ok-okozat lánc 3: A normalizáció HIBÁJA okozza a feature dominanciát

```
NN gradiens: ∂L/∂w = ∂L/∂output × ∂output/∂w

Ha feature_1 range = [0, 1000] és feature_2 range = [0, 0.01]:
  → w_1 gradiens >> w_2 gradiens (1000× !)
  → a modell feature_1-et "túltanulja", feature_2-t "alultanulja"
  → ez NEM overfitting, de UGYANAZ a tünet: rossz generalizáció
  
Tree-ben ez NEM probléma:
  → a fa only THRESHOLD-ökhez hasonlít (pl. "f1 > 500?")
  → a threshold monotón: skálázás nem változtatja az optimális split-et
  → ezért a tree scale-invariant (monotón transzformációkra)
```

### Következmény: RankGauss miért a legjobb NN-hez?

```
RankGauss folyamat:
  1. Rendezzük az értékeket: x_1 ≤ x_2 ≤ ... ≤ x_n
  2. Rank: r_i = i / (n+1)  → uniform [0,1]
  3. Inverse Gaussian CDF: z_i = Φ^{-1}(r_i)  → N(0,1)

Tulajdonságok:
  → Minden feature UGYANABBA a tartományba kerül (N(0,1))
  → Nincs outlier dominancia (a rank vágja)
  → Nemlineáris → megragadja az eloszlás alakját
  → Monoton → megőrzi az információt
  → Online variáns: rolling rank → nem lookahead
  
MIÉRT jobb mint MinMaxScaler?
  MinMax: outlier → minden más érték összenyomódik [0, 0.01]-be
  RankGauss: outlier → rank = 0.99 → z = 2.33 → bounded!
  
MIÉRT jobb mint StandardScaler?
  Z-score: feltételezi hogy normál eloszlás → de financial adat NEM az!
  RankGauss: KÉNYSZERÍTI normál eloszlásba → NN feltételezése teljesül
```

### De: RankGauss veszély!

```
VESZÉLY: Ha a test eloszlás MÁS mint a train eloszlás:
  → Train RankGauss: z = Φ^{-1}(rank_train(x))
  → Test: ugyanaz a transzformáció → de a rank MÁS!
  → Ha out-of-sample új érték > train max → rank > 1 → z > Φ^{-1}(1) = ∞!
  
MEGOLDÁS:
  1. Rolling RankGauss (csak múlt adatra) → nem lookahead
  2. Clip: rank = min(max(rank, 0.001), 0.999) → bounded
  3. Expansion: a scaler fokozatosan bővül → stabilizálódik
```

---

## Ok-okozat lánc 4: Temporális korreláció CSÖKKENTI az effektív sample számot

```
Ha x_t és x_{t+1} korreláltak (ρ = 0.95):
  → x_{t+1} ≈ 0.95 × x_t + noise
  → x_{t+1} szinte UGYANAZ az információ mint x_t
  → 100 korrelált sample ≈ 5 független sample!

Effektív sample szám:
  n_eff = n / (1 + 2 × Σ_{k=1}^{∞} ρ_k)

  ahol ρ_k = autocorrelation lag-k

Példa dollár bar-okkal:
  Ha ρ_1 = 0.3 (mérsékelt korreláció):
    n_eff = n / (1 + 2×0.3) = n / 1.6
    42,742 bar → 26,714 effektív sample
    
  Ha ρ_1 = 0.8 (erős korreláció — idő bar):
    n_eff = n / (1 + 2×0.8) = n / 2.6
    42,742 bar → 16,440 effektív sample

OK: Dollár bar KEVESEBB korrelált mint idő bar!
OK: Dollár bar → több effektív sample → kevesebb overfit
OK: Ez egy OK-okozat ami a dollár bar használatát ALÁTÁMASZTJA
```

### De: blocked CV miért KÖTELEZŐ?

```
HA random split (sklearn default):
  → train: ..., bar_99, bar_101, bar_103, ...
  → test:  ..., bar_100, bar_102, bar_104, ...
  → de bar_100 korrelált bar_99-el és bar_101-el!
  → a modell "látja" a test adatot a train-ben (korreláción keresztül)
  → OOS AUC torzítva felfelé → hamis generalizáció!

HA blocked time-series split:
  → train: bar_0, ..., bar_2000
  → test:  bar_2001, ..., bar_2642
  → NINCS átfedés, NINCS korreláció (ha embargo elég nagy)
  → OOS AUC valós → reális generalizáció
  
HA embargo gap:
  → train: bar_0, ..., bar_2000
  → GAP: bar_2001, ..., bar_2020 (eldobva!)
  → test:  bar_2021, ..., bar_2642
  → A gap megsemmisíti a temporális korrelációt
  → Minél nagyobb a ρ, annál nagyobb gap kell!
```

---

## Ok-okozat lánc 5: Feature redundancia OKOZZA a multikollinearitást

```
Ha feature_A = 0.95 × feature_B + noise:
  → a NN két súlyt tanul: w_A és w_B
  → de w_A × feature_A + w_B × feature_B ≈ (w_A + 0.95×w_B) × feature_A
  → VÉGTELEN sok (w_A, w_B) páros ad ugyanazt az eredményt!
  → a loss landscape "sikk" → a gradiens nem egyértelmű irányt mutat
  → a tanítás instabil → overfitting az egyik súlyra

Tree-ben ez NEM probléma:
  → a fa only EGYES feature-t split-el minden csomópontban
  → feature_A vs feature_B → az egyik nyer, a másik ignorálva
  → nincs multikollinearitás (implicit feature selection)

MEGOLDÁS NN-hez:
  1. PCA — csökkentjük a dimenziót (37 → 10-15)
  2. RankGauss + Drop correlated — ha |corr| > 0.9, dobjuk el
  3. Weight Decay (L2) — bünteti a nagy súlyokat → regularizálja a sikk-et
  4. Dropout — véletlenszerűen kikapcsol feature-eket → implicit ensemble
```

---

## SZINTÉZIS: Az 5 ok-okozat lánc együtt hat

```
Overfitting NN-ben =
    (1) Globális paraméterhatás        → tree vs NN fundamentális különbség
  × (2) Gradiens aszimmetria           → class imbalance → Focal Loss
  × (3) Feature skála dominancia       → RankGauss normalizáció
  × (4) Temporális korreláció          → blocked CV + embargo
  × (5) Multikollinearitás             → PCA / feature redukció / Weight Decay
  
NEM elég csak egyet megoldani!
Mindhárom-ötÖT együtt kell kezelni!
```
