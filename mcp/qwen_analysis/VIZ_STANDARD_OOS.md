# 📊 STANDARD: OOS Vizualizáció — viz_v5.html Formátum

**KÖTELEZŐ FORMÁTUM** — minden OOS vizualizációhoz, KIVÉTELEK NÉLKÜL!

**Minta fájl:** `/data/dev/projects/z-ai-copilot/docs/viz_v5.html`

## Struktúra
```
<html>
<head><meta charset="utf-8" /></head>
<body>
  <div style="height:1200px; width:1600px;">
    <script> /* INLINE Plotly v3.6.0 (telles minim.js beágyazva) */ </script>
    <div id="UUID" class="plotly-graph-div" style="height:100%; width:100%;"></div>
    <script>
      Plotly.newPlot("UUID", [trace1, trace2, ...], layout, {responsive: true})
    </script>
  </div>
</body>
</html>
```

## Plotly Betöltés
- **INLINE** — Plotly teljes JS beágyazva a HTML-be (offline, CDN NEM)
- Generálás: `fig.write_html("file.html", include_plotlyjs=True)`

## 3 Szubplot (yaxis domain split)
1. **Ár + Prediktált Jelzések** — yaxis domain [0.46, 1.0]
   - Trade vonalak: mode="lines", width=2
   - Long: #228B22 (forest green)
   - Short: #B22222 (firebrick red)
   - showlegend: false
   - Minden trade = 1 scatter trace, 2 pont (azonos x, y=nyitás→ár)
   - xaxis matches x3 (közös x tengely)

2. **Predikciós Valószínűségek** — yaxis2 domain [0.23, 0.41]
   - Long/Short/Noise valószínűség vonalak
   - Threshold vonalak: th_L (#00FF00 dashed), th_S (#FF00FF dashed)

3. **Label vs Prediction** — yaxis3 domain [0.0, 0.18]
   - y=0 vonal (white), label/prediction scatter

## Dark Theme (KÖTELEZŐ)
```python
plot_bgcolor = "#111111"
paper_bgcolor = "#000000"
font_color = "white"
gridcolor = "white"
linecolor = "white"
zerolinecolor = "white"
```

## Layout Paraméterek
- height: 1200, width: 1600
- responsive: true
- Annotations: szubplot címek (font size 16, x=0.5, xanchor center)
- Title: "Z.ai Copilot — <modell> | <stat> | th_*=*"
- Shapes: threshold vonalak, y=0 vonal

## Trade Trace Formátum
```json
{
  "line": {"color": "#B22222", "width": 2},
  "mode": "lines",
  "showlegend": false,
  "x": ["2026-08-28T14:00:00", "2026-08-28T14:00:00"],
  "y": [4597.54, 4601.385],
  "type": "scatter",
  "xaxis": "x",
  "yaxis": "y"
}
```
- x: [timestamp, timestamp] — AZONOS idő!
- y: [open_price, close_price] — nyitás→ár vonal
- NINCS marker, NINCS hover text — csak vonalak

## Generálás Pythonból
```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig = make_subplots(rows=3, cols=1, row_heights=[0.54, 0.18, 0.18],
                    shared_xaxes=True, vertical_spacing=0.02)

# Subplot 1: Ár + Trade vonalak
for trade in trades:
    color = '#228B22' if trade.dir == 'Long' else '#B22222'
    fig.add_trace(go.Scatter(
        x=[trade.time, trade.time],
        y=[trade.open, trade.close],
        mode='lines', line=dict(color=color, width=2),
        showlegend=False
    ), row=1, col=1)

# Subplot 2: Valószínűségek
# Subplot 3: Label vs Prediction

fig.update_layout(
    height=1200, width=1600,
    plot_bgcolor='#111111', paper_bgcolor='#000000',
    font=dict(color='white'),
    title=dict(text='...'),
)

fig.write_html(path, include_plotlyjs=True)
```

## NEM SZABAD
- ❌ CDN link (plotly CDN) — MINDIG inline!
- ❌ Marker-alapú trade megjelenítés — VONALAK!
- ❌ Egyedi dark theme (#1a1a2e) — #000000/#111111!
- ❌ Külön statisztika panel — title + annotations!
- ❌ Más div méret — 1200×1600px!
