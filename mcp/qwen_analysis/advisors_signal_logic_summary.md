# Advisors Signal Logic Summary
# Generated: 2026-10-13
# Source: /data/Brain/advisors (11 cloned GitHub repos)

## Key Repos Cloned
1. BAKOME-Hub/BAKOMEGoldScalper - ICT Gold Scalper (FVG, OB, Silver Bullet, MQL5)
2. j1s4nn/EURUSD_Scalping_Robot - 7-indicator scoring EA (MQL5)
3. EA31337/EA31337 - Multi-strategy framework (MQL5)
4. dingmaotu/mql-zmq - ZeroMQ Python bridge (MQL4/5)
5. Aksee123/nq1_Scalping_Strategy - Volume Profile POC (Pine v6)
6. Ahmed-GoCode/tradingview-strategy-collection - DCA+MACD+RSI+Scalp (Pine)
7. l3quochuy-afk/super-scalping-analysis - Ichimoku pivots (Pine v5)
8. ElijahOrtizz/CSA-15 - Multi-confirmation scoring (Pine v5)
9. rs9476/TradingView-5M-Scalping-Indicator - 5-min scalping (Pine)
10. hudson-and-thames/MlFinLab - AFML labeling (Triple Barrier, Meta-Labeling, Python)
11. mhallsmoore/qstrader - Event-driven backtesting (Python)

## Top Labeling/Signal Patterns Found
- Multi-confirmation scoring: CSA-15 (8-point, min 6), EURUSD (7-point, min 4)
- ICT concepts: FVG, Order Blocks, Liquidity Sweeps, Silver Bullet (BAKOME)
- Squeeze detection: BB vs KC (CSA-15) - validates our micro_sqz approach
- Volume Profile POC: magnetic S/R level (NQ1 Scalp) - feature we DON'T have
- Meta-labeling: primary=side, secondary=size (MlFinLab) - could improve our models
- Fresh Trigger: only signal on first bar of new condition (CSA-15)
- Kill Zone / Session filter: time-of-day gating (BAKOME)
- Ensemble voting: 30+ simple strategies (EA31337)

## Priority Features to Add
1. Volume Profile POC (new S/R feature)
2. Fair Value Gap detection (gap pattern)
3. Order Block detection (structural S/R)
4. Session/Kill Zone filter (time-of-day)
5. HTF trend alignment filter
6. Meta-labeling approach (side + size)
