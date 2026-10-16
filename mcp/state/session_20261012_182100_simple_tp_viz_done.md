# Session: simple_tp_viz_done
*Időbélyeg: 2026-10-12T18:21:00.891375*

SIMPLE TP VIZUALIZÁCIÓ KÉSZ — mindhárom modell

Script: /data/dev/LGB_copilot_system/src/05_viz_simple_tp.py
HTML: /data/dev/LGB_copilot_system/docs/simple_tp_viz.html (3.4MB)

3 modell × 4 panel + 1 összehasonlító (Plotly, dark theme):
  Row 1: ROC curve (AUC) — Long/Short/EMA
  Row 2: Threshold → WR% + n_trades (secondary axis)
  Row 3: Predikció eloszlás (zöld=jó, piros=rossz)
  Row 4: Top 15 feature importance (gain)
  Row 5: Összehasonlító — AUC bar, WR@0.5+WR@0.65 bar, Brier bar

Színek: Long=#228B22, Short=#B22222, EMA=#4682B4
Háttér: #111111 (dark)

Docs mappa tisztva — csak simple_tp_viz.html van benne.

Következő: Optuna hyperopt, feature selection, vagy élő predikció integráció