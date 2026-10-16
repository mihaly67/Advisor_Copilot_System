#!/usr/bin/env bash
cd /data/dev/projects/z-ai-copilot

echo "=== V18: top 30 feature (V6 labeling) ==="
/home/Jules/jules_venv/bin/python3 src/train_lgbm_v2.py \
    --version v18 \
    --data Master_csv/processed/labeled_dollar_bars_v6.csv \
    --features models/v17/features_top30.txt \
    2>&1 | tail -25

echo ""
echo "=== V18 short_zero (Long-only baseline) ==="
/home/Jules/jules_venv/bin/python3 src/train_lgbm_v2.py \
    --version v18_long_only \
    --data Master_csv/processed/labeled_dollar_bars_v6.csv \
    --features models/v17/features_top30.txt \
    --short_zero \
    2>&1 | tail -15
