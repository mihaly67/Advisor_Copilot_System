#!/bin/bash
# ============================================================
# Scalper V6 — Bridge + HUD indító/leállító script
# Használat:
#   ./scalper_v6_start.sh          # indítás (bridge háttérben + HUD előtér)
#   ./scalper_v6_start.sh stop     # leállítás (bridge + HUD)
#   ./scalper_v6_start.sh status   # státusz
#   ./scalper_v6_start.sh restart  # újraindítás
# ============================================================

set -e

# ─── KONFIG ───
VENV="/home/Jules/jules_venv"
BRIDGE="/data/LGBM_copilot/src/scalper_v6_online_bridge.py"
HUD="/data/LGBM_copilot/src/dual_hud_v6.py"
BRIDGE_LOG="/tmp/scalper_v6_bridge.log"
HUD_LOG="/tmp/scalper_v6_hud.log"
BRIDGE_PID_FILE="/tmp/scalper_v6_bridge.pid"
HUD_PID_FILE="/tmp/scalper_v6_hud.pid"
# TCP szerver port (Merkava EA InpDomBridgePort=5556, kliensként csatlakozik)
# ZMQ PUB port 5557 (HUD SUB ide csatlakozik)

# QT_QPA_PLATFORM: üres = látható HUD ablak; 'offscreen' = láthatatlan (debug)
#   Alapértelmezett: látható ablak. Debug-hoz: QT_QPA_PLATFORM=offscreen ./scalper_v6_start.sh start
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-}"
export QTWEBENGINE_DISABLE_GPU="1"
export QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --disable-software-rasterizer"
# DISPLAY beállítása ha nincs (GUI-hoz kell a X11-nek)
export DISPLAY="${DISPLAY:-:0}"

# ─── SEGÉD FÜGGVÉNYEK ───
is_bridge_running() {
    # 1. Ellenőrizzük a PID fájlt
    if [ -f "$BRIDGE_PID_FILE" ] && kill -0 "$(cat $BRIDGE_PID_FILE)" 2>/dev/null; then
        return 0
    fi
    # 2. Ha PID fájl nincs, de a folyamat él — azonosítsuk pgrep-tel
    local pid=$(pgrep -f 'scalper_v6_online_bridge.py' | head -1)
    if [ -n "$pid" ]; then
        # Frissítjük a PID fájlt, hogy a későbbi stop működjön
        echo $pid > "$BRIDGE_PID_FILE"
        return 0
    fi
    return 1
}

is_hud_running() {
    if [ -f "$HUD_PID_FILE" ] && kill -0 "$(cat $HUD_PID_FILE)" 2>/dev/null; then
        return 0
    fi
    local pid=$(pgrep -f 'dual_hud_v6.py' | head -1)
    if [ -n "$pid" ]; then
        echo $pid > "$HUD_PID_FILE"
        return 0
    fi
    return 1
}

start_bridge() {
    if is_bridge_running; then
        echo "✅ Bridge már fut (PID $(cat $BRIDGE_PID_FILE))"
        return 0
    fi
    echo "🚀 Bridge indítása... (TCP szerver port 5556, ZMQ PUB 5557)"
    source "$VENV/bin/activate"
    nohup python3 "$BRIDGE" > "$BRIDGE_LOG" 2>&1 &
    local pid=$!
    echo $pid > "$BRIDGE_PID_FILE"
    sleep 2
    if kill -0 $pid 2>/dev/null; then
        echo "   ✅ Bridge fut (PID $pid)"
        echo "   📝 Log: $BRIDGE_LOG"
    else
        echo "   ❌ Bridge indítás sikertelen!"
        tail -5 "$BRIDGE_LOG" 2>/dev/null
        rm -f "$BRIDGE_PID_FILE"
        return 1
    fi
}

