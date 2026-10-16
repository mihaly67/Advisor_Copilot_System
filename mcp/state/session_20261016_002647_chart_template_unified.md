# Session: chart_template_unified
*Időbélyeg: 2026-10-16T00:26:47.656928*

Chart template egységesítés befejezve (2026-10-16):

1. scalper_copilot_chart.py — EGYETLEN template, --horizon param (1min/2min/3min/all)
   - build_chart(instrument, date_str, horizon='2min', max_pts=8000)
   - _build_single() generálja a HTML-t
   - Fájlnév: BTCUSD_copilot_v4_{horizon}_{date}.html
   - Cím/annotation tartalmazza a horizon nevét

2. scalper_copilot_chart_mh.py — thin wrapper, importálja a chart.py-t
   - --horizon all → 3 külön HTML (nem egy zsúfolt 3-panel)
   - A régi 3-panel kód ELTÁVOLÍTVA

3. scalper_copilot_v4.py — pipeline végén auto chart generálás
   - Legjobb horizont (max avg AUC) alapján
   - try/except wrapper — nem breakeli a pipeline-t

4. chart_template_reference.md — frissítve

Generált chartok (2026-10-07):
- BTCUSD_copilot_v4_1min_2026-10-07.html (1.4MB)
- BTCUSD_copilot_v4_2min_2026-10-07.html (1.5MB)
- BTCUSD_copilot_v4_3min_2026-10-07.html (1.7MB)