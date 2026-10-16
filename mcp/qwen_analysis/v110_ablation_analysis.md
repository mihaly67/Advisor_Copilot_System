# V1.10 Normalizálás Ablation Study — Teljes Analízis

**Dátum:** 2026-10-05  
**Script:** `norm_ablation_study.py`  
**Futásidő:** 55 másodperc  

---

## 1. KUTATÁSI KÉRDÉS

1. **Mit jelent az ATR-normalizálás?** A Dist_* feature-k `(Level - Close) / ATR14` formulával készülnek. Mi történik, ha kiveszzük és `%` távolságot használunk `(Level - Close) / Close`?
2. **Stoch irány-kizáró szűrés hatása?** A korábbi session kimutatta, hogy Stoch raw filter káros. De mi van az **irány-kizáró** (anti-directional) szűréssel: Long elvetve ha Stoch<0, Short elvetve ha Stoch>0?

---

## 2. NÉGY KONFIGURÁCIÓ

| # | Név | ATR norm? | Stoch anti? | Leírás |
|---|---|---|---|---|
| A | ATR_norm | ✅ | ❌ | **Baseline** (v110 production) |
| B | raw_pct | ❌ | ❌ | Nyers % távolság (ATR nélkül) |
| C | raw_pct_stoch | ❌ | ✅ | Nyers % + Stoch irány-kizáró |
| D | ATR_norm_stoch | ✅ | ✅ | ATR norm + Stoch irány-kizáró |

### Normalizálás képletek

**ATR-normalizált (jelenleg):**
```python
Dist_Micro_R = (Micro_R - Close) / ATR14   # tipikus érték: 6.4 ± 8.4
Upper_Wick_ATR = Upper_Wick / ATR14         # tipikus érték: 0.18 ± 0.21
```

**Nyers % (ATR nélkül):**
```python
Dist_Micro_R = (Micro_R - Close) / Close    # tipikus érték: 0.002 ± 0.003
Upper_Wick_ATR = Upper_Wick / Close          # tipikus érték: 0.00005 ± 0.00006
```

---

## 3. EREDMÉNYEK

### Főtáblázat

| Config | WR% | Profit | Trades | WR_thr | P_thr | T_thr | Opp swap |
|---|---|---|---|---|---|---|---|
| **A_ATR_norm** | **54.0** | **$2,844** | **8,138** | 52.3 | $3,700 | 11,990 | 2,206 |
| B_raw_pct | 53.0 | $2,606 | 7,989 | 52.1 | $3,464 | 11,418 | 2,311 |
| C_raw_pct_stoch | 49.7 | $598 | 2,474 | 52.1 | $3,464 | 11,418 | 796 |
| D_ATR_norm_stoch | 50.3 | $659 | 2,561 | 52.3 | $3,700 | 11,990 | 789 |

### Normalizálás hatás (azonos Stoch beállítással)

| Összehasonlítás | ΔWR | ΔProfit |
|---|---|---|
| A_ATR_norm → B_raw_pct | **-1.0%** | **-$238** |
| D_ATR_norm_stoch → C_raw_pct_stoch | +0.6% | +$60 |

### Stoch irány-kizáró hatás (azonos normalizálással)

| Összehasonlítás | ΔWR | ΔProfit | ΔTrades |
|---|---|---|---|
| A→D (ATR norm) | **-3.7%** | **-$2,185** | -5,577 |
| B→C (raw %) | **-3.3%** | **-$2,007** | -5,515 |

---

## 4. FEATURE ELOSZLÁS STATISZTIKA

