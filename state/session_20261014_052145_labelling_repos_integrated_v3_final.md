# Session: labelling_repos_integrated_v3_final
*Időbélyeg: 2026-10-14T05:21:45.388614*

TUDÁSTÉR v3.0 KÉSZ — Labelling/normalisation/featuring/learning repo-k beépítve (2026-10-14)

## Beépített repo-k (6 db a Labelling mappából)
1. **quant-ohlcv-features** (540+ indikátor) → L0 feature_eng.json bővítés (quant_ohlcv_catalog + meta_labeling_filter), L2 digest
2. **meta-labeling-alpha-filter** (Gautier Petit) → L1 signal_filter_alpha.py + L2 digest
3. **meta-labeling-harness** (efenn-dev) → L1 meta_labeling_harness.py + L2 digest + AP18 + AP19
4. **lgbm-feature-selection** → L1 feature_selection_lgbm.py (SHAP + correlation pruning)
5. **finmlkit** → L2 digest_finmlkit.md (financial-ml-toolkit v2 összehasonlítás)
6. **llm-quant-research-loop** → RAG-ban kereshető (nem külön digest)

## Új fájlok (5)
- code_templates/feature_selection_lgbm.py — SHAP importance + correlation pruning + multi-TF feature names
- code_templates/meta_labeling_harness.py — MetaLabeler + PurgedWalkForwardCV + DecisionRow
- code_templates/signal_filter_alpha.py — filter_signals_with_meta_model + probability_weighted_sizing
- reference_digests/digest_quant_ohlcv_features.md — 540+ indikátor katalógus
- reference_digests/digest_meta_labeling_harness.md — Narrator vs Trader + alpha filter
- reference_digests/digest_finmlkit.md — finmlkit vs financial-ml-toolkit

## Módosított fájlok (4)
- decision_trees/feature_eng.json — v2.0→v3.0, 9→11 kategória (+quant_ohlcv_catalog +meta_labeling_filter)
- anti_patterns/financial_ml_mistakes.json — AP18 (Post-trade judge) + AP19 (Single-split flattery)
- pipeline_chain/full_pipeline.json — v2.0→v2.1, 13→16 lépés (+feature_selection +meta_labeling_harness +alpha_filter_sizing)
- KNOWLEDGE_INDEX.md — v2.0→v3.0

## Kulcs tanulságok a meta-labeling-harness-ból
- AP18: "Post-trade judge" = NARRATOR (look-ahead) vs "Decision-time meta-labeling" = TRADER
- AP19: Single split Sharpe 1.8 → Walk-forward CV: 1/5 fold veri beta = NEM VALÓS
- Objective: net P&L (NOT accuracy) — 99% accurate skip-only model = $0
- Leak-free: temporal wall + causal features + news cutoff + purged+embargoed CV

## Alpha filter bizonyított eredmények
- Meta-labeled: 12.17% return @ 19.51% vol, Sharpe 0.62 (Fold-3 OOS 2020-2024)
- 50/50 SPY blend: 14.64% @ 13.43% vol, Sharpe 1.09
- 3612 trades, 65.75% win, PF 2.92

## Végleges állapot
- 8 L0 döntési fa, 16 L1 kód sablon, 12 L2 digest, 19 anti-pattern, 16 pipeline lépés
- 1519 RAG chunks, 396KB total, feature_eng v3.0 (11 kategória)