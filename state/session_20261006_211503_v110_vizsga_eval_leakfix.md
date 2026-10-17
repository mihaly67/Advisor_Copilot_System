# Session: v110_vizsga_eval_leakfix
*Időbélyeg: 2026-10-06T21:15:03.713418*

V110 VIZSGA EVAL — LEAKFIX + VIZSGA CSV EREDMÉNYEK

FÁZIS 1: Modell training CSV direkt (leakfix)
- 122,229 bars (2026-06-16 → 2026-09-01)
- 18 feature (10 orig CSV-ből direkt + 8 direction)
- Lookahead sanity check: MINDEN corr < 0.003 → ✅ NINCS lookahead
- OOS: WR=53.7% P=$2,814 T=8,191 (vs előző 56.0% lookahead-dal!)
- Opposite swaps: 2,374 (35.0%)

FÁZIS 2: Vizsga CSV (független, 2026-07-20 → 07-23)
- 2,047 labeled bars (2,152 dollar bars, avg 157.4 sec/bar)
- VIZSGA: WR=42.0% P=$55 T=1,100
- Opposite swaps: 399 (46.3%)
- Konfúzió: Noise oszlop ÜRES (0) — a modell NEM jósol Noise-t sosem!

FÁZIS 3: Összehasonlítás
- OOS WR: 53.7% vs Vizsga WR: 42.0% → GAP = +11.7% 🚨 NAGY GAP!
- Overfitting erősítve

KULCS FELISMERÉSEK:
1. Leakfix WR=53.7% (vs előző 56.0%) → a lookahead ~2.3% WR-t adott!
2. Vizsga WR=42.0% → a modell a vizsgán rosszabb mint véletlen!
3. 11.7% gap → erős overfitting az OOS-ra
4. A modell SOSEM jósol Noise-t (konfúzió Noise oszlop = 0)
5. Dollar bar threshod $1.746M túl nagy a vizsgán (157 sec/bar vs 45 sec/bar)
6. Vizsga időszak (07.20-23) lehet más piaci rezsime

KÖVETKEZŐ LÉPÉSEK:
1. Dollar bar threshold kalibrálás a vizsgára (lehet kisebb kell)
2. Vizsga-adatos dollar bar threshold auto-detect
3. Noise osztály javítása (threshold, vagy 2-osztályú modell)
4. Walk-forward validáció
5. Dir_Conviction feature implementálása

MENTVE:
- Script: /data/dev/projects/z-ai-copilot/src/v110_vizsga_eval.py
- Model: /data/dev/projects/z-ai-copilot/models/v110_vizsga/lgbm_18feat_leakfix.pkl
- Viz: /data/dev/projects/z-ai-copilot/docs/v110_vizsga/ (3 HTML)
- JSON: /data/dev/projects/z-ai-copilot/docs/v110_vizsga/vizsga_results.json