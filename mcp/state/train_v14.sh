#!/usr/bin/env bash
cd /data/dev/projects/z-ai-copilot

echo "=== V14: 100 feature, V7 binary labeling ==="
/home/Jules/jules_venv/bin/python3 src/train_lgbm_v2.py \
    --version v14 \
    --data Master_csv/processed/labeled_dollar_bars_v7.csv \
    2>&1 | tail -35
