# Vizualizáció Tudásépítés — Teljes Kontextus

## 1. Tananyag áttekintés (/data/ml/Knowledge_Base/External_Repos)

### pyqtgraph (0.14.0) — FŐ VIZUALIZÁCIÓS KÖNYVTÁR
- **2D graphicsItems**: BarGraphItem, HistogramLUTItem, FillBetweenItem, LinearRegionItem, InfiniteLine, ImageItem, PlotItem
- **3D OpenGL items**: GLSurfacePlotItem (domborzat), GLBarGraphItem (3D oszlop), GLMeshItem, GLScatterPlotItem, GLLinePlotItem, GLVolumeItem, GLViewWidget
- **3D shaderek**: 'shaded', 'normalColor', 'heightColor', 'balloon'
- **Példák**: GLSurfacePlot.py (4 surface + animáció), GLBarGraphItem.py (10x10 rács)
- **Kompatibilitás**: PyQt5 — azonos event loop, azonnal integrálható

### vispy (0.17.0) — GPU-accelerated OpenGL
- scene.visuals.SurfacePlot(z=z) + TurntableCamera
- Volume, Mesh, Isosurface, line_plot3d
- **Előny**: gyorsabb mint pyqtgraph OpenGL
- **Hátrány**: külön event loop, nehezebben integrálható PyQt5-be

### finplot (1.9.7) — pyqtgraph wrapper pénzügyi plot
- candlestick, volume, RSI — shared X-axis
- **Kompatibilis**: pyqtgraph alapú → azonos PyQt5 event loop
- Zoom: Y-auto-scale highest high / lowest low

### lightweight-charts-python (2.1) — TradingView engine
- QtChart widget (PyQt5) — EZT HASZNÁLJA A HUD
- Candle, Line, Histogram, Area series
- Subchart, markers, horizontal_line, create_line
- Webview alapú (pywebview)

### DearPyGui — C++ GPU-renderelt ImGui
- Nem PyQt5 kompatibilis — külön ablak, külön event loop

### plotly.py — Webes vizualizáció
- 3D: scatter3d, surface, mesh3d
- Dash needed for desktop — nem asztali alkalmazás

### TradingView charting-library
- tv_frontend/ + datafeed.js + index.html
- tv_python_server.py: HTTP /api/history → MT5 CSV bars
- tv_websocket_server.py: ZMQ→WebSocket bridge
- Profi chart, de LICENSE needed

## 2. HUD V6 Architektúra

```
┌─────────────────────────────────────────────────────────┐
│ V6CFD_HUD (1600x900)                                    │
│ ┌──────────────────────┬──────────────────────────────┐ │
│ │ BAL: lightweight_    │ JOBB: QTabWidget             │ │
│ │ charts               │ ┌──────────────────────────┐ │ │
│ │ ┌──────────────────┐ │ │ Tab 1: Feature 3D       │ │ │
│ │ │ Info sáv         │ │ │ (GLSurfacePlotItem)     │ │ │
│ │ │ Price | Pred |   │ │ ├──────────────────────────┤ │ │
│ │ │ Zaj: MLP|LGBM|ENS│ │ │ Tab 2: Contribution     │ │ │
│ │ ├──────────────────┤ │ │ (BarGraphItem waterfall) │ │ │
│ │ │ Candle chart 60% │ │ ├──────────────────────────┤ │ │
│ │ ├──────────────────┤ │ │ Tab 3: Heatmap          │ │ │
│ │ │ Subchart 40%:    │ │ │ (ImageItem RSI×vol→P)   │ │ │
│ │ │ Ens(green/red)   │ │ ├──────────────────────────┤ │ │
│ │ │ MLP(light green) │ │ │ Tab 4: AUC Timeline     │ │ │
│ │ │ LGBM(light blue) │ │ │ (PlotWidget rolling AUC)│ │ │
│ │ │ Noise zones(3x)  │ │ └──────────────────────────┘ │ │
│ │ │ Threshold(0.50)  │ │                              │ │
│ │ │ Anchor 0.0/1.0   │ │                              │ │
│ │ ├──────────────────┤ │                              │ │
│ │ │ S/R + Position   │ │                              │ │
│ │ └──────────────────┘ │                              │ │
│ └──────────────────────┴──────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 3. Modell Architektúra (v14)

- XAUUSD: lgbm_v14.pkl + mlp_meta_v12.pt → Ensemble (w_mlp=0.60)
- BTCUSD: lgbm_v14.pkl + mlp_meta_v12.pt → Ensemble (w_mlp=0.70)
- 27 feature: body_sign_f, consecutive_f, vol_ratio_f, RSI_3_f, RSI_5_f, Slope_3_atr_f, ema8_gap_f, above_ema8_f, above_ema20_f, PastRet_1_f, PastRet_2_f, vol_calm_f, body_ratio_f, wick_u_r_f, wick_l_r_f, Conviction_Bar_f, Fast_Bar_f, body_atr_f, velocity_atr_f, delta_sr_zone_sec, delta_sr_zone_micro, round_10_dist, trend_micro, pivot_dist, delta_pivot_dist, above_pivot
- ZMQ pub: "HUD " prefix → JSON (p_long, p_short, conf, signal, cusum_dir, fade_dir, ml_dir)
- V6 kiterjesztés: mlp_prob, lgbm_prob, feature_contribution, feature_importance, feature_names, RSI_3_f, vol_ratio_f, auc_mlp, auc_lgbm, auc_ens

## 4. OOS Vizsga Eredmények

| | XAUUSD (5 nap) | BTCUSD (4 nap) |
|---|----------------|----------------|
| OOS AUC Ensemble | **0.868** | **0.883** |
| Tréning OOS CV | 0.863 ± 0.008 | 0.856 ± 0.011 |
| Drop | +0.005 ✅ | +0.027 ✅ |

## 5. Következő lépések

1. EA (Merkava v3.0) ZMQ pub kibővítése: mlp_prob, lgbm_prob, feature_contribution, feature_importance
2. pipeline_v14 predict kibővítése: SHAP/LGBM feature contribution
3. Heatmap generálás: RSI_3_f × vol_ratio_f → P(Long) rács
4. Online kapcsolat: MT5 + EA fut → ZMQ → HUD v6
5. AUC timeline: rolling AUC számítás a HUD-ban
