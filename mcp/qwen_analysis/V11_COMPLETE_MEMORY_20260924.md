# V11 COMPLETE — SHORT DIAGNOSIS + NEXT STEPS
*2026-09-24 00:20 — SESSION ZÁRÓ MEMÓRIA*

## HOVA JUTOTTUNK

### Pipeline (V11):
Dollar Bar → 31 feature → Regime-conditional labeling (Short only ADX<20) → LightGBM GPU P4000 → Optuna thresholds → SHAP → Viz

### OOS Metrikák:
- **+386.5$ profit**, 43.1% win rate, 0.94% opposite
- **Long: tökéletes** — 1353 trades, 0.2% opposite
- **Short: katasztrófa** — 26 trades, 38.5% opposite

### SHORT GYÖKÉRPROBLÉMA:
**P(Long) > P(Short) a TRUE Short barok 70.8%-án!**

A modell megtanulta: nagy volatilitás = nem Short, mert:
- Regime-conditional labeling → volatilis Short (ADX>20) = Noise
- LightGBM: ATR_Micro r=-0.412 P(Short)-tal
- Cirkuláris: labeling kizárja volatilis Short → modell nem tanulja → true volatilis Short amik átesznek → rossz predikció

Volatilitás hatás (true Short barokon):
- Low vol (Q1): P(S)=0.463, >0.5: 28%
- High vol (Q5): P(S)=0.352, >0.5: 3.6% ← megsemmisül

Legrosszabb Short predikciók: P(S)=0.11-0.17, P(L)=0.55-0.68, ATR=3.0-4.8

## MEGOLDÁSI IRÁNYOK (döntés nyitott):

1. **Labeling revízió**: volatilis Short maradjon Short függetlenül ADX-től (ATR küszöb)
2. **Meta-labeling (López de Prado)**: 1. modell irány, 2. modell szűrő
3. **Két modell (Low-Vol / High-Vol)**: specialist modellek
4. **Feature engineering**: ATR-adjusted Short indikátor, volatilitás-decoupled

## GPU SETUP:
nvidia-opencl-icd 580.178.04, LightGBM device='gpu', n_jobs=1

## KEY FILES:
- Model: models/lgbm_model_v5_adaptive.pkl
- Thresholds: models/optuna_thresholds_asymmetric_v9.json
- Trainer: src/train_lgbm_fusion_v5.py (GPU, 31 feat, cw {1.5/0.5/1.3})
- Optuna: src/optuna_asymmetric_v9.py (LW=2.0, 31 feat)
- Labeler: src/dom_labeler_v5.py (regime-conditional)
- Feature eng: src/dom_feature_engineer_mtf.py
- SHAP: src/shap_analyzer.py
- Viz: src/visualize_predictions.py (Optuna thresholds)
- Diagnosis: /data/mcp_server/state/short_diagnosis.py
- Session: /data/mcp_server/state/session_20260924_002031_v11_complete_short_diagnosis_next_steps.md

## ÚJ TASK KEZDETHEZ:
1. Olvasd el a session-t: read_session stage="v11_complete_short_diagnosis_next_steps"
2. Tedd fel a 4 megoldási irány kérdést
3. Folytasd a választott irányban
