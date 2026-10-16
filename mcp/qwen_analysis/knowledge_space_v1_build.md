# Knowledge Space v1.0 Build Log
**Dátum:** 2026-10-13
**Cél:** Copilot-ready tudástér építése labeling, data engineering, feature engineering területen

---

## Épített struktúra: `/data/LGBM_copilot/knowledge/`

### L0 — Döntési fák (18KB)
| Fájl | Tartalom | Méret |
|------|----------|-------|
| `decision_trees/labeling.json` | Side labeling, meta-labeling, trend labeling, CUSUM filter | 5.2KB |
| `decision_trees/data_eng.json` | Dollar bars, volume bars, sampling, footprint proxies | 5.3KB |
| `decision_trees/feature_eng.json` | 6 kategória: direction, volatility, regime, momentum, volume_flow, boolean_context | 8.0KB |

### L1 — Kód sablonok (35KB)
| Fájl | Pipeline lépés | Méret |
|------|---------------|-------|
| `code_templates/labeling_cusum_filter.py` | CUSUM esemény detekció | 2.8KB |
| `code_templates/labeling_meta_labeling.py` | Side-aware Triple Barrier meta-labeling | 5.7KB |
| `code_templates/data_dollar_bars.py` | Dollar bar konstrukció | 2.7KB |
| `code_templates/features_direction.py` | 6 direction feature + boolean features | 5.6KB |
| `code_templates/sample_weights.py` | Average uniqueness + return attribution | 3.3KB |
| `code_templates/cross_validation_purged.py` | PurgedKFold + walk-forward | 3.6KB |
| `code_templates/train_lgbm.py` | LightGBM + PurgedKFold CV | 3.6KB |
| `code_templates/instrument_config.py` | Instrument konfig (concept_map-ból) | 3.5KB |

### L2 — Referencia digestek (30KB)
- digest_triple_barrier.md (5.2KB)
- digest_meta_labeling.md (4.0KB)
- digest_direction_features.md (4.7KB)
- digest_sample_weights.md (5.6KB)
- digest_frac_diff.md (3.1KB)
- ml_knowledge_supplement_advanced.md (7.1KB)

### Validáció és Anti-patterns
- `checklists/validation.json` — 5 terület (data_quality, labeling, features, training, evaluation)
- `anti_patterns/financial_ml_mistakes.json` — 12 anti-pattern (AP01-AP12), severity-vel

### Pipeline lánc
- `pipeline_chain/full_pipeline.json` — 11 lépés, quick_reference

### Keresés
- `knowledge_search.py` — lightweight tudástér keresés (JSON+py+md)
- `faiss_search.py` — GPU FAISS szemantikus keresés (P4000)
- `knowledge_vectorize.py` — tudástér vektorizálás ml_rag_v2.db-be

### Index
- `KNOWLEDGE_INDEX.md` — teljes dokumentáció + protocol

---

## Concept Map v2.0 frissítés
- `knowledge_space` szekció hozzáadva concept_map.json-hez
- AGENTS.md 4-szintű tudás-navigáció frissítve (L0→L3)
- `knowledge_space` elérhető rag_query concept módban

## VSCode konfig
- `.vscode/tasks.json` — 5 task (search, pipeline, vectorize, faiss, validate)
- `.vscode/launch.json` — 3 debug konfig (pipeline, knowledge, faiss)

---

## KÖVETKEZŐ LÉPÉSEK
1. Vektorizálás futtatása: `python3 knowledge_vectorize.py` (P4000, ~5 min)
2. FAISS index újraépítés (ha kell)
3. Pipeline end-to-end teszt
4. MCP server rag_query frissítés knowledge_search integrációval
5. Asztali vizualizáció integráció (DearPyGui/PyQtGraph)
6. Trading panel fejlesztés (EA Python fordítás előkészítés)
