#!/bin/bash
### BEGIN INIT INFO
# Provides:          mcp-backend
# Required-Start:    $network $local_fs
# Required-Stop:     $network $local_fs
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: MCP Backend API (visualization + cognitive memory)
# Description:       Always-on HTTP service on port 8420 for HTML rendering,
#                    image analysis, yantrikdb, cortexdb, and GraphRAG.
### END INIT INFO

DAEMON="/home/Jules/jules_venv/bin/python3"
DAEMON_ARGS="/data/mcp_server/mcp_backend_api.py"
PIDFILE="/data/mcp_server/lock/mcp-backend.pid"
LOGFILE="/data/mcp_server/logs/mcp-backend.log"
ENVFILE="/data/mcp_server/env.sh"

case "$1" in
  start)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat $PIDFILE)" 2>/dev/null; then
      echo "mcp-backend already running (PID $(cat $PIDFILE))"
      exit 0
    fi
    echo "Starting mcp-backend..."
    source "$ENVFILE" 2>/dev/null
    nohup $DAEMON $DAEMON_ARGS >> "$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    echo "Started with PID $(cat $PIDFILE) on port 8420"
    ;;
  stop)
    if [ -f "$PIDFILE" ]; then
      PID=$(cat "$PIDFILE")
      kill "$PID" 2>/dev/null && echo "Stopped mcp-backend (PID $PID)" || echo "Process not found"
      rm -f "$PIDFILE"
    else
      echo "mcp-backend not running (no PID file)"
    fi
    ;;
  restart)
    $0 stop; sleep 1; $0 start
    ;;
  status)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat $PIDFILE)" 2>/dev/null; then
      echo "mcp-backend running (PID $(cat $PIDFILE))"
    else
      echo "mcp-backend not running"
    fi
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
    ;;
esac
