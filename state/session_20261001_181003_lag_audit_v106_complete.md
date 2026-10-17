# Session: lag_audit_v106_complete
*Időbélyeg: 2026-10-01T18:10:03.714673*

LAG AUDIT v1.06 KÉSZ — VÉGSŐ KONKLÚZIÓ

## KÉRDÉS: "Ha 7 gyertyát csúsztatok, jó a fedés → lookahead bias?"

## VÁLASZ: NEM lookahead — INDIKÁTOR LAG! (bizonyítva)

### Teszteredmények:

**1. P(Long) vs FwdRet_1 cross-correlation:**
- Legjobb lag: -8 (r=0.2441) → P(Long) 8 bar-ral KÉSIK az árváltozás mögött
- Lag=0 (szinkron): r=-0.0112 → gyakorlatilag NINCS korreláció!
- Pozitív lag (lookahead): r≈0 mindenhol → NINCS előretekintés

**2. Feature-onkénti lag (melyik mennyit késik):**
- PastRet_1: -2 bar (gyors)
- RSI_Fast_5: -2 bar (gyors)
- Micro_RSI_14: -2 bar (gyors)
- Pulse_MACD_Hist: -3 bar (közepes)
- Stoch_D: -4 bar (közepes)
- EMA50_Slope_Up: -6 bar (lassú)
- Slope_Close_14: -8 bar (lassú!) ← a fő "bűnös"
- MomScore_14: -8 bar (lassú!)
- Pulse_DF_Curve: -8 bar (lassú!)

**3. Forward Win Rate (valós predikció lag=0-nál):**
- P(Long)>0.75: 1,870 trades → Fwd WR=48.2%
- P(Short)>0.75: 2,852 trades → Fwd WR=50.1%
- → VÉLETLENSZINT! Nincs valós prediktív erő a KÖVETKEZŐ bar-ra!

**4. Shuffled kontrol:** lag=13, r=0.022 → zaj, a valós -8 lag szignifikáns

### KÓDBIZONYÍTÉK:
- dom_feature_engineer_mtf.py: MINDEN feature .shift(1)-elve (line 7: "Anti-lookahead")
- v102 leakage audit: "Feature lookahead: NINCS — Slope_Close_14 vs Close[i] corr=-0.002"

### MIÉRT PONT 8 BAR LAG?
14 periódusú rolling ablak → félúton (~7 bar) van a simítási késleltetés
Slope_Close_14 és MomScore_14: 14 bar lineáris regresszió → ~7-8 bar lag

### VALÓS PROBLÉMA (nem lookahead!):
- Forward WR≈49% → a modell NEM tudja megjósolni a KÖVETKEZŐ bar irányát!
- A 61.2% WR a LABEL-ből jön (ami 5 perc előre néz triple barrier-rel)
- Label WR ≠ Forward WR — ez a korábbi audit is bizonyította (v1.04 WR=60.9% de forward=49.7%)
- Az "ellentétes trend belépő jelzések" a lag-ból jön: mire jelez, a trend már 8 bar-ja tart

### MEGOLDÁS:
1. Gyorsabb indikátorok: RSI_3, Slope_5, Momentum_3 → lag csökkentése
2. Feature lag kompenzálás: lassú feature-ök shift-elése hogy "gyorsabban" reagáljanak
3. Multi-speed ensemble: gyors modell (5-periódusú) + lassú modell (14-periódusú)

### FÁJLOK:
- /data/dev/projects/z-ai-copilot/src/lag_audit_v106.py (ez a szkript)
- /data/dev/projects/z-ai-copilot/models/v106/lag_audit_results.json (eredmények)