#!/bin/bash
# MCP Bridge Launcher - Ez a script indítja el az MCP szervert VSCode előtt

echo "🚀 MCP Bridge Indító Szerver"
echo "══════════════════════════════════════════════════════════"
echo ""

# Már fut-e az MCP server?
if ps aux | grep -q "[s]erver.py.*mcp_server/server.py"; then
    echo "✅ MCP server MÁR FUT"
    echo "   PID: $(ps aux | grep '[s]erver.py.*mcp_server/server.py' | awk '{print $2}')"
    echo "   Indítva: $(ps aux | grep '[s]erver.py.*mcp_server/server.py' | awk '{print $9}')"
else
    echo "🔵 MCP server indítása..."
    source /home/Jules/jules_venv/bin/activate
    
    # Háttérben indítjuk a server-t
    nohup python3 /data/mcp_server/server.py > /tmp/mcp_server.log 2>&1 &
    sleep 2
    
    # Ellenőrizzük, hogy sikerült-e
    if ps aux | grep -q "[s]erver.py.*mcp_server/server.py"; then
        echo "✅ MCP server ELINDÍTVA"
        echo "   PID: $(ps aux | grep '[s]erver.py.*mcp_server/server.py' | awk '{print $2}')"
    else
        echo "❌ MCP server HIBÁSAN INDÍTVA!"
        echo "   Ellenőrizze a logot: tail -f /tmp/mcp_server.log"
    fi
fi

echo ""
echo "══════════════════════════════════════════════════════════"
echo "🎯 MCP Server készen áll - Most indíthatod a VSCode-ot"
echo ""
echo "MCP Toolok elérhetőek:"
echo "  • read_repo(path) - Repó fájlok olvasása"
echo "  • write_log(path, content) - Napló/kivonat írása"
echo "  • analyze_with_qwen(target_dir) - Qwen2.5-Coder elemzés"
echo "  • list_gpu() - GPU állapot lekérdezése"
echo "  • store_session(stage, knowledge) - Session mentés"
echo "  • read_session(stage) - Session visszolvasás"
echo ""
echo "══════════════════════════════════════════════════════════"