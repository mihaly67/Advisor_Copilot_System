#!/usr/bin/env bash
cd /data/dev/projects/z-ai-copilot

# V11: top 20 feature
echo "=== V11: top 20 feature ==="
/home/Jules/jules_venv/bin/python3 src/shap_prune.py --input v10 --top 20 2>&1

# V12: top 10 feature
echo "=== V12: top 10 feature ==="
/home/Jules/jules_venv/bin/python3 src/shap_prune.py --input v10 --top 10 2>&1

echo "=== V11 features ==="
cat models/v10_pruned/features.txt
echo "=== V12 features ==="
cat models/v10_pruned_10/features.txt 2>/dev/null || echo "checking..."
ls models/v10*/
