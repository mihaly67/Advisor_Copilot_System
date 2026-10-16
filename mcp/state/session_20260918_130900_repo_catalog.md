# Session: /data/Brain és /home/Jules/RAG_epito_ismeretek repó-katalógus

*Időbélyeg: 2026-09-18 13:09*

## /data/Brain (63 könyvtár - AI infrastruktúra gyűjtemény)
Ez a fő "agyi" tudásbázis. Minden megvan az MCP+Qwen+RAG+tudásgráf stack-hez:

### MCP stack
- `modelcontextprotocol-main` - hivatalos MCP spec (JS/TS, schema, plugins)
- `mcp-server-main` - referencia MCP szerver
- `brave-search-mcp-server-main` - webes keresés MCP tool
- `debugger-mcp-main` - hibakereső MCP
- `create-python-server-main` - python MCP szerver generátor

### Qwen
- `Qwen-Agent` - Python, támogatja `[rag, mcp, code_interpreter]` extra-kat. `run_server.py`, `qwen_agent/`, `qwen_server/`
- `/data/ml/Qwen-main` (nem Brain, hanem ml) - Qwen forráskód + technikai jelentés PDF

### Tudásgráf
- `graphrag-main` - Microsoft GraphRAG (alapos, LLM-igényes, 10+ packages)
- `LightRAG-main` - könnyebb alternatíva (kevesebb LLM hívás, Docker support)
- `FlagEmbedding-master` - embedding modellek

### RAG / Langchain stack
- `langchain-master` - langchain framework
- `langgraph-main` - langgraph (agent orchestration)
- `chroma-main` - ChromaDB vector store
- `llama.cpp` - C++ LLM inference engine (van benne `convert_hf_to_gguf.py`)
- `mem0-aio` - memória réteg agent-ekhez
- `llm-api-proxy`, `llm-main` - LLM API proxy-k

### Agent framework-ök
- `autogen-main` - Microsoft AutoGen
- `openai-agents-python` - OpenAI Agents SDK
- `deepagents-main`, `agentic-os-core` - agent OS-ek
- `AutoGPT-master` - AutoGPT platform (FastAPI backend, Next.js frontend)
- `open-interpreter`, `code-interpreter-main` - kód-interpretálók

### UI / frontend
- `open-webui-main` - web UI LLM-ekhez
- `chatbox-main`, `jan-main`, `khoj` - chat UI-k
- `browser-use`, `LaVague`, `UFO`, `OS-Copilot` - böngésző/OS agent-ek

### További fontos
- `gemini-cli-main`, `gemini_extensions` - Gemini integráció
- `infra-main` - infra tooling
- `marker-master` - PDF/markdown konverzió
- `bloop-main`, `bloop-oss` - kódkereső
- `infinity-main` - model serving
- `guardrails` - LLM output validáció
- `ext-auth-main` - external auth
- `jan-main` - lokális AI chat
- `CogAgent`, `donut`, `OmniParser`, `OS-Atlas`, `SeeClick`, `UIED` - vizuális/GUI agent-ek
- `DS4SD.Docling-main` - dokumentumfeldolgozás
- `E2B-main`, `e2b-cookbook-main` - sandboxed kódfuttatás
- `CRSM` - (specifikus projekt)

## /home/Jules/RAG_epito_ismeretek (3.4GB - RAG tooling)
Meglévő RAG építő kód és adatok:

### RAG framework-ök
- `langchain-master`, `langgraph-main` - (Brain-ben is megvan)
- `llama_index-main` - LlamaIndex RAG
- `chroma-main`, `faiss-main` - vector store-ok
- `sentence-transformers-main` - embedding modellek
- `all-MiniLM-L6-v2-main`, `minilm-v2-main`, `Pytorch-MiniLM-master` - MiniLM modellek
- `sqlite-vec-main` - SQLite vektor kiterjesztés
- `simsearch-master` - hasonlósági keresés
- `graphrag-main` - (Brain-ben is megvan)
- `fastembed-main` - gyors embedding
- `towhee` - data pipeline

### Saját scriptek
- `advanced_rag_search.py` - RAG kereső (JAVÍTVA: timeout, iteráció-számláló, GPU kényszerítés)
- `9_perfect_gpu_vectorize.py` - GPU-s vektorizáló (WAL checkpointing, 384 batch size)
- `gpu_limited_vectorize.py` - a /data/ml-ben (a jelenlegi ml.db/ml.index ezt készítette)

### /data/ml (8.9GB - vektorizált tudásbázis)
- `ml.db` (996 MB SQLite, 1 375 785 rekord, `ml_data` tábla: source_repo, filepath, content)
- `ml.index` (2.1 GB FAISS IndexIDMap, L2 távolság)
- `ml.jsonl` (972 MB, a vektorizáció forrása)
- Több mint 100 repo vektorizálva: chartpy, shap, FinRL, LightGBM, vectorbt, ta-lib, Qwen, ray, stb.
- **FONTOS**: `mlfinlab` NINCS benne a vektorizált adatbázisban (ezért nem találta meg a korábbi "dollar bars" keresés)

## /home/Jules/jules_venv (11GB - fő Python környezet)
- Python 3.11.2
- torch 2.1.2+cu118, transformers 4.40.0, sentence-transformers 2.7.0, faiss-cpu 1.7.4
- Újonnan telepítve: mcp 2.2.0, langchain 1.4.1, langgraph 1.2.11, llama-cpp-python 0.3.35, nvidia-cuda-runtime-cu11, nvidia-cublas-cu11
