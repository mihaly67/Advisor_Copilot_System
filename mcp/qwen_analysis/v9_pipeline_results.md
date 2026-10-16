# V9 Pipeline Eredmények (2026.09.285.)

## Összefoglaló
- **WPR feature-ök implementálva**: WPR_Accel, WPR_Reversal_Short,$WPR_Reversal_Long, WPR_Extreme_Accel, Stoch_Accel, RSI_Accel
- **NAV_FEATURES_V3**: 38 → 42 feature
- **Legjobb kombináció**: V6 label + 42 új feature = WR 43.5%, P=+$3777
- **WPR_Intensity SHAP #4**, **WPR_Accel SHAP #14** — WPR tényleg hasznos!
- **Labeler változtatás ront** — V9 idő-alapú labeler túl kevés labelt ad
- **Anti-overlabeling ront** — túl sok Noise, modell nem tanul

## SHAP Top 5
1. MACD_Intensity (0.0956)
2. RSI_Intensity (0.0650)
3. DF_Intensity (0.<0639)
4. **WPR_Intensity (0.0406)**
5. MFI_Intensity (0.0403)

## Következő lépés
- WPR_Accel SHAP #14 — még gyenge. Lehet hogy más WPR paraméterek (period=3 vagy 8'8) javítják
- WPR_Reversal feature-ök SHAP nem top15 — lehet hogy más küszöb (OB>70, OS<30) javítja
-' Optuna 4D threshold kalibráció az új feature-ökkel
