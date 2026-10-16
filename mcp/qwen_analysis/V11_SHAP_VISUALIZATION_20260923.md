# V11 SHAP + Visualization — Final Summary
*2026-09-23 23:46*

## SHAP Feature Importance (Top 10)

| Rank | Feature | SHAP_Total | SHAP_Short | SHAP_Long | Domináns |
|---|---|---|---|---|---|
| 1 | **Regime_ADX** | **1.128** | **2.523** | 0.173 | Short 🔴 |
| 2 | **Regime_Trending** | **0.356** | 0.915 | 0.035 | Short 🔴 |
| 3 | ATR_Micro | 0.075 | 0.025 | 0.061 | Noise |
| 4 | Regime_Slope | 0.039 | 0.059 | 0.017 | Short |
| 5 | Kyle_Lambda | 0.028 | 0.026 | 0.022 | Balanced |
| 6 | Avg_Spread | 0.026 | 0.016 | 0.026 | Balanced |
| 7 | Regime_Mom_10 | 0.026 | 0.044 | 0.018 | Short |
| 8 | Price_Velocity | 0.023 | 0.020 | 0.026 | Balanced |
| 9 | Pulse_DF_Curve | 0.023 | 0.010 | 0.027 | Long |
| 10 | Pulse_MACD_Hist | 0.022 | 0.026 | 0.011 | Short |

## Key SHAP Insights:
- **Regime_ADX dominál** (SHAP=1.128) — Short oldalon 2.523, ez a legfontosabb feature
- **Regime_Trending #2** (0.356) — szintén Short-domináns
- **3 regime feature a top 4-ben** — a regime-conditional labeling valóban működik
- Long oldalon nincs egyetlen domináns feature — kollektív döntés

## Feature Pruning (4 eldobandó, 27 megtartandó):
| Drop | Redundáns | Corr |
|---|---|---|
| Amihud_Illiq | Kyle_Lambda | r=0.938 |
| Bar_Duration_Sec | Pulse_DF_Curve | r=-0.945 |
| RSI_Fast_5 | WPR_14/Stoch_D | r=0.922 |
| WPR_14 | Stoch_D/Regime_ZScore | r=0.912 |

## Visualization Results:
- 2000 bar a TEST setből (utolsó 20%)
- **543 Long signals** (Optuna threshold th_L=0.350)
- **38 Short signals** (Optuna threshold th_S=0.564)
- **1419 Noise** (szűrt ki)
- Threshold vonalak megjelenítve a valószínűség panelen

## HTML Files Generated:
- shap_heatmap.html (4.7M) — Feature × Osztály heatmap
- shap_long_vs_short.html (4.7M) — Long vs Short SHAP
- shap_dependence_long.html (5.4M) — Dependence plotok
- shap_beeswarm.html (29M) — Beeswarm feature hatás
- feature_correlation.html (4.7M) — Korrelációs mátrix
- predictions_visualization.html (5.6M) — Ár + szignálok + prob + label

## Architecture Summary (V11 Final):
1. Dollar Bar ($444k küszöb)
2. 31 feature → 27 pruning után (4 redundáns eldobható)
3. Regime-conditional labeling (Short only when ADX<20)
4. LightGBM GPU (P4000 OpenCL), class_weight={0:1.5, 1:0.5, 2:1.3}
5. Optuna 2-phase asymmetric threshold (200+200 trials)
6. LW=2.0 reward structure (break-even 33.3%)
7. OOS: 43.1% win rate, 0.94% opposite, +386.5$ profit
