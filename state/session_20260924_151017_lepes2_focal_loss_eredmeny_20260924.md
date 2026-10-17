# Session: lepes2_focal_loss_eredmeny_20260924
*Időbélyeg: 2026-09-24T15:10:17.713484*

LÉPÉS 2: FOCAL LOSS — EREDMÉNYEK (2026-09-24)

=== ÖSSZEHASONLÍTÁS ===
Method              γ     AUC   Brier   P-std  BestTh   Profit   Win%  Trades
baseline(γ=0)     0.0  0.5329  0.2503  0.0730    0.30  3250.0$  50.8%    6209
focal(γ=0.5)      0.5  0.5262  0.2502  0.0590    0.30  3251.0$  50.7%    6223
focal(γ=1.0)      1.0  0.5270  0.2497  0.0515    0.30  3251.0$  50.7%    6223
focal(γ=1.5)      1.5  0.5184  0.2501  0.0457    0.30  3258.0$  50.8%    6228
focal(γ=2.0)      2.0  0.5260  0.2496  0.0439    0.30  3258.0$  50.8%    6228
focal(γ=3.0)      3.0  0.5245  0.2495  0.0390    0.30  3258.0$  50.8%    6228
BASELINE(all)      —       —       —       —       —  3258.0$  50.8%    6228

=== KULCS MEGÁLLAPÍTÁSOK ===

1. AUC CSÖKKENT minden γ-nál!
   - baseline=0.5329 → focal γ=0.5=0.5262 → γ=1.0=0.5270 → γ=1.5=0.5184 → γ=2.0=0.5260 → γ=3.0=0.5245
   - A focal loss NEM javítja a diszkriminációt, hanem rontja

2. Brier score marginálisan javult (0.2503 → 0.2495)
   - De ez nem konvertálód profitra

3. P-std (szórás) CSÖKKENT a focal loss hatására
   - baseline=0.0730 → γ=3.0=0.0390 (majdnem fele!)
   - A focal loss "összenyomja" a probabilitásokat a 0.5 köré
   - Ez a KELLŐ ELLENGEKESSÉ irányba hatunk!

4. Profit = BASELINE minden γ-nál
   - A meta modell továbbra sem ad hozzá értéket

5. Érdekes: magasabb th-nál a focal γ=2.0 javítja a trade minőségét
   - th=0.55: focal γ=2.0 → 788 trades, 58.2% win (baseline 1373 trades, 56.2% win)
   - De összességében kevesebb profit

=== VERDIKT: LÉPÉS 2 KUDARCOT VALLOTT ===
- Focal loss nem javítja az AUC-t
- A probabilitás szórás csökken (rossz irány)
- Profit = baseline mindenhol

=== TANULSÁG ===
A probléma nem a loss function-ben van. A feature-ök nem hordoznak elég információt.
A meta_v1 AUC≈0.53 azért alacsony, mert a Target_Meta label (PT/SL binary) nem jósolható
meg a rendelkezésre álló 30 feature-ből.

KÖVETKEZŐ LÉPÉS: Lépés 3 (Purged K-Fold) — validációs módszer javítása