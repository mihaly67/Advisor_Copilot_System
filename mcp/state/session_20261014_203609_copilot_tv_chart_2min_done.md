# Session: copilot_tv_chart_2min_done
*Időbélyeg: 2026-10-14T20:36:09.126844*

COPILOT V4 TV CHART KÉSZ (2026-10-14)

## Scalper Copilot v4.0 — TradingView stílusú chart (lightweight-charts + PyQt5)

Template: /data/vizualizácio/hud_v5_cfd.py (V5 CFD HUD)
Könyvtár: /data/vizualizácio/lightweight-charts-python (TradingView Lightweight Charts)

## scalper_copilot_tv.py — 2min horizont, 1 nap, 4 vizualizáció egyben

### 4 vizualizáció:
1. FELSŐ (70%): Candlestick OHLC + Long ▲ / Short ▼ jelzések
2. ALSÓ (30%): P(Long) zöld + P(Short) piros vonalak
3. Küszöb vonalak: Long thr (zöld pontozott) + Short thr (piros pontozott)
4. Zajzóna: Noise-Lo → Noise-Hi (szürke szaggatott) = küszöb ± noise*sqrt(120)

### Modell (2min):
- Long AUC=0.6529, Short AUC=0.6290
- Long thr_ad=0.425, Short thr_ad=0.382
- Noise mean=0.0012

### Használat:
python3 /data/LGBM_copilot/src/scalper_copilot_tv.py --date 2026-10-05

### Fájlok:
- /data/LGBM_copilot/src/scalper_copilot_tv.py — TV chart
- /data/LGBM_copilot/src/scalper_copilot_v4.py — training pipeline
- /data/LGBM_copilot/src/scalper_copilot_chart.py — Plotly HTML chart

### Vizualizációs stack a tudástérből:
- lightweight-charts-python: TradingView candlestick (PRIMÁRIS)
- DearPyGui: GPU-accelerált HUD (real-time)
- finplot: PyQt5 fast plotting
- hud_v5_cfd.py: reference HUD template