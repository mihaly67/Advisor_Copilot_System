#!/bin/bash
# Szinkronizáló script: MCP szerver fájljai → GitHub mihaly67/Advisor_Copilot_System
# A repo mcp/ mappájába másolja a fontos fájlokat és pusholja.
#
# Használat:
#   export GH_TOKEN=<github_personal_access_token>
#   bash /data/mcp_server/sync_to_github.sh
#
# vagy ha gh CLI autholva van:
#   bash /data/mcp_server/sync_to_github.sh

set -e
REPO="mihaly67/Advisor_Copilot_System"
LOCAL_REPO="/data/Brain/github_sync/Advisor_Copilot_System"
MCP_DIR="/data/mcp_server"
SYNC_DIR="$LOCAL_REPO/mcp"

echo "🔄 MCP → GitHub Sync"
echo "===================="

# 1. Load tokens
[ -f /data/mcp_server/.gh_token ] && source /data/mcp_server/.gh_token
[ -f /data/mcp_server/.zhipu_key ] && source /data/mcp_server/.zhipu_key

# 2. Auth check
if ! gh auth status &>/dev/null; then
    if [ -z "$GH_TOKEN" ]; then
        echo "❌ Nincs GitHub auth. Állíts be GH_TOKEN vagy futtass gh auth login"
        echo "   Token: https://github.com/settings/tokens (scope: repo)"
        exit 1
    fi
    echo "$GH_TOKEN" | gh auth login --with-token
    echo "✅ GH CLI autholva token-nel"
fi
echo "✅ GitHub auth OK ($(gh api user -q .login))"

# 2. Clone/update repo
if [ -d "$LOCAL_REPO" ]; then
    echo "📥 Pulling latest..."
    cd "$LOCAL_REPO" && git pull --rebase 2>/dev/null || true
else
    echo "📥 Cloning $REPO..."
    mkdir -p "$(dirname "$LOCAL_REPO")"
    gh repo clone "$REPO" "$LOCAL_REPO"
fi
cd "$LOCAL_REPO"

# 3. Sync MCP files
echo "📁 Syncing MCP files..."
mkdir -p "$SYNC_DIR/server"
mkdir -p "$SYNC_DIR/tools"
mkdir -p "$SYNC_DIR/config"
mkdir -p "$SYNC_DIR/docs"

# Main server files
cp "$MCP_DIR/server.py" "$SYNC_DIR/server/"
cp "$MCP_DIR/mcp_backend_api.py" "$SYNC_DIR/server/"
cp "$MCP_DIR/env.sh" "$SYNC_DIR/config/"
cp "$MCP_DIR/cortexdb-grpc.init.sh" "$SYNC_DIR/config/"
cp "$MCP_DIR/mcp-backend.init.sh" "$SYNC_DIR/config/"
cp "$MCP_DIR/build_rust_stack.sh" "$SYNC_DIR/config/"
cp "$MCP_DIR/.gitignore" "$SYNC_DIR/" 2>/dev/null

# Tool files (Python only, not compiled)
for f in "$MCP_DIR/tools/"*.py; do
    [ -f "$f" ] && cp "$f" "$SYNC_DIR/tools/"
done

# Analysis/docs
cp -r /data/Brain/_qwen_analysis/ "$SYNC_DIR/docs/brain_analysis/" 2>/dev/null || true

# 4. Git commit & push
echo "💾 Committing..."
cd "$LOCAL_REPO"
git add -A
CHANGES=$(git diff --cached --stat | wc -l)
if [ "$CHANGES" -eq 0 ]; then
    echo "✅ Nincs változás — repo naprakész"
    exit 0
fi

TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
COMMIT_MSG="mcp: sync $TIMESTAMP — $(git diff --cached --stat | tail -1)"

git commit -m "$COMMIT_MSG" 2>&1 | tail -3
echo "🚀 Pushing to $REPO..."
git push origin main 2>&1 | tail -3

echo ""
echo "✅ Szinkronizálva! $CHANGES fájl változott."
echo "   https://github.com/$REPO/tree/main/mcp"
