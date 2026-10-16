# Scalper Copilot Pipeline Terv — 3 Lépcsős Architektúra
*Időbélyeg: 2026-09-23*
*Státusz: TERV — user kiegészítést fog adni*

## Alapelv
1. **Tick gyűjtő** (MQ5) — összegyűjti a nyers adatot + MQ5-ben számolt makró feature-öket
2. **Dollar bar képző** (Python) — tick → dollar bar, forward-fill makró feature-ök
3. **Feature engineering** (Python) — dollar bar szintű feature-ök, labeling, betanítás

## A Scalper_Copilot_Miner_v1.mq5 CSV (811 MB, 18 oszlop)
- **Tick adat:** Timestamp, Bid, Ask, Bid_Volume, Ask_Volume, Spread
- **MTF Close:** 1m_Close, 5m_Close, 15m_Close, 30m_Close
- **MQ5 indikátorok:** ATR_M15, RSI_M15
- **ZigZag S/R:** Micro_R, Sec_R, Ter_R, Micro_S, Sec_S, Ter_S

## Miért jó a Scalper_Copilot CSV a pipeline-hoz?
- Egyetlen CSV-ben megvan minden, amit jelenleg 2 CSV-ből szed (Merkava_MTF + Master_ZigZag)
- Az MQ5-ben számolt makró indikátorok (RSI_M15, ATR_M15) PONTOSABBAK mint a Python resample approximáció
- A ZigZag S/R tick-időben frissül MQ5-ben — merge_asof nem kell
- A `fuse_macro_to_dollar_bars.py` lépés KIESIK — nincs szükség külön ZigZag CSV-re

## Feature felbontás: ki számolja?

| Feature | Ki számolja? | Miért? |
|---|---|---|
| OBI_Raw, OBI_ZScore | Python | Dollar bar Bid/Ask Volume-n |
| Bar_Time_Seconds, Price_Velocity, Tick_Speed | Python | Dollar bar OHLCV-n |
| Dist_5m/15m/30m | Python | Dollar bar Close vs MTF Close |
| ATR_Proxy | Python | Dollar bar OHLCV-n |
| Micro RSI/MACD/BB/ROC/MFI | Python | Dollar bar Close-n (Micro szintű) |
| M15/M30 RSI/MACD/BB/ROC/MFI | **MQ5-ből jön** | Valós M15/M30 gyertyákon pontosabb |
| ATR_M15, RSI_M15 | **MQ5-ből jön** | Valós MT5 gyertyán |
| ZigZag Dist_Micro/Sec/Ter_R/S | **MQ5-ből jön** | Tick-időben frissül |
| Stoch_State_M1 | Python vagy MQ5 | Attól függ |
| Wick_ATR | Python | Dollar bar OHLCV-n |

## Pipeline lépések

### LÉPÉS 1: TICK GYŰJTÉS (MQ5)
- Script: `Scalper_Copilot_Miner_v1.mq5`
- Kimenet: `Scalper_Copilot_MTF_Data.csv` (18 oszlop, 811 MB)
- Időszak: 2026.06.15 → 2026.09.01 (2.5 hónap XAUUSD)

### LÉPÉS 2: DOLLAR BAR KÉPZÉS (Python)
- Script: `prado_dollar_bars.py` (MÓDOSÍTANDÓ)
- Bemenet: Scalper_Copilot_MTF_Data.csv
- Akkumuláció: Σ(Mid_Price × Total_Vol) ≥ $444,000
- Forward-fill a dollár barra: MTF Close + ATR_M15 + RSI_M15 + ZigZag S/R
- Kimenet: `dollar_bars.csv` (~13+ oszlop)

### LÉPÉS 3: FEATURE ENGINEERING (Python)
- Script: `dom_feature_engineer_mtf.py` (MÓDOSÍTANDÓ)
- Bemenet: dollar_bars.csv
- Python számolja: OBI, Velocity, Tick_Speed, Micro RSI/MACD/BB/ROC/MFI
- Felhasználja: MQ5-ből jövő M15/M30, ZigZag (már ott van a dollar_bars-ban)
- Kimenet: `features_dollar_bars.csv` (30+ oszlop)
- → labeler → train → optuna → SHAP → heatmap → feature szelekcó

### KIESŐ LÉPÉS
- `fuse_macro_to_dollar_bars.py` — NEM KELL, mert a ZigZag S/R már benne van a tick CSV-ben

