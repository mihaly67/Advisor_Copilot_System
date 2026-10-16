# NavSystem v2.22 → Python Fordítás + Pipeline Feature Terv
*Időbélyeg: 2026-09-23*
*Státusz: TERV — user kiegészítésre vár, utána implementáció*

## NavSystem v2.22 4 indikátor modul → Python

### PULSE (Hybrid MACD)
- MQL5: Hybrid_Momentum_Pulse_v1.05 → m_val_macd, m_val_dfcurve
- Python: `ta.trend.MACD(close).macd_diff()` + BB/Keltner skálázott diff

### FLOW (HybridFlowIndicator v1.126)
- MQL5: m_val_flow_mfi, m_val_flow_delta, m_val_flow_roc
- Python: `ta.volume.MFIIndicator` + Delta End (pozíció×vol akkumulált) + VROC

### CONTEXT (HybridContextIndicator v3.28)
- MQL5: ZigZag R/S/P (Micro/Sec/Ter) + Trend MA (Fast/Medium/Slow/Super)
- Python: Zig3-réteg ZigZag MÁR BENNE VAN a Scalper_Copilot_Miner CSV-ben!
  + Trend MA: `ta.trend.EMAIndicator(close, window)`

### MOMENTUM (Hybrid Momentum WPR+Stoch v1.04)
- MQL5: m_val_wpr, m_val_stoch_k
- Python: `ta.momentum.WilliamsRIndicator` + `ta.momentum.StochasticOscillator`

### RSI (natív, period=5)
- MQL5: iRSI(5)
- Python: `ta.momentum.RSIIndicator(close, window=5)`

## Teljes Feature Lista (~45-50 feature)

### A. MQ5-ből jövő (forward-fill dollar barra) — 13
Timestamp, Bid, Ask, Bid_Vol, Ask_Vol, Spread, 1m/5m/15m/30m_Close, ATR_M15, RSI_M15, Micro_R/S, Sec_R/S, Ter_R/S

### B. Python mikro (dollar bar szintű) — 12
OBI_Raw, OBI_ZScore, Bar_Time, Velocity, Tick_Speed, Dist_5m/15m/30m, ATR_Proxy, Micro RSI/MACD/BB/ROC/MFI

### C. NavSystem fordítás (ÚJ!) — 12
Pulse MACD, Pulse DF Curve, Flow MFI/Delta/VROC, RSI Fast(5), WPR, Stoch %K, Trend EMA fast/medium/slow/super

### D. Geometria — 7
Dist_Micro/Sec/Ter_R/S ATR-norm, Wick Upper/Lower ATR, Stoch State M1

### E. M15/M30 Makró resample — 10 (vagy kevesebb, ha MQ5 helyettesít)
M15/M30 RSI/MACD/BB/ROC/MFI5

## SHAP + Optuna → ~20-30 feature marad

## Könyvtár: `ta` (technical-analysis) — már a pipeline-ben van
Alternatí"ta: `talib` (TA-Lib C wrapper, gyorsabb)

## Pipeline módosítandó scriptek:
1. prado_dollar_bars.py — 18 oszlop bemenet, forward-fill MQ5 feature-ök
2. dom_feature_engineer_mtf.py — NavSystem feature-ök hozzáadása
3. dom_labeler_v5.py — NEM VÁLTOZIK
4. train_lgbm_fusion_v5.py — feature lista bővítés
5. fuse_macro_to_dollar_bars.py — KIESŐ
6. SHAP + Optuna — ÚJ LÉPÉS