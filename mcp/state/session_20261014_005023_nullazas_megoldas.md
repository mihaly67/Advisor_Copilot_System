# Session: nullazas_megoldas
*Időbélyeg: 2026-10-14T00:50:23.028249*

Scalper nullázási probléma DIAGNÓZIS ÉS MEGOLDÁS:

PROBLÉMA: P(Long) és P(Short) egyidejűleg nullázódik (76.6% both<0.05)
GYÖKÉROK:
1. Túl ritka címkék: Long=1.28%, Short=0.46%, Skip=98.26%
   - horizon=6 + tp=12bps + sl=18bps → szinte soha nem targetolt
2. scale_pos_weight extrém: Long=77.4×, Short=216.4×
   - A modell megtanulta: "99%-ban semmi sem történik" → alaphelyzetben 0-ra predikál
3. Early stopping round 1-nél több foldban → modell alig tanult

MEGOLDÁS (3 lépcső):
1. SL csökkentése: 18→9bps (kevesebb skip, több pozitív label)
   - TP=7bps, SL=9bps → Long=5.5%, Short=3.3% (skip=91%)
2. is_unbalance=True scale_pos_weight helyett
   - LGBM saját balance logika, nem extrém súly
3. Label density penalty Optunában (<3% positive → penalty)

EREDMÉNY (h=6, tp=7, sl=9, sub=7, is_unbalance=True):
- Both<0.05: 76.6% → 4.4% ✅ (nullázás megszűnt!)
- P(Long) [0.00-0.05): 83.9% → 8.2% ✅
- P(Long) [0.10-0.20): leggyakoribb (29.3%) ✅ normális eloszlás
- Long AUC=0.748, Short AUC=0.817 (5-fold CV)
- Long thr=0.66, Short thr=0.62

Chart: candlestick + matches:"x2" sync + thr=0.40 display
255 Long + 2157 Short signals (2026-10-05)