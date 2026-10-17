# Session: btcusd_v14_pipeline_complete
*Időbélyeg: 2026-10-10T23:24:10.679612*

BTCUSD CFD V14 PIPELINE KÉSZ

BTCUSD EREDMÉNYEK:
- MLP:  valAUC=0.794  params=14,849  d/p=13.9  perm_z=16.6
- LGBM: valAUC=0.794  best_iter=350
- ENS:  valAUC=0.801  w_mlp=0.75  w_lgbm=0.25
- OOS:  valAUC=0.776 ± 0.013 (purged CV)

XAUUSD vs BTCUSD ÖSSZEHASONLÍTÁS:
- XAUUSD MLP AUC: 0.821  |  BTCUSD MLP AUC: 0.794  (diff: -0.027)
- XAUUSD ENS AUC: 0.839  |  BTCUSD ENS AUC: 0.801  (diff: -0.038)
- XAUUSD OOS AUC: 0.810  |  BTCUSD OOS AUC: 0.776  (diff: -0.034)
- XAUUSD perm_z:  44.5   |  BTCUSD perm_z:  16.6   (gyengébb signal)

BTCUSD DOLLÁR BAR:
- Threshold: $165,789 (XAUUSD tempo match)
- Bar/nap: 695 (XAUUSD: 701, diff=6) ✅
- Median dur: 60s (XAUUSD: 60s) ✅

BTCUSD FEATURE IMPORTANCE (MLP):
1. consecutive_f +0.289 (XAUUSD: +0.225) — erősebb!
2. trend_micro +00.190 (XAUUSD: +0.172)
3. body_sign_f +0.120 (XAUUSD: +0.103)
4. PastRet_2_f +0.109 (XAUUSD: +0.125)
5. RSI_3_f +0.050 (XAUUSD: +0.032)

MEGJEGYZÉS:
- BTCUSD S/R feature-ök (pivot, sr_zone) 0 importance → nincs S/R adat
  (a dollár bar nem tartalmazza az S/R oszlopokat, mert a gen_dollar_bars
   csak OHLC+ticks+dollar+duration-t generál)
- XAUUSD-nál a dollár bar tartalmazza az indicatorokat (ATR, RSI, EMA, S/R)
  mert a Scalper_Copilot_MTF_Data_v2.csv-ből lett generálva
- BTCUSD-nál hiányzik az indicator-gazdag dollár bar

KÖVETKEZŐ LÉPÉS:
- Indicator-gazdag dollár bar generálás BTCUSD-hez
  (ATR, RSI, EMA, S/R kalkuláció a dollár bar adatokból)
- Vagy: Scalper_Copilot_MTF_Data_v2_BTCUSD.csv → dollár bar (tick-alapú)