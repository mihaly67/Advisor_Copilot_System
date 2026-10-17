#!/bin/bash
# Restart backend API and test chart_analyzer
set -e

echo ">>> Killing old backend..."
pkill -9 -f mcp_backend_api 2>/dev/null || true
sleep 2

echo ">>> Starting new backend..."
nohup /data/mcp_server/venv/bin/python /data/mcp_server/mcp_backend_api.py &>/tmp/mcp_backend_new.log &
sleep 4

echo ">>> Testing health..."
curl -s http://127.0.0.1:8420/ 2>&1 || echo "API not responding yet"

echo ">>> Testing chart-analyze endpoint (regex)..."
curl -s -X POST http://127.0.0.1:8420/chart-analyze \
  -H 'Content-Type: application/json' \
  -d '{"path": "/data/dev/LGB_copilot_system/viz/viz_pred_2026-08-28.html", "method": "regex"}' \
  2>&1 | /data/mcp_server/venv/bin/python -m json.tool 2>&1 | head -30

echo ">>> Testing chart-analyze on viz_v9 (regex)..."
curl -s -X POST http://127.0.0.1:8420/chart-analyze \
  -H 'Content-Type: application/json' \
  -d '{"path": "/data/dev/projects/z-ai-copilot/docs/viz_v9.html", "method": "regex"}' \
  2>&1 | /data/mcp_server/venv/bin/python -m json.tool 2>&1 | head -30

echo ">>> Done!"
