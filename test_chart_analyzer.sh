#!/bin/bash
# Chart analyzer test script
cd /data/mcp_server
VENV=/data/mcp_server/venv/bin/python

echo "=== Test 1: Regex on viz_pred_2026-08-28.html ==="
timeout 20 $VENV -c "
from chart_analyzer import analyze
import json, time
t0 = time.time()
r = analyze(html_path='/data/dev/LGB_copilot_system/viz/viz_pred_2026-08-28.html', method='regex')
print(f'Time: {time.time()-t0:.1f}s')
print(json.dumps(r.get('summary',{}), ensure_ascii=False, indent=2))
" 2>&1

echo ""
echo "=== Test 2: Playwright DOM on viz_pred_2026-08-28.html ==="
timeout 30 $VENV -c "
from chart_analyzer import analyze
import json, time
t0 = time.time()
r = analyze(html_path='/data/dev/LGB_copilot_system/viz/viz_pred_2026-08-28.html', method='playwright')
print(f'Time: {time.time()-t0:.1f}s')
if 'playwright_analysis' in r:
    pa = r['playwright_analysis']
    if 'error' in pa:
        print(f'Playwright error: {pa[\"error\"]}')
    else:
        print(json.dumps(pa.get('plots',{}), ensure_ascii=False, indent=2, default=str)[:2000])
else:
    print('No playwright result')
" 2>&1
