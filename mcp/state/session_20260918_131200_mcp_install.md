# Session: MCP + Qwen telepítés és konfiguráció

*Időbélyeg: 2026-09-18 13:12*

## Telepített csomagok (jules_venv-be)
- **mcp 2.2.0** + **mcp-types 2.2.0** (Model Context Protocol Python SDK)
- **langchain 1.4.1** + **langchain-core 1.6.3** + **langchain-protocol 0.0.19**
- **langgraph 1.2.11** + **langgraph-checkpoint 4.2.0** + **langgraph-prebuilt 1.1.0** + **langgraph-sdk 0.4.4**
- **langsmith 0.12.6** (langchain monitorozáshoz)
- **llama-cpp-python 0.3.35** (prebuilt CUDA 11.8 wheel, 1.2GB, forrás: https://abetlen.github.io/llama-cpp-python/whl/cu118)
- **nvidia-cuda-runtime-cu11 11.8.89** (libcudart.so.11.0)
- **nvidia-cublas-cu11 11.11.3.6** (libcublas.so.11, 418MB)
- Már megvolt: torch 2.1.2+cu118, transformers 4.40.0, sentence-transformers 2.7.0, faiss-cpu 1.7.4

## Letöltött modell
- **Modell**: Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
- **Fájl**: `qwen2.5-coder-7b-instruct-q5_k_m.gguf`
- **Méret**: 5192 MB (Q5_K_M kvantálás - magasabb minőség a Q4-nél)
- **Hely**: `/data/ml/hf_cache/models--Qwen--Qwen2.5-Coder-7B-Instruct-GGUF/snapshots/13fb94bfda8c8cf22497dc57b78f391a9acb426a/`
- **Mi ezt választottuk**: a legokosabb P4000 8GB VRAM korlátok között (7B Coder > 3B Instruct; Q5_K_M > Q4_K_M; llama.cpp Pascal-támogatása szilárdabb mint vLLM AWQ kernelje)

## LD_LIBRARY_PATH (kritikus a llama-cpp-python-hoz)
A prebuilt wheel `libcudart.so.11.0`-t és `libcublas.so.11`-et keresi. A torch cu118 wheel-je is hozza,
de a legbiztosabb a külön nvidia-cuda-runtime-cu11 és nvidia-cublas-cu11 csomagok használata:
```
export LD_LIBRARY_PATH=/home/Jules/jules_venv/lib/python3.11/site-packages/nvidia/cuda_runtime/lib:/home/Jules/jules_venv/lib/python3.11/site-packages/nvidia/cublas/lib:${LD_LIBRARY_PATH:-}
```

## Próbált venv a /data-n (SIKERTELEN)
A `python3 -m venv /data/mcp_venv` létrejött, de a pip 26.2.1-ben bug volt (NoneType version hiba),
majd a cert hiányzott. Ezért az `env.sh` a `jules_venv`-et használja (már működő, torch-cal).
A /data/mcp_venv törölve.

## HF cache átirányítása /data-re
- `/home` partíció: 156GB, 113GB foglalt (76%) - SZŰK
- `/data` partíció: 219GB, 13GB foglalt (7%) - BŐSÉGES
- `export HF_HOME=/data/ml/hf_cache` (minden Qwen-modell ide jön, nem a /home-ra)

## Könyvtárstruktúra
```
/data/mcp_server/
├── env.sh                      # környezeti beállító (GPU izoláció, HF cache, venv, modell)
├── server.py                   # MCP szerver (stdio transport, 6 tool)
├── tools/
│   └── qwen_analyzer.py        # Qwen2.5-Coder repó-elemző wrapper
├── logs/
│   ├── qwen_analyzer.log       # Qwen analyzer időbélyegzett logja
│   └── mcp_server.log          # MCP szerver logja
├── state/
│   ├── session_*.md            # session-tudás (ez a fájl is ide kerül)
│   └── session_index.md        # közös index
└── lock/
    └── mcp.lock                # intelligens lock (PID-alapú, stale detection)
```

/data/Brain/_qwen_analysis/ és /home/Jules/RAG_epito_ismeretek/_qwen_analysis/ - Qwen által írt elemzések
