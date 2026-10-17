#!/usr/bin/env bash
cd /data/dev/projects/z-ai-copilot

echo "=== Feature engineering ujra (V8 feature set: +18 nyers return) ==="
/home/Jules/jules_venv/bin/python3 src/dom_feature_engineer_mtf.py 2>&1 | tail -20

echo ""
echo "=== V7 labeling ujra (binary) ==="
/home/Jules/jules_venv/bin/python3 src/dom_labeler_v7.py 2>&1 | tail -15

echo ""
echo "=== V16: 118 feature (100 + 18 nyers return), V7 binary labeling ==="
/home/Jules/jules_venv/bin/python3 src/train_lgbm_v2.py \
    --version v16 \
    --data Master_csv/processed/labeled_dollar_bars_v7.csv \
    2>&1 | tail -30
