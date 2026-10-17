# Session: predict_logger_v1_diagnosis
*Időbélyeg: 2026-10-11T17:24:28.935591*

# Predict Logger V1 — BTCUSD Élő Diagnózis

## Fájl: /data/dev/projects/z-ai-copilot/src/predict_logger.py (323 sor)
## Indítás: python3 predict_logger.py BTCUSD
## Log: /tmp/btcusd_predict_log.csv + /tmp/btcusd_feature_log.csv

## Élő eredmények (8 bar, 18:15-18:22 UTC):
- MLP: [0.126 - 0.406] μ≈0.22 — SOHA > 0.5
- LGBM: [0.077 - 0.296] μ≈0.15 — SOHA > 0.3 (!)
- ENS: [0.118 - 0.336] — MINDIG SHORT
- Signal: -1 minden bar-ban

## Backtest AUC: MLP=0.874, LGBM=0.877, ENS=0.882
## Élő AUC: ≈ 0.5 (gyanús, modell használhatatlan)

## Feature Drill — FŐ OK:
1. vol_ratio_f = 50.8 (élő) vs ~[0,5] (tanítási) → 10x drift!
2. Slope_3_atr_f = 5.0 (clip határ) → tanítási [-2,2]?
3. body_atr_f = 5.0 (clip határ) → mindig maximalizálva
4. velocity_atr_f = -5.0 (clip határ) → mindig minimalizálva
5. feat_max = 1164.7 (!) → RankGauss rosszul skáláz

## EA hiba: TICK formátum problémák
- `could not convert string to float: '83054.78,83062.38,83061.84,83056.46'`
- Az EA OHLC stringet küld bid helyett (Macro EA port 5555)
- Tick EA (5556) jól működik

## Következő lépések:
1. Feature clip lazítása (±5 → ±10) vagy ATR normalizáció javítás
2. vol_ratio_f újra normalizálás (log transzform?)
3. Scaler újra tanítás élő adaton
4. Platt scaling / isotonic regression kalibráció
5. LGBM-only mód (w_lgbm=1.0) tesztelése
