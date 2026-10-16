# Session: shap_dual_model_kesz_20260925
*Időbélyeg: 2026-09-25T19:37:31.938746*

# SHAP Dual Model — 4. ik pont kész (2026.09.25.)

## SHAP TreeExplainer, 5000 sample a V8 CSV-n (31,139 bar)

## Jules V5 SHAP (10 feature):
| feature | mean_abs | long_abs | short_abs | noise_abs |
|---|---|---|---|---|
| Dist_Ter_R | 0.668 | 0.127 | 0.198 | **0.343** |
| Tick_Speed | 0.587 | 0.155 | 0.160 | **0.273** |
| Dist_Micro_R | 0.490 | 0.147 | 0.122 | **0.221** |
| Dist_Sec_R | 0.323 | 0.101 | 0.110 | 0.112 |
| Dist_Sec_S | 0.321 | 0.197 | 0.060 | 0.064 |

Long-Short SHAP korreláció: 0.107 (közel nulla → nem irány-tudatos)

## NavSystem v1.01 SHAP (11 feature):
| feature | mean_abs | long_abs | short_abs | noise_abs |
|---|---|---|---|---|
| Stoch_D | 3.926 | 1.878 | 1.997 | **0.050** |
| Flow_Delta_10 | 1.876 | 0.907 | 0.917 | **0.053** |
| Pulse_MACD_Hist | 1.071 | 0.470 | 0.551 | **0.051** |
| WPR_14 | 0.296 | 0.115 | 0.150 | 0.031 |

Long-Short SHAP korreláció: -0.077 (közel nulla)

## KULCS FELISMERÉS — noise_abs arány:
- **Jules V5:** noise_abs DOMINÁL (Dist_Ter_R: noise=0.343 vs long=0.127) → a modell elsődlegesen "noise vs signal" -t dönt (breakout detector!)
- **NavSystem v1.01:** noise_abs MINIMÁLIS (Stoch_D: noise=0.050 vs long=1.878) → a modell elsődlegesen "Long vs Short" -ot dönt (direction predictor!)

Ez a noise_abs / (long_abs + short_abs + noise_abs) arány a legjobb metrika:
- Jules: noise dominál → breakout (MIKOR mozgás lesz)
- NavSystem: long+short dominál → direction (MERRE)

## Feature típusok:
- Jules: S/R távolságok (Dist_*) + wick-ek → "milyen közel vagyunk S/R-hez" = mozgás valószínűsége
- NavSystem: Stoch_D, Flow_Delta, Pulse_MACD → momentum/flow → irány

## Fájlok:
- /data/dev/projects/z-ai-copilot/models/jules_v5_shap_importance.csv
- /data/dev/projects/z-ai-copilot/models/nav_3c_v1.01/shap_importance.csv
- /data/dev/projects/z-ai-copilot/docs/shap_dual_model.html