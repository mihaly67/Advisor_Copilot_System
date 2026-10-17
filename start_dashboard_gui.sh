#!/bin/bash
#
# EGY KATTINTÁSOS INDÍTÓ - Valós Idejű Dashboard (PyQt6)
#
# Használat:  bash /data/mcp_server/start_dashboard_gui.sh
# Vagy:        kattints rá a fájlkezelőben
#
cd /data/mcp_server/tools/qwen_assistant

# QPA platform (X11/Wayland detektálás)
if [ -z "$DISPLAY" ] && [ -n "$WAYLAND_DISPLAY" ]; then
    export QT_QPA_PLATFORM=wayland
fi

python3 realtime_dashboard_gui.py
