# Session: data_dev_workspace_20260922
*Időbélyeg: 2026-09-22T15:53:37.955221*

# SESSION: /data/dev Központi Munkaterület — 2026.09.22.

## TASK CÉL
Szoftverfejlesztői infrastruktúra kialakítása: takarítás + /data/dev struktúra + központi venv + projektek migrálás + dokumentáció + verziókövetés.

## KÉSZ ✅

### 1. Takarítás (~38 GB felszabadítva)
- pip cache (17G), hf_cache (14G), ray (1.2G)
- Használatlan repók: skyvern, jan, llama.cpp, donut, khoj, gemini, open-webui, AutoGPT, UFO, LaVague, RagaAI, vibe-kanban, aider, phidata, guardrails, openhands, postgres, lobehub, blackbox-CNN, streamlit, mlflow, FinRL, FlagEmbedding, airflow, openvino
- .zip, __pycache__, nohup.out törlése

### 2. /data/dev Struktúra
- venv/, projects/, libs/, docs/, data/, config/, scripts/, logs/
- .gitignore, .editorconfig, README.md, Makefile, requirements.txt
- Git: 3 commit (665424b → 9227b07 → b5982c4)

### 3. Központi Venv (7.1 GB, 188 csomag)
- Python 3.11.2, lightgbm, torch, optuna, shap, pandas, numpy, pyzmq, PyQt5, pyqtgraph, chromadb, sentence-transformers, faiss-cpu, vectorbt, pyts, loguru, pytest, black, ruff, mypy
- MetaTrader5: Windows-only (mt5linux bridge)
- pyts: pin 0.12.0 (0.13 needs Python 3.12+)

### 4. Projektek Migrálva
- LGBM_mlops → /data/dev/projects/scalper-copilot
- HardverMonitor_dev → /data/dev/projects/hardver-monitor
- Backward symlinks a régi helyeken

### 5. Symlinks
- libs/mql5 → /data/ml/mql5
- libs/pine-script → /data/ml/pine_script
- data/brain-rag.db → /data/Brain/_vectorized/brain_rag.db
- data/ml-rag.db → /data/ml/_vectorized/ml_rag_v2.db
- data/mcp-state → /data/mcp_server/state
- config/cline → /home/Jules/.cline

### 6. Szkriptek
- scripts/setup_dev.sh, start_mcp.sh, backup.sh, init.sh
- Makefile: setup, test, lint, clean, backup, start-mcp
- `dev` alias: cd /data/dev && source venv/bin/activate

### 7. Dokumentáció
- ADR-001: central dev workspace decision
- DEVELOPER_GUIDE.md: konvenciók, struktúra, RAG, rendszer
- .env.template: MCP, Qwen, MT5, ZMQ, Trading config

## LEMEZ: /data 25G/219G, /home 113G/156G