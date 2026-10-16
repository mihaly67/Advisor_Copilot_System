# Session: v107d_fine_horizon_done
*Időbélyeg: 2026-10-02T22:09:23.568976*

v1.07d FINOM HORIZONT SWEEP — 2026-10-02

FINOM SWEEP EREDMÉNYEK (p7, side-free, 96 sec):

| Tag | WR | Profit | Lag | FwdL | FwdS | Circ | Opp | DirTr |
|-----|-----|--------|-----|------|------|------|-----|-------|
| v106_base | 61.0 | 10,555 | -8 | 49.5 | 50.1 | 0.946 | 0 | 12,719 |
| h5_pt1.2_sl1.0 | 36.9 | 1,365 | -1 | 53.8 | 51.8 | -0.09 | 4748 | 12,717 |
| h6$6_pt1.44_sl1.2 | **37.9** | **1,664** | -8 | 52.6 | 50.2 | -0.06 | 4549 | 12,274 |
| h7_pt1.68_sl1.4 | 37.0 | 1,332 | +4 | 51.3 | 48.1 | -0.06 | 4467 | 12,063 |
| h8_pt1.92_sl1.6 | 36.8 | 1,064 | +4 | 49.6 | 48.1 | -0.04 | 3591 | 10,123 |
| h9_pt2.16_sl1.8 | 36.6 | 758 | -8 | 48.5 | 51.3 | -0.05 | 2665 | 7,699 |
| h10_pt2.4_sl2.0 | 35.7 | 519 | -1 | 49.9 | 50.9 | -0.06 | 2438 | 7,392 |
| h11_pt2.64_sl2.2 | 34.7 | 203 | +13 | 50.1 | 48.8 | -0.08 | 1718 | 5,053 |
| h12_pt2.88_sl2.4 | 35.1 | 111 | -8 | **53.6** | **51.9** | -0.03 | 730 | 2,055 |

KULCS MEGÁLLAPÍTÁSOK:

1. OPTIMUM: h6 (6 perc, PT=1.44$, SL=1.2$) — legjobb WR (37.9%) és Profit (1,664)
2. h5-h7: még sok irányos trade (12000+), Opp magas (4500+)
3. h8-h10: DirTr csökken (10000→7400), Opp csökken (3591→2438)
4. h12: már csak 2055 DirTr, Opp=730 — de WR még mindig 35%
5. FwdL legjobb: h12=53.6% és h5=53.8% — a széleken jobb a forward predikció!

TREND:
- WR: 37.9% (h6) → fokozatosan csökken → 34.7% (h11) → 35.1% (h12)
- Profit: 1,664 (h6) → fokozatosan csökken → 111 (h12)
- Opp: 4748 (h5) → fokozatosan csökken → 730 (h12) — kevesebb ellentétes error
- DirTr: 12717 (h5) → fokozatosan csökken → 2055 (h12) — kevesebb trade

KONKLÚZIÓ:
- A side-free label WR sosem emelkedik 38% fölé — MINDIG rosszabb mint véletlen
- A PT/SL skálázás és időhorizont növelés NEM oldja meg a fundamentális problémát
- A probléma: a triple barrier "melyik PT hit először" kérdés zajos ezen a piacon
- 6 perc a legjobb kompromisszum, de az eredmény nem meggyőző

V1.06 MARAD A PRODUCTION MODELL — körkörös de működik!