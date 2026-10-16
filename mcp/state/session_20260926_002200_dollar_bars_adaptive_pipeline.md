# Session: dollar_bars_adaptive_pipeline
*Időbélyeg: 2026-09-26T00:22:00.283527*

## dollar_bars_adaptive.csv Pipeline (Helyes)

### 1. MQL5: Scalper_Copilot_Miner_v1.mq5
- Hely: MQL5/Scripts/Scalper_Copilot_Miner_v1.mq5
- Bemenet: MT5 broker tick adat (CopyTicksRange) + M1/M5/M15/M30 rates
- Másodpercenkénti bucket aggregáció
- MQL5 indikátorok: iATR(PERIOD_M15,14), iRSI(PERIOD_M15,14), CalcSR() rolling High/Low
- Kimenet: Scalper_Copilot_MTF_Data.csv — 18 oszlop:
  Timestamp, Bid, Ask, Bid_Volume, Ask_Volume, Spread,
  1m_Close, 5m_Close, 15m_Close, 30m_Close,
  ATR_M15, RSI_M15, Micro_R, Sec_R, Ter_R, Micro_S, Sec_S, Ter_S

### 2. Python: prado_dollar_bars.py (z-ai-copilot)
- Hely: /data/dev/projects/z-ai-copilot/src/prado_dollar_bars.py
- Bemenet: Scalper_Copilot_MTF_Data.csv (18 oszlop)
- Adaptív küszöb: weight_i = Mid_Price_i × ATR_i / (444000 × ATR_median)
- groupby aggregáció: OHLCV + MTF/indikátor forward-fill (last)
- Kimenet: dollar_bars_adaptive.csv — 22 oszlop

### Utána: dom_labeler → labeled, fuse_macro, train_lgbm

### FONTOS: raw mappában lévő Merkava_MTF_GCE_*.csv (8 oszlop) RÉGI pipeline, NEM az aktuális!
### A Scalper_Copilot_Miner az EGYETLEN script ami a teljes 18 oszlopos bemenetet generálja.