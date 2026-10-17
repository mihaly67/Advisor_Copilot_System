#!/bin/bash
# MCP + Qwen környezeti beállító - P4000 kényszerítés, P2000 elzárás
# Létrehozta: Cline (2026.09.18)

# === GPU IZOLÁCIÓ: CSAK P4000 (GPU 0) LÁTHATÓ, P2000 ELZÁRVA ===
export CUDA_VISIBLE_DEVICES=0
export CUDA_DEVICE_ORDER=PCI_BUS_ID

# === CUDA RUNTIME LIBRARY PATH (llama-cpp-python prebuilt wheel igényli) ===
_CUDA_LIBS="/home/Jules/jules_venv/lib/python3.11/site-packages/nvidia/cuda_runtime/lib:/home/Jules/jules_venv/lib/python3.11/site-packages/nvidia/cublas/lib"
case ":${LD_LIBRARY_PATH:-}:" in
    *:"${_CUDA_LIBS}":*) : ;;
    *) export LD_LIBRARY_PATH="${_CUDA_LIBS}:${LD_LIBRARY_PATH:-}" ;;
esac
unset _CUDA_LIBS

# === HF CACHE ÁTIRÁNYÍTÁSA /data-re (nehogy a /home telepedjen) ===
export HF_HOME=/data/ml/hf_cache
export HUGGINGFACE_HUB_CACHE=/data/ml/hf_cache
export TRANSFORMERS_CACHE=/data/ml/hf_cache
export HF_DATASETS_CACHE=/data/ml/hf_cache

# === VENV aktiválása ===
source /home/Jules/jules_venv/bin/activate

# === MCP szerver könyvtár ===
export MCP_SERVER_DIR=/data/mcp_server
export MCP_LOG_DIR=/data/mcp_server/logs
export MCP_STATE_DIR=/data/mcp_server/state
export MCP_LOCK_DIR=/data/mcp_server/lock

# === Qwen elemzés célkönyvtárak ===
export QWEN_ANALYSIS_BRAIN=/data/Brain/_qwen_analysis
export QWEN_ANALYSIS_RAG=/home/Jules/RAG_epito_ismeretek/_qwen_analysis

# === Modell kiválasztás: 7B vagy 14B ===
# Alapértelmezett: 14B Q4_K_M (okosabb, 70% GPU terhelés)
# Felülbírálható: QWEN_MODEL_PROFILE=7B vagy QWEN_MODEL_PROFILE=14B
export QWEN_MODEL_PROFILE="${QWEN_MODEL_PROFILE:-14B}"

if [ "$QWEN_MODEL_PROFILE" = "14B" ]; then
    # === 14B Q4_K_M — 70% GPU terhelés (34/48 réteg GPU, 14 CPU offload) ===
    export QWEN_MODEL_ID='Qwen/Qwen2.5-Coder-14B-Instruct-GGUF'
    export QWEN_MODEL_FILE='qwen2.5-coder-14b-instruct-q4_k_m.gguf'
    export QWEN_MODEL_PATH='/data/ml/hf_cache/'$QWEN_MODEL_FILE
    export QWEN_GPU_LAYERS=34  # 70% of 48 layers — GPU kap levegőt
    export QWEN_CONTEXT_SIZE=8192
    export QWEN_N_THREADS=14   # 14 CPU réteghez 14 szál (Xeon bőven bírja)
    export QWEN_TOTAL_LAYERS=48
    export QWEN_GPU_TARGET_PERCENT=70  # Monitorhoz: cél 70% GPU kihasználás
else
    # === 7B Q5_K_M — minden réteg GPU-ra (könnyű futás) ===
    export QWEN_MODEL_ID='Qwen/Qwen2.5-Coder-7B-Instruct-GGUF'
    export QWEN_MODEL_FILE='qwen2.5-coder-7b-instruct-q5_k_m.gguf'
    export QWEN_MODEL_PATH='/data/ml/hf_cache/'$QWEN_MODEL_FILE
    export QWEN_GPU_LAYERS=35  # Minden réteg GPU-ra (7B Q5 = ~5.5GB)
    export QWEN_CONTEXT_SIZE=8192
    export QWEN_N_THREADS=18
    export QWEN_TOTAL_LAYERS=28
    export QWEN_GPU_TARGET_PERCENT=100
fi

# === GPU pause/resume mechanizmus ===
# Ha GPU kell másra, a Qwen feldolgozás szünetel
export QWEN_GPU_PAUSE_FILE='/data/mcp_server/lock/qwen_gpu_paused.flag'
export QWEN_GPU_CHECK_INTERVAL=5  # Másodpercenként ellenőrzi a pause flag-et

# === Biztonsági gátlók (nehogy loopba essen) ===
export QWEN_TIMEOUT_SECONDS=600  # 14B-nek több idő kell
export MCP_LOCK_FILE=/data/mcp_server/lock/mcp.lock

# === Verifikáció kiírása ===
echo '=== MCP + QWEN KÖRNYEZET AKTIVÁLVA ==='
echo 'CUDA_VISIBLE_DEVICES:' $CUDA_VISIBLE_DEVICES
echo 'HF_HOME:' $HF_HOME
echo 'QWEN_MODEL_PROFILE:' $QWEN_MODEL_PROFILE
echo 'QWEN_MODEL_PATH:' $QWEN_MODEL_PATH
echo 'QWEN_GPU_LAYERS:' $QWEN_GPU_LAYERS'/'$QWEN_TOTAL_LAYERS
echo 'QWEN_GPU_TARGET:' $QWEN_GPU_TARGET_PERCENT'%'
