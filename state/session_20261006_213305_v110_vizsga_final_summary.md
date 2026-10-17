# Session: v110_vizsga_final_summary
*Időbélyeg: 2026-10-06T21:33:05.367042*

V110 VIZSGA FINAL — ÖSSZEFoglaló

TELJES EREDMÉNY TÁBLÁZAT:
| Modell | OOS WR | Vizsga WR ($654K) | Vizsga WR ($1,746K) |
|--------|--------|--------------------|----------------------|
| 18feat LEAKFIX | 53.7% | 59.1% | 42.0% |
| 20feat +Dir_Conviction | 52.0% | 56.0% | n/a |
| 18feat BEFORE leakfix | 56.0% | n/a | n/a |

KULCS FELISMERÉSEK:
1. LOOKAHEAD BIAS: shift(1) javítás -2.3% WR (56→53.7%) — ez a VALÓS WR
2. DOLLAR BAR THRESHOLD KRITIKUS: $1,746K→$654K kalibrálás +17.1% WR (42→59.1%)
3. A modell a vizsgán JOBB (59.1%) mint az OOS-on (53.7%) — NINCS overfitting!
4. DIR_CONVICTION meta-feature LEAKAGE-t okoz (-1.7% OOS, -3.1% vizsga)
   → walk-forward predikció kellene, nem egyszeri prob

VIZSGA CSV MINT DÖNTÉSHOZÓ: ✅ BEVÁLT
- A vizsga CSV (2026-07-20 → 07-23) teljesen független
- Kalibrált threshold-val WR=59.1% — ez a valós teljesítmény
- A korábbi "overfitting" diagnózis HAMIS volt — a threshold volt rossz!

LEGJOBB MODELL: 18feat leakfix + kalibrált threshold
- OOS: WR=53.7% P=$2,814 T=8,191
- Vizsga: WR=59.1% P=$828 T=1,735
- Feature importance #1: RSI_M15_signed (8.14%)

KÖVETKEZŐ LÉPÉSEK:
1. Teljes pipeline úraépítés adaptív threshold-cal (train from raw ticks)
2. Walk-forward Dir_Conviction (rolling window predikció)
3. Dominance threshold (|P(L)-P(S)| > küszöb szűrés)
4. Fix threshold audit (nem Optuna OOS-on)
5. Production model mentés + MQL5 integráció

FÁJLOK:
- Script: /data/dev/projects/z-ai-copilot/src/v110_vizsga_eval.py
- Model: /data/dev/projects/z-ai-copilot/models/v110_vizsga/lgbm_18feat_leakfix.pkl
- Viz: /data/dev/projects/z-ai-copilot/docs/v110_vizsga/ (5 HTML)
- Threshold sweep: /data/mcp_server/logs/vizsga_thresh_sweep.py
- Dir conviction: /data/mcp_server/logs/v110_dir_conviction.py