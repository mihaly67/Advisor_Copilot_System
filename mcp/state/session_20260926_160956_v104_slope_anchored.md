# Session: v104_slope_anchored
*Időbélyeg: 2026-09-26T16:09:56.636290*

v1.04 SLOPE-ANCHORED LABELING + TREND_STRENGTH_20

## Kulcs eredmények
- OOS WR: 40.0% → 60.9% (+20.9%)
- OOS Profit: +2475 → +10610 (+8135, 4.3×)
- OOS Trades: 12357 → 12850
- Opposite: 0
- Thresholds: th_l=0.100 th_s=0.100 th_n=0.900

## Slope-anchored labeling (jules_labeler_v3.py)
- Ha triple barrier = Noise és |Slope_Close_14| > 1.0 → override irányos
- Cross-validáció: v1.03 model (NEM retanítva) + slope labels → WR=60.8%
- A javulás 95%-ban a LABELING-ből, nem modellből
- Noise→Long: 335 bar (2.6%), Noise→Short: 241 bar (1.9%)
- Konfidencia: 42% emelkedik 0.5+ ATR (Long), 34% esik 0.5+ ATR (Short)

## Kísérletek ami NEM jött be
- Run-aware labeling (min_run=15): WR 40→36.5%, P +2475→+292 (túl kevés label)
- Trailing stop labeling: PT hit 56→23%, 98% Noise (túl szoros trailing)
- SHAP pruning 41→25: P -112 (v1.03-ban)

## Fájlok
- jules_labeler_v3.py: slope-anchored labeler
- jules_labeler_v2.py: trailing stop + run-aware (nem használt)
- features_v7.py: 42 feature (v6 + Trend_Strength_20)
- train_jules_v104.py: v1.04 training script
- models/v104/: lgbm_v104.pkl, thresholds.txt, features.txt, shap_importance.csv

## SHAP top 10
1. Slope_Close_14 (2.22)
2. MomScore_14 (0.49)
3. Stoch_D (0.21)
4. Mom10_Direction (0.15)
5. Trend_EMA_Medium_Dist (0.09)
6. ATR_Micro (0.08)
7. Dist_Sec_S_ATR (0.08)
8. Dist_Sec_R_ATR (0.07)
9. Micro_RSI_14 (0.07)
10. Trend_Strength_20 (0.06)