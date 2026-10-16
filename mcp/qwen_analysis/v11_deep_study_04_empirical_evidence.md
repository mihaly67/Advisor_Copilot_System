# IV. EMPIRIKUS BIZONYÍTÉK — V10 Feature analízis eredmények

## 1. KORRELÁCIÓ — 32 feature-ből MELYIKEK redundánsak?

### |ρ| > 0.9 — MINDENKÉPP dobjuk el az egyiket!

| Feature A | Feature B | ρ | Ok-okozat | Teendő |
|---|---|---|---|---|
| ema8_gap_f | ema8_slope_f | **+1.000** | EMA gap és slope matematikailag ekvivalensek! | Dobjuk el ema8_slope_f |
| body_sign_f | Bullish_Bar_f | **+0.999** | Bullish_Bar = body_sign > 0 → definíció! | Dobjuk el Bullish_Bar_f |
| Slope3_Up_f | Slope3_Down_f | **-0.999** | Up = -Down → anti-korrelált definíció! | Dobjuk el Slope3_Down_f |
| body_f | PastRet_1_f | **+0.996** | body ≈ close-open ≈ 1-bar return | Dobjuk el body_f |
| body_f | velocity_f | **+0.951** | velocity ≈ body/tick ≈ body (konstans tick) | Dobjuk el velocity_f |
| velocity_f | PastRet_1_f | **+0.944** | velocity ≈ PastRet_1 (tranzitív) | Már eldobjuk velocity_f |

### |ρ| = 0.8-0.9 — VALÓSZÍNŰLEG redundáns

| Feature A | Feature B | ρ | Ok-okozat | Teendő |
|---|---|---|---|---|
| ema8_gap_f | Slope_5_f | +0.927 | EMA gap → slope → korrelál | Dobjuk el Slope_5_f |
| ema8_slope_f | Slope_3_f | +0.894 | Slope és EMA slope ekvivalens | Már eldobjuk ema8_slope |
| body_sign_f | consecutive_f | +0.859 | Egymás utáni bullish → consecutive | VIGYÁZAT: SHAP fontosság dönt! |
| RSI_3_f | RSI3_Oversold_f | -0.841 | RSI3_Oversold = I(RSI3 < threshold) | Dobjuk el RSI3_Oversold_f |
| RSI_3_f | Slope3_Up_f | +0.832 | RSI ≈ momentum ≈ slope | Dobjuk el Slope3_Up_f |
| ATR_Micro_5_f | vol_ratio_f | +0.827 | ATR és vol_ratio mindkettő volatilitás | Dobjuk el ATR_Micro_5_f |
| PastRet_2_f | ema8_gap_f | +0.825 | 2-bar return ≈ EMA gap (rövid táv) | VIGYÁZAT: SHAP dönt! |

### KONKLÚZIÓ: 32 → 15-18 feature-re csökkenthető!

```
ELDOBJUK (redundáns vagy alacsony SHAP):
  body_f          ← PastRet_1_f helyettesíti
  velocity_f      ← PastRet_1_f helyettesíti
  Bullish_Bar_f   ← body_sign_f helyettesíti
  ema8_slope_f    ← ema8_gap_f helyettesíti
  Slope3_Down_f   ← Slope3_Up_f helyettesíti (anti-korrelált!)
  Slope_5_f       ← ema8_gap_f + Slope_3_f fedi
  RSI3_Oversold_f ← RSI_3_f fedi
  RSI3_Overbought_f ← RSI_3_f fedi (|ρ|=0.80)
  Slope3_Up_f     ← RSI_3_f fedi
  ATR_Micro_5_f   ← vol_ratio_f fedi
  ema_fast_slow_f ← ema8_gap_f fedi (|ρ|=0.76)

MEGTARTJUK (15-18 feature):
  body_sign_f     — irány info (SHAP top)
  consecutive_f   — momentum erő (SHAP top)
  vol_ratio_f     — volatilitás regime (SHAP #1!)
  ticks_inv_f     — mikrostruktúra (SHAP top)
  RSI_3_f         — momentum oszcillátor
  RSI_5_f         — hosszabb momentum
  Slope_3_f       — rövid távú trend
  ema8_gap_f      — EMA távolság
  above_ema8_f    — EMA pozíció (bináris)
  above_ema20_f   — EMA20 pozíció
  PastRet_1_f     — 1-bar return
  PastRet_2_f     — 2-bar return
  vol_calm_f      — volatilitás regime flag
  body_ratio_f    — candle forma
  wick_u_r_f      — felső kanóc arány
  wick_l_r_f      — alsó kanóc arány
  Conviction_Bar_f — erős mozgás flag
  Fast_Bar_f      — gyors bar flag
```

