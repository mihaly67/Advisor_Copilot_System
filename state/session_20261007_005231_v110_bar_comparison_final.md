# Session: v110_bar_comparison_final
*Időbélyeg: 2026-10-07T00:52:31.013030*

V110 BAR COMPARISON VÉGEREDMÉNY

5 bar típus × 8 PT/SL kombináció = 40 teszt

LEGJOBB STABIL (gap<3%):
1. volbar_3_PT1.5_SL1.0_MB8: OOS=50.4% Viz=51.3% Gap=-0.9% P=$717+$279=$996
2. volbar_3_PT2.0_SL1.5_MB8: OOS=49.5% Viz=50.3% Gap=-0.8% P=$562+$222=$784
3. 100tick_PT2.0_SL1.5_MB8: OOS=50.9% Viz=49.5% Gap=+1.4% P=$200+$94=$294

KULCS MEGÁLLAPÍTÁSOK:
- Volatility bar ATR=$3.0 MŰKÖDIK — a korábbi probléma a PT/SL/MB paraméterek rossz beállítása volt (MB=5 túl kevés volt)
- MB=8 sokkal jobb, mint MB=5 (több idő a move kifejlődésére)
- PT=$1.5 SL=$1.0 a legjobb arány a volbar_3-hoz
- 100tick bar is jó (50.9% OOS) de kevesebb profit
- 1min bar stabil (48.3% OOS, 47.5% Viz) de alacsonyabb WR
- 50tick bar overfitting (gap > 4%)
- volbar_5 overfitting (gap 10%!)

VÉGSŐ AJÁNLÁS: volbar_3_PT1.5_SL1.0_MB8
- Legstabilabb (gap -0.9%)
- Legjobb profit ($996)
- Vizsgán JOBB mint OOS — nincs overfitting