| Feature | ATR mean | ATR std | Raw mean | Raw std | Std arány |
|---|---|---|---|---|---|
| Tick_Speed | 0.0700 | 0.0607 | 0.0700 | 0.0607 | 1.00x |
| Dist_Micro_R | 6.4116 | 8.3694 | 0.0020 | 0.0030 | 0.00x |
| Dist_Micro_S | 6.5947 | 8.1100 | 0.0019 | 0.0026 | 0.00x |
| Dist_Sec_R | 12.0741 | 13.6743 | 0.0036 | 0.0046 | 0.00x |
| Dist_Sec_S | 14.4121 | 19.2167 | 0.0040 | 0.0049 | 0.00x |
| Dist_Ter_R | 23.3495 | 24.5072 | 0.0068 | 0.0073 | 0.00x |
| Dist_Ter_S | 24.9931 | 26.4898 | 0.0069 | 0.0068 | 0.00x |
| Stoch_State_M1 | 0.0001 | 0.7141 | 0.0001 | 0.7141 | 1.00x |
| Upper_Wick_ATR | 0.1762 | 0.2111 | 0.0001 | 0.0001 | 0.00x |
| Lower_Wick_ATR | 0.1764 | 0.2097 | 0.0001 | 0.0001 | 0.00x |

**Kulcs:** ATR-normalizált feature-k std-je **100-3000x** nagyobb mint a nyers %-osé!

---

## 5. KONFÚZIÓS MÁTRIXOK

### A_ATR_norm (baseline)
```
              Act Short  Act Noise  Act Long
Pred Short       1879         0      1231
Pred Noise        564         0       975
Pred Long         975         0      2514
```

### B_raw_pct
```
              Act Short  Act Noise  Act Long
Pred Short       1625         0      1441
Pred Noise        459         0       981
Pred Long         870         0      2613
```

### C_raw_pct_stoch
```
              Act Short  Act Noise  Act Long
Pred Short        452         0       517
Pred Noise        113         0       336
Pred Long         279         0       777
```

### D_ATR_norm_stoch
```
              Act Short  Act Noise  Act Long
Pred Short        523         0       483
Pred Noise        161         0       323
Pred Long         306         0       765
```

**Megjegyzés:** "Act Noise" oszlop mindenhol 0 — a modell sosem jósol Noise-t a stability filter után.

---

## 6. FŐ KÖVETKEZTETÉSEK

### 6.1 ATR-normalizálás → JO ✅
- ATR norm (A) **1.0%-kal jobb WR** és **$238-cal több profit** mint nyers % (B)
- Ok: ATR skálázás nagyobb tartományt ad a feature-knek (std 8-26x vs 0.003-0.007)
- LGBM jobban tud separálni nagyobb varianciájú feature-kkel
- ATR norm megőrzi a volatilitás-kontextust: ugyanannyi ATR távolság = ugyanannyi "jelentőség"

### 6.2 Stoch irány-kizáró → KÁROS ❌
- Stoch anti-directional **-3.3%~-3.7% WR** és **-$2000+ profit** veszteség
- Ok: Stoch(2,3) túl gyors (lag1 autocorr=0.288, lag2=0.01) → zajos
- Stoch irány-kizáró **~55%-át elveti** a jeleknek (11990→6022 trade)
- Az elvetett jelek közt sok jó is van → WR zuhan
- **Ez megerősíti a korábbi felismerést: Stoch CFD-n káros, minden formában!**

### 6.3 Optimális konfiguráció
**A_ATR_norm = ATR normalizált + Stoch KI** továbbra is a legjobb:
- WR=54.0%, P=$2,844, T=8,138
- Nincs érv a Stoch bekapcsolása mellett (sem raw, sem anti-directional)
- Nincs érv az ATR normalizálás eltávolítása mellett

---

## 7. KIMENET FÁJLOK

| Fájl | Méret | Leírás |
|---|---|---|
| `viz_ablation_A_ATR_norm.html` | 1,228 KB | Baseline viz (ATR norm, Stoch KI) |
| `viz_ablation_B_raw_pct.html` | 1,225 KB | Nyers % viz (Stoch KI) |
| `viz_ablation_C_raw_pct_stoch.html` | 1,174 KB | Nyers % + Stoch BE viz |
| `viz_ablation_D_ATR_norm_stoch.html` | 1,176 KB | ATR norm + Stoch BE viz |
| `viz_ablation_comparison.html` | 10 KB | 4 konfig összehasonlítás |
| `viz_ablation_feat_dist.html` | 23,896 KB | Feature eloszlás ATR vs Raw |
| `ablation_results.json` | 3 KB | Numerikus eredmények |
