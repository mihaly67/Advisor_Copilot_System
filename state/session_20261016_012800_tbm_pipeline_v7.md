# Session: tbm_pipeline_v7
*Időbélyeg: 2026-10-16T01:28:00.675323*

Triple Barrier Pipeline v4.0_TBM — 2026-10-16

Változtatások:
1. label_triple_barrier(): ATR-alapú, aszimmetrikus TP/SL (PT=1.5×ATR, SL=1.0×ATR)
   - Trend-following: TP messzebb → erős signál; SL közelebb → bounce = NEM signál
   - Long: TP=40.3%, SL=53.6% → selective (több SL hit = kevesebb false Long)
   - Short: TP=40.9%, SL=53.1% → selective

2. cusum_filter_events(): CUSUM sampling — 31627/68568 bar (46.1%)
   - Threshold dinamikus: ATR mean = 0.00013
   - Csak event bar-okon tanítunk → jobb signal-to-noise

3. train_single_model(): Walk-Forward CV (WF(5))
   - 5 expandáló ablak, 12% test
   - Fallback KFold ha WF < 2 split

4. feature_selection(): min_pct=0.3% (volt 0.5%), force-keep 15 direction feature
   - 59 → 53 feature (+2-4 forced) → direction feature-k bent maradnak

5. Full inference: CUSUM-trained model → ensemble predict TELJES feature-ökön

Eredmények (WF AUC — valós, nem KFold illúzió):
  1min: L=0.556, S=0.534
  2min: L=0.548, S=0.546
  3min: L=0.554, S=0.543

Top feature-k: ret_1, bar_dt, atr_pct, flow_delta, skew_60

Chart: BTCUSD_copilot_v4_2026-10-07.html (1.7MB)