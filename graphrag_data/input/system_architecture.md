# Architektúra — LGBM Copilot v4.01

> **Dátum:** 2026.09.20
> **Hely:** `/data/LGBM_copilot/`

## Rendszer komponensek

### 1. Adatgyűjtés (MT5 EA)
- **Merkava v3.0+ EA** → tick adat → port 5556 (TICK|time|bid|ask|pos|DOM|pivots)
- **Macro script** → pivot R/S, EMA slopes → port 5555 (JSON)
- **Data Miner scriptek** → offline CSV (történeti adat tanításhoz)

### 2. Adatfeldolgozás (Python)
- **Dollar Bar** generálás (dinamikus threshold, vektorizált numpy)
- **Feature engineering** (anti-leakage: shift-before-rolling)
- **3MTF macro** (M15+M30: RSI, MACD, BB Z, ROC, MFI)
- **ZigZag pivot** (real-time MT5-ből, nem offline)

### 3. Címkézés (Triple Barrier) — TERVEZETT
- **ATR-alapú barrier** (nem fix dollar)
- **Dinamikus max_bars** (ATR alapján)
- **Anti-overlabeling** (1.0 ATR távolság új címke előtt)
- **Wick-aware** (intra-bar High/Low stop-out)
- ⚠️ Még nincs implementálva — pipeline jelenleg fix TP/SL címkézést használ

### 4. Modellek
- **LightGBM** (fő modell, 29+ feature, Optuna-tuned)
- **MLP Meta-Advisor** (távoli jövő — strictly OOS LGBM predikciókkal tanítva)
- **Macro Regime** (ridge regression, CatBoost)

### 5. Éles backend
- **TCP listener** port 5555 (macro), 5556 (tick)
- **ZMQ PUB** port 5557 (HUD JSON)
- **4D Asymmetric Threshold** (Argmax + Noise Gating)

### 6. HUD (PyQt5)
- Valós idejű candlestick + signal + probabilities
- P_Noise slider (regime-adaptive)

## Adatfolyam
```
1. MT5 EA → tick → port 5556
2. MT5 EA → macro JSON → port 5555
3. Python: Dollar Bar accumulation → bar close
4. Python: Feature engineering (shift-before-rolling)
5. Python: LightGBM predict_proba → P_Long/P_Short/P_Noise
6. Python: 4D Threshold → Signal
7. Python: MLP Meta-Advisor → confidence filter (távoli jövő)
8. Python: ZMQ PUB → JSON HUD
9. PyQt5 HUD: megjelenítés
10. Python: PING → EA keepalive
```

## Port térkép
| Port | Protokoll | Irány | Tartalom |
|------|-----------|-------|----------|
| 5555 | TCP | EA→Python | Macro JSON (pivots, EMA) |
| 5556 | TCP | EA→Python | Tick (bid, ask, DOM, pivots) |
| 5557 | ZMQ PUB | Python→HUD | JSON (signal, probabilities, OHLC) |
