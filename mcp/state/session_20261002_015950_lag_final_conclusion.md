# Session: lag_final_conclusion
*Időbélyeg: 2026-10-02T01:59:50.307235*

LAG NEM CSÖKKENTHETŐ — VÉGSŐ KONKLÚZIÓ 2026-10-01

A vizualizáció megerősíti: 6-8 bar lag inherens, nem csökkenthető.

3 fix ok:
1. 14-periódusú indikátorok → ~7 bar inherens lag (zaj nélkül nem csökkenthető)
2. Triple barrier 5 perc label → lassú (modell ehhez igazodik)
3. PT=1.5$ fix (költségek miatt) → label ablak nem csökkenthető

Lag = nem bug, hanem feature:
- Markáns trend (30+ bar): lag nem baj, 22+ bar profit marad
- Vánszorgó trend (10 bar): lag kiszűri → EZ JÓ (veszélyes trade-k elkerülése)

Kétfázisú modell: nem lag-ot csökkent, hanem trade minőséget javít (+$88 nettó, +0.4pp WR)

Forward WR ≈ 49% (véletlenszint) → a modell NEM prediktálja a következő bar irányát
Label WR = 61% → a modell a 5-perces label-t prediktálja (ami lassú)