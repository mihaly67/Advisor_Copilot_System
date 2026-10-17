# Session: dollar_bar_60tp_labeling
*Időbélyeg: 2026-10-12T20:39:16.810837*

$60 TP CÍMKÉZÉS KÉSZ — dollár bar-okon, Both=2.9% (volt 36%!)

Config: SIMPLE_TP_DIST=60, SIMPLE_TP_MAX_BARS=10, threshold=$1,041,000 (3 bar/min)

Diagnózis: $30 TP ≈ 1.5× bar range → 36% both = hulladék
Fix: $60 TP ≈ 3× bar range → 2.9% both = JÓ!

Label eloszlás ($60 TP, 10 bar lookahead):
  Long only:  24.8%  — ▲ LONG jelzés
  Short only: 24.8%  — ▼ SHORT jelzés  
  Both:        2.9%  — zaj (elviselhető)
  Neither:    47.5%  — nincs jelzés

2026-08-28: LONG=1,503 SHORT=1,639 Both=226 Neither=2,903 (6,271 bar)
2026-08-25: LONG=1,864 SHORT=1,995 Both=357 Neither=1,894 (6,110 bar)

Viz: /data/dev/LGB_copilot_system/viz/viz_signals_YYYY-MM-DD.html
Script: /data/dev/LGB_copilot_system/viz/viz_signals_1day.py

Következő: feature generálás + LightGBM tréning az új $60 label-ekkel