# LAG AUDIT v1.06 — Lookahead vs Indikátor Lag (2026-10-01)

## Végső Konklúzió: NEM LOOKAHEAD — INDIKÁTOR LAG!

A v1.06 modell predikciója **8 bar-ral késik** az árváltozás mögött. Ez NEM előretekintési hiba (lookahead bias), hanem a 14 periódusú indikátorok inherens simítási késleltetése.

## Bizonyítékok

### 1. Cross-correlation: P(Long) vs Forward Return
| Lag | Corr | Jelzés |
|-----|------|--------|
| -8 | 0.2441 | ◄ BEST — P(Long) 8 bar-ral KÉSIK |
| -4 | 0.1488 | P(Long) 4 bar-ral késik |
| 0 | -0.0112 | Szinkron — NINCS korreláció! |
| +1 | -0.0118 | "Lookahead" — r≈0, irreleváns |

### 2. Forward WR ≈ 49% (véletlenszint!)
Ha lenne lookahead, Forward WR >> 50% lenne.

### 3. Feature lag hierarchia
- **Gyors (< 3 bar)**: PastRet_1, RSI_Fast_5, WPR_14, Micro_RSI_14
- **Közepes (3-5 bar)**: Pulse_MACD_Hist, Stoch_D, PastRet_5, Flow_MFI_5
- **Lassú (> 5 bar)**: EMA50_Slope_Up (6), Slope_Close_14 (8), MomScore_14 (8)

### 4. Kódbizonyíték
`dom_feature_engineer_mtf.py`: minden feature `.shift(1)`-elve.

## Valós probléma: Forward WR = 49%
A modell NEM tudja megjósolni a következő bar irányát. A 61.2% label WR a triple barrier label-ből jön (ami 5 percet néz előre).
