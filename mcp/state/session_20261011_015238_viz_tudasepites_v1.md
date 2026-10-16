# Session: viz_tudasepites_v1
*Időbélyeg: 2026-10-11T01:52:38.422378*

VIZUALIZÁCIÓ TUDÁSÉPÍTÉS — TELJES KONTEXTUS

## 1. MEGLEVŐ HUD (hud_v5_cfd.py)
- PyQt5 + lightweight_charts (QtChart)
- ZMQ receiver (port 5557, "HUD " prefix)
- Fő chart: candlestick (Open/High/Low/Close)
- Subchart (30%): P(Long) zöld line, P(Short) piros line
- Zajzóna: noise_lo=0.425, noise_hi=0.575, threshold=0.50
- Anchor vonalak: 0.0, 1.0 (Y-tengely fixálás)
- Pozíció/Pivot vonalak: bid/ask, S/R micro/sec/ter
- Signal eval: -1 Short, 0 No trade, 1 Long
- HIÁNYZIK: ML modell vizualizáció, zajszint ML, 3D feature térkép, feature importance, AUC timeline

## 2. ELÉRHETŐ KÖNYVTÁRAK (External_Repos)

### pyqtgraph (PYQT5 alapú, már telepítve!)
- **2D**: BarGraphItem, HistogramLUTItem, FillBetweenItem, LinearRegionItem, InfiniteLine
- **3D (OpenGL)**: GLSurfacePlotItem (domborzat!), GLBarGraphItem (3D oszlop!), GLMeshItem, GLScatterPlotItem, GLLinePlotItem, GLVolumeItem, GLViewWidget
- **3D shaderek**: 'shaded', 'normalColor', 'heightColor', 'balloon'
- Fontos: GLSurfacePlotItem.setData(z=2Darray) → domborzati térkép
- Fontos: GLBarGraphItem(pos,size) → 3D hisztogram/oszlopdiagram
- Példa: GLSurfacePlot.py (4 surface + animáció), GLBarGraphItem.py (10x10 rács)

### vispy (GPU-accelerated, OpenGL)
- scene.visuals.SurfacePlot(z=z) — TurntableCamera, fov=60
- scene.visuals.XYZAxis, scene.Axis
- Volume, Mesh, Isosurface
- line_plot3d, scatter, graph
- Gyorsabb mint pyqtgraph OpenGL, de más event loop

### finplot (pyqtgraph wrapper pénzügyi plot!)
- candlestick, volume, RSI — shared X-axis
- pyqtgraph alapú → kompatibilis a meglévő PyQt5 HUD-dal!
- Zoom: Y-auto-scale highest high / lowest low
- Színek: candle_bull/bear, volume_bull/bear

### lightweight-charts-python
- TradingView Lightweight Charts JS engine
- QtChart widget (PyQt5) — EZT HASZNÁLJA A HUD!
- Candle, Line, Histogram, Area series
- Subchart, markers, horizontal_line, create_line
- Webview alapú (pywebview)

### DearPyGui
- C++ GPU-renderelt ImGui
- plot, line_series, bar_series, heatmap
- Nem PyQt5 kompatibilis — külön ablak

### plotly.py
- figure_factory, express, graph_objects
- 3D: scatter3d, surface, mesh3d
- Webes — Dash needed for desktop

### CustomTkinter
- Modern tkinter UI elemek
- Nem plot library — csak UI framework

## 3. MODELL ARCHITEKTÚRA (amit vizualizálni kell)
- v14_XAUUSD: lgbm_v14.pkl + mlp_meta_v12.pt → Ensemble (w_mlp, w_lgbm)
- v14_BTCUSD: ugyanez
- 27 feature: body_sign_f, consecutive_f, vol_ratio_f, RSI_3_f, RSI_5_f, delta_sr_zone_sec, delta_sr_zone_micro, round_10_dist, trend_micro, pivot_dist, above_pivot, ...
- ZMQ pub: "HUD " prefix → p_long, p_short, conf, signal, cusum_dir, fade_dir, ml_dir
- HIÁNYZIK: feature contribution (SHAP), zajszint per modell, feature drift

## 4. TV FRONTEND (TradingView charting-library)
- charting_library/ + datafeed.js + index.html
- tv_python_server.py: HTTP /api/history → MT5 CSV bars
- tv_websocket_server.py: ZMQ→WebSocket bridge
- TradingView charting-library: profi chart, de LICENSE needed

## 5. TERVEZETT VIZUALIZÁCIÓK

### A) P(Long)/P(Short) valószínűség chart — KÉSZ (hud_v5 subchart)
### B) LGBM vs MLP zajszintek — NEW
  - Két line series a subchart-ban: lgbm_prob, mlp_prob
  - Zajzóna per modell: noise_lo/hi dinamikus (rolling std)
### C) Feature importance 3D domborzat — NEW
  - pyqtgraph GLSurfacePlotItem
  - X=feature_idx, Y=time_window, Z=importance
  - Animált: gördülő ablak feature importance
### D) SHAP contribution waterfall — NEW
  - pyqtgraph BarGraphItem (vízszintes)
  - Top 10 feature contribution az aktuális predikcióhoz
### E) Predikció confidence heatmap — NEW
  - pyqtgraph ImageItem vagy GLSurfacePlotItem
  - X=RSI_3_f, Y=vol_ratio_f → Z=P(Long)
  - 2D slice a 27-dim feature térből
### F) Modell AUC timeline — NEW
  - pyqtgraph PlotItem: rolling AUC az utolsó N bar-on
### G) Signal regime histogram — NEW
  - pyqtgraph BarGraphItem: [zaj, CUSUM, ML, ML_override] eloszlás

## 6. AJÁNLOTT TECH STACK
- **Fő chart + subchart**: lightweight-charts (marad a meglévő)
- **3D vizualizáció**: pyqtgraph.opengl (GLSurfacePlotItem, GLBarGraphItem) — MÁR PYQT5 kompatibilis!
- **2D analitikus**: finplot vagy pyqtgraph direkt — shared window
- **Layout**: PyQt5 QSplitter — bal: lightweight chart, jobb: pyqtgraph 3D/2D panel