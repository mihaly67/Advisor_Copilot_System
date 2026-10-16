# Session: advisors_knowledge_build
*Időbélyeg: 2026-10-14T02:02:58.183652*

ADVISORS TUDÁSBŐVÍTÉS BEFEJEZVE (2026-10-13)

## Amit csináltunk
1. Létrehoztuk /data/Brain/advisors/ mappát 3 alkategóriával: mt5_mql5, traderview_pine, python_bots, docs
2. Klónoztunk 11 GitHub repót (~16MB összesen):
   - MT5/MQL5: BAKOMEGoldScalper (ICT+FVG+OB), EURUSD_Scalping_Robot (7-ind scoring), EA31337 (multi-strategy), mql-zmq (Python bridge)
   - TradingView/Pine: nq1_Scalping_Strategy (Vol Profile POC), CSA-15 (8-point scoring), super-scalping-analysis (Ichimoku pivots), tradingview-strategy-collection, TradingView-5M-Scalping-Indicator
   - Python: MlFinLab (AFML labeling), qstrader (event-driven)
3. Kinyertük címkézési/signal logikát minden repóból → ADVISORS_KNOWLEDGE_BASE.md
4. Repository memory indexer: 826 fájl, 8.64 MB indexelve
5. Qwen analysis log elmentve

## Kulcs felfedezések
- FVG (Fair Value Gap): low[i] > high[i-1] = bullish gap, ATR-szűrve — MI NINCS még
- Order Blocks: bearish candle + nagy bullish follow-through — MI NINCS még
- Volume Profile POC: legerősebb S/R szint, mágneses árak — MI NINCS még
- Kill Zone / Session filter: idő-alapú szűrés — MI NINCS még
- Meta-labeling: elsődleges modell = irány, másodlagos = méret — JAVÍTANÁ a modellünkön
- CSA-15 squeeze = mi már van (micro_sqz), validáció
- Fresh Trigger: csak első bar-on szignál — JAVÍTANÁ a signal minőségen

## Prioritás: POC > FVG > OrderBlock > Session > MetaLabeling > TrendScanning

## Fájlok
- /data/Brain/advisors/docs/ADVISORS_KNOWLEDGE_BASE.md (teljes tudásbázis)
- /data/Brain/_qwen_analysis/advisors_signal_logic_summary.md (Qwen log)
