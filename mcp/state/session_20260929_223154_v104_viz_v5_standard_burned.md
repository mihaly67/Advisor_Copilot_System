# Session: v104_viz_v5_standard_burned
*Időbélyeg: 2026-09-29T22:31:54.721783*

V104 3-NAP VIZ KÉSZ — EXACT viz_v5.html STANDARD

STANDARD PERMANENSEN BEÉGETVE:
- /data/Brain/_qwen_analysis/VIZ_STANDARD_OOS.md (teljes leírás)
- Minta: /data/dev/projects/z-ai-copilot/docs/viz_v5.html

STANDARD KULCSOK (KIVÉTELEZ NÉLKÜL):
1. Plotly INLINE (include_plotlyjs=True) — NINCS CDN!
2. Trade vonalak: mode="lines", width=2, Long=#228B22, Short=#B22222, showlegend=false
3. Minden trade = 1 scatter trace, 2 pont (x=[time,time], y=[open,close])
4. Dark theme: plot_bgcolor="#111111", paper_bgcolor="#000000", font="white"
5. 1200×1600px div
6. 3 szubplot (yaxis domain split): Ár+Jelzések | Pred. Valószínűség | Label vs Prediction
7. Annotations (font size 16) szubplot címek
8. Title: "Z.ai Copilot — <modell> | <stat>"
9. Threshold vonalak: th_L (#00FF00 dashed), th_S (#FF00FF dashed)
10. responsive: true

V104 VIZUALIZÁCIÓ:
- /data/dev/projects/z-ai-copilot/docs/v104/viz_v104_3day.html (5508 KB)
- /data/dev/projects/z-ai-copilot/src/viz_v104_3day.py
- 3 nap: 2026-08-28, 2026-08-31, 2026-09-01
- 2148 trade (L:1007 S:1141), WR: 62.3%, P:+$1,869
