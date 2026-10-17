#!/bin/bash
# ============================================================================
# batch_qwen_ml_repos.sh — Qwen mélyelemzés az összes /data/ml repóra
# ============================================================================
# Futtatás:  nohup bash /data/mcp_server/tools/batch_qwen_ml_repos.sh &
# Log:       /data/mcp_server/logs/batch_qwen_ml_repos.log
# ============================================================================

source /data/mcp_server/env.sh

LOGFILE="/data/mcp_server/logs/batch_qwen_ml_repos.log"
PROGRESS_FILE="/data/mcp_server/state/batch_qwen_ml_progress.json"
ML_DIR="/data/ml"
ANALYZER="/data/mcp_server/tools/qwen_analyzer.py"

mkdir -p /data/mcp_server/logs /data/mcp_server/state

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOGFILE"
}

# Prioritási sorrend (trading-relevancia alapján)
PRIORITY_REPOS=(
    "barrier-method-main"
    "triple_barrier-main"
    "LightGBM-main"
    "LightGBM-Quant-Model-master"
    "LGBM-Stock-Prediction-main"
    "mljar-supervised"
    "Stock-Prediction-with-LSTM-GRU-master"
    "Stock-Price-Prediction-LSTM-main"
    "LSTM-Autoencoders-master"
    "LSTM-AutoEncoder-Unsupervised-Anomaly-Detection-master"
    "Anomaly_Detect_LSTM-master"
    "Time-Series-Library-main"
    "PatchTST-main"
    "ts2vec-main"
    "Transformer-Time-Series-Model-main"
    "SiamTST-main"
    "TimeSiam-main"
    "FinRL-master"
    "FinRL-Meta-master"
    "FinRL-Trading-master"
    "vectorbt-main"
    "qlib-main"
    "tensortrade-master"
    "TradingAgents-main"
    "AgenticTrading-main"
    "Reinforcement-Learning-for-Market-Making-main"
    "reinforcement_learning_trading_agent-master"
    "airl-market-making-main"
    "MARLlib-master"
    "marl-master"
    "rl_markets-main"
    "rmm.arl-master"
    "ROMA-main"
    "PantheonRL-master"
    "kalshi-ai-trading-bot-main"
    "xauusd-scalping-ai"
    "Hunter-main"
    "quantreplay-main"
    "Quant_Repos"
    "mt5linux-master"
    "pymt5linux-main"
    "mql-zmq"
    "python-mmap-ipc-master"
    "ta-lib-main"
    "ta-lib-python-master"
    "Technical-Analysis-Indicators---Pandas-master"
    "stumpy-main"
    "yfinance-main"
    "ArcticDB-master"
    "findatapy-main"
    "finmarketpy-main"
    "PyPortfolioOpt-master"
    "Riskfolio-Lib-master"
    "quantstats-main"
    "optuna-master"
    "shap-master"
    "shap"
    "mlflow-master"
    "zenml-master"
    "prefect-main"
    "airflow-main"
    "DART-master"
    "AlphaPy-master"
    "Anomaly-Detection-with-Siamese-Neural-Nets-master"
    "dtaianomaly-main"
    "dtaidistance-main"
    "hidden_markov-master"
    "hidden-markov-model-master"
    "hidden_markov_model_temporal_graphs-main"
    "hmmlearn-master"
    "Hands-On-Markov-Models-with-Python-master"
    "river-main"
    "deep-river-master"
    "eventstudy-main"
    "Event_Study-main"
    "eventstudy-master"
    "EventStudy-master"
    "easy-event-study-main"
    "Parallel_Trends-main"
    "stock-prediction-main"
    "Stock-Prediction-Models-master"
    "Machine-Learning-for-Finance-master"
    "algrythm"
    "loguru-master"
    "pydantic-main"
    "pybind11-master"
)

# Összes repó amik nincsenek a prioritási listában
ALL_REPOS=()
for d in "$ML_DIR"/*/; do
    name=$(basename "$d")
    ALL_REPOS+=("$name")
done

# Egyesítés: prioritásiak először, utána a többi
PROCESSED=()
for repo in "${PRIORITY_REPOS[@]}"; do
    if [ -d "$ML_DIR/$repo" ]; then
        PROCESSED+=("$repo")
    fi
done
for repo in "${ALL_REPOS[@]}"; do
    skip=false
    for p in "${PRIORITY_REPOS[@]}"; do
        if [ "$repo" = "$p" ]; then
            skip=true
            break
        fi
    done
    if ! $skip; then
        PROCESSED+=("$repo")
    fi
done

TOTAL=${#PROCESSED[@]}
log "=========================================="
log "BATCH QWEN ML REPO ANALYSIS INDITASA"
log "Összes repó: $TOTAL"
log "=========================================="

DONE_COUNT=0
SKIP_COUNT=0
FAIL_COUNT=0

echo "{\"total\": $TOTAL, \"done\": 0, \"skipped\": 0, \"failed\": 0, \"current\": \"\"}" > "$PROGRESS_FILE"

for repo in "${PROCESSED[@]}"; do
    target="$ML_DIR/$repo"

    if [ -d "$target/_qwen_analysis" ]; then
        log "[SKIP] $repo — már elemzve"
        SKIP_COUNT=$((SKIP_COUNT + 1))
        continue
    fi

    IDX=$((DONE_COUNT + SKIP_COUNT + FAIL_COUNT + 1))
    log "[ANALYZE] ($IDX/$TOTAL) $repo"
    echo "{\"total\": $TOTAL, \"done\": $DONE_COUNT, \"skipped\": $SKIP_COUNT, \"failed\": $FAIL_COUNT, \"current\": \"$repo\"}" > "$PROGRESS_FILE"

    # Lock várakozás
    while [ -f /data/mcp_server/lock/mcp.lock ]; do
        PID=$(cat /data/mcp_server/lock/mcp.lock 2>/dev/null)
        if kill -0 "$PID" 2>/dev/null; then
            sleep 10
        else
            rm -f /data/mcp_server/lock/mcp.lock
            break
        fi
    done

    timeout 600 python3 "$ANALYZER" "$target" --max-files 25 --max-tokens 1800 >> "$LOGFILE" 2>&1
    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        log "  ✅ $repo kész"
        DONE_COUNT=$((DONE_COUNT + 1))
    else
        log "  ❌ $repo HIBA (exit $EXIT_CODE)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        rm -f /data/mcp_server/lock/mcp.lock
    fi

    sleep 5
done

log "=========================================="
log "BATCH BEFEJEZVE: Kész=$DONE_COUNT Kihagyva=$SKIP_COUNT Hiba=$FAIL_COUNT Összes=$TOTAL"
log "=========================================="
echo "{\"total\": $TOTAL, \"done\": $DONE_COUNT, \"skipped\": $SKIP_COUNT, \"failed\": $FAIL_COUNT, \"current\": \"\", \"end\": \"$(date -Iseconds)\"}" > "$PROGRESS_FILE"

