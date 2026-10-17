# Session: key_insight_lgbm_regime
*Időbélyeg: 2026-09-23T22:24:24.415399*

KULCSFELISMERÉS: LightGBM fa minden bar függetlenül dönt, nincs memória/szekvencia. XAUUSD 2 éve uptrend-ben visszaesésekkel → fa tanulja "+200 után Short" ami ROSSZ mert uptrend korrekció, nem trendforduló. Short opposite 47.4%. Megoldás: Régime feature-ök (EMA_200, ADX, D1 slope, Z-score) → fa kondicionálja döntést uptrend kontextusban. Tréningablak: 2026-06(-318)→07(+70)→08(+384)→09(-100). Long/Short=1.25. V9: 23 feature, Long precision 51%, Short precision 39%.