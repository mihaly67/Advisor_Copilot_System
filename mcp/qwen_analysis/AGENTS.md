# 🧠 ML & Brain Knowledge — Strict Grounding Protocol

## CÉL
Az LLM NE írjon ML algoritmust fejből. MINDIG a tudástárból dolgozzon.

---

## 4-SZINTŰ TUDÁS-NAVIGÁCIÓ

| Szint | Hely | Méret | Funkció |
|-------|------|-------|---------|
| **L0** | `knowledge/decision_trees/*.json` | 18KB | Döntési fa: MI-t? Paraméterek? Anti-patterns? |
| **L1** | `knowledge/code_templates/*.py` | 35KB | Másolható, paraméterezhető kódsablonok |
| **L2** | `knowledge/reference_digests/*.md` | 30KB | Mély implementációs leírás + BTCUSD params |
| **L3** | RAG (ml_rag_v2.db + brain_rag.db) | 5GB | Konkrét kódrészletek szabadon |

**Tudástér**: `/data/LGBM_copilot/knowledge/` — KNOWLEDGE_INDEX.md
**Token spórolás**: L0+L1+L2 = ~83KB vs flat RAG 50 chunk = ~150KB (2× kevesebb!)

---

## KÖTELEZŐ PROTOCOL (MINDEN ML TASK ELŐTT)

1. `concept_map.json` → keresd meg a releváns koncept-et
2. Olvasd el a hozzá tartozó `digest_*.md`-t
3. Olvasd el a referenciakódot (concept_map mutatja a fájd+függvényt)
4. Implementálj a referenciakód struktúrája szerint
5. Hivatkozz a forrásra kommentben: `# Based on: AFML Ch.3 / labeling.py::triple_barrier_labels`

---

## ❌ TILTOTT

- "Írok egy TBM-et..." → NEM! `labeling.py::triple_barrier_labels` létezik!
- "Kitalálok direction feature-t..." → NEM! `digest_direction_features.md` tartalmazza!
- "Egy sima KFold elég..." → NEM! `PurgedKFold` kötelező financial label-ekkel!
- RSI/ADX/Stochastic mint direction feature → AUC≈0.53, TILTOTT!
- Meta-labeling mint direction prediction → NEM! Az SIZE FILTER (0/1)!
- Unweighted training financial label-ekkel → TILTOTT!
- sklearn KFold financial label-ekkel → LEAKS! PurgedKFold kötelező!
- Bármely instrument paramérek fejből → concept_map `instruments[SYMBOL]`-ból!

---

## ✅ KÖTELEZŐ

- Direction feature-k: `digest_direction_features.md` sorrendjében (DF_Curve → Flow_Delta → PV_Corr → Mom_Persist → Vol_Adj_Mom → VR_1_4)
- Sample weights: uniqueness × return × time_decay → `model.fit(sample_weight=...)`
- PurgedKFold vagy CPCV, pct_embargo ≥ 0.01
- Labeling pipeline: side (+1/-1) → meta (0/1), SOHA fordítva!
- Referencia hivatkozás minden implementált függvényben

---

## TUDÁSTÉR INDEX

| Fájl | Szint | Tartalom |
|------|-------|----------|
| `concept_map.json` | L1 | 6 domain: labeling, feature_engineering, sample_weights, cross_validation, training, navsystem_indicators |
| `module_index.json` | L2 | 5 modul: labeling, labeling_advanced, sample_weights, feature_engineering, trade_labeling_oop |
| `digest_triple_barrier.md` | L3 | TBM + side-aware + BTCUSD |
| `digest_meta_labeling.md` | L3 | Meta-labeling + position sizing |
| `digest_direction_features.md` | L3 | 6 direction feature + Python proxy |
| `digest_sample_weights.md` | L3 | Uniqueness, PurgedKFold, CPCV |
| `digest_frac_diff.md` | L3 | FFD + min-d search |
| `ml_knowledge_supplement_advanced.md` | L3 | Mikrostruktúra, entrópia, ortogonális |

## RAG QUERY

```bash
# Koncept navigáció (L1)
python3 /data/Brain/_qwen_analysis/rag_query.py triple_barrier --concept

# DB keresés (L4 — ml_rag_v2.db, 333K chunk)
python3 /data/Brain/_qwen_analysis/rag_query.py CUSUM filter --top-k 5

# Szemantikus keresés (FAISS + MiniLM — GPU szükséges)
python3 /data/mcp_server/tools/ml_vectorize_v2.py --search "triple barrier"
python3 /data/mcp_server/tools/brain_vectorize.py --search "mcp tool"
```

## REFERENCIA REPO-K

