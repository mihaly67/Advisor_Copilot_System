# Session: oos_vizsga_final
*Időbélyeg: 2026-10-11T01:18:48.734040*

SOSEM LÁTOTT OOS VIZSGA — VÉGLEGES EREDMÉNY

XAUUSD (5 nap, 2026-09-14..18): AUC=0.868 (MLP=0.856, LGBM=0.862, Ens=0.868)
BTCUSD (4 nap, 2026-10-05..08): AUC=0.883 (MLP=0.866, LGBM=0.879, Ens=0.883)

Tréning OOS CV vs Sosem látott:
  XAUUSD: 0.863 → 0.868 (+0.005) ✅ Nincs drop
  BTCUSD: 0.856 → 0.883 (+0.027) ✅ Nincs drop

KULCS FIX: Scalper_Copilot sub-minute adat → M1 resample → tréning threshold dollár bar
  - Scalper ~52 sor/perc, M1 = 1 sor/perc
  - Resample: raw['Bid'].resample('1min').agg(OHLC)
  - Threshold: tréning M1 History-ból számolva (XAUUSD=$4,435, BTCUSD=$165,789)

SCRIPT: src/oos_vizsga.py (teljes instrument-független OOS vizsga)
  - M1 resample → dollár bar (tréning threshold) → enrich → modell → AUC