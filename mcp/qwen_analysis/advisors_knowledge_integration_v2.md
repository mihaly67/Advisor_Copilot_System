# Advisors Knowledge Integration v2.0 — 2026-10-14

## Összefoglaló
A /data/Brain/advisors/ 11 klónozott GitHub repo signal/címkézési/featuring logikája beépítve a /data/LGBM_copilot/knowledge/ tudástérbe.

## Új fájlok
| Fájl | Szint | Tartalom |
|------|-------|----------|
| model_selection.json | L0 | Single vs Meta-Labeling vs L/S Split vs Ensemble + threshold + AUC |
| features_ict.py | L1 | FVG, OrderBlock, LiquiditySweep detektálás |
| features_volume_profile.py | L1 | Volume Profile POC + Value Area |
| features_session.py | L1 | Session/KillZone + HTF trend filter |
| signal_quality.py | L1 | MultiConfirmation, FreshTrigger, Cooldown |
| model_selection.py | L1 | Meta-labeling pipeline, Ensemble voting, Threshold opt |
| digest_ict_concepts.md | L2 | FVG+OB+LiqSweep+Session+POC teljes leírás |
| digest_model_selection.md | L2 | Meta vs Ensemble, Threshold, Scoring rendszerek |

## Módosított fájlok
- labeling.json: +trend_scanning, +scoring_labeling, +method_comparison
- feature_eng.json: +ict, +session, +signal_quality kategóriák (18 új feature)
- financial_ml_mistakes.json: +AP13-AP17 (5 új anti-pattern)
- full_pipeline.json: v2.0, 13 lépés (+signal_filter, +model_select)
- KNOWLEDGE_INDEX.md: v2.0

## Vektorizáció: 31 fájl → 232 chunk ml_rag_v2.db-ben

## Projektion: V3 AUC 0.7035 → V4 AUC 0.72-0.75 ICT feature-ekkel
