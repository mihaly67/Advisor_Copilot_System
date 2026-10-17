# Session: btcusd_indicator_rich_pipeline_final
*Időbélyeg: 2026-10-10T23:45:20.121629*

BTCUSD INDICATOR-GAZDAG PIPELINE V14 — VÉGLEGES EREDMÉNY

BTCUSD (indicator-gazdag dollár bar, 32 oszlop):
  MLP:  valAUC=0.868  params=14,849  d/p=13.9  perm_z=30.0
  LGBM: valAUC=0.877  best_iter=498
  ENS:  valAUC=0.880  w_mlp=0.60  w_lgbm=0.40
  OOS:  valAUC=0.857 ± 0.010 (purged CV)

XAUUSD (referencia):
  MLP:  valAUC=0.821
  LGBM: valAUC=0.833
  ENS:  valAUC=0.839  w_mlp=0.65
  OOS:  valAUC=0.810 ± 0.009

BTCUSD > XAUUSD! Az indicator-gazdag dollár bar +9% AUC javulást hozott.

Feature importance BTCUSD (MLP):
  1. consecutive_f +0.153
  2. body_sign_f +0.063
  3. delta_pivot_dist +0.057  ← S/R feature most aktív!
  4. PastRet_2_f +0.049
  5. PastRet_1_f +0.047
  6. delta_sr_zone_sec +0.042 ← S/R feature most aktív!

FÁJLOK:
  /data/dev/projects/z-ai-copilot/src/enrich_dollar_bars.py (új)
  /data/dev/projects/z-ai-copilot/src/gen_dollar_bars_instrument.py (visszaállítva)
  /data/dev/projects/z-ai-copilot/Master_csv/processed/dollar_bars_full_BTCUSD.csv (32 oszlop)
  /data/dev/projects/z-ai-copilot/models/v14_BTCUSD/ (mlp+lgbm+ensemble)

KÖVETKEZŐ: enrich_dollar_bars.py integrálása a pipeline-be (automatikus futtatás)