## Feature szelekcó (SHAP + Optuna)
- SHAP feature importance → heatmap → redundáns feature-ök azonosítása
- Ha MQ5 RSI_M15 és Python M15_RSI_14 korrelál → egyik kiesik
- Ha ZigZag Ter_R/S nem hasznos → kiesik
- Optuna 4D aszimmetrikus küszöb kalibráció

## Jules eredeti pipeline-ja (referencia)
- ① Merkava_Data_Miner_MTF_v1.06.mq5 → tick CSV (8 oszlop)
- ② Merkava_Master_Data_Miner_v5.mq5 → ZigZag CSV (13 oszlop)
- ③ prado_dollar_bars.py → dollar_bars.csv
- ④ dom_feature_engineer_mtf.py → features_dollar_bars.csv
- ⑤ dom_labeler_v5.py → labeled
- ⑥ fuse_macro_to_dollar_bars.py → fused (ZigZag merge_asof)
- ⑦ train_lgbm_fusion_v5.py → model

## Új pipeline (egyszerűsített)
- ① Scalper_Copilot_Miner_v1.mq5 → tick CSV (18 oszlop, minden benne)
- ② prado_dollar_bars.py (módosítva) → dollar_bars.csv
- ③ dom_feature_engineer_mtf.py (módosítva) → features_dollar_bars.csv
- ④ dom_labeler_v5.py → labeled
- ⑤ train_lgbm_fusion_v5.py → model
- ⑥ optuna_threshold_tuner_v5.py → 4D küszöb
- ⑦ SHAP → feature szelekcó → heatmap

## Dollár Bar elmélet (López de Prado)
- Defin=ció: Σ(tick_i.price × tick_i.volume) ≥ θ → Dollár Bar lezárul
- θ = $444,000 (kb. 1/50 átlagos napi XAUUSD forgalom)
- Időfüggetlen: 2 mp alatt is felépülhet, vagy 10 percig is tarthat
- Bemenet: Timestamp, Bid, Ask, Bid_Volume, Ask_Volume — EZZENYI
- OHLCV: Open=első tick Mid, High(=max Mid), Low(=min Mid), Close=utolsó tick Mid

## CSV gyűjtő scriptek (teljes feltérképezés)

### Ténylegesen használt (Jules pipeline):
| Script | CSV | Oszlopok | Típus |
|---|---|---|---|
| Merkava_Data_Miner_MTF_v1.06.mq5 | Merkava_MTF_GCE_0527_0717_Data.csv (174 MB) | 8: Timestamp, Bid, Ask, Bid_Vol, Ask_Vol, 5m/15m/30m_Close | Tick |
| Merkava_Master_Data_Miner_v5.mq5 | Master_ZigZag_GCEQ26_M1.csv (7.4 MB) | 13: Time, OHLCV, Micro/Sec/Ter R/S | M1+ZigZag |
| Scalper_Copilot_Miner_v1.mq5 (én) | raw/Scalper_Copilot_MTF_Data.csv (811 MB) | 18: Tick+Spread+MTF+ATR+RSI+ZigZag | Tick |

### NEM használt scriptek a pipeline-ban:
- Merkava_Data_Miner_MTF_v1.05 (régi, azonos v1.06)
- Merkava_Data_Miner_Script_v1_04 (komplex NavSystem)
- Merkava_Macro_Miner_v2 (ATR/EMA/ADX)
- Merkava_Macro_Miner_v3_AMA (AMA)
- Merkava_DOM_Miner_v1.1 / DOM_Miner (order book depth)
- DataMiner_TickExporter_v1_00 (pure tick)
- Tick_Exporter_Script_v3, Data_Exporter_Script_v1.0, Feature_Exporter_Script, Feature_Exporter_Script_BATCHED, AI_Labeled_Data_Exporter_v8.1, PointValue_Analyzer (Gemini&User, UNICODE)

### NEM használt CSV-k:
- Merkava_MTF_MGCQ26_0720_23_vizsga_Data.csv (22 MB) — tesztfuttatás

### Python scriptek (pipeline):
- prado_dollar_bars.py — tick→dollar bar ($444k)
- dom_feature_engineer_mtf.py — dollar bar feature engineering (37 oszlop)
- dom_labeler_v5.py — triple barrier labeling (PT=1.5$, SL=1.0$)
- fuse_macro_to_dollar_bars.py — ZigZag+Stoch+Wick fúzió (KIESŐ új pipeline-ban)
- train_lgbm_fusion_v5.py — LightGBM betanítás
- optuna_threshold_tuner_v5.py — 4D küszöb
- mt5_live_copilot_v2.00.py — élő ZMQ copilot

## VÁRAKOZÓ: User kiegészítés a tervhez