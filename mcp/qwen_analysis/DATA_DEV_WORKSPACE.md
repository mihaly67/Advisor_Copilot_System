# /data/dev — Központi Fejlesztői Munkaterület

> **Létrehozva:** 2026.09.22.
> **Git commit-ek:** 3 (665424b → 9227b07 → b5982c4)

## 🗺️ Végső Struktúra

```
/data/dev/
├── venv/                          # Központi Python venv (7.1 GB, 188 csomag)
├── projects/
│   ├── scalper-copilot/           # ← LGBM_mlops (migrálva)
│   └── hardver-monitor/           # ← HardverMonitor_dev (migrálva)
├── libs/
│   ├── mql5/ → /data/ml/mql5/     # MQL5 EA forrás
│   ├── pine-script/ → /data/ml/pine_script/
│   └── common/                    # Közös Python modulok
├── docs/
│   ├── adr/                       # Architecture Decision Records
│   │   └── ADR-001-central-dev-workspace.md
│   ├── api/
│   └── guides/
│       └── DEVELOPER_GUIDE.md
├── data/
│   ├── brain-rag.db → /data/Brain/_vectorized/brain_rag.db
│   ├── ml-rag.db → /data/ml/_vectorized/ml_rag_v2.db
│   └── mcp-state/ → /data/mcp_server/state/
├── config/
│   ├── cline/ → /home/Jules/.cline
│   └── env/
│       └── .env.template
├── scripts/
│   ├── setup_dev.sh
│   ├── start_mcp.sh
│   ├── backup.sh
│   └── init.sh
├── logs/
├── .gitignore
├── .editorconfig
├── README.md
├── Makefile
└── requirements.txt
```

## Backward Symlinks (régi útvonalak)
- `/home/Jules/LGBM_mlops` → `/data/dev/projects/scalper-copilot`
- `/home/Jules/HardverMonitor_dev` → `/data/dev/projects/hardver-monitor`

## Központi Venv (188 csomag, 7.1 GB)
- lightgbm 4.7, torch 2.14, optuna 5.0, shap 0.51
- pandas 3.0, numpy 2.4, scikit-learn 1.9
- pyzmq 27.2, PyQt5 5.15, pyqtgraph 0.14
- chromadb 1.5, sentence-transformers 6.1, faiss-cpu 1.15
- vectorbt 1.1, pyts 0.12, loguru 0.7
- pytest 9.1, black 26.5, ruff 0.16, mypy 2.3

## Lemezhasználat
| Partíció | Előtte | Utána | Felszabadítva |
|----------|--------|-------|---------------|
| /data | 37G/219G | 25G/219G | 12G (venv 7.1G + repók törlése) |
| /home | 128G/156G | 113G/156G | 15G (pip cache 17G + projekt migrálás -2G) |

## Takarítás (összesen ~38 GB törölve)
- pip cache: 17 GB
- hf_cache: 14 GB
- Használatlan repók: skyvern, jan, llama.cpp, donut, khoj, gemini, open-webui, AutoGPT, UFO, LaVague, RagaAI, vibe-kanban, aider, phidata, guardrails, openhands, postgres, lobehub, ray, blackbox-CNN, streamlit, mlflow, FinRL, FlagEmbedding, airflow, openvino
- .zip fájlok, __pycache__, nohup.out

## Megjegyzések
- MetaTrader5: Windows-only, Linux-on mt5linux bridge használata
- pyts 0.13.0: Python 3.12+ kell, pin 0.12.0 (Python 3.11.2 van)
- `dev` alias: `alias dev="cd /data/dev && source /data/dev/venv/bin/activate"`
