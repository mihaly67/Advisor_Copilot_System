# Session: simple_tp_1day_viz_done
*Időbélyeg: 2026-10-12T18:46:15.865457*

SIMPLE TP 1-NAP VIZUALIZÁCIÓ KÉSZ

Script: /data/dev/LGB_copilot_system/viz/viz_simple_tp_1day.py
HTML kimenet: /data/dev/LGB_copilot_system/viz/viz_simple_tp_YYYY-MM-DD.html

5 panel (1 nap, mindhárom modell):
  1. Ár OHLC candles + trade háromszögek (TP hit ▲ zöld, FP ✗ x)
  2. Predikció görbék: P(Long), P(Short), P(EMA) + threshold vonalak (0.5, 0.65)
  3. Kumulatív WR (futó win rate) 3 modell
  4. Bars held eloszlás (TP elérésig hány bar)
  5. EMA side + Bar_Sign szinkronizáció

Használat: python3 viz/viz_simple_tp_1day.py --date 2026-08-28 --thr 0.5

Eredmények (test set napok):
  2026-08-25: Long WR=70.2%, Short WR=72.5%, EMA WR=75.3%
  2026-08-28: Long WR=62.7%, Short WR=67.5%, EMA WR=70.3%

Régi viz_labeling HTML-ek törölve a viz mappából.
Színek: Long=#228B22, Short=#B22222, EMA=#4682B4, Háttér=#1a1a2e