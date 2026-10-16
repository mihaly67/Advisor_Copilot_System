# Session: ml_vectorize_v2_complete
*Időbélyeg: 2026-09-22T05:48:33.544598*

## ML Vektorizáció v2 — KÉSZ

### Eredmények
- **Script**: `/data/mcp_server/tools/ml_vectorize_v2.py` (660 sor)
- **DB**: `/data/ml/_vectorized/ml_rag_v2.db` (2436 MB)
- **JSONL**: `/data/ml/_vectorized/ml_chunks_v2.jsonl`
- **Log**: `/data/ml/_vectorized/vectorize_v2_log.txt`

### Metrikák
- Repo-k: 123
- Chunk-ok: 284578 (100% vektorizálva)
- Graph élek: 2446 (imports kapcsolatok)
- Modell: all-MiniLM-L6-v2 (384-dim)
- Chunking: 130.2s
- Embedding: 897.1s (~15 perc, 317 chunk/s GPU-n)
- Graph: 1.9s

### Chunk típusok
- block: 144292 (JS/TS/Rust/C++/Go/Java regex)
- function: 69875 (Python AST)
- class: 32211 (Python AST)
- section: 21537 (Markdown heading)
- file: 7285, module: 4772, config: 4606

### Top repo-k
1. openvino-master: 89260
2. mlflow-master: 23237
3. airflow-main: 22079
4. ta-lib-main: 14577
5. prefect-main: 13289

### Keresés tesztek (mind sikeres)
1. "gramian angular field GAF CNN" → 328 találat, top 5: gaf-cnn, Gramian-Angular-Fields, datagene gaf_encode_mat, gramian-angular-field, cnn_gaf (0.55-0.57 score)
2. "triple barrier labeling meta-labeling" → 255 találat, top: barrier-method README, Quant_Repos mlfinlab apply_pt_sl_on_t1 (0.59 score)
3. "feature importance SHAP LightGBM" --repo Light* → 269 találat, top: LightGBM Features.rst, plot_importance függvény (0.58 score)

### Kizárások
- hf_cache, ray, neo4j, lobehub-canary, ml-agents-develop
- Régi vektorizációs artifacts: ml.db, ml.jsonl, ml.index, 12_vectorize_*.py, gpu_limited_vectorize.py
- _vectorized mappa (saját maga)

### Fontos: a régi ml.db (951 MB) érintetlen maradt!