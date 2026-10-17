# Session: vegső_konkluzio
*Időbélyeg: 2026-10-12T23:22:27.737514*

VÉGSŐ KONKLÚZIÓ: Feature-ök nem prediktálnak irányt

Három megközelítés, mind AUC≈0.53 (random):
1. DIR modell (combo first-arrival Long vs Short): AUC=0.5316
2. TREND modell (sign of 5-bar forward return): AUC=0.5319  
3. Forward return >$5 label: AUC=0.53

Tick_Speed kivevése után top feature-ök:
- Bar_Direction #1, Return_1bar #4, Tick_Imbalance #9 — irány feature-ök megvannak
- De AUC=0.53 → nem elegendőek

OK: Long modell (TP hit prediction) AUC=0.615 WR=57.5% — ez MŰKÖDIK
NEM OK: Bármelyik irány-predikció AUC≈0.53 — NEM működik

A fundamentális probléma: OHLC-alapú feature-ök nem tartalmaznak elegendő
irány-információt. Order flow (bid/ask, trade direction) kellene hozzá.

A Long/Short modellek (TP hit prediction) működnek, de NEM irányt prediktálnak
— azt mondják "van-e esély $30 TP elérésére", nem "melyik irányba megy az ár".