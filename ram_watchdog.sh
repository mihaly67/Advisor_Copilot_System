#!/bin/bash
# RAM watchdog — cron-ból fut, figyeli a memóriát és takarít ha kell
# Ha buff/cache > 20GB és free < 5GB → drop_caches
# Ha swap használat > 2GB → figyelmeztet

TOTAL=$(free -m | awk '/^Mem:/{print $2}')
USED=$(free -m | awk '/^Mem:/{print $3}')
FREE=$(free -m | awk '/^Mem:/{print $4}')
CACHE=$(free -m | awk '/^Mem:/{print $6}')
SWAP_USED=$(free -m | awk '/^Swap:/{print $3}')

TIMESTAMP=$(date '+%Y-%m-%d %H:%M')

# Drop caches if cache > 20GB and free < 5GB
if [ "$CACHE" -gt 20480 ] && [ "$FREE" -lt 5120 ]; then
    echo "$TIMESTAMP CACHE=$(${CACHE}MB) FREE=$(${FREE}MB) → dropping caches"
    sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches' 2>/dev/null
else
    echo "$TIMESTAMP OK used=${USED}MB free=${FREE}MB cache=${CACHE}MB swap=${SWAP_USED}MB"
fi

# Alert if swap > 2GB
if [ "$SWAP_USED" -gt 2048 ]; then
    echo "$TIMESTAMP ⚠️ SWAP ALERT: ${SWAP_USED}MB in swap!"
    # Kill biggest memory hog if swap > 5GB
    if [ "$SWAP_USED" -gt 5120 ]; then
        HOG_PID=$(ps aux --sort=-%mem | awk 'NR==2{print $2}')
        HOG_CMD=$(ps aux --sort=-%mem | awk 'NR==2{print $11}')
        echo "$TIMESTAMP 🔴 Killing $HOG_CMD (PID $HOG_PID) — swap critical"
        kill $HOG_PID 2>/dev/null
    fi
fi
