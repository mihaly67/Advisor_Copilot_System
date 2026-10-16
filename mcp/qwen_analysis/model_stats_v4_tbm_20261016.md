Loading predictions: /data/LGBM_copilot/models/scalper/BTCUSD_v4_preds_20261016_015348.csv
  68568 rows loaded

======================================================================
1. ALAPVETO ADATSTATISZTIKA
======================================================================
  Verzio: scalper_copilot_v4.0_TBM
  Instrument: BTCUSD
  Osszes bar: 68717
  Osszes sample: 68568
  Feature-k szama: 50
  Dollar threshold: $10M
  TP dollar: $50
  Profit mult (PT): 1.5xATR
  Stop mult (SL): 1.0xATR
  CUSUM filter: BE
  Noise mean: 0.001235
  Noise std: 0.000402
  Noise weight: 50
  Predikcio: 2026-10-05 00:16:40 -> 2026-10-08 23:58:44
  Idotartam: 3 days 23:42:04

======================================================================
2. WF AUC ES LABEL RATA (TBM cimkezes)
======================================================================

  1min (60s):
    Long  AUC: 0.5549  | Short AUC: 0.5345  | Delta: +0.0205
    Long  Thr: 0.200 (adaptiv: 0.2124)
    Short Thr: 0.200 (adaptiv: 0.2124)
    Label LR: 0.4126 (41.3% TP) | SR: 0.4102 (41.0% TP)
    SL rata: Long 58.7% | Short 59.0%

  2min (120s):
    Long  AUC: 0.5475  | Short AUC: 0.5467  | Delta: +0.0007
    Long  Thr: 0.200 (adaptiv: 0.2124)
    Short Thr: 0.400 (adaptiv: 0.4247)
    Label LR: 0.4324 (43.2% TP) | SR: 0.4292 (42.9% TP)
    SL rata: Long 56.8% | Short 57.1%

  3min (180s):
    Long  AUC: 0.5497  | Short AUC: 0.5440  | Delta: +0.0056
    Long  Thr: 0.200 (adaptiv: 0.2124)
    Short Thr: 0.400 (adaptiv: 0.4247)
    Label LR: 0.4364 (43.6% TP) | SR: 0.4331 (43.3% TP)
    SL rata: Long 56.4% | Short 56.7%

======================================================================
3. SIGNAL ELOSZLAS (predikciok statisztikaja)
======================================================================

  1min:
    Valid predikciok: 68509 / 68568 (99.9%)
    Long  jelek: 48467 (70.68%)
    Short jelek: 20042 (29.23%)
    Flat  jelek: 59 (0.09%)
    P(Long)  — mean: 0.4783, std: 0.0507, min: 0.2698, max: 0.6536, median: 0.4826
    P(Short) — mean: 0.4447, std: 0.0280, min: 0.2833, max: 0.5243, median: 0.4490
    P5: L=0.3876 S=0.3924
    P25: L=0.4464 S=0.4275
    P50: L=0.4826 S=0.4490
    P75: L=0.5148 S=0.4662
    P95: L=0.5533 S=0.4823
    P(L)>P(S): 48467 (70.7%) | P(S)>P(L): 20042 (29.3%)

  2min:
    Valid predikciok: 68509 / 68568 (99.9%)
    Long  jelek: 41719 (60.84%)
    Short jelek: 26668 (38.89%)
    Flat  jelek: 181 (0.26%)
    P(Long)  — mean: 0.4614, std: 0.0217, min: 0.3943, max: 0.5851, median: 0.4608
    P(Short) — mean: 0.4483, std: 0.0178, min: 0.3252, max: 0.5186, median: 0.4504
    P5: L=0.4277 S=0.4174
    P25: L=0.4458 S=0.4379
    P50: L=0.4608 S=0.4504
    P75: L=0.4755 S=0.4614
    P95: L=0.4974 S=0.4719
    P(L)>P(S): 41719 (60.9%) | P(S)>P(L): 26790 (39.1%)

  3min:
    Valid predikciok: 68509 / 68568 (99.9%)
    Long  jelek: 44342 (64.67%)
    Short jelek: 24049 (35.07%)
    Flat  jelek: 177 (0.26%)
    P(Long)  — mean: 0.4697, std: 0.0240, min: 0.4016, max: 0.6008, median: 0.4689
    P(Short) — mean: 0.4514, std: 0.0178, min: 0.3248, max: 0.5198, median: 0.4537
    P5: L=0.4326 S=0.4210
    P25: L=0.4520 S=0.4407
    P50: L=0.4689 S=0.4537
    P75: L=0.4858 S=0.4642
    P95: L=0.5101 S=0.4757
    P(L)>P(S): 44342 (64.7%) | P(S)>P(L): 24167 (35.3%)

