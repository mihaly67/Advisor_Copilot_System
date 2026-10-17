# Session: norm_ablation_study_complete
*Időbélyeg: 2026-10-05T21:02:29.031715*

NORMALIZÁLÁS ABLATION STUDY KÉSZ (55s)

4 KONFIGURÁCIÓ EREDMÉNYEK (OOS, 24,446 bars):
  A: ATR_norm         WR=54.0% P=$2844 T=8138  (baseline)
  B: raw_pct          WR=53.0% P=$2606 T=7989  (ATR nélkül)
  C: raw_pct_stoch    WR=49.7% P=$598  T=2474  (nyers + Stoch)
  D: ATR_norm_stoch   WR=50.3% P=$659  T=2561  (ATR + Stoch)

FŐ FELISMERÉSEK:
1. ATR normalizálás JO: +1.0% WR, +$238 profit vs nyers %
2. Stoch irány-kizáró KÁROS: -2.1% WR, -$2063 profit (nyeres)
3. Stoch irány-kizáró KÁROS: -2.2% WR, -$2177 profit (ATR)
4. A legjobb: A_ATR_norm (baseline) = ATR norm + Stoch KI

FEATURE STAT: ATR normalizált std 8-26x nagyobb mint raw % std
  → ATR skálázás jobb LGBM separabilitást ad
  → Raw % értékek túl kis tartomány (0.001-0.007)

KONFÚZIÓ: Mindegyik config "Actual Noise" oszlop = 0
  → A modell sosem jósol Noise-t (csak Short/Long)
  → Opposite swap (S→L + L→S): A=2206, B=2311, C=796, D=789
  → Stoch drasztikusan csökkenti opposite-t, de WR is zuhan

KIMENET:
  Script: /data/dev/projects/z-ai-copilot/src/norm_ablation_study.py
  Viz: /data/dev/projects/z-ai-copilot/docs/v110_ablation/
  Models: /data/dev/projects/z-ai-copilot/models/v110_ablation/