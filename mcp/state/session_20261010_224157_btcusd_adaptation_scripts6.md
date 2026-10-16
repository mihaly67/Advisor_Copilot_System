# Session: btcusd_adaptation_scripts6
*Időbélyeg: 2026-10-10T22:41:57.327150*

BTCUSD CFD ADAPTÁCIÓ KÉSZ (scriptek)

MQ5 SCRIPTEK (instrument-független):
1. Collect_M1_History.mq5 v4.0 → _Symbol auto, filename auto, digits auto
2. Scalper_Copilot_Miner_v2.mq5 v2.1 → auto filename, digits auto, %.*f format

PYTHON SCRIPT:
3. gen_dollar_bars_instrument.py → python3 gen_dollar_bars_instrument.py BTCUSD
   - Auto threshold: median_price * 2.5 → ugyanaz bar density mint XAUUSD
   - BTCUSD: ~$80,000 * 2.5 = $200,000/bar → ~400 bar/nap

PIPELINE:
4. pipeline_v14.py → python3 pipeline_v14.py BTCUSD
   - DOLLAR_BARS: dollar_bars_full_{INSTRUMENT}.csv
   - MODEL_DIR: models/v14_{INSTRUMENT}/

KÖNYVTÁRAK:
- Master_csv/raw/CFD_BTCUSD/ — BTCUSD raw CSV-k ide kerülnek
- Master_csv/processed/dollar_bars_full_BTCUSD.csv — dollár bar
- models/v14_BTCUSD/ — MLP + LGBM ensemble modell

FÁJLNÉV KONVENCIÓ:
- M1_History_{INSTRUMENT}.csv
- ScalperD_Copilot_MTF_Data_v2_{INSTRUMENT}.csv
- dollar_bars_full_{INSTRUMENT}.csv
- models/v14#_BTCUSD/mlp_meta_v12.pt, lgbm_v14.pkl, features.txt, ensemble_config.json

KÖVETKEZŐ LÉPÉS (kézi):
1. MT5-ben BTCUSD CFD chart megnyitása
2. Collect_M1_History.mq5 ráhúzása → M1_History_BTCUSD.csv
3. Scalper_Copilot_Miner_v2.mq5 ráhúzása → Scalper_Copilot_MTF_Data_v2_BTCUSD.csv
4. Raw CSV áthelyezése Master_csv/raw/CFD_BTCUSD/-ba
5. python3 gen_dollar_bars_instrument.py BTCUSD
6. python3 pipeline_v14.py BTCUSD