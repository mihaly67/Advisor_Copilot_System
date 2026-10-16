# Session: v11_complete_short_diagnosis_next_steps
*Időbélyeg: 2026-09-24T00:20:31.510293*

## V11 COMPLETE STATE + SHORT DIAGNOSIS — 2026-09-24

### PIPELINE ARCHITECTURE (V11):
1. Dollar Bar aggregáció ($444k küszöb) — /data/dev/projects/z-ai-copilot/Master_csv/processed/labeled_dollar_bars_adaptive.csv
2. 31 feature (8 microstructure + 8 regime + 15 indicator)
3. Regime-conditional labeling: Short only when ADX<20 (dom_labeler_v5.py)
4. LightGBM GPU P4000 (OpenCL), class_weight={0:1.5, 1:0.5, 2:1.3}
5. Optuna 2-phase asymmetric threshold (200+200 trials, LW=2.0)
6. SHAP validated, Visualization with thresholds

### FINAL METRICS (OOS, 6228 bars):
- Accuracy: 46.8%, Win rate: 43.1%
- Opposite: 0.94% (13/1379 trades)
- Profit: +386.50$, Avg/trade: +0.280$
- Long: 1353 trades, 584 wins (43.2%), 3 opposite (0.2%) ← TÖKÉLETES
- Short: 26 trades, 11 wins (42.3%), 10 opposite (38.5%) ← KATASZTRÓFA

### THRESHOLDS (Optuna calibrated):
th_long=0.350, th_noise_long=0.202, th_short=0.564, th_noise_short=0.577

### SHAP TOP 5:
1. Regime_ADX (1.128) — Short-dominant (2.523)
2. Regime_Trending (0.356) — Short-dominant
3. ATR_Micro (0.075)
4. Regime_Slope (0.039)
5. Kyle_Lambda (0.028)

### FEATURE PRUNING (4 eldobandó, 27 megtartandó):
Amihud_Illiq (r=0.938 Kyle_Lambda), Bar_Duration_Sec (r=-0.945 Pulse_DF_Curve), RSI_Fast_5 (r=0.922 WPR_14), WPR_14 (r=0.912 Stoch_D)

### === SHORT DIAGNOSIS — GYÖKÉRPROBLÉMA ===

A P(Short) zuhan volatilis dropokon. A modell 70.8%-ban P(Long)>P(Short)-t mond TRUE Short barokon!

P(Short) eloszlás TRUE Short barokon (n=1061):
- mean=0.423, median=0.429
- P(Long) mean=0.500 — HOSSZABB mint P(Short)!
- P(Long)>P(Short): 751/1061 (70.8%) — A MODELL ELLENTÉTES IRÁNYBA HÚZ

Volatilitás vs P(Short) (TRUE Short barokon):
- Q1_low (n=264): P(S)=0.463, P(L)=0.488, >0.5: 28%
- Q5_high (n=138): P(S)=0.352, P(L)=0.486, >0.5: 3.6%  ← KATASZTRÓFA

Legrosszabb Short predikciók — MIND magas ATR:
- P(S)=0.17 P(L)=0.68 | ATR=3.03
- P(S)=0.11 P(L)=0.55 | ATR=4.40

Feature korreláció P(Short)-tal (true Short barokon):
- ATR_Micro: r=-0.412 ← NAGY ATR = ALACSONY P(SHORT)!!!
- Kyle_Lambda: r=-0.409
- Amihud_Illiq: r=-0.379

### A CIRKULÁRIS PROBLÉMA:
1. Regime-conditional labeling: Short only when ADX<20 → volatilis Short (ADX>20) = Noise
2. Modell tanul: nagy ATR = nem Short
3. De true Short barok (amik ADX<20-nál történtek de volatilisak) → modell nem tudja predikálni
4. A labeling logikusan kizárja a rossz Short-ot, de ezzel a modell Short-oldala agyon van verve

### MEGOLDÁSI IRÁNYOK (döntés nyitott):

1. **Labeling revízió**: volatilis Short maradjon Short függetlenül ADX-től, de ATR küszöbbel szűrjünk
   - Pro: egyszerű, címkék jobbak
   - Con: visszaesünk az eredeti túl sok opposite Short-hoz?

2. **Meta-labeling (López de Prado)**: 
   - Első modell: irány (Long/Short) — a jelenlegi
   - Második modell: szűrő (trade/no-trade) — size/meta-label
   - Pro: elegáns, a Short nem kell hogy jól működjön az első modellben
   - Con: komplexebb, két modell karbantartás

3. **Két modell (Low-Vol és High-Vol)**:
   - Külön LightGBM a volatilis és nem volatilis régióban
   - Pro: specialist modellek
   - Con: kevesebb adat, overfitting risk

4. **Feature engineering: ATR-adjusted Short indikátor**:
   - Új feature: Short jel erőssége normalizálva ATR-rel
   - Volatilitás-decoupled feature-ök
   - Pro: nem kell a labelinget változtatni
   - Con: nem biztos hogy elég

### GPU SETUP (P4000):
- nvidia-opencl-icd 580.178.04 telepítve
- LightGBM 4.7.0 device='gpu', gpu_platform_id=0, gpu_device_id=0
- n_jobs=1 (CPU nem 100%)
- OpenCL 3.0 CUDA 13.0.100 platform

### KEY FILES:
- Model: /data/dev/projects/z-ai-copilot/models/lgbm_model_v5_adaptive.pkl
- Thresholds: /data/dev/projects/z-ai-copilot/models/optuna_thresholds_asymmetric_v9.json
- Trainer: /data/dev/projects/z-ai-copilot/src/train_lgbm_fusion_v5.py (GPU, 31 features, class_weight {0:1.5,1:0.5,2:1.3})
- Optuna: /data/dev/projects/z-ai-copilot/src/optuna_asymmetric_v9.py (LW=2.0, 31 features)
- Labeler: /data/dev/projects/z-ai-copilot/src/dom_labeler_v5.py (regime-conditional Short)
- Feature eng: /data/dev/projects/z-ai-copilot/src/dom_feature_engineer_mtf.py (31 features)
- SHAP: /data/dev/projects/z-ai-copilot/src/shap_analyzer.py
- Viz: /data/dev/projects/z-ai-copilot/src/visualize_predictions.py (Optuna thresholds)
- Diagnosis: /data/mcp_server/state/short_diagnosis.py
- Confusion: /data/mcp_server/state/confusion_v10b.py

HTML outputs: /data/dev/projects/z-ai-copilot/docs/ (shap_heatmap, shap_long_vs_short, shap_dependence_long, shap_beeswarm, feature_correlation, predictions_visualization)

### NEXT TASK (új sessionnel kezdjük):
A fenti 4 megoldási irány valamelyikével folytatjuk. User kérdésként fel kell tenni új task elején.