======================================================================
4. KERESZT-HORIZON KONZISZTENCIA
======================================================================

  1min vs 2min:
    Egyezes: 57489 (83.9%)
    Mindketto non-zero: 68387
    Konszenzus: 57489 (84.1%) | Konfliktus: 10898 (15.9%)

  2min vs 3min:
    Egyezes: 63414 (92.6%)
    Mindketto non-zero: 68349
    Konszenzus: 63334 (92.7%) | Konfliktus: 5015 (7.3%)

  1min vs 3min:
    Egyezes: 58959 (86.1%)
    Mindketto non-zero: 68391
    Konszenzus: 58959 (86.2%) | Konfliktus: 9432 (13.8%)

  3-way konszenzus:
    Mindharom non-zero: 68349
    Mindharom egyezik: 55687 (81.5%)

======================================================================
5. FEATURE IMPORTANCE ELEMZES
======================================================================

  long_1min — Top 10 (total: 28726):
    ret_1                          2774.8  (  9.7%)
    bar_dt                         2110.7  (  7.3%)
    atr_pct                        1846.0  (  6.4%)
    body                           1147.4  (  4.0%)
    skew_60                        1081.9  (  3.8%)
    bar_dt_rel                     1024.2  (  3.6%)
    vol_ma_5                        812.6  (  2.8%)
    skew_20                         807.8  (  2.8%)
    ret_3                           805.8  (  2.8%)
    poc_dist                        781.9  (  2.7%)

  short_1min — Top 10 (total: 15483):
    ret_1                          1773.8  ( 11.5%)
    bar_dt                         1509.3  (  9.7%)
    bar_dt_rel                      951.7  (  6.1%)
    skew_60                         818.7  (  5.3%)
    flow_delta                      731.7  (  4.7%)
    atr_pct                         646.6  (  4.2%)
    rv_60                           632.2  (  4.1%)
    pv_corr                         452.6  (  2.9%)
    body                            390.9  (  2.5%)
    ret_3                           374.5  (  2.4%)

  long_2min — Top 10 (total: 11085):
    ret_1                          1917.4  ( 17.3%)
    atr_pct                         560.3  (  5.1%)
    skew_60                         487.1  (  4.4%)
    flow_delta                      417.5  (  3.8%)
    ret_3                           372.5  (  3.4%)
    pv_corr                         345.4  (  3.1%)
    vol_ma_5                        309.3  (  2.8%)
    skew_20                         287.4  (  2.6%)
    body                            253.0  (  2.3%)
    poc_dist                        253.0  (  2.3%)

  short_2min — Top 10 (total: 7470):
    ret_1                          1696.6  ( 22.7%)
    skew_60                         509.6  (  6.8%)
    flow_delta                      477.6  (  6.4%)
    rv_60                           270.6  (  3.6%)
    poc_dist                        240.1  (  3.2%)
    bar_range                       216.7  (  2.9%)
    ret_3                           210.5  (  2.8%)
    atr_pct                         202.8  (  2.7%)
    body                            171.4  (  2.3%)
    pv_corr                         165.4  (  2.2%)

  long_3min — Top 10 (total: 12281):
    ret_1                          2253.1  ( 18.3%)
    atr_pct                         595.0  (  4.8%)
    skew_60                         573.6  (  4.7%)
    flow_delta                      533.9  (  4.3%)
    ret_3                           392.5  (  3.2%)
    bar_range                       369.0  (  3.0%)
    skew_20                         368.3  (  3.0%)
    pv_corr                         347.8  (  2.8%)
    poc_dist                        332.2  (  2.7%)
    rv_10                           289.4  (  2.4%)

  short_3min — Top 10 (total: 7197):
    ret_1                          1719.3  ( 23.9%)
    skew_60                         492.9  (  6.8%)
    flow_delta                      362.4  (  5.0%)
    rv_60                           213.0  (  3.0%)
    atr_pct                         191.2  (  2.7%)
    poc_dist                        189.6  (  2.6%)
    ema_fast_slope                  185.3  (  2.6%)
    bar_range                       176.4  (  2.5%)
    skew_20                         173.0  (  2.4%)
    ret_2                           165.1  (  2.3%)

  --- Feature rangsor stabilitas ---
  Legstabilabb (kis rang-variancia 6 modellben):
    ret_1                      rangok: [0, 0, 0, 0, 0, 0]  var: 0.0
    skew_60                    rangok: [4, 3, 2, 1, 2, 1]  var: 1.1
    rsi_28                     rangok: [46, 43, 45, 41, 44, 43]  var: 2.6
    htf_trend                  rangok: [44, 42, 47, 43, 45, 47]  var: 3.6
    cum_dir_10                 rangok: [49, 48, 49, 44, 49, 46]  var: 3.6
    mom_persistence            rangok: [48, 47, 48, 48, 47, 42]  var: 4.6
    atr_pct                    rangok: [2, 5, 1, 7, 1, 4]  var: 4.9
    ret_20                     rangok: [36, 30, 33, 32, 32, 29]  var: 5.0
    skew_20                    rangok: [7, 14, 7, 11, 6, 8]  var: 7.8
    vol_ret_5                  rangok: [43, 40, 39, 46, 46, 45]  var: 7.8
  Leginstabilabb:
    lower_wick                 rangok: [34, 45, 41, 36, 41, 23]  var: 50.2
    rpos_60                    rangok: [42, 32, 36, 20, 35, 25]  var: 52.9
    ema_fast_slope             rangok: [27, 19, 26, 10, 24, 6]  var: 64.6
    df_curve                   rangok: [33, 25, 37, 33, 10, 26]  var: 77.6
    vol_ma_5                   rangok: [6, 18, 6, 17, 11, 35]  var: 98.2
    hour_sin                   rangok: [29, 12, 42, 26, 37, 20]  var: 100.2
    fvg_size                   rangok: [14, 46, 16, 42, 30, 48]  var: 188.9
    bar_dt                     rangok: [1, 1, 22, 13, 36, 37]  var: 217.2

