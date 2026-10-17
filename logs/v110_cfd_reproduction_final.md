# Jules V1.10 CFD Reprodukció — VÉGSŐ EREDMÉNYEK

## Pipeline konfiguráció
- **Bemenet**: v2 CFD CSV (XAUUSD, tick-count volume proxy)
- **Threshold**: $1,746,000 (kalibrált: $444K × CFD_flow/Jules_flow = $444K × 3.93)
- **Cél**: Jules 37.6 sec/bar reprodukálása CFD adaton

## Dollar Bars
| | Jules (Futures, $444K) | CFD (tick-count, $1,746K) |
|---|---|---|
| Bar-ek | 75,451 | 162,065 |
| Sec/bar mean | 37.6s | **40.1s** ✅ |
| Sec/bar median | 21.0s | **21.0s** ✅ |
| Total_Volume mean | 149.8 | 429.3 |

## Label Distribution
- Long: 39.6%, Noise: 20.7%, Short: 39.7%

## Model Performance (OOS: 24,446 bars)
| Szűrő | WR | Profit | Trades |
|---|---|---|---|
| Threshold only | **48.3%** | 3,712.5 | 17,850 |
| + Stoch Filter | **47.3%** | 1,641.0 | 8,969 |
| + Stability | **47.7%** | 451.5 | 2,331 |

## Diagnosztika
- **Circ**: 0.1167
- **Leakage**: NO LEAKAGE ✅
- **Walk-Forward**: 49.3% ± 2.6% ✅
  - Fold 1: 54.1%, Fold 2: 46.6%, Fold 3: 49.5%, Fold 4: 48.1%, Fold 5: 48.1%

## Feature Importance
1. Dist_Ter_R: 12.15%
2. Dist_Ter_S: 11.46%
3. Dist_Sec_R: 11.45%
4. Dist_Micro_R: 11.18%
5. Dist_Sec_S: 11.14%
6. Dist_Micro_S: 11.07%
7. Tick_Speed: 9.32%
8. Stoch_State_M1: 8.20%
9. Upper_Wick_ATR: 7.06%
10. Lower_Wick_ATR: 6.97%

## Kulcs megállapítások
1. **CFD-re sikeresen adaptáltuk Jules rendszerét** — threshold kalibráció elég
2. **WR ~48% OOS** — a modell tanul, de közel van az 50%hez (random)
3. **NO LEAKAGE** — a pipeline tiszta
4. **WF 49.3%** — stabil, de marginális
5. A volume CSAK a dollar bar képzésbe megy be — a 10 feature független a volume mértékegységétől
6. A tick-count proxy más eloszlást ad (Bid≈Ask), de a bar duráció egyezik
