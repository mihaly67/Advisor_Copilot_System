# Session: tudaster_v1_0_teljes
*Időbélyeg: 2026-10-13T18:51:15.483274*

TUDÁSTÉR v1.0 TELJES ÉPÍTÉS — 2026-10-13

## ÉPÍTETT STRUKTÚRA: /data/LGBM_copilot/knowledge/

### L0 Döntési fák (18KB)
- labeling.json: side_labeling, meta_labeling, trend_labeling, cusum_filter + sample_weights + cross_validation
- data_eng.json: DollarBar, VolumeBar, TimeBar, ImbalanceBar, CUSUM_sampling, FootprintData + 8 pipeline_steps
- feature_eng.json: 6 kategória (direction, volatility, regime, momentum, volume_flow, boolean_context) + feature_selection + leakage_prevention

### L1 Kód sablonok (35KB)
- labeling_cusum_filter.py: CUSUM esemény detekció (Prado)
- labeling_meta_labeling.py: Side-aware TBM meta-labeling
- data_dollar_bars.py: Dollar bar konstrukció
- features_direction.py: 6 direction feature + boolean features + context combinations
- sample_weights.py: Average uniqueness + return attribution + time decay
- cross_validation_purged.py: PurgedKFold + walk-forward CV
- train_lgbm.py: LightGBM + PurgedKFold + sample_weight
- instrument_config.py: Instrument konfig concept_map-ból

### L2 Referencia digestek (30KB)
- 5 digest + 1 supplement másolva Brain-ből

### Validáció
- validation.json: 5 terület (data_quality, labeling, features, training, evaluation) × 5-6 check
- financial_ml_mistakes.json: 12 anti-pattern (AP01-AP12) severity-vel

### Pipeline
- full_pipeline.json: 11 lépés (ingestion→bars→CUSUM→label→features→weights→train→eval→threshold→sizing→deploy)

### Keresés
- knowledge_search.py: lightweight tudástér keresés (JSON+py+md)
- faiss_search.py: GPU FAISS szemantikus keresés P4000-n
- knowledge_vectorize.py: DB vektorizáló + FAISS index építő

### Integráció
- concept_map.json v2.0: knowledge_space szekció
- AGENTS.md: 4-szintű tudás-navigáció (L0→L3)
- KNOWLEDGE_INDEX.md: teljes dokumentáció + protocol
- .vscode/tasks.json + launch.json

### RAG tesztek
✅ ML RAG keyword: triple_barrier → mlfinlab CoreFunctions
✅ ML RAG keyword: CUSUM filter → snippets.getTEvents
✅ Brain RAG keyword: LightRAG → graph retrieval
✅ Knowledge indexelve MCP memóriába (24 fájl)

### PENDING
- Vektorizálás futtatása (knowledge_vectorize.py — P4000 szabad)
- FAISS index újraépítés
- MCP server rag_query frissítés knowledge_search-sal
- Pipeline end-to-end teszt
- Asztali vizualizáció integráció
- Trading panel fejlesztés