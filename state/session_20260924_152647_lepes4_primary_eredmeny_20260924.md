# Session: lepes4_primary_eredmeny_20260924
*Időbélyeg: 2026-09-24T15:26:47.512015*

LÉPÉS 4: ERŐSEBB PRIMARY MODEL — EREDMÉNYEK (2026-09-24)

=== TRIPLE BARRIER PARAM SCAN ===
Eredeti Target_Meta PT rate: 51.6%
Legjobb match: ATR_Micro, pt_mult=0.5, sl_mult=0.5, max_bars=5 → 52.6% PT rate
(Korábbi rossz paraméterek: pt_mult=2.0, sl_mult=1.0 → 18% PT rate → negatív profit)

=== ÖSSZEHASONLÍTÁS (jó paraméterekkel, 52% PT rate) ===
Primary          PT%     AUC   Brier   Base$   Meta$       Δ   Win%  Trades
slope14        52.6%  0.4953  0.2534   3480$   3478$     -2$  52.0%    6227
ema_fast       53.4%  0.5069  0.2528   3915$   3894$    -21$  54.3%    6201
rsi50          52.9%  0.5074  0.2523   3576$   3571$     -5$  52.5%    6212
mom5           52.4%  0.5005  0.2533   3483$   3473$    -10$  52.0%    6217
breakout       52.3%  0.5006  0.2531   3444$   3448$     +4$  51.8%    6224
vote4          52.6%  0.5063  0.2521   3504$   3500$     -4$  52.1%    6220
pvel           52.7%  0.5102  0.2523   3531$   3513$    -18$  52.2%    6204
trend_align    52.5%  0.5031  0.2531   3495$   3495$     +0$  52.0%    6228

=== KORÁBBI (rossz paraméterek: pt=2.0, sl=1.0, 18% PT rate) ===
Ekkor AUC 0.53-0.57 volt! De baseline profit -$2600-tól -$2925-ig (negatív!)
Meta modell alig vett trade-t (7-53), de Δ hatalmas (+$2700-2900)

=== KULCS MEGÁLLAPÍTÁSOK ===

1. AUC ≈ 0.50 minden primary-nél (RANDOM!)
   - A re-labeling AUC=0.4953-0.5102 — alig jobb a randomnál
   - Az eredeti Target_Meta AUC=0.5333 volt — az eredeti label volt jobban predikálható

2. Meta modell Δ ≈ 0 minden primary-nél
   - breakout: +$4 (legjobb, de marginális)
   - ema_fast: -$21 (legrosszabb)
   - A meta modell nem tudja szűrni a rossz trade-eket

3. EMA_FAST a legjobb BASELINE profit ($3915, 54.3% win rate)
   - slope14 eredeti: $3480 (52.0%)
   - ema_fast +12% jobb profit mint slope14!
   - De meta modell nem tudja javítani

4. A PROBLÉMA NEM A PRIMARY MODEL!
   - Minden 8 primary-nél AUC≈0.50
   - A 30 feature NEM predikálja a trade outcome-ot
   - A primary megválasztása nem számít a meta modell szempontjából

5. ÉRDEKES: rossz triple barrier paraméterekkel (18% PT rate)
   az AUC magasabb volt (0.56-0.57)!
   - Ez azt jelenti, hogy a nehezebb label (18% PT) jobban predikálható
   - De a profit struktúra (PT=+2, SL=-1) miatt 18% PT rate → negatív profit
   - A meta modell jól szűri (csak 7-53 trade), de túl kevés

=== VERDIKT: LÉPÉS 4 RÉSZBEN SIKERES ===
- ✅ Találtunk jobb primary-t: ema_fast (+12% baseline profit)
- ❌ De a meta modell továbbra sem ad hozzá értéket (Δ≈0)
- A gyökérprobléma: a 30 feature nem predikálja a Target_Meta-t (AUC≈0.50)

=== KÖVETKEZŐ LÉPÉS: Lépés 5 (Sample-Uniqueness Weighting) ===
Triple barrier overlapping label-ek → sample_weight = uniqueness
De az adatban 0% overlapping label volt...
Ehelyett próbáljunk valami mást: feature engineering / új feature-k