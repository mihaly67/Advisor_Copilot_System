# 🧠 LGBM Copilot Knowledge Space — Index v3.0

## CÉL
Ez a tudástér a Cline AI copilot számára készült, hogy a labeling, data engineering, feature engineering, model selection és signal quality területen mély tudással rendelkezzen, és a tudásból KÖZVETLENül tudjon kódot generálni.

## ARCHITEKTÚRA: 4-SZINTŰ TUDÁS-NAVIGÁCIÓ

| Szint | Hely | Méret | Funkció |
|-------|------|-------|---------|
| **L0** | `decision_trees/*.json` | 25KB | Döntési fa: MI-t? Paraméterek? Anti-patterns? |
| **L1** | `code_templates/*.py` | 45KB | Másolható, paraméterezhető kód sablonok |
| **L2** | `reference_digests/*.md` | 42KB | Mély implementációs leírás + BTCUSD params |
| **L3** | RAG (ml_rag_v2.db + brain_rag.db) | 5GB | Konkrét kódrészletek szabadon |

---

## DÖNTÉSI FÁK (L0)

| Fájl | Tartalom |
|------|----------|
| `decision_trees/labeling.json` | Side, meta, trend scanning, scoring labeling, CUSUM + method comparison |
| `decision_trees/data_eng.json` | Dollar bars, volume bars, sampling, footprint proxies |
| `decision_trees/feature_eng.json` | 11 kategória: direction, volatility, regime, momentum, volume_flow, ict, session, signal_quality, boolean, **quant_ohlcv_catalog (540+)**, **meta_labeling_filter** |
| `decision_trees/model_selection.json` ⭐ | Single vs Meta-Labeling vs L/S Split vs Ensemble + threshold + feature count |
| `decision_trees/repo_catalog.json` ⭐ | Trading systems + data eng + feature eng + experiment tracking (59 repo) |
| `decision_trees/repo_catalog_p2.json` ⭐ | Portfolio/risk + viz + MCP/agent + RAG + anomaly + time series (80+ repo) |
| `decision_trees/visualization.json` | Desktop GUI + backtest viz |
| `decision_trees/rag_building.json` | RAG infra |

## KÓD SABLONOK (L1)

| Fájl | Pipeline lépés |
|------|---------------|
| `code_templates/data_dollar_bars.py` | Dollar bar |
| `code_templates/labeling_cusum_filter.py` | CUSUM esemény |
| `code_templates/labeling_meta_labeling.py` | Meta-labeling |
| `code_templates/features_direction.py` | 6 direction feature |
| `code_templates/features_ict.py` ⭐ | ICT: FVG, OrderBlock, LiquiditySweep |
| `code_templates/features_volume_profile.py` ⭐ | Volume Profile POC + Value Area |
| `code_templates/features_session.py` ⭐ | Session/KillZone + HTF trend |
| `code_templates/signal_quality.py` ⭐ | MultiConfirmation, FreshTrigger, Cooldown |
| `code_templates/model_selection.py` ⭐ | Meta pipeline, Ensemble, Threshold opt |
| `code_templates/sample_weights.py` | Uniqueness + attribution |
| `code_templates/cross_validation_purged.py` | PurgedKFold |
| `code_templates/train_lgbm.py` | LightGBM CV |
| `code_templates/feature_selection_lgbm.py` ⭐ | SHAP importance + correlation pruning |
| `code_templates/meta_labeling_harness.py` ⭐ | Take/skip meta-labeler + PurgedWalkForwardCV |
| `code_templates/signal_filter_alpha.py` ⭐ | Alpha filter + prob-weighted sizing |

⭐ = NEW from advisors/Labelling repos (2026-10-14)

## REFERENCIA DIGESTEK (L2)

| Fájl | Téma |
|------|------|
| `reference_digests/digest_triple_barrier.md` | TBM implementáció + BTCUSD params |
| `reference_digests/digest_meta_labeling.md` | Meta-labeling + position sizing |
| `reference_digests/digest_direction_features.md` | 6 direction feature + Python proxy |
| `reference_digests/digest_sample_weights.md` | Uniqueness, PurgedKFold, CPCV |
| `reference_digests/digest_frac_diff.md` | FFD + min-d search |
| `reference_digests/digest_ict_concepts.md` ⭐ | FVG+OB+LiqSweep+Session+POC (advisors) |
| `reference_digests/digest_model_selection.md` ⭐ | Meta vs Ensemble, Threshold, Scoring (advisors) |
| `reference_digests/digest_quant_ohlcv_features.md` ⭐ | 540+ OHLCV indicators (quant-ohlcv-features) |
| `reference_digests/digest_meta_labeling_harness.md` ⭐ | Honest take/skip + alpha filter (harness+alpha-filter) |
| `reference_digests/digest_finmlkit.md` ⭐ | Financial ML toolkit v2 (finmlkit) |
| `reference_digests/digest_repo_catalog.md` ⭐ | System-level repo catalog (195 repo) |
| `reference_digests/ml_knowledge_supplement_advanced.md` | Mikrostruktúra, entrópia |

## ANTI-PATTERNS: 19 (AP01-AP19)
AP01-AP12: eredeti AFML | AP13-AP17: from advisors | AP18-AP19 ⭐: from meta-labeling harness

## PIPELINE: 16 lépés
ingestion→bars→CUSUM→label→features→signal_filter→weights→model_select→train→eval→threshold→sizing→deploy→**feature_selection**⭐→**meta_labeling_harness**⭐→**alpha_filter_sizing**⭐

## ❌ TILTOTT (AP01-AP17)
- AP01-08: eredeti AFML violations (fix pip, meta as dir, symmetric, KFold, RSI/ADX, raw price, time bars, unweighted)
- AP13: FVG no ATR filter | AP14: POC needs footprint → proxy | AP15: Signal every bar → FreshTrigger
- AP16: Single model → meta pipeline | AP17: No session → KillZone

## ADVISORS INTEGRÁCIÓ (2026-10-14)
Forrás: `/data/Brain/advisors/` — 11 repo (BAKOME, CSA-15, NQ1, EURUSD, EA31337, MlFinLab)

| Beépített | Szint | Fájl |
|-----------|-------|------|
| FVG+OB+LiqSweep | L0+L1+L2 | feature_eng.json, features_ict.py, digest_ict_concepts.md |
| Volume Profile POC | L0+L1+L2 | feature_eng.json, features_volume_profile.py |
| Session/KillZone+HTF | L0+L1 | feature_eng.json, features_session.py |
| MultiConfirm+FreshTrigger | L0+L1 | feature_eng.json, signal_quality.py |
| Meta-Labeling+Ensemble | L0+L1+L2 | model_selection.json, model_selection.py, digest_model_selection.md |
| Trend Scanning+Scoring | L0 | labeling.json |
| AP13-AP17 | — | financial_ml_mistakes.json |
