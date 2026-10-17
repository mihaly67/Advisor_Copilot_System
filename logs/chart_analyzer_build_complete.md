# Chart Analyzer Tool — Build Complete

## Összefoglaló

A `chart_analyzer` MCP tool sikeresen megépítve. Ez egy **DOM-based adatkinyerő** Plotly HTML chartokhoz, ami **Playwright page.evaluate()** segítségével JavaScript futtat a böngészőben, hogy kinyerje a Plotly objektumokból a strukturált adatokat — **screenshot + vision API hívás nélkül**.

## Architektúra

```
chart_analyzer MCP tool (server.py)
    ↓ HTTP POST
Backend API (/chart-analyze, port 8420)
    ↓
chart_analyzer.py
    ├── method="regex"  → extract_plotly_traces_regex()  [~2s, no deps]
    ├── method="playwright" → _playwright_extract()      [~8s, Playwright+JS]
    └── method="auto" → mindkettő
```

## Fájlok

| Fájl | Művelet | Leírás |
|------|---------|--------|
| `/data/mcp_server/chart_analyzer.py` | ÚJ | Standalone modul (16.6KB) |
| `/data/mcp_server/mcp_backend_api.py` | MÓDOSÍTOTT | `/chart-analyze` endpoint |
| `/data/mcp_server/server.py` | MÓDOSÍTOTT | `chart_analyzer` MCP tool (15. tool!) |
| `/data/mcp_server/test_chart_analyzer.sh` | ÚJ | Teszt script |
| `/data/mcp_server/restart_and_test.sh` | ÚJ | Backend restart + teszt |

## Telepített dependenciák
- `playwright==1.64.0` (venv-ben)
- Chromium Headless Shell 156.0.8078.4 (`~/.cache/ms-playwright/`)

## Tesztelt eredmény (viz_v9.html — 5.7MB)

```
Title: Z.ai Copilot — v9 (8 feat) | Long+Short | Long:72 Short:689 Noise:1239 | th_L=0.35 th_S=0.56
Panels: Ár + Prediktált Jelzések, Predikciós Valószínűségek, Label vs Prediction
Class counts: Long:72, Short:689, Noise:1239
Thresholds: th_L=0.35 (green), th_S=0.564 (magenta), y=0.0 (white)
Trace names: P(Long), P(Short), P(Noise), Actual Label, Predicted
Plotly: v3.6.0 (inline bundled)
Dimensions: 1600×1200
```

## Tool API

```python
chart_analyzer(
    path: str = "",       # HTML fájl útvonal (pl. /data/dev/.../viz_v9.html)
    html: str = "",       # HTML tartalom string (path helyett)
    method: str = "auto", # "auto" (regex+playwright) | "regex" | "playwright"
    wait_ms: int = 3000   # Plotly render várakozás ms (playwright módban)
) -> str  # Formázott eredmény szöveg
```

## Kinyerhető adatok

### Regex mód (gyors, ~2s)
- Title, panelek (annotations), küszöb vonalak (shapes)
- Trace nevek és típusok
- Osztály számok (címből)
- Candlestick OHLCV range
- Időtartam (első/utolsó timestamp)
- Predikció valószínűség statisztikák (min/max/mean)

### Playwright DOM mód (részletes, ~8s)
- Minden trace összes mezője (x, y, open, high, low, close, customdata, stb.)
- Layout összes tulajdonsága
- Interaktív adatok (zoom, select, hover)
- Screenshot + PIL képelemzés
- DOM meta (script-ek száma, div-ek, body méret)

## Megoldott probléma
- **ZhipuAI vision API nem elérhető** nemzetközi account-on → DOM query megkerüli
- **5.7MB HTML** regex lassú volt → tail-only scan optimalizálás
- **Candlestick típus** nem mindig jelen van (viz_v9 scatter-t használ) → regex adaptív

## Következő lépések
1. `bash /data/mcp_server/restart_and_test.sh` — backend restart + teszt
2. Git push: `cd /data/mcp_server && git add -A && git commit -m 'feat: chart_analyzer' && git push`
3. `html_analyzer` tool variáns (generikus HTML vizsgálat, nem csak Plotly)
4. RAG-ba indexelés: chart elemzések → tudásgráf csomópontok
