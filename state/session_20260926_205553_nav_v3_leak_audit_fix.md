# Session: nav_v3_leak_audit_fix
*Időbélyeg: 2026-09-26T20:55:53.213323*

ADATSIVÁRGÁS AUDIT + MEGOLDÁS (NavSystem v3):

AUDIT EREDMÉNY:
1. Feature shift: ✅ Minden |r(fwd0)| < |r(fwd1)| — nincs klasszikus lookahead
2. Pivot interakciók: ✅ Nincs szivárgás
3. Oversold: ✅ WR(fwd1) > WR(fwd0)
4. Nav_Consensus ↔ Slope_Close_14: ⚠️ r=+0.44 → proxy szivárgás a label-hez
5. Label → fwd5 WR: 🔴 80% → label túl informatív

MEGOLDÁS:
1. Nav_Consensus, Nav_LongVotes, Nav_ShortVotes kiszedve (54→51 feature)
2. Dupla shift javítás: build script .shift(1) ELTÁVOLÍTVA, csak to_lgbm_features shift(1)
3. Full Fix modell (models/nav_v3_fix/): OOS 7957 trades, WR=46.4%, P=+3128, acc=56.4%
4. Oversold WR=53.2% — IGAZI JEL (nem szivárgás)
5. SHAP top: Stoch_Oversold, Stoch_Intensity, MACD_Direction, MACD_Accel

KONKLÚZÓ: A "túl jó" eredmények NEM szivárgásból jöttek, hanem a label informativitásából. A proxy kiszedése nem rontja a modellt. A dupla shift javítás 1 bar frissebb adatot ad a feature-öknek.