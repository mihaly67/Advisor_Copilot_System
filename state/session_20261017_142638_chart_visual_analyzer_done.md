# Session: chart_visual_analyzer_done
*Időbélyeg: 2026-10-17T14:26:38.077085*

Chart Visual Analyzer MCP tool COMPLETE (2bb3a6a). 16th MCP tool.
- chart_visual_analyzer.py: generates interactive HTML with 5 Plotly charts
- Full data extraction via JS_EXTRACT_FULL (downsampled to 2000 points)
- Charts: (1) P(DIR=Long) + dominancia fill, (2) Long/Short signal scatter, (3) Ár-tartomány hisztogram + fedés, (4) Amplitúdó Z-score anomália, (5) Dominancia váltás timeline
- Backend API /chart-visual-analyze endpoint live on :8420
- Results on viz_pred_2026-08-28.html: 35.5% Long / 64.5% Short, 821 transitions, 372 counter-signals, 67.1% overlap, 0 amplitude bursts
- HTML auto-saved next to source file