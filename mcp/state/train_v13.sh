#!/usr/bin/env bash
cd /data/dev/projects/z-ai-copilot

echo "=== V13: 100 feature (uj irany-specifikusokkal) ==="
/home/Jules/jules_venv/bin/python3 src/train_lgbm_v2.py \
    --version v13 \
    --data Master_csv/processed/labeled_dollar_bars_v6.csv \
    2>&1 | tail -30
