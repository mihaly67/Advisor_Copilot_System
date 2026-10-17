#!/bin/bash
# Session-záró push: gyors git add+commit+push a GitHub repo-ba.
# Hívja a VSCode settings-ből "onExit" vagy manuálisan session végén.
#
# Használat: bash /data/mcp_server/session_push.sh "commit üzenet"

set -e
REPO_DIR="/data/Brain/github_sync/Advisor_Copilot_System"
MCP_DIR="/data/mcp_server"
MSG="${1:-session-sync $(date '+%Y-%m-%d %H:%M')}"

echo "🔄 Session push: $MSG"

# 1. Sync MCP files into repo
mkdir -p "$REPO_DIR/mcp/server" "$REPO_DIR/mcp/config"
cp "$MCP_DIR/server.py" "$REPO_DIR/mcp/server/" 2>/dev/null
cp "$MCP_DIR/mcp_backend_api.py" "$REPO_DIR/mcp/server/" 2>/dev/null
cp "$MCP_DIR/env.sh" "$REPO_DIR/mcp/config/" 2>/dev/null
cp "$MCP_DIR/cortexdb-grpc.init.sh" "$REPO_DIR/mcp/config/" 2>/dev/null
cp "$MCP_DIR/mcp-backend.init.sh" "$REPO_DIR/mcp/config/" 2>/dev/null
cp "$MCP_DIR/build_rust_stack.sh" "$REPO_DIR/mcp/config/" 2>/dev/null
cp "$MCP_DIR/sync_to_github.sh" "$REPO_DIR/mcp/config/" 2>/dev/null
for f in "$MCP_DIR/tools/"*.py; do cp "$f" "$REPO_DIR/mcp/tools/" 2>/dev/null; done

# 2. Quick commit + push
cd "$REPO_DIR"
git add -A
CHANGES=$(git diff --cached --stat 2>/dev/null | wc -l)
if [ "$CHANGES" -eq 0 ]; then
    echo "✅ Nincs változás — skip push"
    exit 0
fi
git commit -m "$MSG" --quiet 2>/dev/null
git push origin main --quiet 2>&1
echo "✅ Pushed $CHANGES változás → mihaly67/Advisor_Copilot_System"
