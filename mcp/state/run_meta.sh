#!/usr/bin/env bash
cd /data/dev/projects/z-ai-copilot

echo "=== META V1: 30 feature, V8 meta-labeling ==="
/home/Jules/jules_venv/bin/python3 src/train_lgbm_meta.py \
    --version meta_v1 \
    --data Master_csv/processed/labeled_dollar_bars_v8.csv \
    --features models/v17/features_top30.txt \
    2>&1

echo ""
echo "=== META V2: all 114 feature ==="
/home/Jules/jules_venv/bin/python3 src/train_lgbm_meta.py \
    --version meta_v2 \
    --data Master_csv/processed/labeled_dollar_bars_v8.csv \
    2>&1 | tail -25