### HATÁS az MLP-re:

```
32 feature → 18 feature:
  - Input dim csökken: 32 → 18 (44% csökkentés!)
  - MLP params: W=1 H=16 L=2 → 32×16+16 + 16×16+16 + 16+1 = 865
                    → 18×16+16 + 16×16+16 + 16+1 = 593
  - data/param: 42,742/865 = 49.4 → 42,742/593 = 72.1 ✅ JOBB!
  - Multikollinearitás csökkent → stabilabb gradiens → kevesebb overfit!
```

---

## 2. AUTOKORRELÁCIÓ — temporális dependency empirikus mértéke

### Kritikus feature-ök (|ρ₁| > 0.5):

| Feature | ρ₁ | n_eff/n | Következmény |
|---|---|---|---|
| ticks_inv_f | **+0.837** | 0.374 | NAGYON korrelált! eff. sample csak 37%! |
| above_ema8_f | +0.627 | 0.444 | EMA pozíció lassan változik |
| Fast_Bar_f | +0.619 | 0.447 | Gyors bar clusterekben jön |
| consecutive_f | +0.547 | 0.477 | Momentum clusterek |
| above_ema20_f | +0.505 | 0.497 | EMA20 még lassabb |

### Alacsony autokorreláció (|ρ₁| < 0.15) — "i.i.d.-szerű":

| Feature | ρ₁ | n_eff/n | Következmény |
|---|---|---|---|
| wick_l_r_f | -0.034 | 0.936 | ✅ Majdnem független! |
| body_ratio_f | -0.029 | 0.946 | ✅ Majdnem független! |
| Conviction_Bar_f | -0.021 | 0.960 | ✅ Független! |
| wick_u_r_f | -0.001 | 0.997 | ✅ Tökéletesen független! |

### OK-okozat: MIÉRT független a wick_u_r?

```
wick_u_r = (high - max(open,close)) / (high - low)
  → ez a kanóc ARÁNY, nem az abszolút érték
  → a kanóc arány random — nem függ az előző bar-tól
  → ez SCALE-FREE design — a normalizálás teszi függetlenné!
  
  → OK: a scale-free design NEM CSAK normalizál, hanem
       TEMPORÁLIS FÜGGETLENSÉGET is teremt!
  → OK: ez a decision_features.py filozófiája empirikusan igazolva!
```

### Effektív sample szám:

```
Átlag |ρ₁| = 0.326 az összes feature-ön
N = 2,642 → N_eff = 1,599 (61%)

DE: ha a legkorreláltabb feature-öket eldobjuk:
  ticks_inv_f, above_ema8_f, Fast_Bar_f eldobása →
  átlag |ρ₁| csökken → N_eff nő!
  
  ÉS: a per-bar megközelítésben (42,742 bar):
  N_eff ≈ 42,742 × 0.61 = 26,073 → Még mindig elég!
```

---

## 3. FEATURE SKÁLA — melyikek NEM scale-free?

### NAGY RANGE (nem bounded):

