# Session: pivot_v2_2year_complete
*Időbélyeg: 2026-10-10T09:38:13.887065*

PIVOT V2 COMPLETE — 2.66 ÉV M1 ADATON:

1. M1 adat merge: MQ5 (904k bar 2024-01→2026-07) + Tick M1 (76k bar 2026-06→2026-09) = 944,320 M1 bar (2.66 év)
   - Mentve: M1_OHLC_merged.csv (50.1 MB)

2. Pivot szintek v2 (okos pipeline):
   - 6 metódus: classic(HLC/HLCC), fibonacci, camarilla, woodie, ATR pivotal, round_number
   - TF: D1 + H4 (H1 kihagyva - túl sűrű)
   - Early dedup ($3) a touch előtt: 235k → 1,240 szint (200x csökkentés!)
   - Vektorizált touch: 1,240 × 944k = 1.17G ops → 3.6s (CHUNK=500)
   - Teljes pipeline: 11.3s

3. Eredmények:
   - Touch≥5: 1170 szint (mikro)
   - Touch≥10: 1144
   - Touch≥20: 1108
   - Touch≥50: 1053
   - Touch≥100: 957 (makró)
   - Top: $2034.10 (camarilla/R1 H4) T=10,479
   - ATR Pivotal dominálja a top 10-et (volatilitás-alapú szélsőértékek)

4. Lépcsőzetes touch skála: 5→10→20→50→100 (mikro→makró)
5. Mentve: pivot_levels.csv (1170 szint)