# Adat vs Overfitting — V11 MLP Alapvizsgálat

## Nyers adat összefoglaló

| Adat | Méret | Időtartam | Megjegyzés |
|---|---|---|---|
| Tick (v2.csv) | 4,150,493 sor / 799 MB | 2026.06.16→09.01 | 2.5 hónap |
| Tick (külön_vizsga) | 386,708 sor / 74 MB | 2026.09.14→09.18 | 5 nap OOS |
| M1 bar (ZigZag) | 75,367 bar / 8 MB | 2026.06.16→09.01 | M1 aggregált |
| Dollár bar | 42,742 bar / 8.7 MB | 2.5 hónap | $444K threshold |
| CUSUM event | 2,642 event | 2.5 hónap | 34/event nap |
| TP event | 583 (22.1%) | | Meta-label |

## Az alapvető probléma

### Event-based (LGBM stílus): 2,642 sample

| MLP config | Params | Data/Param | Verdict |
|---|---|---|---|
| W=1 H=8 L=1 | 305 | 6.9 | ⚠️ gyenge |
| W=1 H=16 L=2 | 865 | 2.4 | ❌ OVERFIT |
| W=5 H=8 L=1 | 1,497 | 1.4 | ❌ OVERFIT |
| W=10 H=8 L=1 | 2,793 | 0.8 | ❌ OVERFIT |

**KÖVETKEZMÉNY**: Event-based MLP 2.5 hónappal **lehetetlen**. Még a legkisebb (H=8, L=1) is borderline.

### Per-bar: 42,742 sample

| MLP config | Params | Data/Param | Verdict |
|---|---|---|---|
| W=1 H=8 L=1 | 305 | 112.0 | ✅ sok adat |
| W=1 H=16 L=2 | 865 | 39.5 | ✅ jó |
| W=1 H=32 L=2 | 2,561 | 13.3 | ✅ jó |
| W=5 H=16 L=2 | 3,281 | 10.4 | ✅ jó (határon) |
| W=5 H=32 L=2 | 12,129 | 2.8 | ❌ OVERFIT |
| W=10 H=32 L=2 | 12,961 | 2.6 | ❌ OVERFIT |

**KÖVETKEZMÉNY**: Per-bar tiny/small MLP működhet, de class imbalance 72:1!

### Éves adat extrapoláció

| Év | Event | Bar | tiny H=16 L=2 | med H=32 L=2 W=5 |
|---|---|---|---|---|
| 1 | 12,523 | 202,575 | ev:11.6 / bar:187 | ev:1.0 / bar:13 |
| 2 | 25,046 | 405,150 | ev:23.2 / bar:375 | ev:2.1 / bar:27 |
| 3 | 37,569 | 607,725 | ev:34.7 / bar:562 | ev:3.1 / bar:38 |

**1 év per-bar adat → medium MLP is OK!**

## Overfitting — mitől függ?

### 1. Data/Param ratio (a legfontosabb!)
- **> 20**: jó generalizáció várható
- **10-20**: elfogadható, de CV szükséges
- **5-10**: gyenge, erős regularizáció kell
- **< 5**: garantált overfitting gradient descent-nél

### 2. Class imbalance
- 72:1 arány → a modell "megtanulja" hogy mindig 0-t mondjon → 98.6% accuracy de 0% hasznos predikció
- **Focal Loss** kötelező: γ=2-3 fókuszál a nehezen osztályozható sample-ökre
- **Oversampling** (SMOTE) vagy **class weighting** is segíthet

### 3. Temporal dependency
- Idősor adat → szomszédos bar-ok korreláltak
- **Effektív sample szám < nominális** (augmented Dickey-Fullal: eff_sample ≈ nominal / √autocorr)
- Dollár bar-ok kevésbé korreláltak mint idő bar-ok → dollar bar jobb

### 4. Feature redundancy
- 37 feature között korreláció → effektív dimenzió < 37
- PCA vagy RankGauss csökkentheti a dimenziót
- LGBM top 5 feature dominál → lehet hogy 5-10 feature elég MLP-nek is

### 5. Normalizáció minősége
- Rossz normalizáció → feature skálák dominálják a gradienst
- **RankGauss** → uniform, bounded, NN-barát
- **Rolling z-score** → nem lookahead, de edge effects

## Overfitting detektálás — 6 módszer

### 1. Train/Val loss gap (ALAP)
- Tanítás közben: train_loss vs val_loss plot
- **Overfit signal**: val_loss nő miközben train_loss csökken
- **Early stopping**: patience=20

### 2. Purged walk-forward CV (KÖTELEZŐ)
- Idősor: időrendben split, NEM random!
- **Embargo gap**: train és test között → lookahead megelőzés
- 5 fold OOS értékelés
- Ha OOS_AUC << IS_AUC → overfit

### 3. Learning curve (DIAGNOSZTIKA)
- 20%, 40%, 60%, 80%, 100% adat → tanítás → val_AUC
- Ha val_AUC nem javul → underfitting (több param kell)
- Ha train_AUC >> val_AUC → overfitting (kevesebb param kell)

### 4. Random label permutation test (VALIDÁCIÓ)
- Label-ök véletlen megkeverése → tanítás
- Ha random_AUC ≈ modell_AUC → NEM tanult semmit!
- Ha modell_AUC >> random_AUC → igazi signal (pl. 0.72 >> 0.50)

### 5. Bootstrap predikció CI (BIZONYTALANSÁG)
- 100 bootstrap sample → 100 predikció
- Ha CI széles → modell bizonytalan (pl. ±0.15)
- Ha CI keskeny DE rossz → systematikus hiba

### 6. Dropout sensitivity (REGULARIZÁCIÓ TESZT)
- p=0.0 vs 0.3 vs 0.5
- Ha p=0.5 jelentősen javít → overfitting volt
- Ha dropout nem segít → underfitting vagy jó

## Döntés: mit tegyünk?

### Opció A: 2.5 hónap, per-bar, tiny MLP
- ✅ Megvan az adat, most lehet dolgozni
- ✅ 42,742 sample, tiny MLP (H=16, L=2) → data/param=39.5
- ⚠️ Class imbalance 72:1 → Focal Loss + class weight
- ⚠️ Csak Long predikció (vagy külön Long/Short modell)
- ❌ Generalizáció kérdéses — 2.5 hónap kevés a piac változékonyságához

### Opció B: 1+ év adat letöltés, per-bar, medium MLP
- ✅ 200K+ sample → medium MLP is OK
- ✅ Több piac régió (trending + ranging + volatile)
- ✅ Robusztusabb modellek
- ❌ Adat letöltés időbe telik (MT5 download)
- ❌ Pipeline módosítás (több fájl merge)

### Opció C: 2.5 hónap per-bar, DE feature-redukcio után
- ✅ Top 5-10 feature → kisebb input dim → kevesebb param
- ✅ 37→10 feature → W=1 H=16 L=2 params=10*16+16+16*16+16+16+1 = 437
- ✅ data/param = 42,742/437 = 97.8 → nagyon jó!
- ⚠️ De kevesebb feature → kevesebb információ

### AJÁNLÁS: Opció A először (gyors validáció), aztán Opció B (éles modell)
1. Először: per-bar tiny MLP 2.5 hónappal → bizonyítsuk hogy működik
2. Ha működik: 1-2 év adat letöltés → medium MLP
3. Ha nem működik: diagnosztika miért nem → feature/design változtatás
