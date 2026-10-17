#!/bin/bash
### BEGIN INIT INFO
# Provides:          cortexdb-grpc
# Required-Start:    $network $local_fs
# Required-Stop:     $network $local_fs
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: CortexDB gRPC Shared Brain Server
# Description:       gRPC server on :47821 for shared cognitive memory across agents.
### END INIT INFO

DAEMON="/home/Jules/go/bin/cortexdb-grpc"
DAEMON_ARGS="-db /data/mcp_server/data/cortexdb_shared.db -addr 127.0.0.1:47821 -token ''"
PIDFILE="/data/mcp_server/lock/cortexdb-grpc.pid"
LOGFILE="/data/mcp_server/logs/cortexdb-grpc.log"

case "$1" in
  start)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat $PIDFILE)" 2>/dev/null; then
      echo "cortexdb-grpc already running (PID $(cat $PIDFILE))"
      exit 0
    fi
    echo "Starting cortexdb-grpc..."
    nohup $DAEMON $DAEMON_ARGS >> "$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    echo "Started with PID $(cat $PIDFILE) on port 47821"
    ;;
  stop)
    if [ -f "$PIDFILE" ]; then
      PID=$(cat "$PIDFILE")
      kill "$PID" 2>/dev/null && echo "Stopped cortexdb-grpc (PID $PID)" || echo "Process not found"
      rm -f "$PIDFILE"
    else
      echo "cortexdb-grpc not running (no PID file)"
    fi
    ;;
  restart)
    $0 stop; sleep 1; $0 start
    ;;
  status)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat $PIDFILE)" 2>/dev/null; then
      echo "cortexdb-grpc running (PID $(cat $PIDFILE))"
    else
      echo "cortexdb-grpc not running"
    fi
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
    ;;
esac
