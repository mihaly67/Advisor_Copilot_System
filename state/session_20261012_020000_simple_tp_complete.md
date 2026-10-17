# Session: simple_tp_complete
*Időbélyeg: 2026-10-12T02:00:00.802885*

SIMPLE TP CÍMKÉZÉS KÉSZ — Jó + Rossz label mindkét irányba.

Label variációk a labeled_BTCUSD.csv-ben:
1. label_long: 1=jó (TP hit $30 5p), 0=rossz (miss) → Long WR=58.9%, Rossz=41.1%
2. label_short: 1=jó (TP hit $30 5p), 0=rossz (miss) → Short WR=59.4%, Rossz=40.6%
3. label_combo: 2=jó_long, 1=jó_short, 0=rossz (45.7% / 45.5% / 8.8%)
4. label_ema: EMA-filtered jó/rossz → WR=64.1%, Info=+14.1% vs 50%
5. ema_side: +1=bull, -1=bear (5m EMA20 slope)
6. side + label + bars_held: kompatibilis a régi pipeline-nel

Script: /data/dev/LGB_copilot_system/src/02_label_simple_tp.py
Output: /data/dev/LGB_copilot_system/output/labeled_BTCUSD.csv
Config: SIMPLE_TP_DIST=30, SIMPLE_TP_MAX_BARS=18, SIMPLE_TP_EMA_PERIOD=20, SIMPLE_TP_EMA_RS_SEC=300

Következő: feature generálás + LightGBM tréning (Long modell, Short modell, combo modell)