| Feature | μ | σ | [min, max] | Probléma |
|---|---|---|---|---|
| body_f | 0.047 | 3.158 | [-31.5, 56.4] | Abszolút ár-különbség! |
| body_abs_f | 1.966 | 2.471 | [0, 56.4] | Abszolút! |
| consecutive_f | -0.030 | 4.217 | [-12, 13] | COUNT — nem scale-free! |
| RSI_3_f | 42.563 | 30.053 | [0, 100] | Nem centred! |
| RSI_5_f | 48.357 | 27.524 | [0, 100] | Nem centred! |
| Slope_3_f | 0.044 | 1.821 | [-12.7, 22.2] | Abszolút slope! |
| ATR_Micro_5_f | 3.275 | 1.946 | [0.96, 20.8] | Abszolút ATR! |

### NEAR ZERO STD (túl kicsiny variancia):

| Feature | μ | σ | [min, max] | Probléma |
|---|---|---|---|---|
| ticks_inv_f | 0.010 | 0.004 | [0.004, 0.034] | Tömörített — kis dinamika |
| PastRet_1_f | 0.000 | 0.001 | [-0.008, 0.014] | Return nagyon kicsi |
| ema8_gap_f | 0.000 | 0.001 | [-0.007, 0.011] | EMA gap kicsi |
| ema8_slope_f | 0.000 | 0.000 | [-0.002, 0.003] | Még kisebb! |

### OK-okozat: a NEAR ZERO STD miért VESZÉLYES NN-hez?

```
Ha σ(feature) = 0.001:
  → a feature gyakorlatilag KONSTANS → 0.000 ± 0.001
  → az NN gradiens: ∂L/∂w ∝ feature → kicsi gradiens!
  → a súly ALULTANUL — a modell nem használja a feature-t!
  
  DE LGBM-ben a feature HASZNOS (SHAP fontos!):
  → LGBM threshold: "PastRet_1 > 0.001?" → igen/nem → információ!
  → NN: 0.001 × w → kicsi → elnyelődik a többi feature-ben
  
  OK: a skálázatlan feature-t az NN "nem látja"!
  OK: RankGauss kényszeríti N(0,1)-be → σ = 1 → az NN "látja"!
  OK: ez a FUNDAMENTÁLIS ok amiért normalizáció KELL NN-hez!
```

### SKEWED (torzított eloszlás):

| Feature | μ | σ | μ/σ | Probléma |
|---|---|---|---|---|
| vol_calm_f | 0.968 | 0.176 | 5.5 | 97%-ban 1 (calm) → ritka a non-calm! |

---

## SZINTÉZIS: Mit jelent ez a V11-re?

```
1. Feature redukció: 32 → 18 feature
   → 44% kevesebb param → data/param 72.1 → JOBB!
   → kevesebb multikollinearitás → stabilabb tanítás!

2. Normalizáció KÖTELEZŐ:
   → 7 feature LARGE RANGE → RankGauss kell!
   → 4 feature NEAR ZERO STD → RankGauss KELL (különben NN nem látja!)
   → RSI [0,100] → centring kell: (RSI-50)/50 → [-1,+1]

3. Autokorreláció kezelés:
   → ticks_inv_f ρ₁=0.84 → vagy eldobjuk, vagy embargo=20+
   → vagy: rolling differencing: Δticks_inv = ticks_inv[t] - ticks_inv[t-1]
   → Δfeature kevésbé korrelált → több effektív sample!

4. Effektív sample:
   → N_eff ≈ 26,000 per-bar (61% a nominálisnak)
   → MLP H=16 L=2: data/param = 26,000/593 = 43.8 ✅
   → MLP H=32 L=2: data/param = 26,000/1,825 = 14.2 ✅ (még mindig jó!)
   
5. A feature redukció + normalizáció EGYÜTT:
   → 18 feature + RankGauss + H=16 L=2 → data/param=43.8
   → Class imbalance 72:1 → Focal Loss γ=2
   → Blocked CV + embargo=10
   → Early stopping patience=20
   → → EZ a biztonságos konfiguráció!
```
