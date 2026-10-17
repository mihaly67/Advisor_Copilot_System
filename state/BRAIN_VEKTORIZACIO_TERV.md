# BRAIN VEKTORIZÁCIÓS TERV — 2026.09.21

## CÉL
96 repo → szemantikus + logikai keresés másodpercek alatt,
mélységi/szélességi paraméterezéssel, kontextus-tudatos találatokkal.

---

## 1. ADATMODELL: JSONL → SQLite (nem csak vektor!)

### Miért JSONL + SQLite, nem csak vektor?

A sima vektor-DB csak "hasonló szöveget" talál. De a copilot fejlesztéshez kell:
- **Logikai keresés**: "Melyik repo implementál triple barrier-t ÉS Python-ban írták?"
- **Kontextus**: találat → melyik repo → melyik fájl → melyik függvény hívja
- **Mélység**: függvény → hívófüggvény → modul → repo (felfelé)
- **Szélesség**: ugyanaz a pattern más repókban (keresztben)

Ezért **két réteg** kell:

### Réteg 1: CHUNK (jsonl → SQLite)
```
id, repo, path, ext, lang, chunk_type, chunk_name,
line_start, line_end, content, dependencies, exports
```

| Mező | Példa | Leírás |
|------|-------|--------|
| repo | "LightRAG-main" | Forrás repo |
| path | "lightrag/llm.py" | Fájlelérési út a repón belül |
| ext | "py" | Kiterjesztés |
| lang | "python" | Nyelv (python, js, rust, cpp, md) |
| chunk_type | "function" | function / class / method / module / section / config |
| chunk_name | "llm_query_embed" | Függvény/osztály/section neve |
| content | "def llm_query..." | A kódszöveg |
| dependencies | ["torch", "numpy"] | Importok / függőségek |
| exports | ["llm_query_embed"] | Exportált nevek |

### Réteg 2: EMBEDDING (SQLite BLOB)
```
chunk_id → embedding BLOB (384-dim float32)
```

### Réteg 3: GRAPH (SQLite — logikai kapcsolatok)
```
id, from_chunk, to_chunk, edge_type
```
| edge_type | Leírás |
|-----------|--------|
| imports | A importálja B-t |
| calls | A függvény hívja B függvényt |
| inherits | A osztály örököl B-ből |
| contains | A fájl tartalmazza B chunk-ot |
| references | A hivatkozik B-re (docs, config) |

---

## 2. CHUNKING STRATÉGIA

### Kizárandó fájlok
```
KIZÁRÁS: .png .jpg .svg .gif .ico .webp
         .csv .parquet .arrow .feather
         .bin .onnx .gguf .so .o .wasm .map .lock
         .zip .tar .gz .whl .egg
KIZÁRÁS KÖNYVTÁRAK: node_modules/ .git/ __pycache__/ venv/
                   dist/ build/ .next/ target/ .venv/
```

### Chunking nyelvenként

