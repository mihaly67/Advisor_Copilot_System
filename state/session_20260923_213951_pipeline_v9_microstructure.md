# Session: pipeline_v9_microstructure
*Időbélyeg: 2026-09-23T21:39:51.489785*

V9 Pipeline Status: 23 feature, 40.2% accuracy, Long recall=44%, Long precision=51%, Opposite=30.7%
Microstructure features (DOM nélkül, AFML Ch.19): Trade_Flow_Imb, VPIN, Run_Length, Micro_Price_Dist, Roll_Spread, Kyle_Lambda, Kyle_Vol_Sync, Amihud_Illiq
Run_Length legjobb diszkriminátor (d=+0.058), VPIN #2 feature (SHAP)
Labeling: PT_Long=1.2$, PT_Short=1.8$, SL=1.0$, max_bars=8, Long=46.3%, Short=37.1%, Noise=16.6%
Pivot distance nem diszkriminál (Cohen d<0.04), pivot velocity segít (d=-0.045)
Minden feature Cohen d<0.08 — strukturális probléma scalping horizonon
Files: src/dom_feature_engineer_mtf.py (microstructure+velocity+interaction flags), src/dom_labeler_v5.py (asymmetric), src/train_lgbm_fusion_v5.py (23 features), src/shap_analyzer.py, src/visualize_predictions.py
Key diagnosis: breakout near R only 43-49% Long, S wick bounce 56-62% Long, pivot velocity better than distance
Next: Optuna 4D threshold calibration, VPIN>0.5 filter, Run_Length>2 filter