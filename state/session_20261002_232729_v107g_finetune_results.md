# Session: v107g_finetune_results
*Időbélyeg: 2026-10-02T23:27:29.072302*

v107g FINOMHANGOLAS — VÉGSŐ EREDMÉNY 2026-10-02

TOP 10 (Profit alapjan):

| Tag | WR | Profit | ThN | Circ | Lag | FwdL | PT | SL | maxb |
|-----|-----|--------|-----|------|-----|------|----|----|------|
| **m10_pt0.6_sl0.6_b5** | **65.9%** | **12,581** | 0.87 | 0.7135 | **-9** | **50.3** | 0.6 | 0.6 | 5 |
| m10_pt0.6_sl0.6_b8 | 65.9% | 12,575 | 0.88 | 0.7131 | -9 | 50.1 | 0.6 | 0.6 | 8 |
| ts20_pt0.6_sl0.6_b5 | 65.7% | 12,495 | 0.92 | 0.4994 | -15 | 49.7 | 0.6 | 0.6 | 5 |
| ts20_pt0.6_sl0.6_b8 | 65.6% | 12,488 | 0.92 | 0.4995 | -15 | 49.7 | 0.6 | 0.6 | 8 |

KULCS FELFEDEZÉSEK:

1. OPTIMUM: PT=0.6$, SL=0.6$, maxb=5 — SZŰK BARRIER A NYERŐ!
   - v1.06: WR=61%, P=10,555, Circ=0.946, Lag=-8
   - m10_pt0.6_sl0.6: WR=65.9%, P=12,581, Circ=0.713, Lag=-9
   - ts20_pt0.6_sl0.6: WR=65.7%, P=12,495, Circ=0.499, Lag=-15

2. Mom10_Direction a NYERŐ:
   - WR=65.9% (+4.9% vs v1.06!)
   - Profit=12,581 (+19% vs v1.06!)
   - Lag=-9 (jobb mint ts20 -15!)
   - FwdL=50.3% (van forward prediktív erő)
   - Circ=0.713 (25%-kal kevesebb körkörösség)

3. Trend_Strength_20 a legkevésbé körkörös:
   - Circ=0.499 (47%-kal kevesebb!)
   - De Lag=-15 (rosszabb)
   - Profit hasonló

4. PT=0.6$ SL=0.6$ a kulcs — szűk barrier + gyors kilépés
   - maxb=5 a legjobb (5 bars = ~5 perc)
   - Nagyobb PT/SL rosszabb (1.0+ már WR<55%)

5. AZONOS OPTIMUM MINDKÉT INDIKÁTORNAK: PT=0.6 SL=0.6 maxb=5

KÖVETKEZŐ:
- m10_pt0.6_sl0.6_b5 legyen v1.08 production candidate
- Two-phase S1×S2 + this config
- Forward audit (nincs-e lookahead a szűk barrier-ben)