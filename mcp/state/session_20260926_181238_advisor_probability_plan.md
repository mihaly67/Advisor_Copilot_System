# Session: advisor_probability_plan
*Időbélyeg: 2026-09-26T18:12:38.740379*

PROJEKT CÉL: Emberi döntéstámogatás — valószínűség-görbe P(Long)/P(Short)/P(Noise) + threshold szintek.

MEGLÉVŐ ARCHITEKTÚRA:
- MT5 EA → TCP 5555 → Python Copilot → ZMQ PUB 5557 → HUD (PyQt5)
- Copilot: mt5_live_copilot_v2.0_no_stoch.py — 10 feature LGBM, predict_proba → P(Long)/P(Short)/P(Noise)
- HUD: hud_v1.17_nn.py — P(Long)/P(Short)/P(Noise) görbék + threshold vonalak + pivot szintek

FEATURE-ÖK AMIK ÉRNEK:
1. NavSystem 11 indikátor (Pulse/Flow/Momentum/RSI) — értékük + zero/közép pont = irányjelzés
2. Pivot távolságok (6 db Dist_*_ATR) — közelség = reakció valószínűség
3. Pivot interakció ESEMÉNYEK (12 db Wick_Rej/Breakout/Bnc/Breakdown) — 54-57% WR
4. Pivot velocity (6 db *_Vel) — mozgás iránya a pivot felé/ellene
5. Trend_Strength_20 — hosszabb távú trend kontextus

LABELING: v3 slope-anchored — triple barrier + slope anchoring → WR 60.8%

MIT KELL MÓDOSÍTANI:
1. Copilot feature lista bővítése: 10 → 20-22 feature (FEATURES_V7 42-ből a legfontosabbak)
2. Modell újra tanítása a bővített feature listával
3. Threshold szintek Optuna kalibrációja (th_long, th_short, th_noise)
4. HUD: NavSystem indikátor panel hozzáadása (minden indikátor értéke + zero vonal)

KULCS FELISMERÉS: Az indikátorok ZERO/KÖZÉP pontja = Noise szűrő. Ha az indikátor a közép körül van → NINCS irányjelzés. Ha az indikátor az extrémum felé mozog → irányjelzés.
- RSI ≈ 50 → Noise
- WPR ≈ -50 → Noise
- Stoch K ≈ 50 → Noise
- MFI ≈ 50 → Noise
- MACD_Hist ≈ 0 → Noise