======================================================================
6. FEATURE KATEGORIA ELEMZES
======================================================================

  long_2min — Kategoria osszesites:
    Return                imp:   2940.5  ( 26.5%)  [6/6 feat]
    Volatility            imp:   2413.9  ( 21.8%)  [10/10 feat]
    Skewness              imp:    774.5  (  7.0%)  [2/2 feat]
    Microstructure        imp:   1569.6  ( 14.2%)  [8/8 feat]
    Order Flow            imp:    708.0  (  6.4%)  [3/3 feat]
    Momentum              imp:    784.2  (  7.1%)  [8/8 feat]
    EMA Slope             imp:    317.7  (  2.9%)  [2/2 feat]
    Direction             imp:    695.8  (  6.3%)  [3/3 feat]
    HTF Trend             imp:    450.1  (  4.1%)  [4/4 feat]
    Position              imp:    339.6  (  3.1%)  [3/3 feat]
    Temporal              imp:     91.2  (  0.8%)  [1/1 feat]

  short_2min — Kategoria osszesites:
    Return                imp:   2220.8  ( 29.7%)  [6/6 feat]
    Volatility            imp:   1261.1  ( 16.9%)  [10/10 feat]
    Skewness              imp:    665.4  (  8.9%)  [2/2 feat]
    Microstructure        imp:   1131.1  ( 15.1%)  [8/8 feat]
    Order Flow            imp:    515.7  (  6.9%)  [3/3 feat]
    Momentum              imp:    443.3  (  5.9%)  [8/8 feat]
    EMA Slope             imp:    263.0  (  3.5%)  [2/2 feat]
    Direction             imp:    380.4  (  5.1%)  [3/3 feat]
    HTF Trend             imp:    230.1  (  3.1%)  [4/4 feat]
    Position              imp:    265.4  (  3.6%)  [3/3 feat]
    Temporal              imp:     93.6  (  1.3%)  [1/1 feat]

