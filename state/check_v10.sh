#!/usr/bin/env bash
cd /data/dev/projects/z-ai-copilot
echo "=== V10 SHAP TOP 25 ==="
head -26 models/v10/shap_importance.csv
echo ""
echo "=== V10 METRICS ==="
cat models/v10/metrics.json
