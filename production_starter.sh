#!/bin/bash
source /data/mcp_server/env.sh
nohup /data/mcp_server/venv/bin/python3 /data/mcp_server/server.py >> /tmp/mcp-bridge.log 2>&1 &
echo $! > /tmp/mcp-bridge.pid
echo "MCP server started with PID: $(cat /tmp/mcp-bridge.pid)"
