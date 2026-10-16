# Session: jules_cfd_3way_comparison
*Időbélyeg: 2026-10-07T19:46:34.480995*

Jules CFD Correct Pipeline — 3 összehasonlítás — 2026-10-07

3 PIPELINE ÖSSZEHASONLÍTÁS:
1. M1 feature (előző): Stoch/Wick M1 gyertyán → OOS WR=41.2%, Vizsga=39.4%
2. DB OHLC, Dist_=0 (dollár bar ATR, túl nagy értékek): OOS WR=51.1%, Vizsga=46.6%
3. DB OHLC, Dist_=CSV (M1 ATR norm): OOS WR=43.0%, Vizsga=39.4%

KULCS FELISMERÉS:
- Dollár bar OHLC Stoch/Wick: +10% WR vs M1
- Dist_* feature-k KÁROSAK ha mikro feature-k jók (-8% WR)
- Legjobb: 4 feature (Tick_Speed, Stoch, Wick) Dist_* nélkül
- Stability filter túl szigorú (3/3 → 45 trade)

JULES 10 FEATURE CFD-ON: csak 4 hasznos
- Futures-ön Dist_* fontos (S/R távolság)
- CFD-én mikro feature-k eldöntik, makro S/R felesleges

KÖVETKEZŐ: 4-feature modell (Tick_Speed, Stoch_State_M1, Upper_Wick_ATR, Lower_Wick_ATR)