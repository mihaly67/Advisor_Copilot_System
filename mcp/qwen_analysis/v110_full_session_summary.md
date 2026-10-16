# V1.10 Session Összefoglaló — Normalizálás + Irány Feature-k + Új Felismerés

**Dátum:** 2026-10-05 → 2026-10-06  
**Status:** LEKAPCSOLÁS ELŐTT — MINDEN MENTVE  

---

## 1. MINDEN EREDMÉNY EGY HELYEN

### 1.1 Normalizálás Ablation Study (4 konfig)

| Config | WR% | Profit | Trades | Leírás |
|---|---|---|---|---|
| **A_ATR_norm** 🏆 | **54.0%** | **$2,844** | **8,138** | ATR normalizált, Stoch KI (baseline) |
| B_raw_pct | 53.0% | $2,606 | 7,989 | Nyers % távolság, Stoch KI |
| C_raw_pct_stoch | 49.7% | $598 | 2,474 | Nyers % + Stoch irány-kizáró |
| D_ATR_norm_stoch | 50.3% | $659 | 2,561 | ATR norm + Stoch irány-kizáró |

**Következtetések:**
- ATR normalizálás JO (+1.0% WR vs nyers %)
- Stoch irány-kizáró KÁROS (-3.3% WR, -$2000+ profit)
- ATR norm std 100-3000x nagyobb mint raw % std → jobb LGBM separabilitás

### 1.2 Irány Feature-k Study (10 → 18 feature)

| Config | N_feat | WR% | Profit | Opp Swap | Swap% |
|---|---|---|---|---|---|
| A_10feat (baseline) | 10 | 54.0% | $2,844 | 2,206 | 33.4% |
| **B_18feat (+8 dir)** | **18** | **56.0%** | **$3,181** | **2,144** | **32.5%** |

**Következtetések:**
- +2.0% WR, +$336 profit, -62 opposite swap
- RSI_M15_signed = #1 legfontosabb feature (7.97%)
- 8 új feature-ből 5 bekerült top 15-be

### 1.3 Teljes javulás láncolat

```
v110 baseline (10 feat, ATR norm, Stoch KI):  WR=54.0%  P=$2,844  Swap=33.4%
                        ↓ +8 irány feature
v110+direction (18 feat, ATR norm, Stoch KI): WR=56.0%  P=$3,181  Swap=32.5%
```

---

## 2. 8 ÚJ IRANY FEATURE (és fontosság a 18feat modellben)

| Rank | Feature | Képlet | Importance | Típus |
|---|---|---|---|---|
| **1** | **RSI_M15_signed** | (RSI_M15 - 50) / 50 | **7.97%** | 🆕 ÚJ |
| 2 | Dist_Micro_R | (Micro_R - Close) / ATR14 | 7.21% | Eredeti |
| 3 | Dist_Micro_S | (Close - Micro_S) / ATR14 | 7.20% | Eredeti |
| 4 | Dist_Ter_R | (Ter_R - Close) / ATR14 | 7.01% | Eredeti |
| 5 | Dist_Ter_S | (Close - Ter_S) / ATR14 | 6.87% | Eredeti |
| 6 | Dist_Sec_R | (Sec_R - Close) / ATR14 | 6.80% | Eredeti |
| 7 | Dist_Sec_S | (Close - Sec_S) / ATR14 | 6.66% | Eredeti |
| **8** | **MACD_Hist_ATR** | MACD_Hist / ATR14 | **5.76%** | 🆕 ÚJ |
| 9 | Tick_Speed | 1 / Bar_Time_Sec | 5.64% | Eredeti |
| **10** | **RSI_signed** | (RSI14 - 50) / 50 | **5.29%** | 🆕 ÚJ |
| **11** | **ROC_5** | Micro_ROC_5 | **5.22%** | 🆕 ÚJ |
| **12** | **BB_ZScore** | Micro_BB_ZScore | **4.64%** | 🆕 ÚJ |
| **13** | **MFI_signed** | (MFI - 50) / 50 | **4.45%** | 🆕 ÚJ |
| **14** | **OBI_ZScore** | OBI_ZScore | **4.43%** | 🆕 ÚJ |
| **15** | **Price_Vel_ATR** | Price_Velocity / ATR14 | **4.12%** | 🆕 ÚJ |
| 16 | Upper_Wick_ATR | Upper_Wick / ATR14 | 3.92% | Eredeti |
| 17 | Stoch_State_M1 | (Stoch - 50) / 50 | 3.52% | Eredeti |
| 18 | Lower_Wick_ATR | Lower_Wick / ATR14 | 3.30% | Eredeti |

---

## 3. 🔑 ÚJ FELISMERÉS — RELATÍV IRÁNY PREDIKCIÓ (felhasználó megfigyelése)

### A probléma
Jelenlegi jelalkotás:
```
Long jel:  P(Long) > THL  AND  P(Long) > P(Short)  AND  P(Noise) < THN
Short jel: P(Short) > THS  AND  P(Short) > P(Long)  AND  P(Noise) < THN
```

