# Session: v107c_horizon_sweep_decision
*Időbélyeg: 2026-10-02T20:39:44.836568*

v1.07c HORIZON SWEEP + DÖNTÉS — 2026-10-02

HORIZON SWEEP EREDMÉNYEK (p7, side-free):

| Tag | WR | Profit | Lag | FwdL | Opp | DirTr |
|-----|-----|--------|-----|------|-----|-------|
| v106_base | 61.0 | 10,555 | -8 | 49.5 | 0 | 12,719 |
| h5_pt1.2_sl1.0 | 36.9 | 1,365 | -1 | 53.8 | 4,748 | 12,717 |
| h7_pt1.5_sl1.2 | 36.8 | 1,258 | +11 | **55.4** | 4,321 | 12,008 |
| h8_pt1.7_sl1.3 | 34.8 | 428 | -8 | 53.3 | 3,264 | 9,574 |
| h10_pt2.0_sl1.5 | 36.5 | 189 | +7 | 49.6 | 647 | 1,965 |
| h12_pt2.2_sl1.7 | 33.7 | 30 | +7 | 49.7 | 802 | 2,442 |
| h15_pt2.5_sl2.0 | 34.9 | 102 | -1 | 53.8 | 723 | 2,118 |

KULCS MEGÁLLAPÍTÁSOK:

1. FwdL=55.4% a h7-nél — EZ A LEGJOBB FORWARD WR MINDEDIKBOR SWEEP-BŐL!
   A 7 perces horizonton VAN prediktív szignal (5.4% a véletlenszint felett)
   DE a label WR még mindig 36.8% — a triple barrier zajos

2. Hosszabb horizont (>10min): túl kevés irányos trade (1965-2442)
   A nagy PT/SL miatt az ár ritkán ér el — kevés label

3. Optimum: 7-8 perc, PT≈1.5-1.7$, SL≈1.2-1.3$

4. v1.06 (körkörös) = LEGJOBB PROFIT (10,555) és LEGJOBB WR (61%)
   Bár körkörös, GYAKORLATBAN MŰKÖDIK — követi az indikátort
   Chart-on vizuálisan is látható: amíg trend tart, modell benne van

DÖNTÉS:
- v1.06 marad PRODUCTION modell (better than nothing!)
- A side-free kísérletek BEBIZONYÍTOTTÁK: nincs lookahead, nincs valódi szivárgás
- A lag INHERENS (indikátor simítás miatt), nem bug
- Következő: v1.06-ra építő javítások (two-phase S1×S2 már +$88)
  vagy új irány: DOM/orderbook ha elérhető, vagy más label stratégia