| Nyelv | Chunk típus | Stratégia |
|-------|------------|-----------|
| **Python** | function, class, method | AST parse → top-level functions + class methods |
| **JavaScript/TS** | function, class, export | Regex: function/export/class blokkok |
| **Rust** | fn, impl, trait | Regex: fn/impl/trait blokkok |
| **C/C++** | function, struct, class | Regex: függvények, struct/class |
| **Markdown** | section, heading | Heading-ek (#, ##, ###) szerinti darabolás |
| **Config** | toml/yaml/json | Egész fájl egy chunk (kicsi) |
| **Shell** | function | Regex: function blokkok |
| **Egyéb** | file | Egész fájl egy chunk ha <8KB |

### Chunk méret limit
- **Min**: 100 char (filter: kisebbet eldobál)
- **Max**: 8000 char (nagyobbat feldaraboljuk, overlap 200 char)
- **Átlag cél**: 500-2000 char (optimális embedding hossz)

---

## 3. REPO-FELDOLGOZÁS PIPELINE

```
/data/Brain/LightRAG-main/
  ├── lightrag/llm.py     → [chunk: fn:llm_query_embed, fn:llm_query_generate]
  ├── lightrag/graph.py   → [chunk: fn:insert_graph, class:GraphStore]
  ├── README.md           → [chunk: section:Overview, section:Installation]
  └── pyproject.toml      → [chunk: config:pyproject]

→ JSONL: /data/Brain/_vectorized/chunks.jsonl
→ SQLite: /data/Brain/_vectorized/brain_rag.db
```

### Kimenet szerkezet
```
/data/Brain/_vectorized/
  ├── brain_rag.db          ← SQLite (chunks + embeddings + graph)
  ├── chunks.jsonl          ← nyers chunk adat (backup/inspect)
  └── vectorize_log.txt     ← napló
```

---

## 4. KERESÉS — SZEMANTIKUS + LOGIKAI + KONTEXTUS

### Keresési módok

| Mód | Paraméter | Példa |
|-----|-----------|-------|
| **Szemantikus** | query text | "triple barrier labeling" |
| **Logikai** | repo, lang, chunk_type, name | repo="LightGBM-main" AND chunk_type="class" |
| **Kombinált** | szemantikus + filter | "feature importance" AND lang="python" AND repo="LightGBM*" |
| **Mélységi** | from_chunk + edge_type | Ki hívja ezt a függvényt? (imports, calls) |
| **Szélességi** | pattern + across repos | "triple barrier" MINDEN repo-ban |

### Keresési API
```python
def brain_search(
    query: str,                    # Szemantikus query
    top_k: int = 10,              # Találatok száma
    repo: str = None,             # Repo szűrő (glob: "Light*")
    lang: str = None,             # Nyelv szűrő ("python")
    chunk_type: str = None,       # Típus szűrő ("function")
    depth: int = 0,               # Mélység: 0=none, 1=hívók, 2=hívó hívói
    breadth: bool = False,        # Szélesség: ugyanez pattern más repókban
    min_score: float = 0.3,       # Min cosine similarity
) -> list[SearchResult]:
```

### SearchResult
```python
@dataclass
class SearchResult:
    chunk_id: int
    repo: str
    path: str
    chunk_type: str
    chunk_name: str
    content: str
    score: float                  # Cosine similarity
    context: list[ChunkRef]       # Szülő/gyerek chunk-ok (depth>0)
    cross_repo: list[ChunkRef]    # Ugyanaz pattern más repókban (breadth=True)
```

---

## 5. IDŐBECSLÉSEK

| Lépés | Idő | Megjegyzés |
|-------|-----|------------|
| Chunking (96 repo, ~12K fájl) | ~2 perc | Python AST + regex, CPU |
| JSONL írás | ~5 mp | |
| SQLite töltés | ~10 mp | |
| Embedding (chunk-ek száma) | | |
| - Becsült chunk-ek: ~30-40K | ~3-4 perc | GPU P4000, batch=128 |
| Graph építés (imports/calls) | ~1 perc | Python AST import parse |
| **Összesen** | **~8 perc** | |

### Keresési idő
| Mód | Idő |
|-----|-----|
| Szemantikus (30K vektor, dot product) | <0.5 mp |
| Logikai (SQL WHERE) | <0.1 mp |
| Kombinált | <0.5 mp |
| Mélységi (depth=2, graph traverse) | <1 mp |
| Szélességi (cross-repo pattern) | <2 mp |

---

## 6. IMPLEMENTÁCIÓ

### Egy script: `/data/mcp_server/tools/brain_vectorize.py`

```
brain_vectorize.py --chunk              # JSONL + SQLite chunk generálás
brain_vectorize.py --embed              # Embedding GPU-n
brain_vectorize.py --graph              # Import/call graph építés
brain_vectorize.py --all                # Minden egyszerre
brain_vectorize.py --search "query"     # Szemantikus keresés
brain_vectorize.py --search "query" --repo "Light*" --depth 1
brain_vectorize.py --info               # Statisztika
```

### Python AST chunking (Python fájlokhoz)
```python
import ast
tree = ast.parse(source)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        # chunk = function
    elif isinstance(node, ast.ClassDef):
        # chunk = class + methods
```

### Regex chunking (JS/TS/Rust/C++/MD)
```python
# JS/TS: function foo() {}, export default class {}
# Rust: fn foo() {}, impl Foo {}
# MD: ## Heading ... ### Heading
```

---

## 7. METRIKÁK CÉL

| Metrikus | Cél |
|----------|-----|
| Chunk-ek száma | 30-40K |
| DB méret | ~200-300 MB (chunks + embeddings + graph) |
| Vektorizálás ideje | <5 perc |
| Keresés (szemantikus) | <0.5 mp |
| Keresés (depth=2) | <1 mp |
| Keresés (breadth) | <2 mp |
| Repo lefedettség | 96/96 (100%) |