start_hud() {
    if is_hud_running; then
        echo "✅ HUD már fut (PID $(cat $HUD_PID_FILE))"
        return 0
    fi
    echo "🖥️  HUD indítása..."
    source "$VENV/bin/activate"
    nohup python3 "$HUD" > "$HUD_LOG" 2>&1 &
    local pid=$!
    echo $pid > "$HUD_PID_FILE"
    sleep 3
    if kill -0 $pid 2>/dev/null; then
        echo "   ✅ HUD fut (PID $pid)"
        echo "   📝 Log: $HUD_LOG"
    else
        echo "   ❌ HUD indítás sikertelen!"
        tail -10 "$HUD_LOG" 2>/dev/null
        rm -f "$HUD_PID_FILE"
        return 1
    fi
}

stop_bridge() {
    if is_bridge_running; then
        local pid=$(cat $BRIDGE_PID_FILE)
        echo "⏹️  Bridge leállítása (PID $pid)..."
        kill $pid 2>/dev/null || true
        sleep 2
        kill -9 $pid 2>/dev/null || true
        rm -f "$BRIDGE_PID_FILE"
        echo "   ✅ Bridge leállt"
    else
        echo "   ℹ️  Bridge nem futott"
        rm -f "$BRIDGE_PID_FILE"
    fi
}

stop_hud() {
    if is_hud_running; then
        local pid=$(cat $HUD_PID_FILE)
        echo "⏹️  HUD leállítása (PID $pid)..."
        kill $pid 2>/dev/null || true
        sleep 2
        kill -9 $pid 2>/dev/null || true
        rm -f "$HUD_PID_FILE"
        echo "   ✅ HUD leállt"
    else
        echo "   ℹ️  HUD nem futott"
        rm -f "$HUD_PID_FILE"
    fi
}

show_status() {
    echo "═══════════════════════════════════════════════════"
    echo "  Scalper V6 Bridge + HUD Státusz"
    echo "═══════════════════════════════════════════════════"
    if is_bridge_running; then
        echo "  🟢 Bridge: FUT (PID $(cat $BRIDGE_PID_FILE))"
        echo "     Log: $BRIDGE_LOG"
        echo "     Utolsó 3 sor:"
        tail -3 "$BRIDGE_LOG" 2>/dev/null | sed 's/^/       /'
    else
        echo "  🔴 Bridge: nem fut"
    fi
    echo "  ─────────────────────────────────────────────────"
    if is_hud_running; then
        echo "  🟢 HUD:    FUT (PID $(cat $HUD_PID_FILE))"
        echo "     Log: $HUD_LOG"
    else
        echo "  🔴 HUD:    nem fut"
    fi
    echo "═══════════════════════════════════════════════════"
}

# ─── FŐ LOGIKA ───
case "${1:-start}" in
    start)
        echo "╔═══════════════════════════════════════════════════╗"
        echo "║   Scalper V6 Bridge + HUD INDÍTÁSA               ║"
        echo "╚═══════════════════════════════════════════════════╝"
        start_bridge
        start_hud
        echo ""
        show_status
        echo ""
        echo "🎯 Leállítás: $0 stop"
        echo "📊 Státusz:   $0 status"
        ;;
    stop)
        echo "╔═══════════════════════════════════════════════════╗"
        echo "║   Scalper V6 Bridge + HUD LEÁLLÍTÁSA            ║"
        echo "╚═══════════════════════════════════════════════════╝"
        stop_hud
        stop_bridge
        echo ""
        show_status
        ;;
    restart)
        echo "🔄 Újraindítás..."
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        show_status
        ;;
    *)
        echo "Használat: $0 {start|stop|restart|status}"
        echo "  start   (alapértelmezett) — bridge + HUD indítása"
        echo "  stop    — bridge + HUD leállítása"
        echo "  restart — újraindítás"
        echo "  status  — státusz lekérdezése"
        echo ""
        echo "Architektúra (ÉLŐ):"
        echo "  TCP port 5556 — Merkava EA csatlakozik ide (kliens)"
        echo "  ZMQ port 5557 — HUD SUB ide csatlakozik"
        echo "  LGBM modellek: BTCUSD_v6_{long,short}_2min_shap.txt"
        echo "  QT_QPA_PLATFORM=offscreen — láthatatlan HUD (debug)"
        exit 1
        ;;
esac
