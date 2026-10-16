# Session: two_phase_viz_complete
*Időbélyeg: 2026-10-02T01:36:07.742930*

KÉTFÁZISÚ VIZUALIZÁCIÓ KÉSZ — 2026-10-01

## VIZUALIZÁCIÓ: 3 panel
1. OHLC Candlestick + S1×S2 predikciós háromszögek + v106 szürke háromszögek
2. Stage 1 (kék) + Stage 2 (narancs) valószínűségek
3. Megegyezés/Ellentmondás bar chart (zöld/piros)

## TELJES OOS ELLANTMONDÁS STATISZTIKA (12,889 bar):
- Megegyezés: 11,691 (92.2%) ← S1 és S2 egyetértenek
- Ellentmondás: 0 (0.0%) ← SOHA nem mondanak ellent!
- S1 irány, S2 vár: 509 (4.0%) ← timing szűrés
- S1 vár, S2 irány: 482 (3.8%) ← S2 jelez de S1 nem lát irányt
- Mindkettő Noise: 207

## KULCS FELFEDEZÉS: 0 ellentmondás!
S1 (lassú, irány) és S2 (gyors, timing) SOHA nem mondanak ellent!
Ok: mindkettő ugyanarra a label-re van tanítva → sosem fordul elő
hogy S1=Long és S2=Short egyszerre.

## TIMING SZŰRÉS MŰKÖDIK:
- S1 irány + S2 VÁR → forward WR Long=52.1% (alig jobb mint véletlen)
- S2 jogosan szűri ki ezeket: a timing rossz!
- A 4% S1-wait trade szűrés = költségmegtakarítás

## FÁJL:
- /data/dev/projects/z-ai-copilot/docs/v106/viz_two_phase.html (400 KB)
- /data/dev/projects/z-ai-copilot/src/viz_two_phase.py