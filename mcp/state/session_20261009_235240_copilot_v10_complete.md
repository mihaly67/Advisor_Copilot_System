# Session: copilot_v10_complete
*Időbélyeg: 2026-10-09T23:52:40.675115*

COPILOT V10 KÉSZ

copilot_v10.py — teljes pipeline + extrém súlyozás + predikció/zaj, görbe + HANG

Extrém súlyozás 3 mód:
- sigmoid (gamma=20): smooth transition, threshold körül éles
- power (gamma=3): (p-th)^γ — ultra-szelektív, csak 0.50+ felett aktiv
- step: bináris 0/1

Pozíció sizing: lot = 0.01 * sigmoid_weight * 10 (max 0.10 lot)

Predikció vs Zaj görbe — KEY RESULT:
LONG:
  [0.30-0.35): Win=1.8% vs Zaj=21% → ❌ ZAJ (PnL=-6.8%)
  [0.40-0.45): Win=55% vs Zaj=22% → ⚠️ FIGYEL (PnL=+1.5%)
  [0.45-0.50): Win=85% vs Zaj=30% → ✅ TRADE (PnL=+5.9%)
SHORT:
  [0.38-0.41): Win=56% vs Zaj=21% → ⚠️ FIGYEL (PnL=+2.8%)
  [0.41-0.44): Win=85% vs Zaj=24% → ✅ TRADE (PnL=+6.0%)

A modell 0.40+ felett kezd kilépni a zajból — 37% pont differencia signal vs zaj!

Fájlok:
- src/copilot_v10.py — copilot script
- models/v10/copilot_predictions.csv — 2,642 event predikciók
- models/v10/viz_curves.csv — predikció/zaj görbe adat