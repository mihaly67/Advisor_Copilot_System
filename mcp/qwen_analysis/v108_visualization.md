# v1.08 Vizualizáció — Standard Plotly + Matplotlib

## Fájlok

### Standard Plotly HTML (2-panel: Candlestick + Probability)
- `/data/dev/projects/z-ai-copilot/docs/v108/viz_v108_m10_pred.html` (263 KB) — v1.08-M10 (Mom10_Direction)
- `/data/dev/projects/z-ai-copilot/docs/v108/viz_v108ts_pred.html` (263 KB) — v1.08-TS (Trend_Strength_20)

### Matplotlib Összehasonlító (6-panel)
- `/data/dev/projects/z-ai-copilot/docs/v108/v108_comparison.png` (677 KB, 2984×2182)
- `/data/dev/projects/z-ai-copilot/docs/v108/v108_comparison.pdf` (639 KB)

## VIZ_STANDARD megfelelés
- ✅ 2 panel: Candlestick + Probability
- ✅ Short=#B22222, Long=#228B22, Noise=#888888
- ✅ Dark theme: #111111 plot, #000000 paper
- ✅ CDN Plotly (<500 KB)
- ✅ Post-process JS gridcolor fix
- ✅ Triangle markers (▲ Long, ▼ Short, ● Noise)
- ✅ THN threshold line

## Generátor
- `/data/dev/projects/z-ai-copilot/src/viz_v108.py`