Ha P(Noise) > THN (0.40) → MINDIG Noise, **még akkor is ha P(Long) >> P(Short)**!

### A felismerés
**Ha P(Long) > P(Short), az irány-információ ÉRVÉNYES még akkor is ha P(Noise) magasabb mindkettőnél.** A két predikció egymáshoz képesti helyzete prediktív! A zaj mértéke csak a bizonyosságot csökkenti, de NEM semmisíti meg az irányt.

### Számított példa
```
Bar #1: P(Long)=0.35, P(Short)=0.25, P(Noise)=0.40
  → Jelenleg: Noise (P(Noise) > THN=0.40)
  → De: P(Long) > P(Short) → irány = LONG!
  → A Noise 0.40 nem jelenti azt, hogy nincs irány

Bar #2: P(Long)=0.30, P(Short)=0.30, P(Noise)=0.40
  → Noise (helyes — nincs egyértelmű irány)
```

### Implementációs lehetőségek

#### Opció A: Relatív irány feature (legígéretesebb)
```python
# ÚJ FEATURE: Directional conviction
# = sign(P(Long) - P(Short)) * |P(Long) - P(Short)|
# Pozitív = Long conviction, Negatív = Short conviction
# Független THN-től!
Dir_Conviction = P(Long) - P(Short)  # tartomány: [-1, +1]
```
Ez feature-ként beléphet a modellbe — a LGBM megtanulja, hogy magas conviction + magas noise = óvatosabb, de még mindig irányos.

#### Opció B: Kétfokozatú jelalkotás
```python
# 1. Erős jel: P(Noise) < THN → hagyományos signal
# 2. Gyenge jel: P(Noise) >= THN DE P(Long) - P(Short) > DOMINANCE
#    → "irány-jel" (kisebb position size)
```

#### Opció C: THN lazítása dominancia esetén
```python
# Ha |P(Long) - P(Short)| > DOMINANCE_THRESHOLD:
#   THN_eff = THN + 0.10  # lazább noise küszöb
# Különben:
#   THN_eff = THN  # szigorú
```

### Swap adatok alátámasztják!
```
A_10feat:  P(L)-P(S) swap=0.020 correct=0.032
B_18feat:  P(L)-P(S) swap=0.028 correct=0.035
```
Amikor a modell TÉVESZT (swap), a P(L)-P(S) gap KICSI (0.02-0.03).
Amikor a modell HELYES, a gap NAGYOBB (0.03-0.04).
→ **A conviction (P(L)-P(S)) DISZKRIMINÁL** a jó és rossz predikciók között!

---

## 4. SWAP ANALÍZIS (33.4% opposite = fő gyengeség)

### Feature mintázat swap vs correct (A_10feat baseline)

| Feature | Swap mean | Correct mean | Diff |
|---|---|---|---|
| Tick_Speed | 0.1415 | 0.1178 | +0.024 |
| Dist_Ter_R | 35.82 | 32.56 | +3.26 |
| Dist_Ter_S | 13.87 | 16.13 | **-2.26** |
| Stoch_State_M1 | 0.071 | 0.023 | +0.049 |

**Minta:** Swap-kor "távolabb R-től, közelebb S-hez" de a modell mégis rossz irányt jósol → **irány információ hiányzik!**

---

## 5. KONFÚZIÓS MÁTRIXOK

### A_10feat (baseline, 10 feature)
```
              Act Short  Act Noise  Act Long
Pred Short       1879         0      1231
Pred Noise        564         0       975
Pred Long         975         0      2514
```
Opposite swap: 2,206 (33.4%)

### B_18feat (18 feature, legjobb)
```
              Act Short  Act Noise  Act Long
Pred Short       1804         0      1274
Pred Noise        460         0       884
Pred Long         870         0      2642
```
Opposite swap: 2,144 (32.5%)

---

## 6. ÖSSZES FÁJL LISTA

### Scriptek
| Fájl | Leírás |
|---|---|
| `src/norm_ablation_study.py` | Normalizálás ablation (4 config, 55s) |
| `src/direction_features_study.py` | Irány feature-k study (10 vs 18, 49s) |
| `src/jules_v110_reproduction.py` | Eredeti v110 pipeline |
| `src/viz_v110_jules_pred.py` | v110 production viz |

### Modellek
| Fájl | Leírás |
|---|---|
| `models/v110_ablation/lgbm_A_ATR_norm.pkl` | Baseline 10 feat ATR norm |
| `models/v110_ablation/lgbm_B_raw_pct.pkl` | 10 feat nyers % |
| `models/v110_ablation/lgbm_C_raw_pct_stoch.pkl` | 10 feat nyers + Stoch |
| `models/v110_ablation/lgbm_D_ATR_norm_stoch.pkl` | 10 feat ATR + Stoch |
| `models/v110_direction/lgbm_A_10feat.pkl` | 10 feat baseline (direction study) |
| `models/v110_direction/lgbm_B_18feat.pkl` | **18 feat (LEGJOBB!)** |
| `models/production_v110_jules/lgbm_v110_jules.pkl` | Production v110 |

