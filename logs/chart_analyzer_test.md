# Chart Analyzer Test Results

## viz_v9.html (5.7MB, Plotly v3.6.0 inline)

### Regex Analysis (verified from viz_v9_analysis.json)

**Title:** Z.ai Copilot — v9 (8 feat) | Long+Short | Long:72 Short:689 Noise:1239 | th_L=0.35 th_S=0.56

**Panels:**
1. Ár + Prediktált Jelzések (Entry bar Open) — top panel (y: 0.46–1.0)
2. Predikciós Valószínűségek — middle panel (y: 0.23–0.41)
3. Label vs Prediction — bottom panel (y: 0.0–0.18)

**Trace names:** Pred Short (689), Pred Noise (1239), P(Long), P(Short), P(Noise), Actual Label, Predicted

**Class counts:** Long:72, Short:689, Noise:1239

**Thresholds:** th_L=0.35 (green dashed), th_S=0.564 (magenta dashed), y=0.0 (white)

**Chart dimensions:** 1600x1200

**Plotly version:** 3.6.0 (inline bundled)

### Summary
- ✅ Title extraction
- ✅ Panel names (annotations)
- ✅ Class counts from title
- ✅ Threshold lines (shapes)
- ✅ Trace names
- ✅ Axis domains (panel positions)
- ⚠️ Candlestick data empty (viz_v9 uses scatter for price, not candlestick type)
- ⚠️ Scatter y_stats empty (regex needs improvement for nested JSON)

## viz_pred_2026-08-28.html (973KB, Plotly CDN v2.35.2)

This file uses:
- `<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>` (CDN, not inline)
- `Plotly.newPlot('viz_20261012_231353', [{"type": "candlestick", ...}, ...])`
- Candlestick + scatter traces
- Title: "Copilot — 2026-08-28 — BTCUSD"

## Implementation Status

### Files Created/Modified
1. **NEW:** `/data/mcp_server/chart_analyzer.py` — standalone chart analysis module
2. **MODIFIED:** `/data/mcp_server/mcp_backend_api.py` — added `/chart-analyze` endpoint
3. **MODIFIED:** `/data/mcp_server/server.py` — added `chart_analyzer` MCP tool (15th tool!)

### Methods
1. **Regex** — Fast, no dependencies. Extracts: title, panels, thresholds, trace names, class counts
2. **Playwright DOM** — Full extraction via JS execution on Plotly objects + screenshot
3. **Auto** — Both methods combined

### Performance
- Regex on 5.7MB HTML: ~2-3s (needs optimization for very large files)
- Regex on 973KB HTML: <1s expected
- Playwright DOM: ~5-10s (browser launch + render + JS execution)
