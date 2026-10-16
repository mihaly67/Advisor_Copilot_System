# Session: viz_skeleton_complete
*Időbélyeg: 2026-10-11T20:13:52.315836*

LGB Copilot Vizualizációs csontváz KÉSZ

Fájlok:
  /data/dev/LGB_copilot_system/viz/
    README.md — Leírás, szín konvenciók, script lista
    _plotly_template.py (167 sor) — Közös Plotly HTML generátor
      - Színek: C_GREEN=#228B22, C_RED=#B22222, C_GRAY=#808080, C_BLUE=#4682B4
      - triangle_markers() — háromszög kontúr nélkül (line width=0)
      - barrier_line_shapes() — TP/SL barrier vonalak
      - prob_curve() — valószínűség görbe
      - noise_band_shapes() — szürke zaj sáv
      - generate_html() — Plotly HTML generátor (CDN alapú)
      - save_html() — fájl mentés
      - base_layout() — sötét téma layout
    viz_labeling_1day.py (222 sor) — TB címkézés vizualizáció 1 napra
      - --csv, --date (kötelező), --out
      - load_one_day() — CSV betöltés + 1 nap szűrés
      - extract_tb_events() — TB event kinyerés (dummy ha nincs label)
      - build_viz() — ár vonal + háromszögek + barrier + kumulatív + zaj
    viz_labeling_2024-06-16.html (177KB) — teszt HTML

Tesztelve:
  python3 viz/viz_labeling_1day.py --csv RAW_CSV/BTCUSD/M1_History_BTCUSD.csv --date 2024-06-16 --out /tmp/viz_test.html
  Eredmény: 1434 bar, 667 TP, 767 SL (dummy), 177KB HTML ✅