### Vizualizációk
| Fájl | Méret | Leírás |
|---|---|---|
| `docs/v110_ablation/viz_ablation_A_ATR_norm.html` | 1,228 KB | Baseline viz |
| `docs/v110_ablation/viz_ablation_B_raw_pct.html` | 1,225 KB | Nyers % viz |
| `docs/v110_ablation/viz_ablation_C_raw_pct_stoch.html` | 1,174 KB | Nyers+Stoch viz |
| `docs/v110_ablation/viz_ablation_D_ATR_norm_stoch.html` | 1,176 KB | ATR+Stoch viz |
| `docs/v110_ablation/viz_ablation_comparison.html` | 10 KB | 4 config összehasonlítás |
| `docs/v110_ablation/viz_ablation_feat_dist.html` | 23,896 KB | Feature eloszlás |
| `docs/v110_direction/viz_dir_A_10feat.html` | 1,227 KB | 10 feat baseline viz |
| `docs/v110_direction/viz_dir_B_18feat.html` | 1,225 KB | 18 feat viz |
| `docs/v110_direction/viz_dir_comparison.html` | 10 KB | 10 vs 18 összehasonlítás |

### JSON eredmények
| Fájl | Leírás |
|---|---|
| `docs/v110_ablation/ablation_results.json` | 4 config numerikus eredmények |
| `docs/v110_direction/direction_results.json` | 10 vs 18 feat eredmények |

### Dokumentáció (Brain)
| Fájl | Leírás |
|---|---|
| `/data/Brain/_qwen_analysis/v110_ablation_analysis.md` | Ablation részletes analízis |
| `/data/Brain/_qwen_analysis/v110_direction_features_analysis.md` | Direction részletes analízis |
| `/data/Brain/_qwen_analysis/v110_jules_cfd_handoff.md` | V110 handoff doksi |

---

## 7. KÖVETKEZŐ LÉPÉSEK (folytatáshoz)

### 🔴 PRIORITÁS 1: Relatív irány conviction feature
- Új feature: `Dir_Conviction = P(Long) - P(Short)` (modell kimenetéből)
- VAGY: P(Long)/P(Short) ratio mint feature
- Train újra 19 feature-rel → várható további WR javulás
- **A felhasználó megfigyelése alapján ez a legígéretesebb irány!**

### 🟡 PRIORITÁS 2: Dominance threshold
- Minimális P(Long)-P(Short) küszöb a jelalkotásban
- Swap-kor P(L)-P(S) = 0.02-0.03 → 0.05 küszöb kiszűrné a bizonytalan jeleket
- Lehet, hogy kevesebb trade de magasabb WR

### 🟢 PRIORITÁS 3: További irány feature-k
- EMA slope (close - EMA50) / ATR
- VWAP pozíció (close - VWAP) / ATR
- Close momentum signed: sign(close[t] - close[t-5])
- Dist_* irány-kiemelés: közeledik vagy távolodik a pivot?

### ⚪ PRIORITÁS 4: Optuna threshold optimalizálás az 18feat modellre
- THL, THS, THN újra-optimalizálása 18 feature-rel
- Lehet, hogy más optimum mint 10 feature-rel

---

## 8. ADAT ÉS KONFIGURÁCIÓ

### Adat
- CSV: `/data/dev/projects/z-ai-copilot/Master_csv/processed/jules_v110_labeled.csv`
- 122,229 bars (97,783 train / 24,446 OOS)
- 48 oszlop (10 használt + 38 nem használt eredetileg)

### LGBM hyperparaméterek (minden config azonos)
```python
LGBM_PARAMS = {
    'n_estimators': 781, 'learning_rate': 0.0142, 'num_leaves': 57,
    'max_depth': 6, 'min_child_samples': 24, 'colsample_bytree': 0.566,
    'class_weight': 'balanced', 'objective': 'multiclass',
    'random_state': 42, 'n_jobs': -1, 'verbose': -1
}
```

### Threshold-ok
```python
THL = 0.390  # Long küszöb
THS = 0.400  # Short küszöb
THN = 0.400  # Noise küszöb (abs mode)
SW  = 2      # Stability window
```

### VIZ_STANDARD v1.0 (minden vizualizáció)
- 2 panel: (1) OHLC Candlestick + predikciós háromszögek, (2) Valószínűség + Threshold
- Short=#B22222 FireBrick, Long=#228B22 ForestGreen, Noise=#888888 Gray
- Dark theme: #111111 plot, #000000 paper, #333333 grid
- CDN Plotly, Post-process grid fix

---

**MINDEN MENTVE. LEKAPCSOLÁS UTÁN INNEN FOLYTATJUK:**
1. Relatív irány conviction feature implementálása
2. Dominance threshold tesztelés
3. 18feat modell Optuna optimalizálás
