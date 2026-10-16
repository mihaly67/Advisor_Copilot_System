# Session: brain_vectorize_complete
*Időbélyeg: 2026-09-22T01:06:03.359666*

## Brain Vektorizáció — KÉSZ

### Eredmények
- **Script**: `/data/mcp_server/tools/brain_vectorize.py` (636 sor)
- **DB**: `/data/Brain/_vectorized/brain_rag.db` (2079 MB)
- **JSONL**: `/data/Brain/_vectorized/chunks.jsonl`
- **Log**: `/data/Brain/_vectorized/vectorize_log.txt`

### Metrikák
- Repo-k: 89
- Chunk-ok: 246908 (nem 30-40K, mert 52095 fájl volt, nem 12K)
- Vektorizált: 246908/246908 (100%)
- Graph élek: 1665 (imports kapcsolatok)
- Modell: all-MiniLM-L6-v2 (384-dim)
- Chunking: 88.7s
- Embedding: 765.2s (~13 perc, 323 chunk/s GPU-n)
- Graph: 1.8s

### Chunk típusok
- block: 101979 (JS/TS/Rust/C++/Go/Java regex)
- function: 61622 (Python AST)
- section: 41007 (Markdown heading)
- class: 25615 (Python AST)
- config: 6813, file: 6777, module: 3095

### Top repo-k
1. llama.cpp: 25657
2. phidata: 18442
3. AutoGPT-master: 16187
4. qdrant: 14467
5. chroma-main: 12358

### Keresés tesztelve
- "triple barrier labeling": 389 találat (nem releváns — Brain repo-k nem tartalmaznak ML trading kódot)
- "MCP server tool definition": 4617 találat, top 5 mind releváns (0.75-0.80 score)
- Keresés <1s (model betöltéssel együtt ~5s)

### CLI parancsok
- `--all`: chunk+embed+graph
- `--chunk`: csak chunking
- `--embed`: csak embedding
- `--graph`: csak graph
- `--search "q"`: szemantikus keresés
- `--search "q" --repo "Light*" --depth 1 --breadth`: szűrt + graph + cross-repo
- `--info`: statisztika

### 3-réteg design
1. CHUNK: SQLite + JSONL, nyelv-specifikus (Python AST, regex, Markdown heading)
2. EMBEDDING: 384-dim BLOB, cosine sim, batch=128
3. GRAPH: imports élek (dependency → export kapcsolat)