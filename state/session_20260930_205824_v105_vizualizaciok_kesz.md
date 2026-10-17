# Session: v105_vizualizaciok_kesz
*Időbélyeg: 2026-09-30T20:58:24.592170*

# v1.05 Vizualizaciok Kesz — 2026.09.30

## 5 SCENARIO VIZUALIZACIOK

| Scenario | THL | THS | THN | File | 3-day WR |
|----------|-----|-----|-----|------|----------|
| Laza     | 0.30| 0.35| 0.55| viz_v105_laza.html   | 65.5% |
| S1       | 0.35| 0.40| 0.50| viz_v105_s1.html     | 66.2% |
| S2       | 0.45| 0.50| 0.40| viz_v105_s2.html     | 68.1% |
| S3       | 0.50| 0.55| 0.35| viz_v105_s3.html     | 70.9% |
| Szigor   | 0.55| 0.55| 0.30| viz_v105_szigor.html | 72.3% |

## FAJLOK
- Script: /data/dev/projects/z-ai-copilot/src/viz_v105_all.py
- HTML: /data/dev/projects/z-ai-copilot/docs/v105/ (5x ~444 KB)
- Sablon: /data/dev/projects/z-ai-copilot/src/viz_standard_template.py
- Standard doc: /data/dev/projects/z-ai-copilot/docs/v104/VIZ_STANDARD.md

## MINDEN HTML TARTALMAZ
- Panel 1: OHLC Candlestick + ▲ Long (erdőzöld) + ▼ Short (téklavörös) + ● Noise
- Panel 2: P(Long)/P(Short)/P(Noise) + THL/THS/THN vonalak
- Dark theme, CDN Plotly, grid fix
