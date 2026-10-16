# Session: scalper_continuous_kesz
*Időbélyeg: 2026-10-13T22:36:11.330564*

SCALPER CONTINUOUS PIPELINE — KÉSZ 2026-10-13

MODELL EREDMÉNYEK:
- Long model:  AUC=0.608, threshold=0.32 ✅
- Short model: AUC=0.586, threshold=0.32 ✅
- 12 predikció/perc (56 tick/min / 5 subsample)
- 37 feature, 64K sample
- Tick-level labeling: horizon=20, TP=5bps, SL=5bps
- Long: 26.6%, Short: 28.2%, Skip: 45.2%
- Top features: tv_60 (volatility), micro_sqz, ter_sqz (S/R squeeze), tv_20, d_ter_r

PIPELINE CHAIN:
1. Scalper EA tick data (Bid/Ask + MTF indikátorok)
2. Subsample every 5th tick (~12 pred/min)
3. Forward-looking tick labeling (did price go up/down by 5bps in 20 ticks?)
4. 37 MTF features (S/R, RSI, ATR, volume, returns, volatility, skew)
5. TWO LightGBM models: P(Long) + P(Short)
6. Optimal threshold via F1 score

FÁJLOK:
- /data/LGBM_copilot/src/scalper_continuous.py — pipeline
- /data/LGBM_copilot/src/scalper_chart.py — P(Long)/P(Short) chart
- /data/LGBM_copilot/src/scalper_predict.py — EA predictor
- /data/LGBM_copilot/models/scalper/ — Long + Short models + meta

ELTÉRÉS A RÉGI MODELLTŐL:
- Régi: event-alapú (RSI crossover) → ~1 pred/perc, AUC=0.51
- Új: tick-alapú (continuous) → ~12 pred/perc, Long AUC=0.61, Short AUC=0.59
- 4x jobb AUC, 12x több predikció!