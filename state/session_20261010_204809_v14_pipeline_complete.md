# Session: v14_pipeline_complete
*Időbélyeg: 2026-10-10T20:48:09.852729*

V14 pipeline kész: ATR-normalizált feature-ök (Slope_3_atr, body_atr, velocity_atr), rolling retrain (12 hónap), ensemble próbált (0 közös feature LGBM-mel). Eredmény: valAUC=0.823, gap=0.0008 (3.4x jobb mint V12), OOS AUC=0.807±0.009, nincs overfitting. Modell: h=64,l=4,dp=0.1, 27 feature. Fájl: src/pipeline_v14.py. Ensemble megoldás: MLP signal → ZMQ → EA.