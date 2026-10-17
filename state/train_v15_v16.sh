#!/usr/bin/env bash
cd /data/dev/projects/z-ai-copilot

echo "=== V15: 15 bar binary labeling ==="
/home/Jules/jules_venv/bin/python3 src/train_lgbm_v2.py \
    --version v15 \
    --data Master_csv/processed/labeled_dollar_bars_v7_15.csv \
    2>&1 | tail -25

echo ""
echo "=== V16: V6 labeling (triple barrier szimmetrikus), top 20 SHAP ==="
/home/Jules/jules_venv/bin/python3 src/train_lgbm_v2.py \
    --version v16 \
    --data Master_csv/processed/labeled_dollar_bars_v6.csv \
    --features models/v10/features_top20.txt \
    --short_zero \
    2>&1 | tail -25
