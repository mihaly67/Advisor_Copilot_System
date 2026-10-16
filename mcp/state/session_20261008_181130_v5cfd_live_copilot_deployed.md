# Session: v5cfd_live_copilot_deployed
*Időbélyeg: 2026-10-08T18:11:30.374930*

# V5 CFD Live Copilot Deployed (2026-10-08)

## Telepített fájlok
1. **Copilot**: `/home/Jules/LGBM_mlops/Micro_LGBM/src/mt5_live_copilot_v5_cfd.py` (313 sor)
   - TCP:5555 (MacroReceiver — EA pivot adatok)
   - TCP:5556 (TickReceiver — tick → dollár bar → predikció)
   - ZMQ:5557 (HUD broadcast)
   - Model: `/data/dev/projects/z-ai-copilot/models/jules_cfd_v5/lgbm_v5.pkl` (binary LGBM, 16 feat)
   
2. **HUD**: `/home/Jules/LGBM_mlops/HUD_Development/hud_v5_cfd.py` (153 sor)
   - PyQt5 + lightweight_charts
   - Fő chart: ár OHLC + pivot vonalak (R-M/S-M/R-S/S-S/R-T/S-T) + Bid/Ask
   - Sub chart: P(Long) zöld, P(Short) piros + 0.50 küszöb vonal
   - Info sáv: signal + P(L)% + P(S)% + CUSUM irány + Fade irány

3. **Start script**: `/home/Jules/LGBM_mlops/start_v5_cfd.sh`
   - Leállítja a régi copilot/hud processzeket
   - Elindítja copilot-ot (jules_venv) → /tmp/v5cfd_copilot.log
   - Elindítja HUD-ot (jules_venv) → /tmp/v5cfd_hud.log

## Signal osztályozás
- **-1** = Short (🔴)
- **0** = No trade (⚪)  
- **+1** = Long (🟢)

## Fade CUSUM logika
- CUSUM UP event → Fade Short (-1)
- CUSUM DOWN event → Fade Long (+1)
- ML egyetért Fade-dzsel + conf > 0.10 → Fade irány
- ML ellenkezik + conf > 0.30 → ML irány
- Egyébként → Fade irány
- Nincs CUSUM event → ML dönt ha conf > 0.3, különben No trade

## Feature set (16)
S/R: Dist_Micro_R, Dist_Micro_S, Dist_Ter_R, Dist_Ter_S
Bar: Bar_Direction
CUSUM: CUSUM_Direction (online CUSUM filter)
Mom: Pulse_DF_Curve, Price_Velocity, Micro_RSI_14
Trend: Trend_EMA_Fast_Dist, Trend_EMA_Medium_Dist
Nav: DF_Direction=0, MACD_Direction=0, Nav_Consensus=0 (nincs live forrás)
Regime: Regime_ADX=0, Regime_Trending=0 (nincs live forrás)

## CUSUM filter
- Online implementáció (nem batch!)
- Threshold: daily_vol × avg_price × 1.5 (dynamikus, 50 bar warmup után)
- Forward-fill: utolsó ismert CUSUM irány kitölti a gap-eket

## Teszt eredmény (élő)
- EA csatlakozott: MACRO:5555 + TICK:5556 ✅
- Model betöltődött: LGBMClassifier 16 feats ✅
- HUD ZMQ connected: 5557 ✅
- Dollár bar-ok képződnek ✅
- Predikciók jönnek (P(L)≈50-57%, CUSUM még warmup) ✅

## Kihagyva (kérés szerint)
- Optuna hiperparaméter optimalizáció
- Shallow MLP (PyTorch)
