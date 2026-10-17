# Session: FINAL_v3_complete_shutdown
*Időbélyeg: 2026-10-14T05:26:40.533483*

=== TUDÁSTÉR v3.0 — TELJES SESSION MENTÉS ===
Dátum: 2026-10-14
Státusz: KÉSZ, mind beépítve

## ARCHITEKTÚRA ÁTTEKINTÉS
4-szintű tudás-navigáció:
- L0: decision_trees/*.json (8 fájl, 43KB) — MI-t? Paraméterek? Anti-patterns?
- L1: code_templates/*.py (16 fájl, 63KB) — másolható kód sablonok
- L2: reference_digests/*.md (12 fájl, 56KB) — mély implementációs leírás
- L3: RAG (ml_rag_v2.db + brain_rag.db, 5GB+) — konkrét kódrészletek

## L0 DÖNTÉSI FÁK (8)
1. labeling.json (7.7KB) — Side, meta, trend scanning, scoring, CUSUM + method comparison
2. data_eng.json (5.3KB) — Dollar bars, volume bars, sampling, footprint proxies
3. feature_eng.json (18.3KB, v3.0) — 11 kategória:
   direction, volatility, regime, momentum, volume_flow, ict, session,
   signal_quality, boolean_context, quant_ohlcv_catalog (540+), meta_labeling_filter
4. model_selection.json (5.4KB) — Single vs Meta-Labeling vs L/S Split vs Ensemble
5. repo_catalog.json (5.1KB) — Trading systems + data eng + feature eng + experiment (59 repo)
6. repo_catalog_p2.json (4.1KB) — Portfolio/risk + viz + MCP/agent + RAG + anomaly + TS (80+ repo)
7. visualization.json (4.4KB) — Model debug + backtest eval + live dashboard + feature exploration
8. rag_building.json (3.4KB) — RAG infra: FAISS, Chroma, sqlite-vec

## L1 KÓD SABLONOK (16)
1. data_dollar_bars.py — Dollar bar construction
2. labeling_cusum_filter.py — CUSUM event detection
3. labeling_meta_labeling.py — Meta-labeling (direction + size)
4. features_direction.py — 6 direction feature (DF_Curve, Flow_Delta, PV_Corr, Mom_Pers, RSI_Dev, Bias)
5. features_ict.py — ICT: FVG, OrderBlock, LiquiditySweep
6. features_volume_profile.py — Volume Profile POC + Value Area
7. features_session.py — Session/KillZone + HTF trend
8. signal_quality.py — MultiConfirmation, FreshTrigger, Cooldown
9. model_selection.py — Meta pipeline, Ensemble, Threshold opt
10. sample_weights.py — Uniqueness + attribution
11. cross_validation_purged.py — PurgedKFold
12. train_lgbm.py — LightGBM CV
13. instrument_config.py — BTCUSD config
14. feature_selection_lgbm.py — SHAP importance + correlation pruning + multi-TF names
15. meta_labeling_harness.py — MetaLabeler + PurgedWalkForwardCV + DecisionRow
16. signal_filter_alpha.py — Alpha filter + probability-weighted sizing

## L2 REFERENCIA DIGESTEK (12)
1. digest_triple_barrier.md — TBM implementáció + BTCUSD params
2. digest_meta_labeling.md — Meta-labeling + position sizing
3. digest_direction_features.md — 6 direction feature + Python proxy
4. digest_sample_weights.md — Uniqueness, PurgedKFold, CPCV
5. digest_frac_diff.md — FFD + min-d search
6. digest_ict_concepts.md — FVG+OB+LiqSweep+Session+POC (advisors)
7. digest_model_selection.md — Meta vs Ensemble, Threshold, Scoring
8. digest_quant_ohlcv_features.md — 540+ OHLCV indicators (quant-ohlcv-features)
9. digest_meta_labeling_harness.md — Honest take/skip + alpha filter
10. digest_finmlkit.md — Financial ML toolkit v2
11. digest_repo_catalog.md — System-level repo catalog (195 repo)
12. ml_knowledge_supplement_advanced.md — Mikrostruktúra, entrópia

## ANTI-PATTERNS (19)
AP01: Label leakage (future info in features)
AP02: Meta-labeling as direction (it's SIZE filter)
AP03: Cross-validation without purging
AP04: Too many noisy features (overfitting)
AP05: Ignoring feature correlation (redundancy)
AP06: Imbalanced classes without adjustment
AP07: Look-ahead bias in features
AP08: Single time-series split
AP09: Accuracy as objective (use Sharpe/P&L)
AP10: Ignoring stationarity
AP11: Overfitting to backtest
AP12: Sample weight ignorance
AP13: Signal without multi-confirmation (advisors)
AP14: Stale signal entry (advisors)
AP15: Overtrading — no cooldown/filter (advisors)
AP16: Ignoring kill zone timing (advisors)
AP17: No signal quality scoring (advisors)
AP18: Post-trade judge = NARRATOR (meta-labeling-harness) CRITICAL
AP19: Single-split validation flattery (meta-labeling-harness) CRITICAL

## PIPELINE (16 lépés, v2.1)
1. ingestion → 2. bars → 3. CUSUM → 4. label → 5. features →
6. signal_filter → 7. weights → 8. model_select → 9. train →
10. eval → 11. threshold → 12. sizing → 13. deploy →
14. feature_selection → 15. meta_labeling_harness → 16. alpha_filter_sizing

## BEÉPÍTETT REPO-K TELJES LISTA

### Advisors (11 GitHub trading bot → signal logika)
BAKOME, nq1_Scalp, CSA-15, EURUSD_Scalper, MlFinLab, EA31337, qstrader,
AgenticTrading, Plus 3 more → FVG, OB, POC, Session, FreshTrigger,
MultiConfirmation, Meta-labeling

### Labelling/normalisation/featuring/learning (6 repo)
1. quant-ohlcv-features — 540+ indikátor (7 kategória, signal(df,n,name) interface)
2. meta-labeling-alpha-filter — Signal refinement (Sharpe 1.09 50/50 blend)
3. meta-labeling-harness — Honest take/skip eval (Narrator vs Trader)
4. lgbm-feature-selection — SHAP + correlation pruning
5. finmlkit — Financial ML toolkit v2 (JIT, HDF5, footprints)
6. lgbm-feature-selection — Time series utils

### System-level repo catalog (195 repo osztályozva)
3 CRITICAL: financial-ml-toolkit, LightGBM, optuna
21 HIGH: freqtrade, qlib, vectorbt, xauusd-scalping-ai, AgenticTrading,
  ta-lib, AlphaPy, shap, river, quantstats, barrier-method, LightGBM-Quant,
  triple_barrier, mql-zmq, Qwen-Agent, langgraph, deepagents, MCP, LightRAG,
  sentence-transformers, cline
35 MEDIUM: findatapy, ArcticDB, prefect, zenml, hmmlearn, PyPortfolioOpt, ...
40+ LOW: kutatási/niche

## KULCS ARCHITEKTÚRA MINTÁK (5)
1. Pipeline (qlib+freqtrade): DataHandler→Feature→Label→Model→Backtest→Execute
2. Strategy (freqtrade): populate_indicators → populate_buy_trend
3. Online learning (river): model.learn_one(x,y) → concept drift adaptáció
4. Vectorized backtest (vectorbt): vbt.Portfolio.from_signals()
5. SHAP selection: TreeExplainer → feature importance → pruning

## ALPHA FILTER BIZONYÍTOTT EREDMÉNYEK
Meta-labeled: 12.17% return @ 19.51% vol, Sharpe 0.62 (Fold-3 OOS 2020-2024)
50/50 SPY blend: 14.64% @ 13.43% vol, Sharpe 1.09
3612 trades, 65.75% win, PF 2.92
Params: th_long=0.45, th_short=0.50, min_gap=0.10, top_k=3/day, target_vol=0.20, leverage_cap=3

## RAG ÁLLAPOT
ml_rag_v2.db: 333K+ chunks (ML kód FAISS)
brain_rag.db: 247K chunks (Agent/RAG/MCP)
Knowledge chunks: 1519 (LGBM_copilot tudástér)
Embedding: all-MiniLM-L6-v2 (384 dim, P4000 GPU)
Total tudástér méret: 396KB

## META-LABELING HARNESS KULCS TANULSÁGOK
- "The trap is the post-trade judge" — Narrator vs Trader
- Single split Sharpe 1.8 → Walk-forward: 1/5 fold beats beta = NOT REAL
- Objective: net P&L (NOT accuracy) — 99% accurate skip-only = $0
- Leak-free: temporal wall + causal features + news cutoff + purged+embargoed CV
- Verdict can say "no" — profitable / reduces-loss / no-edge

## FEATURE ENGINEERING V3.0 KATEGÓRIÁK (11)
1. direction — DF_Curve, Flow_Delta, PV_Corr, Mom_Pers, RSI_Dev, Bias
2. volatility — ATR, BB_width, CUSUM_vol, Parkinson, Garman-Klass
3. regime — HMM, K-means vol, trend/mean-rev
4. momentum — RSI, MACD, Stoch, ADX, CCI
5. volume_flow — OBV, MFI, CMF, VPVR, taker_ratio
6. ict — FVG, OrderBlock, LiquiditySweep (advisors)
7. session — KillZone, HTF_trend, session_overlap
8. signal_quality — MultiConfirm, FreshTrigger, Cooldown
9. boolean_context — CUSUM_Up, Above_EMA20, BB_Squeeze, etc.
10. quant_ohlcv_catalog — 540+ indikátor (momentum:240, vol:107, volume:82, trend:73, price:19, liq:8, comp:11)
11. meta_labeling_filter — p_take, p_margin, meta_threshold, meta_gap, weight_mode, vol_target, leverage_cap