# V1.10 Irány Feature-k Study — Teljes Eredmény

**Dátum:** 2026-10-05  
**Script:** `direction_features_study.py`  
**Futásidő:** 49 másodperc  

---

## 1. KUTATÁSI KÉRDÉS

A baseline (A_ATR_norm) WR=54.0% de opposite swap=33.4%. Az eddigi 10 feature mind **magnitúdót** mér (távolság, wick méret) — egyik sem kódolja közvetlenül az **irányt**. Ha hozzáadunk 8 irány-információt hordozó feature-t, javul-e a WR és csökken-e a swap?

---

## 2. 8 ÚJ IRANY FEATURE

| # | Feature | Képlet | Tartomány | Mit kódol |
|---|---|---|---|---|
| 1 | **RSI_M15_signed** | (RSI_M15 - 50) / 50 | [-1, +1] | M15 trend irány |
| 2 | **MACD_Hist_ATR** | MACD_Hist / ATR14 | ~[-2, +2] | Trend erő iránnyal |
| 3 | **RSI_signed** | (RSI14 - 50) / 50 | [-1, +1] | Mikro trend irány |
| 4 | **ROC_5** | Micro_ROC_5 | ~[-1, +1] | 5-bar változás iránya |
| 5 | **BB_ZScore** | Micro_BB_ZScore | ~[-3, +3] | Ár pozíció BB-n belül |
| 6 | **MFI_signed** | (MFI - 50) / 50 | [-1, +1] | Flow irány |
| 7 | **OBI_ZScore** | OBI_ZScore | ~[-3, +3] | Order flow imbalance |
| 8 | **Price_Vel_ATR** | Price_Velocity / ATR14 | ~[-2, +2] | Ármozgás irány+erő |

---

## 3. EREDMÉNYEK

### Főtáblázat

| Config | N_feat | WR% | Profit | Trades | Opp Swap | Swap% |
|---|---|---|---|---|---|---|
| A_10feat (baseline) | 10 | 54.0 | $2,844 | 8,138 | 2,206 | 33.4% |
| **B_18feat (+8 dir)** | **18** | **56.0** | **$3,181** | **7,934** | **2,144** | **32.5%** |

### Javulás
- ✅ **+2.0% WR** (54.0 → 56.0)
- ✅ **+$336 profit** ($2,844 → $3,181)
- ✅ **-62 opposite swap** (2,206 → 2,144)
- ✅ **-0.9% swap%** (33.4% → 32.5%)
- ✅ **P(L)-P(S) gap swap-kor nőtt**: 0.020 → 0.028 (modell magabiztosabb)

### Konfúziós mátrixok

**A_10feat:**
```
              Act Short  Act Noise  Act Long
Pred Short       1879         0      1231
Pred Noise        564         0       975
Pred Long         975         0      2514
```

**B_18feat:**
```
              Act Short  Act Noise  Act Long
Pred Short       1804         0      1274
Pred Noise        460         0       884
Pred Long         870         0      2642
```

---

## 4. FEATURE IMPORTANCE (18feat modell)

| Rank | Feature | Importance | Típus |
|---|---|---|---|
| **1** | **RSI_M15_signed** | **7.97%** | 🆕 ÚJ |
| 2 | Dist_Micro_R | 7.21% | Eredeti |
| 3 | Dist_Micro_S | 7.20% | Eredeti |
| 4 | Dist_Ter_R | 7.01% | Eredeti |
| 5 | Dist_Ter_S | 6.87% | Eredeti |
| 6 | Dist_Sec_R | 6.80% | Eredeti |
| 7 | Dist_Sec_S | 6.66% | Eredeti |
| **8** | **MACD_Hist_ATR** | **5.76%** | 🆕 ÚJ |
| 9 | Tick_Speed | 5.64% | Eredeti |
| **10** | **RSI_signed** | **5.29%** | 🆕 ÚJ |
| **11** | **ROC_5** | **5.22%** | 🆕 ÚJ |
| **12** | **BB_ZScore** | **4.64%** | 🆕 ÚJ |
| **13** | **MFI_signed** | **4.45%** | 🆕 ÚJ |
| **14** | **OBI_ZScore** | **4.43%** | 🆕 ÚJ |
| **15** | **Price_Vel_ATR** | **4.12%** | 🆕 ÚJ |
| 16 | Upper_Wick_ATR | 3.92% | Eredeti |
| 17 | Stoch_State_M1 | 3.52% | Eredeti |
| 18 | Lower_Wick_ATR | 3.30% | Eredeti |

**Kulcs:** RSI_M15_signed a #1 legfontosabb feature! A 8 új feature közül 5 a top 15-ben van.

---

## 5. KÖVETKEZTETÉSEK

### 5.1 Irány feature-k hatása → POZITÍV ✅
- +2.0% WR javulás a 8 irány feature hozzáadásával
- RSI_M15_signed (M15 trend irány) a legfontosabb új feature
- A modell magabiztosabb: P(L)-P(S) gap nőtt swap-kor

### 5.2 Swap még mindig magas (32.5%)
- Bár csökkent 33.4% → 32.5%, még mindig 1/3 rossz irány
- További javítás lehetséges:
  - Dominance threshold: P(L)-P(S) > 0.05
  - Több irány feature (EMA slope, VWAP pozíció)
  - Dist_* irány-kiemelés (közeledik/távolodik a pivot)

### 5.3 ATR normalizálás + irány feature-k = jó kombináció
- ATR norm (7/10 eredményes) + irány feature-k (+2% WR)
- A két megközelítés KOMPLEMENTER, nem konkurens

---

## 6. KIMENET

| Fájl | Méret | Leírás |
|---|---|---|
| viz_dir_A_10feat.html | 1,227 KB | Baseline viz (10 feat) |
| viz_dir_B_18feat.html | 1,225 KB | 18 feat viz |
| viz_dir_comparison.html | 10 KB | A vs B összehasonlítás |
| direction_results.json | 2 KB | Numerikus eredmények |
