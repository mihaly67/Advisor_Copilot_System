# Scalper Copilot v4.0 — Chart Template Referencia

## Template forrás
`/data/dev/projects/scalper-copilot/Micro_LGBM/src/live_forward_test_results_20260813_SL1.html`

## Template struktúra (Plotly standalone, dark theme)
- **FELSŐ ablak** (yaxis domain [0.32, 1.0]): Candlestick OHLC + jelzések
- **ALSÓ ablak** (yaxis2 domain [0, 0.291]): Probability görbék [0,1] range
- **xaxis** matches x2, showticklabels:false (idő csak alul)
- **Dark theme**: paper_bgcolor=rgb(17,17,17), plot_bgcolor=rgb(17,17,17)
- **Annotations**: cím felül, horizont név alul
- **Shapes**: Long Threshold lime dash, Short Threshold red dash, Max Noise gray dash
- **Beágyazott Plotly** v3.7.0 CDN

## Színek
- Long: **erdőzöld #228B22** (forestGreen)
- Short: **téglavörös #B22222** (BrickRed/Firebrick)
- Noise: **szürke #888888**

## Chart rendszer (egységesítés: 2026-10-16)

### `scalper_copilot_chart.py` — EGYETLEN chart template
- **Single-horizon**, 2 panel (ár + probability) — clean, olvasható
- `--horizon 1min|2min|3min|all` paraméter
- Fájlnév: `BTCUSD_copilot_v4_{horizon}_{date}.html`
- Pipeline automatikusan generálja a legjobb horizonttal

### `scalper_copilot_chart_mh.py` — Wrapper (multi-horizon)
- Importálja a `scalper_copilot_chart.py`-t
- `--horizon all` → 3 KÜLÖN HTML (nem egy zsúfolt 3-panel)
- Hátra kompatibilitás: `--horizon 2min` csak a 2min-et

### `scalper_copilot_tv.py` — TradingView stílus (experimental)
- PyQt5 + lightweight_charts — interaktív desktop widget

### Pipeline integráció
- `scalper_copilot_v4.py` végén automatikus chart generálás
- Legjobb horizont (max avg AUC) alapján

## Modell metrika (2min)
- Long AUC=0.6529, Short AUC=0.6290
- Long thr_ad=0.425, Short thr_ad=0.382
- Noise mean=0.0012

## Charts mappa
```
/data/LGBM_copilot/charts/
  BTCUSD_copilot_v4_1min_2026-10-07.html   # 1min clean
  BTCUSD_copilot_v4_2min_2026-10-07.html   # 2min clean (alapértelmezett)
  BTCUSD_copilot_v4_3min_2026-10-07.html   # 3min clean
```
