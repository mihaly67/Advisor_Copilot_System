# Z.ai v1.10 CFD Dollar Bar Sweep — Összefoglaló

**Dátum:** 2026-10-07  
**Pipeline:** v110_dollarbar_sweep_viz.py  
**Adatforrás:** CFD CSV (Scalper_Copilot_MTF_Data_v2.csv + külön_vizsga.csv)  
**Tick-szám:** 4,150,493 train + 386,708 vizsga  

---

## Dollar Bar Sweep Eredmények (8 konfiguráció)

| # | Konfiguráció | OOS WR | OOS P$ | OOS T | Viz WR | Viz P$ | Viz T | Gap | Stabil? |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **$444K-adapt-18f-MB8** | **49.4%** | **$113** | 482 | **46.7%** | **$38** | 227 | +2.7% | ✅ |
| 2 | $444K-adapt-18f-MB5 | 49.0% | $120 | 537 | 44.4% | $25 | 225 | +4.6% | |
| 3 | $654K-adapt-18f-MB8 | 44.3% | $66 | 619 | 39.9% | -$0 | 283 | +4.4% | |
| 4 | $654K-adapt-18f-MB5 | 44.1% | $32 | 311 | 37.1% | -$10 | 143 | +7.0% | |
| 5 | $888K-adapt-18f-MB8 | 40.9% | $12 | 540 | 40.4% | $3 | 267 | +0.5% | ✅ |
| 6 | $888K-adapt-18f-MB5 | 40.3% | $2 | 310 | 32.7% | -$29 | 159 | +7.6% | |
| 7 | $1.7M-adapt-18f-MB5 | 34.8% | -$40 | 310 | 27.2% | -$50 | 158 | +7.6% | |
| 8 | $1.7M-adapt-18f-MB8 | 34.2% | -$55 | 380 | 30.2% | -$49 | 199 | +4.0% | |

---

## Volbar Referencia (eddigi legjobb)

| Konfig | OOS WR | OOS P$ | OOS T | Viz WR | Viz P$ | Viz T | Gap |
|---|---|---|---|---|---|---|---|
| **volbar_3_PT1.5_SL1.0_MB8** | **50.8%** | **$616** | 2281 | **51.7%** | **$241** | 826 | **-0.9%** |

---

## Kulcs Megállapítások

### 1. Threshold skalálás — egyértelmű trend
- **$444K > $654K > $888K > $1.7M** — monoton csökkenő WR
- Nagyobb threshold = kevesebb bar = kevesebb információ = rosszabb predikció
- A $1.7M (futures kalibrált) threshold **katasztrofális** CFD-n: 34.2% OOS, 30.2% Viz

### 2. $444K a legjobb dollárbár threshold CFD-n
- OOS=49.4%, Viz=46.7% — de még mindig elmarad a volbar-tól (50.8%/51.7%)
- MB8 > MB5 következetesen (stabilabb címkézés)

### 3. $888K-MB8: legstabilabb gap (0.5%)
- Alacsony WR (40.9%/40.4%), de OOS≈Viz — nem overfittel
- Lehet, hogy konzervatívabb threshold-szal stabilabb, de kevésbé profitábilis

### 4. Volbar továbbra is veri a dollárbárt
- Volbar: 50.8% OOS / 51.7% Viz / -0.9% gap
- Best dollar: 49.4% OOS / 46.7% Viz / +2.7% gap
- A volbar jobb információtartalom-megosztást ad (idő-alapú volatilitás vs. Mid_Price proxy)

### 5. prado_dollar_bars.py helyes logika
- `Dollar_Value = Mid_Price × 1.0` (tick-count proxy) — működik CFD-n
- ATR-normalás adaptívan: `weight = Mid_Price × ATR / (threshold × ATR_median)`
- jules_v110_reproduction.py FATAL BUG: Bid_Volume+Ask_Volume=0 CFD-n

---

## Bar Számok Train/Vizsga

| Threshold | Train bars | Vizsga bars | Átlag tick/bar |
|---|---|---|---|
| $444K | 42,742 | 4,063 | 97 |
| $654K | 29,018 | 2,759 | 143 |
| $888K | 21,371 | 2,032 | 194 |
| $1.7M | 10,869 | 1,034 | 381 |

---

## Optimalizált Threshold-ök

| Konfig | THL | THS | THN |
|---|---|---|---|
| $444K-MB5 | 0.508 | 0.353 | 0.273 |
| $444K-MB8 | 0.533 | 0.386 | 0.264 |
| $654K-MB8 | 0.532 | 0.376 | 0.546 |
| $888K-MB8 | 0.481 | 0.351 | 0.335 |

---

## Fájlok

- **Script:** `/src/v110_dollarbar_sweep_viz.py`
- **Eredmények JSON:** `/docs/v110_dollarbar/dollarbar_sweep_results.json`
- **Vizualizációk (8 HTML):** `/docs/v110_dollarbar/viz_VIZSGA_*.html`
  - viz_VIZSGA_444K-adapt-18f-MB5.html (826 KB)
  - viz_VIZSGA_444K-adapt-18f-MB8.html (826 KB)
  - viz_VIZSGA_654K-adapt-18f-MB5.html (561 KB)
  - viz_VIZSGA_654K-adapt-18f-MB8.html (566 KB)
  - viz_VIZSGA_888K-adapt-18f-MB5.html (416 KB)
  - viz_VIZSGA_888K-adapt-18f-MB8.html (420 KB)
  - viz_VIZSGA_1p7M-adapt-18f-MB5.html (215 KB)
  - viz_VIZSGA_1p7M-adapt-18f-MB8.html (217 KB)

---

## Következtetés

**CFD-n a dollárbár $444K threshold a legjobb, de a volbar (ATR=3.0) továbbra is felülmúlja.**  
A $1.7M futures kalibrált threshold teljesen használhatatlan CFD-n — ez magyarázi a korábbi "56% WR" futures eredmények invaliditását (rossz CSV + data leakage + rossz threshold).
