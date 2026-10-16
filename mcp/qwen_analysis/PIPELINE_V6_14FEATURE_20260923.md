# Pipeline V6 — 14 Feature Agresszív Pruning
*2026-09-23 18:25*

## ÁTTÖRÉS: Long recall 17% → 37% (+118%!)

| Verzió | Feature | Accuracy | Short R | Long R | Noise R | Macro F1 |
|---|---|---|---|---|---|---|
| V1 eredeti | 48 | 40.28% | 73% | **17%** | 19% | 0.33 |
| V3 javított | 48 | 40.73% | 68% | 25% | 15% | 0.34 |
| V5 konzervatív | 38 | 41.08% | 71% | 24% | 13% | 0.34 |
| **V6 agresszív** | **14** | 37.74% | **38%** | **37%** | **38%** | **0.37** |

## KIEGYENSÚLYOZOTT RECALL — minden osztály 37-38%!

A V1-ben a Short recall 73% volt, Long 17% → 4.3x aránytalanság.
V6-ban mindhárom osztály 37-38% → **tökéletesen kiegyensúlyozott**.

## SHAP Top 5 feature

| Feature | SHAP_Long | SHAP_Short | SHAP_Noise | Long−Short |
|---|---|---|---|---|
| ATR_Micro | **0.092** | 0.101 | 0.189 | -0.009 |
| Avg_Spread | 0.047 | 0.032 | 0.052 | **+0.015** ✅ |
| Bar_Duration_Sec | 0.042 | 0.031 | 0.039 | **+0.011** ✅ |
| Dist_Micro_R_ATR | 0.032 | 0.032 | 0.038 | +0.000 |
| Dist_Micro_S_ATR | 0.030 | 0.025 | 0.042 | **+0.006** ✅ |

## Pivot Long_minus_Short javulás (V1 → V6)

| Feature | V1 | V6 | Javulás |
|---|---|---|---|
| Dist_Micro_R_ATR | -0.011 | **+0.000** | ✅ semlegessé vált |
| Dist_Micro_S_ATR | -0.001 | **+0.006** | ✅ pozitív |
| Dist_Ter_R_ATR | +0.001 | **+0.002** | ✅ pozitív |
| Dist_Ter_S_ATR | -0.001 | **+0.000** | ✅ semlegessé vált |
| Dist_Sec_R_ATR | -0.021 | -0.024 | 🔴 még Short |
| Dist_Sec_S_ATR | -0.020 | -0.010 | 🟡 javuló |
| Trend_EMA_Super_Dist | +0.036 | -0.007 | 🔴 visszaesés |

## SHAP pruning javaslat (automatikus)
- Pulse_DF_Curve (r=-0.944 Bar_Duration_Sec) — DE MEGTARTJUK
- Trend_EMA_Super_Dist (r=0.853 Dist_Ter_R_ATR) — DE MEGTARTJUK

## Megszünt: Micro_R Noise dominancia!
V1: Micro_R SHAP_Noise=0.382 → V6: nincs Micro_R, ATR_Micro SHAP_Noise=0.189
Az abszolút szint eldobása megszüntette a Noise túlsúlyt.

## 14 feature végleges lista
1. Dist_Micro_R_ATR
2. Dist_Micro_S_ATR
3. Dist_Sec_R_ATR
4. Dist_Sec_S_ATR
5. Dist_Ter_R_ATR
6. Dist_Ter_S_ATR
7. Pulse_DF_Curve
8. Trend_EMA_Super_Dist
9. Avg_Spread
10. ATR_Micro
11. Stoch_D
12. Wick_Upper_ATR
13. Wick_Lower_ATR
14. Bar_Duration_Sec

## Következő lépések
1. Labeling aszimmetria (Long PT=1.2$, Short PT=1.5$)
2. Optuna 4D threshold calibration
3. MQL5 CalcSR javítás (Ter lookback 3→10)
