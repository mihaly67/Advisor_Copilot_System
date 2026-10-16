# Session: v104_baseline_stats_sweep_features
*Időbélyeg: 2026-09-30T18:40:34.595448*

# v1.04 Baseline Statisztika + Threshold Sweep + Feature Scan — 2026.09.30

## BASELINE MENTVE (v104_baseline/)
- Model: /data/dev/projects/z-ai-copilot/models/v104_baseline/lgbm_v104.pkl
- Scripts: train_jules_v104_baseline.py, threshold_audit_v104_baseline.py, viz_v104_pred_baseline.py

## BASELINE MODELL STATISZTIKA (lgbm_v104.pkl, 42 feat)

### OOS Classification Report (default threshold)
```
              precision    recall  f1-score   support
       Short       0.62      0.85      0.72      3785
       Noise       0.45      0.25      0.32      5048
        Long       0.63      0.76      0.69      4056
    accuracy                           0.59     12889
```

### Kulcs metrika
- Noise recall: 24.9% (5048 Noise bar-ból csak 1258 felismerve!)
- Noise→Long: 1819 (36.0%) — Noise hibásan Long-nak
- Noise→Short: 1971 (39.0%) — Noise hibásan Short-nak
- Dir correctly as Dir: 80.1%
- Dir→Noise: 19.9%

### Feature Importance (top 10)
1. ATR_Micro (3933)
2. Dist_Ter_R_ATR (3587)
3. Dist_Ter_S_ATR (3494)
4. Dist_Sec_S_ATR (3341)
5. Dist_Sec_R_ATR (3202)
6. Dist_Micro_R_ATR (3180)
7. Trend_Strength_20 (3028)
8. Dist_Micro_S_ATR (2828)
9. Stoch_D (2669)
10. Slope_Close_14 (2655)

## THRESHOLD SWEEP EREDMENYEK

### Profit top (teljes OOS)
| THL | THS | THN | Trades | WR% | Profit | P/tr | DN% | PL ratio |
|-----|-----|-----|--------|-----|--------|------|-----|----------|
| 0.25| 0.30| 0.70| 12173  |61.3 | 10216  |0.839|38.7| 1.58     |
| 0.25| 0.35| 0.70| 12037  |61.5 | 10154  |0.844|38.5| 1.59     |
| 0.25| 0.40| 0.70| 11873  |61.5 | 10042  |0.846|38.5| 1.60     |
| 0.35| 0.40| 0.70| 11657  |61.5 |  9865  |0.846|38.5| 1.60     |

### WR top (min 3000 trades)
| THL | THS | THN | Trades | WR% | Profit | P/tr | DN% | PL ratio |
|-----|-----|-----|--------|-----|--------|------|-----|----------|
| 0.25| 0.30| 0.30|  5344  |66.8 |  5369  |1.005|33.2| 2.01     |

### Kiemelt kombinaciok
| THL | THS | THN | Trades | WR% | Profit | P/tr | DN% | PL |
|-----|-----|-----|--------|-----|--------|------|-----|-----|
| 0.35| 0.40| 0.50| 10081  |62.4 |  8786  |0.872|37.6|1.66|
| 0.40| 0.45| 0.45|  9137  |62.7 |  8047  |0.881|37.3|1.68|
| 0.45| 0.50| 0.40|  8051  |63.8 |  7369  |0.915|36.2|1.77|
| 0.50| 0.55| 0.35|  6706  |64.9 |  6344  |0.946|35.1|1.85|
| 0.30| 0.35| 0.55| 10836  |62.1 |  9339  |0.862|37.9|1.64|
| 0.25| 0.30| 0.60| 11412  |61.7 |  9714  |0.851|38.3|1.61|

## UJ FEATURE SCAN (Noise-vs-Dir)

### Top 10 uj feature AUC = 0.7009 (binary Noise-vs-Dir)
1. RSI_M15 (926 imp)
2. Regime_ADX (891)
3. Amihud_Illiq (776)
4. Regime_Slope (691)
5. Trend_EMA_Slow_Dist (688)
6. Trend_EMA_Super_Dist (681)
7. Kyle_Lambda (668)
8. Kyle_Vol_Sync (628)
9. EMA50_Slope_Up (35)
10. Regime_Short_Context (16)

### Kategoria AUC
- REGIME: 0.5976 (8 feat)
- FLOW: 0.5844 (3 feat)
- MICROSTRUCTURE: 0.5677 (5 feat)
- INFORMED: 0.5612 (4 feat)

### Ajanlott 13 uj feature (|corr|>0.02)
1. Kyle_Vol_Sync (-0.051) INFORMED
2. Trend_EMA_Super_Dist (+0.038) PRICE_DIST
3. Trend_EMA_Slow_Dist (+0.034) PRICE_DIST
4. RSI_M15 (-0.032) — nagyobb timeframe RSI
5. Kyle_Lambda (-0.032) INFORMED
6. Regime_Short_Context (-0.029) REGIME
7. Regime_Slope (-0.025) REGIME
8. EMA50_Slope_Up (-0.024)
9. Regime_ADX (-0.023) REGIME
10. Amihud_Illiq (-0.022) INFORMED
11. Micro_Price_Dist (+0.022) PRICE_DIST
12. VPIN (+0.021) INFORMED
13. Price_Vel_Up (+0.021)

## KULCS FELFEDEZES
- A modell LEGBIZTATLANABB a Noise felismeresben (recall 24.9%)
- 74% Noise bar hibásan iránynak jósolva → ez a DirAsNoise hiba forrása
- Uj feature-ek (Regime, INFORMED, nagyobb TF) AUC=0.70 a Noise-vs-Dir szétválasztásban
- Ha ezek bekerülnek a modellbe, a Noise recall javulhat → DirAsNoise csökken
