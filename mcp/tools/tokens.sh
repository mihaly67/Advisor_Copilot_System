#!/bin/bash
# Token számláló indító — aliassegéd
# Használat:
#   tokens              — egyszeri jelentés
#   tokens today        — csak mai
#   tokens watch        — élő figyelés
#   tokens warn 4000    — figyelmeztet 4000 token felett
CMD="$1"
case "$CMD" in
    today)
        python3 /data/mcp_server/tools/token_counter.py --today
        ;;
    watch)
        python3 /data/mcp_server/tools/token_counter.py --watch
        ;;
    warn)
        LIMIT="${2:-4000}"
        python3 /data/mcp_server/tools/token_counter.py --watch --warn "$LIMIT"
        ;;
    *)
        python3 /data/mcp_server/tools/token_counter.py
        ;;
esac
