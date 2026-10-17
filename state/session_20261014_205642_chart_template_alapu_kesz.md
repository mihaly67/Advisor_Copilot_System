# Session: chart_template_alapu_kesz
*Időbélyeg: 2026-10-14T20:56:42.692494*

COPILOT V4 CHART TEMPLATE ALAPÚ KÉSZ (2026-10-14)

## Template: /data/dev/projects/scalper-copilot/Micro_LGBM/src/live_forward_test_results_20260813_SL1.html

Ebből a template-ből építettük újra a chart generátort:
- FELSŐ (68%): Candlestick + Long▲ erdőzöld + Short▼ téglavörös + zaj szint sáv
- ALSÓ (29%): P(Long) erdőzöld #228B22 + P(Short) téglavörös #B22222 + küszöb + zaj vonal
- Dark theme rgb(17,17,17) — template minta szerint
- yaxis domain [0.32,1.0], yaxis2 domain [0,0.291] — template minta szerint
- Shapes: Long thr lime dash, Short thr red dash, Noise gray dash — template minta
- Annotations: "M1 Price Action..." felül, "LightGBM Probabilities" alul

## Színek
- Long: erdőzöld #228B22 (ForestGreen)
- Short: téglavörös #B22222 (BrickRed)
- Több görbe: Long [forestgreen→seagreen→mediumseagreen], Short [firebrick→indianred→crimson]

## Fájlok
- /data/LGBM_copilot/src/scalper_copilot_chart.py — Plotly CDN, csak 2min
- /data/LGBM_copilot/charts/BTCUSD_copilot_v4_2026-10-0{5,6,7,8}.html — 4 nap
- /data/Brain/_qwen_analysis/chart_template_reference.md — template referencia

## Tudástárba mentve
A template referencia elmentve a Brain-be, RAG-ból visszakereshető.