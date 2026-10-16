# Predikcio Lag — Korrigalt Elemzes

## NEM LOOK-AHEAD! 
Look-ahead eseten a predikcio ELORE mutatna. A 6-7 bar keses az indikatorok
BACKWARD-LOOKING simitasa miatt van.

## Gyanus indikatorok (14-15 period):
- Slope_Close_14 → ~7 bar lag
- Micro_RSI_14 → simit, kesik
- EMA50_Slope_Up → 50 period, nagyon lassu
- Trend_Strength_20 → 20 period ablak

## Kovetkezo feladat:
1. Cross-correlation lag analizis (P(Long) vs ar valtozas, lag=-10..+10)
2. Feature-onkenti lag meres
3. Gyors indikatorok tesztelese (RSI_3, Slope_5, Mom_3)
4. Cel: 2-3 bar ala csokkenteni a lag-et
