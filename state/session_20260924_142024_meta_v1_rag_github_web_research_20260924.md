# Session: meta_v1_rag_github_web_research_20260924
*Időbélyeg: 2026-09-24T14:20:24.824680*

META_V1 FEJLESZTÉS — RAG + GitHub + Webes Kutatás (2026-09-24)

=== GITHUB REPO-K (4 találat) ===

1. Farxida/prediction-market-ml (6 stars) — LEGÉRTÉKESEBB
   - LightGBM AUC=0.678 (vs mi 0.533!)
   - 78 feature, 10/78 = noise (NMI clustering)
   - PurgedKFold + walk-forward (5/5 ablak profitábilis, p=0.003)
   - Platt + isotonic calibration
   - Meta-labeling + focal loss
   - Half-Kelly risk manager, drawdown protection, regime detection
   - Deflated Sharpe Ratio (López de Prado Ch.8)
   - Éles: 86x alpha decay (backtest $8.61/trade → live -$0.10/trade)
   - 117 tests, production-grade engineering

2. hamzaalisayeed-eng/QuantAlgo2 (0 stars) — Meta-labeling architektúra
   - Primary: rule-based strategies (momentum, breakout, cross-sectional ranking)
   - Meta-model: LightGBM, P(win | signal context) → bet/no-bet + sizing
   - Calibration: explicit (train_meta_model.py calibrál)
   - use_meta flag per strategy (trend-following HURT by meta filter!)
   - Purged + embargoed walk-forward CV
   - Sample-uniqueness weighting for overlapping labels
   - Key insight: trend-following strategies HURT by meta filter (screens out rare huge winners)

3. sommersut/crypto-triple-barrier-lgbm (0 stars) — Triple Barrier + Purged K-Fold
   - TP: entry + 2× ATR, SL: entry - 1× ATR, max 5 bars
   - Meta-labeling: position sizing based on probability
   - PurgedKFold: purge samples whose [entry, exit] overlaps test window
   - Walk-forward with periodic re-training
   - Bug audit: eredetileg sok bug (inverted purge, hardcoded position size)

4. hudson-and-thames/mlfinlab (4.9k stars, 1.3k forks) — Hivatalos AFML library
   - All rights reserved license (nem használható kereskedelmi célra)
   - Modulok: Data Structures, Labeling, Sampling, Feature Engineering, Models, Clustering, Cross-Validation, Hyper-Parameter Tuning, Feature Importance, Bet Sizing

=== RAG TALÁLATOK (saját DB) ===
- LGBM-Stock-Prediction: Triple Barrier + Walk Forward + random search hyperparameter tuning
- mlfinlab labeling: apply_pt_sl_on_t1 (Snippet 3.2, page 45)
- DART: Ensemble ML signal generator, Kelly Criterion, fractional Kelly 0.5-0.75x
- Kalshi: Kelly_fraction=0.75, max_position_size_pct=5.0
- tensortrade: Walk-forward (anchored expanding + rolling window)
- Alpha Scientist: Walk-forward model building — quarterly recalc, 365-day rolling window, RSQ 0.008→0.108

=== KULCS FEJLESZTÉSI LEHETŐSÉGEK META_V1-HEZ ===

1. ISOTONIC/PLATT CALIBRATION (优先)
   - A P(trade) distribúció túl szűk (IQR 0.464-0.542)
   - sklearn CalibratedClassifierCV isotonic regression-rel
   - Farxida repo kifejezetten használja: "Platt + isotonic calibration"
   - Ez szélesítheti a P(trade) range-et és javíthatja a kalibrációt

2. FOCAL LOSS (优先)
   - Farxida repo focal loss-t használ class imbalance-re
   - class_weight='balanced' helyett focal loss (γ=2.0)
   - LightGBM: objective='binary' + custom focal loss
   - Jobban kezeli a hard examples-t

3. PURGED K-FOLD + EMBARGO
   - A mi 80/20 statikus split-ünk túl naiv
   - Triple barrier overlapping labels → purge samples whose [entry,exit] overlaps test
   - López de Prado Ch.7: PurgedKFold + embargo
   - Javítja az OOS validációt

4. ERŐSEBB PRIMARY MODEL
   - Mi: Slope_Close_14 (>0 → Long, <0 → Short) → 51.6% PT rate (ceiling)
   - QuantAlgo2: több rule-based strategy (momentum, breakout, cross-sectional)
   - Javaslat: EMA crossover, RSI threshold, breakout signals kombinálása
   - Vagy: ML-based primary (3-class LGBM V20 → side, meta_v1 → bet/no-bet)

5. FEATURE CLUSTERING (NMI + ONC)
   - Farxida: 10/78 feature = noise (NMI clustering)
   - Mi: 3/30 redundáns (Num_Ticks, Tick_Speed, Flow_Delta_10)
   - ONC (Optimal Number of Clusters) → feature csoportok azonosítása
   - Minden csoportból 1 reprezentáló feature megtartása

6. WALK-FORWARD VALIDATION
   - Alpha Scientist: quarterly recalc, 365-day rolling window
   - Mi: 80/20 statikus split (naiv)
   - Walk-forward: rolling window + periodic retrain
   - Reálisabb OOS performance

7. SAMPLE-UNIQUENESS WEIGHTING
   - Triple barrier → overlapping labels
   - López de Prado: sample_weight = uniqueness
   - LightGBM: sample_weight paraméter
   - Csökkenti a label redundancy hatását