| Repo | Útvonal | Chunk | Relevancia |
|------|---------|-------|-----------|
| financial-ml-toolkit | `/data/ml/.../financial-ml-toolkit-main/pipeline/` | — | **PRIMARY** TBM, features, weights |
| triple_barrier-main | `/data/ml/triple_barrier-main/` | — | OOP TBM reference |
| mlfinlab | `/data/ml/Quant_Repos/mlfinlab/` | — | AFML official |
| ml_rag_v2.db | `/data/ml/_vectorized/` | 333K | ML kód FAISS index |
| brain_rag.db | `/data/Brain/_vectorized/` | 247K | Agentic/RAG/MCP kód |
| LightRAG-main | `/data/Brain/LightRAG-main/` | 2.3K | Graph-based RAG framework |
| Qwen-Agent | `/data/Brain/Qwen-Agent/` | 863 | Qwen agent + tools + MCP |
| graphrag-main | `/data/Brain/graphrag-main/` | 1.7K | Microsoft GraphRAG |
| langgraph-main | `/data/Brain/langgraph-main/` | 3.1K | Stateful multi-actor agents |
| deepagents-main | `/data/Brain/deepagents-main/` | 5.3K | Deep agents + ACP protocol |
| mem0-aio | `/data/Brain/mem0-aio/` | 110 | Memory management |
| MCP server | `/data/mcp_server/server.py` | — | Saját MCP: read_repo, write_log, analyze, session |
| brain_vectorize.py | `/data/mcp_server/tools/` | — | Brain RAG: --search FAISS |
| ml_vectorize_v2.py | `/data/mcp_server/tools/` | — | ML RAG: --search FAISS |

## BRAIN REPO-K (89 repo, 247K chunk)

Top chunk count: llama.cpp (26K), AutoGPT (16K), qdrant (14K), chroma (12K), openai-agents-python (9K), phidata (18K), langchain (8K), deepagents (5K), openhands (5.5K)

## INSTRUMENTUMOK (concept_map.json → instruments)

| Szimbólum | Dollar bar | TP | SL | VB | Megjegyzés |
|-----------|-----------|-----|-----|-----|-----------|
| BTCUSD | 500K USD | 2.0σ | 2.0σ | 50 bars | Crypto, no footprint |
| XAUUSD | 5M USD | 2.5σ | 1.5σ | 100 bars | Gold, wider TP, tighter SL |

**SOHA** ne hardcode-olj instrument paramétereket! Mindig `concept_map.json → instruments[SYMBOL]`-ból!
Új instrument: csak új key a concept_map `instruments` dict-be.

## VSCODE + MCP KÖRNYEZET

**MCP**: Cline → qwen-mcp-server (`/data/mcp_server/server.py`) — 8 tool, **MINDEN auto-approved**
**Kiegészítők**: Python+Pylance+debugpy, C/C++ pack+CMake, Black+isort, GitLens, YAML, TOML, Docker
**Cron**: changelog, code-style, dead-code, dependency, docs, test-coverage, type-check
**Auto-approve**: read, readFile, listDirectory, searchCodebase, runCommands, editFile, createFile — MINDEN true
**Git**: user=Jules, editor=code--wait, rebase=true, defaultBranch=main
**Részletek**: `/data/Brain/_qwen_analysis/vscode_mcp_environment.md`

## QWEN 7B P4000 — ŐSZINTE KÉPESSÉG

**Sebesség**: 25 tok/s átlag | **VRAM**: 5864/8192 MiB (72%) | **Load**: 1.5s

| Kategória | Minőség | Példa |
|-----------|---------|-------|
| 🟢 Config, refactor, summary, stub | 7-8/10 | JSON config, list comp, pytest stub |
| 🟡 Közepes kód gen, elemzés | 5-6/10 | Struktúra jó, részletek hibásak |
| 🔴 Pénzügyi ML, production, math | 2-3/10 | TBM hibás, meta-labeling téves, 17×23+45=406❌ |

**VERDIKT**: "Gyors piszkos vázlat-gép" — NEM okos kódoló! Repo áttekintés + scaffold jó. Production kód NEM.
**Részletek**: `/data/Brain/_qwen_analysis/qwen_capability_assessment.md`

## 🚧 HIÁNYOK — AMI MÉG KELL

**Telens lista**: `/data/Brain/_qwen_analysis/ROADMAP_HIANYOK.md`

| # | Feladat | Prioritás | Állapot |
|---|---------|-----------|---------|
| 1 | **Adatforrás tisztázása** (MQL5? CSV? API?) | 🔴 Kritikus | ❌ |
| 2 | **Labeling pipeline futtatása** (1 sikeres TBM) | 🔴 Kritikus | ❌ |
| 3 | **Direction features** (6 feature generálás) | 🔴 Kritikus | ❌ |
| 4 | **Meta-labeling pipeline** (side→meta→size) | 🔴 Kritikus | ❌ |
| 5 | FAISS integráció rag_query-be | 🟡 Fontos | 30% |
| 6 | Qwen 14B letöltés + teszt | 🟡 Fontos | ❌ |
| 7 | Pipeline orchestrator (end-to-end) | 🟡 Fontos | ❌ |
| 8 | VSCode tasks.json + launch.json | 🟢 Jó lenne | ❌ |

**Session memória**: `/data/Brain/_qwen_analysis/SESSION_MEMORY_20261013.md`
