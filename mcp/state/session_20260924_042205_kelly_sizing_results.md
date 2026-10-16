# Session: kelly_sizing_results
*Időbélyeg: 2026-09-24T04:22:05.551163*

Kelly position sizing implementálva és tesztelve (meta_v1, $444K, 30 feature).

Eredmények:
- FLAT 1%: Profit=32.4, Sharpe=5.55, 6168 trade
- Kelly 0.25x: Profit=230.5, Sharpe=5.45, 6168 trade, AvgSize=6.61%
- Kelly 0.25x th0.45: Profit=216.0, Sharpe=5.75, 5104 trade, Win=51.5%
- Kelly 0.25x th0.50: Profit=162.8, Sharpe=6.18, 3133 trade, Win=52.6%
- Kelly+Conf th0.45: Profit=208.6, Sharpe=5.76, 5104 trade

$222K threshold: rontott (AUC 0.533→0.523, Win 50.8%→47.6%). Visszatérés $444K.

P(trade) distribution nagyon szűk: 25th=0.464, 75th=0.542 — modell probabilities túl közel 0.5-hez.
Long/Short szimmetrikus: Long 50.9%, Short 50.8% — nincs aszimmetria.
Kelly 0.25x = 7x profit flat-hoz képest.