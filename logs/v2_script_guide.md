# Scalper_Copilot_Miner_v2 — Fordítási és futtatási útmutató

## Állapot
- **Script**: `/home/Jules/.wine/drive_c/Program Files/MetaTrader 5 IC Markets EU/MQL5/Scripts/Scalper_Copilot_Miner_v2.mq5`
- **Fordítás**: 0 errors, 1 warning (2026-10-04 15:57)
- **.ex5**: 14878 bájt

## Előző futás eredménye (RÉGI verzió)
- CSV: 4,150,493 sor (1 másodperc = 1 sor)
- **Bid_Volume = 0.0, Ask_Volume = 0.0 MINDENHOL**
- Ok: XAUUSD CFD tick-jein nincs TICK_FLAG_BUY/SELL flag
- Csak TICK_FLAG_BID/TICK_FLAG_ASK van (árajánlat-frissítés)

## JAVÍTOTT verzió (BID/ASK flag alapú proxy)
- BUY/SELL flag → Ask/Bid ticks (ha van)
- **ASK flag → Ask ticks (vevő nyomás)**
- **BID flag → Bid ticks (eladó nyomás)**
- Ha semmi flag → 50/50 split
- InpUseTickProxy=true → ha volume_real=0, tick-count proxy-t használ

## Futtatás MT5-ben
1. Nyisd meg az XAUUSD M1 chartot
2. Navigator → Scripts → Scalper_Copilot_Miner_v2
3. Drag & drop a chart-ra
4. Input ablak: InpStartDate=2026.06.16, InpEndDate=2026.09.01, InpUseTickProxy=true
5. OK → script fut (~2 perc)
6. Eredmény: MQL5/Files/Scalper_Copilot_MTF_Data_v2.csv
