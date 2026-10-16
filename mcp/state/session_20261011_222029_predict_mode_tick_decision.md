# Session: predict_mode_tick_decision
*Időbélyeg: 2026-10-11T22:20:29.984181*

LGB Copilot BTCUSD — PREDIKCIÓ FREKVENCIA DÖNTÉS

## DÖNTÉS: TICK SZINTŰ PREDIKCIÓ

NEM M1 bar completion, NEM dollár bar completion — MINDEN TICK-RE!

### Érvek:
- Ez COPILOT, nem robot — a trader folyamatosan látja P(Long), P(Short)
- XAUUSD scalper legalább 3 predikció/perc volt
- BTCUSD ~50 tick/perc → minden tick = új predikció
- LGBM inference ~0.05ms, feature ~0.5ms → 0.6ms total
- Tick-ek 1-2 sec-enként → bőven belefér

### Architektúra:
- TANÍTÁS: dollár bar-on (100 bar/nap, 10perc/bar, TB label)
- ÉLŐ PREDIKCIÓ: TICK szinten (EA küld tick → feature + predict → HUD)
- Throttle: minimum 500ms predikciók között (ne terhelje CPU)

### Config:
  PREDICT_MODE = 'tick'
  PREDICT_MIN_INTERVAL_MS = 500

### LGBM a középpont:
- MLP később, párhuzamosan, függetlenül
- Irány + pivot + rezsim figyelés → később
- Most: LGBM only, KÉT modell (long + short)
