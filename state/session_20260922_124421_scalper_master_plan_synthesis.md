# Session: scalper_master_plan_synthesis
*Időbélyeg: 2026-09-22T12:44:21.140192*

SCALPER MASTER PLAN - RAG synthesis in progress.

Key components mined from RAG and existing codebase:
1. LGBM copilot: mt5_live_copilot_v2.00.py, train_lgbm_fusion_v5.py, dom_feature_engineer_mtf.py, dom_labeler_v5.py
2. HUD: hud_v1.16.py (lightweight_charts.QtChart + ZMQ SUB 5557 + PyQt5)
3. ZMQ bridge: ZMQReceiverThread (port 5557), MQL5 EA streams ticks
4. Dollar Bar engine: $444k threshold, FIFO deque(maxlen=200)
5. 3MTF architecture: M15+M30 macro + Dollar Bar micro features
6. Feature Fusion: ZigZag pivot distances + M1 Stochastic + Dollar Bars
7. 4D Asymmetric Threshold: Long P>0.55 Noise<0.35, Short P>0.45 Noise<0.30
8. Anti-overlabeling: ATR-distance redundancy filter
9. RAG repos: lightweight-charts, tradingview-mcp (CDP 9222), metatrader-mcp-server, PineTS, pinescriptv6, OctoBot, mt5-quant (89 tools), freqtrade, GAF-CNN pipeline
10. Air-gap concept: Clone desktop + hidden Python EA + IPC bridge to live MT5
11. IPC bridges: ZMQ PUB/SUB, mql-zmq binding, mt5-apibridge concept
12. OctoBot: TradingView webhook → bot execution
13. tradingview-interactive-brokers: TV signals → IBKR/Alpaca

Existing architecture already has: ZMQ tick streaming, Dollar Bar engine, LGBM inference, HUD with chart + probability oscillator, position manager, signal/noise threshold sliders