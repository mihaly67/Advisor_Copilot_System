# Session: jules_v102_reconstruction
*Időbélyeg: 2026-09-26T02:41:03.961740*

JULES v1.02 PIPELINE REKONSTRUKCIÓ SZIKRÁZVA (2026.09.26.)

## Eredmények
- Test Accuracy: 51.7%
- OOS Accuracy: 52.1% (>50% cél elérve!)
- Predikció eloszlás OOS: Short 21.5% / Noise 61.1% / Long 17.4%
- Threshold WR: 39.7% (test), 39.4% (OOS)
- Profit: +548 (test), +1310 (OOS) — szimmetrikus 2:1 RR

## Rekonstrukció kulcsai
1. **Labeler** (`jules_labeler.py`): Side=Slope_Close_14>0 + Target_Meta szimmetrikus triple barrier
   - PT=1.5×ATR_Micro (nem 2.0!)
   - SL=1.0×ATR_Micro
   - max_bars=15 (nem 5!)
   - Forrás: AI_Labeled_Data_Exporter_v8.1.mq5 input params
2. **class_weight**: {0:1.0, 1:0.7, 2:1.0} — Noise=0.7 a sweet spot (>50% accuracy)
3. **LGBM params**: n_est=500, lr=0.05, num_leaves=31, max_depth=5, min_child=50
4. **Threshold profit**: LW=+2.0, LL=-1.0, SW=+2.0, SL=-1.0 (szimmetrikus)

## Fájlok
- `src/jules_labeler.py` — Side + Target_Meta generáló
- `src/train_jules_v102.py` — training + OOS eval
- `Master_csv/processed/labeled_train.csv` — Jules label-elt adat
- `Master_csv/processed/labeled_oos.csv` — OOS label-elt adat

## Következő lépések
1. Optuna hyperparameter tuning (user külön kérte)
2. Scalper_Copilot_MTF_Data_külön_vizsga.csv futtatása a pipeline-on (feature extraction kell)
3. SHAP elemzés az új modellre