# Session: v3_audit_fix_final
*Időbélyeg: 2026-10-11T00:52:02.035601*

PIPELINE V3 AUDIT + FIX — VÉGLEGES EREDMÉNYEK

AUDIT TALÁLATOK:
1. ✅ Feature computation: Nincs look-ahead (shift(1) minden feature-n)
2. ✅ Triple Barrier: Look-ahead by design (helyes), purged CV embargo=10 kezeli
3. ✅ RankGauss: fit csak train-en → nincs leakage
4. ✅ Dollar bar threshold: offline artifact, minimális impact
5. 🚨 S/R Distribution Shift: Scalper_Copilot S/R más skálájú mint enrich swing S/R
   - 2025: Dist_SR_ATR std=40.83 (Scalper_Copilot) vs 1.62 (enrich swing)
   - Fix: S/R MINDIG újraszámoljuk, soha nem smart_fill Scalper_Copilot S/R-t
   - Eredmény: perm_z 120→57 (XAUUSD), AUC realisztikusabb

VÉGLEGES EREDMÉNYEK (S/R always recomputed):
  XAUUSD: MLP=0.877 LGBM=0.883 ENS=0.886 OOS=0.863±0.008 perm_z=57.2
  BTCUSD: MLP=0.874 LGBM=0.877 ENS=0.882 OOS=0.856±0.011 perm_z=33.6

FEATURE IMPORTANCE (konzisztens mindkét instrumentum):
  XAUUSD top 5: consecutive_f(0.138), delta_pivot_dist(0.082), body_sign_f(0.054), delta_sr_zone_sec(0.052), PastRet_2_f(0.050)
  BTCUSD top 5: consecutive_f(0.130), delta_pivot_dist(0.067), delta_sr_zone_sec(0.056), body_sign_f(0.055), trend_micro(0.052)

FÁJLOK:
  src/enrich_dollar_bars.py — S/R MINDIG újraszámoljuk (nincs smart_fill S/R-re)
  src/gen_dollar_bars_instrument.py — instrument-független dollár bar
  src/run_pipeline.py — orchestrátor (gen_dollar_bars → enrich → pipeline_v14)
  src/pipeline_v14.py — instrument param, MLP+LGBM ensemble

KÖVETKEZŐ:
  - run_pipeline.py párhuzamos futtatás (XAUUSD BTCUSD)
  - MQ5 Collect script → M1_History_{INSTRUMENT}.csv (már instrument-független)
  - Új instrument hozzáadása: csak M1_History kell, a több automatikus