# Pipeline V5 — Pruning + Javítás Eredmények
*2026-09-23 18:05*

## Modell verziók összehasonlítása

| Verzió | Feature | Accuracy | Short R | Long R | Noise R | Macro F1 |
|---|---|---|---|---|---|---|
| V1 eredeti | 48 | 40.28% | 73% | **17%** | 19% | 0.33 |
| V2 fordított pivot | 48 | 40.52% | 74% | 16% | 19% | 0.33 |
| V3 DF-norm + Ter200 | 48 | 40.73% | 68% | **25%** | 15% | 0.34 |
| V4 agresszív prune | 26 | 40.68% | 73% | 19% | 16% | 0.33 |
| **V5 konzervatív prune** | **38** | **41.08%** | 71% | **24%** | 13% | **0.34** |

## V5 SHAP Top 5 Long Feature
1. **Ter_S**: 0.359 ← #1 Long (200-bar rolling low, újraszámolt)
2. **Trend_EMA_Super_Dist**: 0.051 ← fordított logika működik
3. ATR_Micro: 0.049
4. Close_15m: 0.038
5. Avg_Spread: 0.036

## V5 Pivot Long_minus_Short — 4 pozitív!
- Trend_EMA_Super_Dist: +0.036 ✅ Long-ot segít
- Dist_Sec_S_ATR: +0.002 ✅ Long-ot segít
- Dist_30m: +0.005 ✅ Long-ot segít
- Dist_Ter_R_ATR: +0.001 ✅ Long-ot segít

## Elvégzett javítások
1. **Pulse_DF_Curve ATR-normalizálás**: (MACD - BB_Mavg) / ATR
2. **Ter_R/Ter_S újraszámolás 200-bar lookback-kel** (MQL5 90min helyett)
3. **Fordított pivot/EMA logika**: (R-Close)/ATR és (Close-S)/ATR
4. **Konzervatív pruning**: 10 duplikált feature eldobva (momentum + bar meta + EMA duplikátum)
5. **Pivot abszolút szintek megtartva** (Micro_R, Sec_R, Sec_S, Ter_S, Close_Xm)

## Megszüntetett hibák
- Close_1m/5m/15m/30m r≈1.0 → MQL5 MTF merge probléma (nem Python hiba)
- Sec_R=Ter_R → MQL5 CalcSR túl hasonló lookback (75 vs 90 min)
- Pulse_DF_Curve r=-0.999 → abszolút árszint volt, most ATR-normalizált

## Következő lépések
1. Labeling aszimmetria: Long PT=1.2$, Short PT=1.5$ ( könnyebb Long label)
2. Vagy max_bars=8 Long-nál, 5 Short-nál
3. Optuna 4D threshold calibration
4. MQL5 javítás: Ter lookback 3→10 (300 min)