======================================================================
7. ORANKENTI SIGNAL ELOSZLAS
======================================================================

  2min — orankenti signal:
     Ora    Long   Short     Net
       0     481     476      +5
       1    1147     842    +305
       2    1096     719    +377
       3    1269     827    +442
       4    1580    1273    +307
       5    1792    1260    +532
       6    1303    1025    +278
       7    1641    1097    +544
       8    1292     866    +426
       9    1452     956    +496
      10    1367    1041    +326
      11    1775    1125    +650
      12    1651    1027    +624
      13    1497     992    +505
      14    1602    1013    +589
      15    1787    1231    +556
      16    3140    1748   +1392
      17    3260    1934   +1326
      18    3140    1724   +1416
      19    2677    1553   +1124
      20    2212    1276    +936
      21    1854    1110    +744
      22    1662     954    +708
      23    1042     599    +443

======================================================================
8. VERZIO TORTENET (WF AUC osszehasonlitas)
======================================================================

  Verzio                    CV         1mL    1mS    2mL    2mS    3mL    3mS
  V1 KFold(5) 35feat        KFold    0.594  0.602  0.653  0.629  0.602  0.604
  V2 +direction/ICT         KFold    0.698  0.608  0.649  0.631  0.591  0.571
  V3 WF+feat sel            WF(5)    0.577  0.658  0.571  0.556  0.579  0.562
  V4 HTF Gate               KFold    0.655  0.624  0.639  0.652  0.586  0.601
  V6 CUSUM Bias             WF(5)    0.578  0.570  0.571  0.560  0.579  0.562
  V4.0 TBM (JELENLEGI)      WF(5)    0.555  0.535  0.548  0.547  0.550  0.544 ◄

  MEGJEGYZES: KFold AUC > 0.65 ILLUZIO (data leak)!
  Valos teljesitmeny: WF AUC = 0.54-0.58 tartomany

======================================================================
9. OSSZEFOGLALO ES KOVETKEZTESEK
======================================================================

  Felfedezesek:
  1. ret_1 DOMINAL minden modellben (20-35% total importance)
  2. Volatility feature-k masodik legfontosabb kategoria
  3. Direction feature-k (df_curve, pv_corr, variance_ratio) kozepesek
  4. HTF trend feature-k gyengék — SLOW kesik, FAST zajos
  5. Session feature-k ELTAVOLITVA — AUC nem romlott
  6. CUSUM sampling 46%-ot tart — jobb signal-to-noise
  7. TBM aszimmetrikus: PT=1.5xATR > SL=1.0xATR (trend-following)
  8. WF-CV valos AUC: 0.54-0.56 (KFold illuzio: 0.65+)

  Javasolt kovetkezo lepesek:
  a) Meta-labeling: primary side -> meta filter (AFML Ch.3)
  b) Sample weights: uniq-count alapu (AFML Ch.4)
  c) Dollar-bar threshold jelcsokkentes (zaj szures)
  d) Tobb adat (--full flag, hosszabb idotartam)
  e) Feature interaction: ret_1 x atr_pct, flow_delta x skew_60

✅ Modell statisztika elemzes KESZ
