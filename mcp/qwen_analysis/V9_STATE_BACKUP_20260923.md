# V9 Pipeline Állapotmentés
*2026-09-23 21:40 — áramszünet védelem*

## Modell: V9 Microstructure (23 feature)
- Accuracy: 40.2%
- Long recall: 44%, precision: 51%
- Short recall: 34%, precision: 39%
- Opposite (Short↔Long): 30.7%
- Label: PT_Long=1.2$, PT_Short=1.8$, SL=1.0$, max_bars=8

## Feature lista (23)
MICROSTRUCTURE (8): Trade_Flow_Imb, VPIN, Run_Length, Micro_Price_Dist, Roll_Spread, Kyle_Lambda, Kyle_Vol_Sync, Amihud_Illiq
MOMENTUM (4): Price_Velocity, WPR_14, RSI_Fast_5, Pulse_MACD_Hist
PIVOT VEL (2): Micro_R_Vel, Micro_S_Vel
PIVOT DIST (2): Dist_Micro_R_ATR, Dist_Micro_S_ATR
NAVSYSTEM (3): Pulse_DF_Curve, Avg_Spread, ATR_Micro
GEOMETRY (3): Wick_Upper_ATR, Wick_Lower_ATR, Bar_Duration_Sec
OSCILLATOR (1): Stoch_D

## SHAP Top 5
1. ATR_Micro (0.133)
2. Kyle_Lambda (0.038)
3. Pulse_DF_Curve (0.034)
4. Avg_Spread (0.033)
5. Stoch_D (0.032)

## Fájlok
- src/dom_feature_engineer_mtf.py — microstructure+velocity+interaction flags
- src/dom_labeler_v5.py — asymmetric labeling
- src/train_lgbm_fusion_v5.py — 23 features
- src/shap_analyzer.py — SHAP analysis
- src/visualize_predictions.py — Plotly viz
- models/lgbm_model_v5_adaptive.pkl — trained model

## Ismert problémák
- Cohen d < 0.08 minden feature — strukturális
- Opposite 30.7% — alacsony zajküszöb mellett versenyző predikciók
- Breakout zajos (43-49% Long), S bounce jobb (56-62%)
