# Session: mh_chart_3horizon
*Időbélyeg: 2026-10-14T21:49:32.461823*

Scalper Copilot v4.0 — Multi-Horizon Chart kesz (scalper_copilot_chart_mh.py)

Layout (1100px):
- yaxis  [0.40, 1.00] — Price candlestick + markerek + zaj
- yaxis2 [0.27, 0.37] — 1min P(Long)/P(Short) 
- yaxis3 [0.14, 0.24] — 2min P(Long)/P(Short)
- yaxis4 [0.01, 0.11] — 3min P(Long)/P(Short)

File: /data/LGBM_copilot/src/scalper_copilot_chart_mh.py
Chart: /data/LGBM_copilot/charts/BTCUSD_copilot_v4_mh_2026-10-07.html (2445KB)

Szignál stat (2026-10-07):
- 1min: L=2656 S=4457 Skip=8347  P(S)>P(L): 70.8%
- 2min: L=3622 S=5461 Skip=6377  P(S)>P(L): 49.8% (legkiegyenlítettebb!)
- 3min: L=263  S=10814 Skip=4383 P(S)>P(L): 76.9% (short dominancia!)

Kulcs felismeres: 2min a legkiegyenlítettebb horizon, a short modell 
bar_dt alapu panik-detektorkent mukodik, tiszta trendben ellentetes 
szignálokat ad (mean-reversion). ICT feature-k (FVG, OrderBlock, 
LiqSweep) hianyzanak — ezek direkten iranyt adnanak.