# Session: mukodo_modell_chart
*Időbélyeg: 2026-10-13T21:59:21.939568*

MŰKÖDŐ MODELL + CHART + PREDICTOR — 2026-10-13

MODELL EREDMÉNYEK:
- BTCUSD MTF model: AUC=0.515, Accuracy=55.6% (PT=2.0σ, SL=1.0σ)
- Side model: RSI momentum (crossover + extreme)
- 10,585 events, 33 features, trained on 110K M1 bars (2.5 hónap)
- Take rate: 38.15% (asymmetric barriers)
- Top features: rsi, atr_pct, rvol_20, sec_width, micro_width, dist_1m_close

PIPELINE CHAIN:
1. M1 OHLCV + MTF indikátorok (Scalper_EA → CSV)
2. Resample to 1min bars + MTF indicators
3. RSI momentum side model (RSI crossover + extreme)
4. Triple Barrier meta-labeling (PT=2.0σ, SL=1.0σ, max=30)
5. 33 MTF features (distances, S/R positions, ATR, RSI, returns, volatility)
6. Sample weights (uniqueness × return attribution)
7. LightGBM 5-fold CV → meta-model
8. Model save + chart generation

FÁJLOK:
- /data/LGBM_copilot/src/train_mtf_v3.py — teljes pipeline
- /data/LGBM_copilot/src/copilot_chart.py — ár + P(Take) chart
- /data/LGBM_copilot/src/copilot_predict.py — EA predictor
- /data/LGBM_copilot/models/BTCUSD_mtf_model_*.txt — LightGBM modell
- /data/LGBM_copilot/models/BTCUSD_mtf_meta_*.json — meta config
- /data/LGBM_copilot/models/BTCUSD_ea_config.json — EA integráció
- /data/LGBM_copilot/charts/BTCUSD_copilot_*.png — chart

OPTIMALIZÁLÁSOK:
- sample_weights: O(n+m) diff array + cumsum (0.19s vs 300s+)
- data_dollar_bars: numpy array access (vs iterrows)
- PurgedKFold: datetime support via searchsorted

KÖVETKEZŐ:
- EA Python fordítás (PyInstaller/Nuitka) — kezelőpanel később
- Több feature engineering (lagged returns, cross-timeframe signals)
- Hyperparameter tuning (Optuna)
- Walk-forward validation
- XAUUSD modell tanítás