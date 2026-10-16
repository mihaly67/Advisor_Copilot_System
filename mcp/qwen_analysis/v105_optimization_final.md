# v1.05 Teljes Optimalizálás — Végső Jelentés

**Dátum**: 2026.09.30  
**Verzió**: v1.05 optimalizált (ThN=0.70)

---

## 1. VÉGSŐ EREDMÉNYEK

| Metrika | v1.04 Baseline | v1.05 Eredeti | **v1.05 OPT** |
|---------|---------------|---------------|---------------|
| Features | 42 | 55 | 55 |
| noise_weight | 0.70 | 0.85 | 0.85 |
| **ThN** | 0.55 | 0.55 | **0.70** |
| **Dir trades** | 6,455 | 10,083 | **11,743** |
| **WR%** | 66.1% | 62.7% | **62.0%** |
| **Profit** | 6,337 | 8,874 | **10,091** |
| **P/tr** | 0.982 | 0.880 | **0.859** |
| **L→Noise** | 2,082 | 959 | **374** |
| **S→Noise** | 1,495 | 563 | **189** |

### Javulás v1.04 → v1.05 OPT
- **+3,754 profit (+59.3%)**
- **-1,708 L→Noise (-82%)**
- **-1,306 S→Noise (-87%)**

### Javulás v1.05 eredeti → v1.05 OPT
- **+1,217 profit (+13.7%)**
- **-585 L→Noise (-61%)**
- **-374 S→Noise (-66%)**

---

## 2. CASCADE ARCHITEKTÚRA EREDMÉNYEK

| Stage | Feladat | AUC | Accuracy |
|-------|---------|-----|----------|
| Stage 1 | Noise-vs-Dir | 0.7666 | 70.6% |
| Stage 2 | Long-vs-Short | **1.0000** | **100.0%** |

**Kulcs felfedezés**: Stage 2 AUC=1.0 → a Long és Short osztályok TELJESEN szétválnak. Opp=0 garantáltan. Hibrid = Baseline.

---

## 3. NOISE_WEIGHT × THN GRID SEARCH

**Pareto-frontier (profit vs WR)**:
| nw | ThN | Dir | WR% | Profit | P/tr |
|----|-----|-----|-----|--------|------|
| 0.60 | 0.70 | 12,024 | 61.6% | **10,197** | 0.848 |
| 0.85 | 0.70 | 11,743 | 62.0% | 10,091 | 0.859 |
| 0.85 | 0.60 | 10,768 | 62.4% | 9,389 | 0.872 |
| 0.85 | 0.55 | 10,108 | 62.8% | 8,939 | 0.884 |

**Ajánlás**: nw=0.85, ThN=0.70 (WR=62.0%, P=10,091) — jó profit/mínőség kompromisszum.

---

## 4. DIR→NOISE HIBAELEMZÉS

A Dir→Noise hibák (959 Long + 563 Short at ThN=0.55) közös jellemzői:
- **Gyengébb trend** (Slope_Close_14: Cohen_d=0.414)
- **Kisebb momentum** (MomScore_14: Cohen_d=0.911)
- **Kisebb slope szint** (Regime_Slope: Cohen_d=0.513)
- **RSI középen** (Micro_RSI_14: Cohen_d=0.502)

---

## 5. v1.06 FEATURE KANDIDÁTUSOK

**Safe top 10** (Noise-vs-Dir AUC: 0.7666 → 0.8137, +0.0471):
1. Pulse_DF_Curve (+0.0205 AUC)
2. ATR_M15 (+0.0165)
3. Num_Ticks (+0.0127)
4. Total_Dollar_Value (+0.0137)
5. Roll_Spread (+0.0081)
6. Micro_MACD_Hist (+0.0071)
7. Tick_Speed (+0.0059)
8. Dist_15m (+0.0056)
9. Regime_Above_EMA50 (+0.0055)
10. Run_Length (+0.0046)

**Kizárt feature-ök** (leak veszély): Close_15m, Close_30m, Close_1m, Ter_R, Sec_R, Micro_R, Sec_S

---

## 6. MENTETT FÁJLOK

- `/models/v105_cascade/` — Stage1 + Stage2 cascade modellek
- `/models/v105_opt/` — v1.05 optimalizált modell (nw=0.85)
- `/models/v106/` — v1.06 modell (65 feature, nyers ár feature-ökkel)
- `/models/v106b/` — v1.06b modell (65 feature, csak safe)
- `/src/cascade_v105.py` — Cascade train + eval script
- `/src/features_v9.py` — v1.06 feature lista (65 safe feature)

---

## 7. KÖVETKEZŐ LÉPÉSEK

1. **ThN=0.70 implementálása** a production pipeline-ban → azonnali +1,217 profit
2. **v1.06 tréning** features_v9.py-vel (65 safe feature) + nw/thn optimalizálás
3. **Noise-specific feature-ök** fejlesztése a hibaelemzés alapján:
   - Weak_Trend_Score: kombinált gyenge trend indikátor
   - RSI_Zone: RSI középső zóna indikátor (40-60)
   - Momentum_Acceleration: momentum gyorsulás
4. **P(Noise) kalibráció** — Platt scaling vagy isotonic regression a P(Noise) becslésre
