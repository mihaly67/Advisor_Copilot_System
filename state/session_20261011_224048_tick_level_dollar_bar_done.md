# Session: tick_level_dollar_bar_done
*Időbélyeg: 2026-10-11T22:40:48.648016*

LGB Copilot BTCUSD — TICK SZINTŰ DOLLÁR BAR (+3 predikció/perc)

## A KULCS FELISMERÉS:
A Scalper EA TICK-eket küld (5556 port) → dollár bar TICK szinten épül!
NEM M1 gyertyazárás, hanem dollár bar completion = predikció pont!

## Jules régi rendszere (mt5_live_copilot_v5_cfd.py):
- DOLLAR_BAR_THRESHOLD = $444K (XAUUSD tick szint)
- Tick érkezik → cumsum += mid_price
- Ha cumsum >= threshold → dollár bar complete → feature + predict + broadcast
- XAUUSD: ~0.36 bar/perc ($444K threshold CSV adatból)
- Élőben: több tick → több bar/perc!

## ÚJ BTCUSD beállítások:
- DOLLAR_BAR_THRESHOLD = $1,041,000 (tick szintű)
- 332,642 bar (77 nap) → 4,320 bar/nap → 3.0 bar/perc
- Duration medián: 17s (!!!) — 17 másodpercenként predikció
- Ticks/bar medián: 16 — 16 tick-enként zárul egy dollár bar
- Direction: +1=167,480 -1=165,162 (kiegyensúlyozott)
- ATR: mean=$25.30 median=$22.78

## TB Címkézés (PT=1.5×ATR, SL=1.0×ATR, max=20 bar):
- TP: 122,290 (36.8%), SL: 210,332 (63.2%)
- Long: 36.7% TP, Short: 36.9% TP
- Avg bars TP: 5.2, SL: 3.8

## Config:
- DOLLAR_BAR_TARGET_BPM = 3  (bar/perc = predikció/perc)
- DOLLAR_BAR_THRESHOLD = 1,041,000
- PREDICT_MODE = 'dollar_bar'
- 01_gen_dollar_bars.py: TICK szintű (Scalper CSV Bid/Ask)

## Viz (2026-07-15): 4,223 bar, TP=1568 SL=2655
